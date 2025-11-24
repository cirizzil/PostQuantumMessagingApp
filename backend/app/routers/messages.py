from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime
from typing import List
from app.models import MessageCreate, MessageResponse, MessageRequestResponse, MessageRequestAction
from app.auth import get_current_user
from app.encryption import encrypt_message, decrypt_message  # Legacy support
from app.pq_encryption import encrypt_message_pq, decrypt_message_pq, get_user_public_key, get_user_private_key
from app import database as db_module
from bson import ObjectId, Binary
import base64

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate,
    current_user: dict = Depends(get_current_user)
):
    """Send a message to a specific user"""
    if not message_data.content or not message_data.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty"
        )
    
    # Validate recipient_id
    if not ObjectId.is_valid(message_data.recipient_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid recipient ID"
        )
    
    recipient_id = ObjectId(message_data.recipient_id)
    
    # Check if recipient exists
    recipient = await db_module.database.users.find_one({"_id": recipient_id})
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient user not found"
        )
    
    # Don't allow sending to yourself
    if recipient_id == ObjectId(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send message to yourself"
        )
    
    # Check if users have previously messaged each other
    # If not, create a message request instead of a direct message
    current_user_id_obj = ObjectId(current_user["_id"])
    existing_conversation = await db_module.database.messages.find_one({
        "$or": [
            {
                "sender_id": current_user_id_obj,
                "recipient_id": recipient_id
            },
            {
                "sender_id": recipient_id,
                "recipient_id": current_user_id_obj
            }
        ]
    })
    
    # If no existing conversation, create a message request
    if not existing_conversation:
        # Check if recipient has post-quantum keys
        if "pq_public_key" not in recipient:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recipient does not have post-quantum keys. They may need to re-register."
            )
        
        try:
            # Get recipient's public key
            recipient_public_key = get_user_public_key(recipient)
            
            # Encrypt message using post-quantum key exchange
            ciphertext, nonce, auth_tag, kem_ciphertext = encrypt_message_pq(
                message_data.content,
                recipient_public_key
            )
            
            # Create message request document
            # Store plaintext for sender so they can see their own messages
            request_doc = {
                "sender_id": ObjectId(current_user["_id"]),
                "sender_username": current_user["username"],
                "recipient_id": recipient_id,
                "recipient_username": recipient["username"],
                "content_encrypted": Binary(ciphertext),  # Encrypted for recipient
                "content_plaintext": message_data.content,  # Plaintext for sender
                "nonce": Binary(nonce),
                "auth_tag": Binary(auth_tag),
                "kem_ciphertext": Binary(kem_ciphertext),
                "encryption_type": "post_quantum",
                "status": "pending",
                "timestamp": datetime.utcnow()
            }
            
            # Insert message request
            result = await db_module.database.message_requests.insert_one(request_doc)
            
            print(f"[MESSAGE_REQUEST] Created request: ID={result.inserted_id}, From={current_user['username']}, To={recipient['username']}")
            
            return MessageResponse(
                id=str(result.inserted_id),
                username=current_user["username"],
                content=message_data.content,  # Return original plaintext
                timestamp=request_doc["timestamp"],
                sender_id=str(current_user["_id"]),
                recipient_id=str(recipient_id)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create message request: {str(e)}"
            )
    
    # STEP 5: Post-Quantum Message Encryption (for existing conversations)
    # ----------------------------------------
    # Check if recipient has post-quantum keys
    if "pq_public_key" not in recipient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recipient does not have post-quantum keys. They may need to re-register."
        )
    
    try:
        # Get recipient's public key
        recipient_public_key = get_user_public_key(recipient)
        
        # Encrypt message using post-quantum key exchange
        ciphertext, nonce, auth_tag, kem_ciphertext = encrypt_message_pq(
            message_data.content,
            recipient_public_key
        )
        
        # Create message document with post-quantum encryption
        # Store plaintext for sender so they can see their own messages
        message_doc = {
            "sender_id": ObjectId(current_user["_id"]),
            "sender_username": current_user["username"],
            "recipient_id": recipient_id,
            "recipient_username": recipient["username"],
            "content_encrypted": Binary(ciphertext),  # Encrypted for recipient
            "content_plaintext": message_data.content,  # Plaintext for sender to see their own messages
            "nonce": Binary(nonce),
            "auth_tag": Binary(auth_tag),
            "kem_ciphertext": Binary(kem_ciphertext),  # Post-quantum KEM ciphertext
            "encryption_type": "post_quantum",  # Mark as post-quantum encrypted
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to encrypt message: {str(e)}"
        )
    
    # Insert message
    result = await db_module.database.messages.insert_one(message_doc)
    message_doc["_id"] = result.inserted_id
    
    print(f"Message sent: ID={message_doc['_id']}, From={current_user['username']}, To={recipient['username']}, Has plaintext={'content_plaintext' in message_doc}")
    
    # Return decrypted message for response
    return MessageResponse(
        id=str(message_doc["_id"]),
        username=message_doc["sender_username"],
        content=message_data.content,  # Return original plaintext
        timestamp=message_doc["timestamp"],
        sender_id=str(message_doc["sender_id"]),
        recipient_id=str(message_doc["recipient_id"])
    )


