from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from bson import ObjectId


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
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


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
    created_at: datetime

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


# Message Models
class MessageCreate(BaseModel):
    content: str


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

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


# Token Models
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None

