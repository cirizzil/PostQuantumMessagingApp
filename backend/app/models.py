from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from bson import ObjectId
import re


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, _field_schema):
        return {"type": "string"}


# User Models
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=8, max_length=128)
    area_code: str = Field(..., min_length=1, max_length=5, description="Area code (e.g., +1, +44)")
    phone_number: str = Field(..., min_length=7, max_length=15, description="Phone number (7-15 digits)")
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength requirements"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        # Check for at least one digit
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one digit")
        
        # Check for at least one special character (including underscore, dash, etc.)
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\/;~`]', v):
            raise ValueError("Password must contain at least one special character")
        
        return v
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("Username can only contain letters, numbers, and underscores")
        return v
    
    @field_validator('area_code')
    @classmethod
    def validate_area_code(cls, v: str) -> str:
        """Validate area code format (e.g., +1, +44, +91)"""
        if not re.match(r'^\+\d{1,4}$', v):
            raise ValueError("Area code must start with + followed by 1-4 digits (e.g., +1, +44)")
        return v
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """Validate phone number is numerical only"""
        if not re.match(r'^\d+$', v):
            raise ValueError("Phone number must contain only numbers")
        if len(v) < 7:
            raise ValueError("Phone number must be at least 7 digits")
        if len(v) > 15:
            raise ValueError("Phone number must be at most 15 digits")
        return v


class UserLogin(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class User(BaseModel):
    id: Optional[PyObjectId] = None
    username: str
    password_hash: str
    created_at: datetime = datetime.utcnow()

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


class UserResponse(BaseModel):
    id: str
    username: str
    area_code: Optional[str] = None  # Only return if user wants to share
    secret_code: Optional[str] = None  # Only return if user wants to share
    created_at: datetime

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


class UserSearchRequest(BaseModel):
    area_code: str = Field(..., description="Area code (e.g., +1, +44)")
    phone_number: str = Field(..., description="Phone number (7-15 digits)")


# Message Models
class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)  # Max 10KB message
    recipient_id: str  # ID of the user to send the message to


class Message(BaseModel):
    id: Optional[PyObjectId] = None
    user_id: PyObjectId
    username: str
    content_encrypted: bytes  # Encrypted content
    nonce: bytes  # For AES-GCM
    auth_tag: bytes  # For AES-GCM
    timestamp: datetime = datetime.utcnow()

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


class MessageResponse(BaseModel):
    id: str
    username: str
    content: str  # Decrypted content
    timestamp: datetime
    sender_id: str
    recipient_id: str

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


# Message Request Models
class MessageRequestResponse(BaseModel):
    id: str
    sender_id: str
    sender_username: str
    recipient_id: str
    content: str  # Decrypted preview
    timestamp: datetime
    status: str  # "pending", "accepted", "declined"

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


class MessageRequestAction(BaseModel):
    request_id: str
    action: str  # "accept" or "decline"


# Token Models
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None