@router.get("", response_model=List[MessageResponse])
async def get_messages(
    other_user_id: str = Query(..., description="ID of the other user in the conversation"),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get messages from a conversation with another user"""
    # Validate other_user_id
    if not ObjectId.is_valid(other_user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    other_user_id_obj = ObjectId(other_user_id)
    current_user_id_obj = ObjectId(current_user["_id"])
    
    # Fetch messages where current user is either sender or recipient with the other user
    # This gets the conversation between the two users
    query = {
        "$or": [
            {
                "sender_id": current_user_id_obj,
                "recipient_id": other_user_id_obj
            },
            {
                "sender_id": other_user_id_obj,
                "recipient_id": current_user_id_obj
            }
        ]
    }
    
    # Fetch messages from database, sorted by timestamp descending
    cursor = db_module.database.messages.find(query).sort("timestamp", -1).limit(limit)
    messages = await cursor.to_list(length=limit)
    
    # Debug: Log how many messages were found
    print(f"[GET_MESSAGES] Found {len(messages)} raw messages for conversation between {current_user['username']} (ID: {current_user['_id']}) and user {other_user_id}")
    if len(messages) > 0:
        for i, msg in enumerate(messages[:3]):  # Show first 3
            print(f"  Message {i+1}: ID={msg['_id']}, Sender={msg.get('sender_id')}, Recipient={msg.get('recipient_id')}, Has plaintext={'content_plaintext' in msg}")
    
    # STEP 6: Post-Quantum Message Decryption
    # ----------------------------------------
    # Get current user's private key (need to decrypt it)
    # Note: In production, you might want to cache the decrypted private key
    # after login, or use a different key management approach
    
    # Check if current user has post-quantum keys
    if "pq_private_key_encrypted" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your account does not have post-quantum keys. Please contact support."
        )
    
    # For now, we'll need the user's password to decrypt their private key
    # In a real implementation, you might:
    # 1. Decrypt private key at login and store in session (less secure)
    # 2. Use a master key approach
    # 3. Ask for password when needed (better security, worse UX)
    # 
    # For this implementation, we'll try to decrypt with a cached approach
    # You'll need to implement password caching or re-authentication
    
    decrypted_messages = []
    print(f"[GET_MESSAGES] Processing {len(messages)} messages for decryption...")
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
            
            # Check encryption type
            encryption_type = msg.get("encryption_type", "legacy")
            
            if encryption_type == "post_quantum":
                # Post-quantum decryption
                if "kem_ciphertext" not in msg:
                    raise ValueError("Missing KEM ciphertext for post-quantum message")
                
                kem_ciphertext = msg["kem_ciphertext"]
                if isinstance(kem_ciphertext, Binary):
                    kem_ciphertext = kem_ciphertext.as_bytes()
                
                # Get user's private key from cache (decrypted at login)
                from app.key_manager import get_cached_private_key
                
                # Determine which user's private key we need
                # Messages are encrypted with the RECIPIENT's public key
                # So we can only decrypt messages where we are the recipient
                recipient_id_obj = msg.get("recipient_id")
                sender_id_obj = msg.get("sender_id")
                current_user_id_obj = ObjectId(current_user["_id"])
                
                # Check if we are the recipient (can decrypt) or sender (cannot decrypt)
                if recipient_id_obj == current_user_id_obj:
                    # We are the recipient - we can decrypt this message
                    user_id = str(current_user["_id"])
                    private_key = get_cached_private_key(user_id)
                    
                    if private_key is None:
                        # Private key not cached - this is a critical error
                        # Return a helpful error message instead of skipping silently
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Cannot decrypt messages: private key not available. Please log out and log in again to cache your private key."
                        )
                    
                    # Decrypt using post-quantum
                    decrypted_content = decrypt_message_pq(
                        ciphertext, nonce, auth_tag, kem_ciphertext, private_key
                    )
                elif sender_id_obj == current_user_id_obj:
                    # We are the sender - use stored plaintext if available
                    # Otherwise try to decrypt (might fail if keys don't match)
                    if "content_plaintext" in msg:
                        decrypted_content = msg["content_plaintext"]
                    else:
                        # Fallback: try to decrypt (will likely fail with InvalidTag)
                        # But we'll catch the error and show a placeholder
                        try:
                            # Try to decrypt - this will likely fail but worth trying
                            user_id = str(current_user["_id"])
                            private_key = get_cached_private_key(user_id)
                            if private_key:
                                decrypted_content = decrypt_message_pq(
                                    ciphertext, nonce, auth_tag, kem_ciphertext, private_key
                                )
                            else:
                                decrypted_content = "[Message sent - unable to decrypt]"
                        except:
                            decrypted_content = "[Message sent - content encrypted for recipient]"
                else:
                    # This shouldn't happen - message is neither from us nor to us
                    raise ValueError(f"Cannot decrypt message: current user is neither sender nor recipient")
            else:
                # Legacy decryption (backward compatibility)
                decrypted_content = decrypt_message(ciphertext, nonce, auth_tag)
            
            decrypted_messages.append(MessageResponse(
                id=str(msg["_id"]),
                username=msg["sender_username"],
                content=decrypted_content,
                timestamp=msg["timestamp"],
                sender_id=str(msg["sender_id"]),
                recipient_id=str(msg["recipient_id"])
            ))
            print(f"  [SUCCESS] Decrypted message {msg['_id']}: {decrypted_content[:50]}...")
        except HTTPException:
            # Re-raise HTTP exceptions (like 401 for missing key) - don't skip
            raise
        except Exception as e:
            # If decryption fails for other reasons, log error but still include message with error indicator
            import traceback
            from app.key_manager import get_cached_private_key
            user_id = str(current_user["_id"])
            cached_key = get_cached_private_key(user_id)
            
            print(f"[ERROR] Failed to decrypt message {msg['_id']}: {e}")
            print(f"  Error type: {type(e).__name__}")
            print(f"  User: {current_user['username']} (ID: {current_user['_id']})")
            print(f"  Has cached key: {cached_key is not None}")
            print(f"  Sender ID: {msg.get('sender_id')}, Recipient ID: {msg.get('recipient_id')}")
            print(f"  Current user is sender: {sender_id_obj == current_user_id_obj}")
            print(f"  Current user is recipient: {recipient_id_obj == current_user_id_obj}")
            
            # If we're the sender and have plaintext, use it
            if sender_id_obj == current_user_id_obj and "content_plaintext" in msg:
                decrypted_content = msg["content_plaintext"]
                print(f"  -> Using stored plaintext for sender")
            else:
                # For recipient, show error message so they know something went wrong
                decrypted_content = f"[Unable to decrypt message - please log out and log back in]"
                print(f"  -> Showing error message to recipient")
            
            # Still add the message so user knows it exists
            decrypted_messages.append(MessageResponse(
                id=str(msg["_id"]),
                username=msg["sender_username"],
                content=decrypted_content,
                timestamp=msg["timestamp"],
                sender_id=str(msg["sender_id"]),
                recipient_id=str(msg["recipient_id"])
            ))
            continue
    
    print(f"[GET_MESSAGES] Returning {len(decrypted_messages)} decrypted messages (out of {len(messages)} total)")
    return decrypted_messages


@router.get("/requests", response_model=List[MessageRequestResponse])
async def get_message_requests(
    current_user: dict = Depends(get_current_user)
):
    """Get pending message requests for the current user"""
    current_user_id_obj = ObjectId(current_user["_id"])
    
    # Find all pending requests for current user (as recipient)
    cursor = db_module.database.message_requests.find({
        "recipient_id": current_user_id_obj,
        "status": "pending"
    }).sort("timestamp", -1)
    
    requests = await cursor.to_list(length=100)
    
    # If no requests found, return empty list
    if not requests:
        return []
    
    # Decrypt request previews
    decrypted_requests = []
    
    # Check if current user has post-quantum keys
    if "pq_private_key_encrypted" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your account does not have post-quantum keys. Please contact support."
        )
    
    from app.key_manager import get_cached_private_key
    user_id = str(current_user["_id"])
    private_key = get_cached_private_key(user_id)
    
    if private_key is None:
        # Return empty list instead of error - user might not have cached key yet
        # They can log in again to cache it
        return []
    
    for req in requests:
        try:
            # Handle MongoDB Binary type
            ciphertext = req["content_encrypted"]
            nonce = req["nonce"]
            auth_tag = req["auth_tag"]
            kem_ciphertext = req["kem_ciphertext"]
            
            if isinstance(ciphertext, Binary):
                ciphertext = ciphertext.as_bytes()
            if isinstance(nonce, Binary):
                nonce = nonce.as_bytes()
            if isinstance(auth_tag, Binary):
                auth_tag = auth_tag.as_bytes()
            if isinstance(kem_ciphertext, Binary):
                kem_ciphertext = kem_ciphertext.as_bytes()
            
            # Decrypt request content
            decrypted_content = decrypt_message_pq(
                ciphertext, nonce, auth_tag, kem_ciphertext, private_key
            )
            
            decrypted_requests.append(MessageRequestResponse(
                id=str(req["_id"]),
                sender_id=str(req["sender_id"]),
                sender_username=req["sender_username"],
                recipient_id=str(req["recipient_id"]),
                content=decrypted_content,
                timestamp=req["timestamp"],
                status=req["status"]
            ))
        except Exception as e:
            import traceback
            print(f"[ERROR] Failed to decrypt request {req['_id']}: {e}")
            print(f"  Error type: {type(e).__name__}")
            print(f"  Request sender: {req.get('sender_username')}, recipient: {req.get('recipient_username')}")
            print(f"  Current user: {current_user['username']} (ID: {current_user['_id']})")
            print(f"  Has cached key: {private_key is not None}")
            # Check if it's a key issue
            if "private key" in str(e).lower() or "key" in str(e).lower() or "InvalidTag" in str(type(e).__name__):
                print(f"  -> Key/decryption error detected")
                # For InvalidTag errors, the issue is likely that the message was encrypted with a different key
                # This can happen if keys were regenerated or if there's a mismatch
                # Skip this request but log it
            continue
    
    return decrypted_requests


@router.post("/requests/{request_id}/action")
async def handle_message_request(
    request_id: str,
    action_data: MessageRequestAction,
    current_user: dict = Depends(get_current_user)
):
    """Accept or decline a message request"""
    if not ObjectId.is_valid(request_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request ID"
        )
    
    if action_data.action not in ["accept", "decline"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action must be 'accept' or 'decline'"
        )
    
    request_id_obj = ObjectId(request_id)
    current_user_id_obj = ObjectId(current_user["_id"])
    
    # Find the request
    request = await db_module.database.message_requests.find_one({
        "_id": request_id_obj,
        "recipient_id": current_user_id_obj,
        "status": "pending"
    })
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message request not found or already processed"
        )
    
    if action_data.action == "accept":
        # Convert request to a regular message
        # Preserve plaintext if it exists so sender can see their message
        message_doc = {
            "sender_id": request["sender_id"],
            "sender_username": request["sender_username"],
            "recipient_id": request["recipient_id"],
            "recipient_username": request["recipient_username"],
            "content_encrypted": request["content_encrypted"],
            "nonce": request["nonce"],
            "auth_tag": request["auth_tag"],
            "kem_ciphertext": request["kem_ciphertext"],
            "encryption_type": request.get("encryption_type", "post_quantum"),
            "timestamp": request["timestamp"]
        }
        # Preserve plaintext if it exists
        if "content_plaintext" in request:
            message_doc["content_plaintext"] = request["content_plaintext"]
        
        # Insert as regular message
        await db_module.database.messages.insert_one(message_doc)
        
        # Update request status
        await db_module.database.message_requests.update_one(
            {"_id": request_id_obj},
            {"$set": {"status": "accepted"}}
        )
        
        return {"message": "Message request accepted", "status": "accepted"}
    
    else:  # decline
        # Update request status
        await db_module.database.message_requests.update_one(
            {"_id": request_id_obj},
            {"$set": {"status": "declined"}}
        )
        
        return {"message": "Message request declined", "status": "declined"}

