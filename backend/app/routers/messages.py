from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime
from typing import List
from app.models import MessageCreate, MessageResponse
from app.auth import get_current_user
from app.encryption import encrypt_message, decrypt_message
from app.database import database
from bson import ObjectId, Binary

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate,
    current_user: dict = Depends(get_current_user)
):
    """Send a message to the global chat"""
    if not message_data.content or not message_data.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty"
        )
    
    # Encrypt the message content
    ciphertext, nonce, auth_tag = encrypt_message(message_data.content)
    
    # Create message document
    # Store binary data as Binary for proper MongoDB handling
    message_doc = {
        "user_id": ObjectId(current_user["_id"]),
        "username": current_user["username"],
        "content_encrypted": Binary(ciphertext),
        "nonce": Binary(nonce),
        "auth_tag": Binary(auth_tag),
        "timestamp": datetime.utcnow()
    }
    
    # Insert message
    result = await database.messages.insert_one(message_doc)
    message_doc["_id"] = result.inserted_id
    
    # Return decrypted message for response
    return MessageResponse(
        id=str(message_doc["_id"]),
        username=message_doc["username"],
        content=message_data.content,  # Return original plaintext
        timestamp=message_doc["timestamp"]
    )


@router.get("", response_model=List[MessageResponse])
async def get_messages(
    limit: int = Query(default=50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get recent messages from the global chat"""
    # Fetch messages from database, sorted by timestamp descending
    cursor = database.messages.find().sort("timestamp", -1).limit(limit)
    messages = await cursor.to_list(length=limit)
    
    # Decrypt and format messages
    decrypted_messages = []
    for msg in reversed(messages):  # Reverse to show oldest first
        try:
            # Handle MongoDB Binary type if present
            ciphertext = msg["content_encrypted"]
            nonce = msg["nonce"]
            auth_tag = msg["auth_tag"]
            
            # Convert Binary to bytes if needed
            if isinstance(ciphertext, Binary):
                ciphertext = ciphertext.as_bytes()
            if isinstance(nonce, Binary):
                nonce = nonce.as_bytes()
            if isinstance(auth_tag, Binary):
                auth_tag = auth_tag.as_bytes()
            
            decrypted_content = decrypt_message(ciphertext, nonce, auth_tag)
            decrypted_messages.append(MessageResponse(
                id=str(msg["_id"]),
                username=msg["username"],
                content=decrypted_content,
                timestamp=msg["timestamp"]
            ))
        except Exception as e:
            # If decryption fails, skip the message (or log error)
            print(f"Failed to decrypt message {msg['_id']}: {e}")
            continue
    
    return decrypted_messages

