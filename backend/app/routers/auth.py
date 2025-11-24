from fastapi import APIRouter, HTTPException, status, Depends, Response, Request
from fastapi.responses import JSONResponse
from datetime import timedelta
from typing import List
from app.models import UserCreate, UserLogin, Token, UserResponse, UserSearchRequest
from app.auth import verify_password, get_password_hash, create_access_token, get_current_user
from app.config import settings
from app import database as db_module
from app.rate_limiter import check_rate_limit
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
    
    # STEP 4: Generate Post-Quantum Key Pair for New User
    # ---------------------------------------------------
    # Generate post-quantum key pair for secure message exchange
    from app.post_quantum import PostQuantumKEM, encrypt_private_key
    import base64
    
    public_key, private_key = PostQuantumKEM.generate_keypair()
    
    # Encrypt private key with user's password for secure storage
    encrypted_private_key = encrypt_private_key(private_key, user_data.password)
    
    # Encode keys as base64 for database storage
    public_key_b64 = base64.b64encode(public_key).decode('utf-8')
    encrypted_private_key_b64 = base64.b64encode(encrypted_private_key).decode('utf-8')
    
    # Create user document
    from datetime import datetime
    full_phone_number = f"{user_data.area_code}{user_data.phone_number}"
    user_doc = {
        "username": user_data.username,
        "password_hash": password_hash,
        "area_code": user_data.area_code,
        "phone_number": user_data.phone_number,
        "full_phone_number": full_phone_number,  # Combined for easy lookup
        "pq_public_key": public_key_b64,  # Post-quantum public key (shareable)
        "pq_private_key_encrypted": encrypted_private_key_b64,  # Encrypted private key
        "pq_keys_generated_at": datetime.utcnow(),  # Track when keys were generated
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
    
    # STEP 7.5: Decrypt and Cache Private Key After Login
    # ---------------------------------------------------
    # Decrypt user's post-quantum private key and cache it for message decryption
    # This allows decryption without asking for password every time
    from app.key_manager import decrypt_and_cache_private_key
    
    try:
        if "pq_private_key_encrypted" in user:
            decrypt_and_cache_private_key(user, user_data.password)
            print(f"Successfully cached private key for user {user['username']}")
        else:
            print(f"Warning: User {user['username']} does not have post-quantum keys")
    except Exception as e:
        # Log error but don't fail login - user can still use the app
        # but won't be able to decrypt old messages until they re-authenticate
        import traceback
        print(f"ERROR: Failed to cache private key for user {user['username']}: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        # Don't raise - allow login to proceed, but user won't be able to decrypt messages
    
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
    """Logout and clear access token cookie and cached keys"""
    # Clear cached private key
    from app.key_manager import clear_user_keys
    user_id = str(current_user["_id"])
    clear_user_keys(user_id)
    
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    return {"message": "Logged out successfully"}


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


@router.get("/users/{user_id}/public-key")
async def get_user_public_key(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    STEP 7.6: Get User Public Key Endpoint
    ---------------------------------------
    Retrieves a user's post-quantum public key for message encryption.
    Public keys are safe to share and are needed to encrypt messages.
    
    Args:
        user_id: ID of the user whose public key to retrieve
    
    Returns:
        JSON with public_key (base64 encoded)
    """
    # Validate user_id
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    user_id_obj = ObjectId(user_id)
    
    # Find user
    user = await db_module.database.users.find_one({"_id": user_id_obj})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user has post-quantum keys
    if "pq_public_key" not in user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have post-quantum keys"
        )
    
    return {
        "user_id": str(user["_id"]),
        "username": user["username"],
        "public_key": user["pq_public_key"],  # Already base64 encoded
        "key_algorithm": "CRYSTALS-Kyber-768",
        "key_generated_at": user.get("pq_keys_generated_at")
    }
