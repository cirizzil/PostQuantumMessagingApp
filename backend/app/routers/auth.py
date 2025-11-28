from fastapi import APIRouter, HTTPException, status, Depends, Response, Request
from fastapi.responses import JSONResponse
from datetime import timedelta
from typing import List
from app.models import UserCreate, UserLogin, Token, UserResponse, UserSearchRequest
from app.auth import verify_password, get_password_hash, create_access_token, get_current_user
from app.config import settings
from app import database as db_module
from app.rate_limiter import check_rate_limit
from app.session_manager import clear_session_key
from bson import ObjectId

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: Request, user_data: UserCreate):
    """Register a new user with rate limiting (5 per minute per IP)"""
    check_rate_limit(request, "5/minute")
    # Check if user already exists
    if db_module.database is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    existing_user = await db_module.database.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if phone number is already taken (area_code + phone_number must be unique)
    full_phone = f"{user_data.area_code}{user_data.phone_number}"
    existing_phone = await db_module.database.users.find_one({"full_phone_number": full_phone})
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This phone number is already registered. Please use a different number."
        )
    
    # Hash password
    password_hash = get_password_hash(user_data.password)
    
    # Create user document
    from datetime import datetime
    full_phone_number = f"{user_data.area_code}{user_data.phone_number}"
    user_doc = {
        "username": user_data.username,
        "password_hash": password_hash,
        "area_code": user_data.area_code,
        "phone_number": user_data.phone_number,
        "full_phone_number": full_phone_number,  # Combined for easy lookup
        "created_at": datetime.utcnow()
    }
    
    # Insert user
    result = await db_module.database.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    
    return UserResponse(
        id=str(user_doc["_id"]),
        username=user_doc["username"],
        created_at=user_doc.get("created_at")
    )


@router.post("/login", response_model=UserResponse)
async def login(request: Request, response: Response, user_data: UserLogin):
    """Login and set access token in httpOnly cookie with rate limiting (10 per minute per IP)"""
    check_rate_limit(request, "10/minute")
    # Find user
    user = await db_module.database.users.find_one({"username": user_data.username})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Verify password
    if not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=access_token_expires
    )
    
    # Set token in httpOnly cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.jwt_access_token_expire_minutes * 60,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax"
    )
    
    return UserResponse(
        id=str(user["_id"]),
        username=user["username"],
        created_at=user.get("created_at")
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=str(current_user["_id"]),
        username=current_user["username"],
        created_at=current_user.get("created_at")
    )


@router.post("/logout")
async def logout(response: Response, current_user: dict = Depends(get_current_user)):
    """Logout and clear access token cookie"""
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    return {"message": "Logged out successfully"}


@router.get("/ws-token")
async def get_websocket_token(
    current_user: dict = Depends(get_current_user)
):
    """Get a token for WebSocket authentication"""
    from datetime import timedelta
    
    # Create a short-lived token for WebSocket (1 hour)
    token = create_access_token(
        data={"sub": current_user["username"]},
        expires_delta=timedelta(hours=1)
    )
    
    return {"token": token, "user_id": str(current_user["_id"])}


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all users (excluding the current user).
    Returns a list of all registered users.
    """
    current_user_id_obj = ObjectId(current_user["_id"])
    
    # Find all users except the current user
    cursor = db_module.database.users.find({
        "_id": {"$ne": current_user_id_obj}
    }).sort("username", 1)
    
    users = await cursor.to_list(length=1000)
    
    return [
        UserResponse(
            id=str(user["_id"]),
            username=user["username"],
            created_at=user.get("created_at")
        )
        for user in users
    ]


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: str,
    response: Response,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a user account and all associated data.
    
    Any authenticated user can delete any other user's account. This will:
    - Delete the user from the database
    - Delete all messages where the user is sender or recipient
    - Delete all message requests where the user is sender or recipient
    - Clear the user's session keys
    - If deleting own account: Clear the access token cookie (logout)
    """
    # Validate user_id format
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user_id_obj = ObjectId(user_id)
    current_user_id_obj = ObjectId(current_user["_id"])
    is_deleting_self = user_id_obj == current_user_id_obj
    
    # Verify user exists
    user = await db_module.database.users.find_one({"_id": user_id_obj})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # 1. Delete all messages where user is sender or recipient
        messages_result = await db_module.database.messages.delete_many({
            "$or": [
                {"sender_id": user_id_obj},
                {"recipient_id": user_id_obj}
            ]
        })
        print(f"[DELETE_USER] Deleted {messages_result.deleted_count} messages")
        
        # 2. Delete all message requests where user is sender or recipient
        requests_result = await db_module.database.message_requests.delete_many({
            "$or": [
                {"sender_id": user_id_obj},
                {"recipient_id": user_id_obj}
            ]
        })
        print(f"[DELETE_USER] Deleted {requests_result.deleted_count} message requests")
        
        # 3. Clear session keys
        clear_session_key(user_id)
        print(f"[DELETE_USER] Cleared session keys for user {user_id}")
        
        # 4. Delete the user
        await db_module.database.users.delete_one({"_id": user_id_obj})
        print(f"[DELETE_USER] Deleted user {user['username']} (ID: {user_id}) by {current_user['username']}")
        
        # 5. Clear access token cookie (logout) only if deleting own account
        if is_deleting_self and response:
            response.delete_cookie(key="access_token", httponly=True, samesite="lax")
        
        return {
            "message": "User account deleted successfully",
            "deleted_messages": messages_result.deleted_count,
            "deleted_requests": requests_result.deleted_count,
            "deleted_user": user["username"]
        }
        
    except Exception as e:
        print(f"[DELETE_USER] Error deleting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


