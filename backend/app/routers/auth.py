from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta
from app.models import UserCreate, UserLogin, Token, UserResponse
from app.auth import verify_password, get_password_hash, create_access_token, get_current_user
from app.config import settings
from app.database import database
from bson import ObjectId

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user"""
    # Check if user already exists
    existing_user = await database.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Hash password
    password_hash = get_password_hash(user_data.password)
    
    # Create user document
    from datetime import datetime
    user_doc = {
        "username": user_data.username,
        "password_hash": password_hash,
        "created_at": datetime.utcnow()
    }
    
    # Insert user
    result = await database.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    
    return UserResponse(
        id=str(user_doc["_id"]),
        username=user_doc["username"],
        created_at=user_doc.get("created_at")
    )


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """Login and get access token"""
    # Find user
    user = await database.users.find_one({"username": user_data.username})
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
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=str(current_user["_id"]),
        username=current_user["username"],
        created_at=current_user.get("created_at")
    )

