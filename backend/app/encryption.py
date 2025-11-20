"""
Simple AES-GCM encryption for message content at rest.
"""
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
import base64
import os
from app.config import settings


def get_encryption_key() -> bytes:
    """
    Get encryption key from environment variable.
    Expects a base64-encoded 32-byte key, or a hex-encoded key.
    """
    key_str = settings.app_encryption_key
    
    # Try to decode as base64 first
    try:
        key = base64.b64decode(key_str)
        if len(key) == 32:
            return key
    except:
        pass
    
    # Try hex encoding
    try:
        key = bytes.fromhex(key_str)
        if len(key) == 32:
            return key
    except:
        pass
    
    # If it's a string, derive a key from it (not ideal, but better than nothing)
    if isinstance(key_str, str):
        import hashlib
        key = hashlib.sha256(key_str.encode()).digest()
        return key
    
    raise ValueError("APP_ENCRYPTION_KEY must be a 32-byte key (base64 or hex encoded)")


def encrypt_message(plaintext: str) -> tuple[bytes, bytes, bytes]:
    """
    Encrypt a message using AES-GCM.
    Returns: (ciphertext, nonce, auth_tag)
    """
    key = get_encryption_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 12 bytes for GCM
    
    plaintext_bytes = plaintext.encode('utf-8')
    ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, None)
    
    # AESGCM.encrypt returns ciphertext + auth_tag concatenated
    # For GCM, auth_tag is 16 bytes
    auth_tag = ciphertext[-16:]
    ciphertext_only = ciphertext[:-16]
    
    return ciphertext_only, nonce, auth_tag


def decrypt_message(ciphertext: bytes, nonce: bytes, auth_tag: bytes) -> str:
    """
    Decrypt a message using AES-GCM.
    """
    key = get_encryption_key()
    aesgcm = AESGCM(key)
    
    # Reconstruct the full ciphertext (ciphertext + auth_tag)
    full_ciphertext = ciphertext + auth_tag
    
    plaintext_bytes = aesgcm.decrypt(nonce, full_ciphertext, None)
    return plaintext_bytes.decode('utf-8')

