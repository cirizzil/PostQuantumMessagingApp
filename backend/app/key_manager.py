"""
Post-Quantum Key Management Module
===================================

STEP 7: Key Management for Post-Quantum Private Keys
-----------------------------------------------------
This module handles secure storage and retrieval of decrypted private keys.

Challenge: Private keys are encrypted with user passwords, but we can't
store passwords. We need a way to decrypt messages without asking for
password every time.

Solution: Session-based key cache
- After successful login, decrypt private key once
- Store decrypted key in memory (session cache) with expiration
- Keys are automatically cleared on logout or expiration
- Keys are never stored in database or sent to client
"""

import time
from typing import Optional, Dict
from app.pq_encryption import get_user_private_key
from app.post_quantum import decrypt_private_key
import base64


class KeyCache:
    """
    In-memory cache for decrypted private keys.
    Keys are stored temporarily and expire after a set time.
    """
    
    def __init__(self, ttl_seconds: int = 3600):  # 1 hour default
        """
        Initialize key cache.
        
        Args:
            ttl_seconds: Time-to-live for cached keys in seconds
        """
        self._cache: Dict[str, tuple] = {}  # user_id -> (private_key, expiry_time)
        self.ttl = ttl_seconds
    
    def store(self, user_id: str, private_key: bytes):
        """
        Store a decrypted private key in cache.
        
        Args:
            user_id: User's ID (string)
            private_key: Decrypted private key (bytes)
        """
        expiry = time.time() + self.ttl
        self._cache[user_id] = (private_key, expiry)
    
    def get(self, user_id: str) -> Optional[bytes]:
        """
        Retrieve a decrypted private key from cache.
        Returns None if not found or expired.
        
        Args:
            user_id: User's ID (string)
        
        Returns:
            private_key: Decrypted private key or None
        """
        if user_id not in self._cache:
            return None
        
        private_key, expiry = self._cache[user_id]
        
        # Check if expired
        if time.time() > expiry:
            del self._cache[user_id]
            return None
        
        return private_key
    
    def remove(self, user_id: str):
        """
        Remove a key from cache (e.g., on logout).
        
        Args:
            user_id: User's ID (string)
        """
        if user_id in self._cache:
            del self._cache[user_id]
    
    def clear_expired(self):
        """Remove all expired keys from cache."""
        current_time = time.time()
        expired_keys = [
            user_id for user_id, (_, expiry) in self._cache.items()
            if current_time > expiry
        ]
        for user_id in expired_keys:
            del self._cache[user_id]


# Global key cache instance
_key_cache = KeyCache(ttl_seconds=3600)  # 1 hour TTL


def decrypt_and_cache_private_key(user: dict, password: str) -> bytes:
    """
    STEP 7.1: Decrypt and Cache Private Key
    -----------------------------------------
    Decrypts a user's private key using their password and caches it.
    This should be called once after successful login.
    
    Args:
        user: User document from database (dict)
        password: User's password (string)
    
    Returns:
        private_key: Decrypted post-quantum private key (bytes)
    
    Raises:
        ValueError: If decryption fails
    """
    user_id = str(user["_id"])
    
    # Decrypt private key
    private_key = get_user_private_key(user, password)
    
    # Cache it
    _key_cache.store(user_id, private_key)
    
    return private_key


def get_cached_private_key(user_id: str) -> Optional[bytes]:
    """
    STEP 7.2: Get Cached Private Key
    ----------------------------------
    Retrieves a cached private key for a user.
    Returns None if not cached or expired.
    
    Args:
        user_id: User's ID (string)
    
    Returns:
        private_key: Decrypted private key or None
    """
    return _key_cache.get(user_id)


def clear_user_keys(user_id: str):
    """
    STEP 7.3: Clear Cached Keys
    ----------------------------
    Removes cached keys for a user (e.g., on logout).
    
    Args:
        user_id: User's ID (string)
    """
    _key_cache.remove(user_id)


def get_or_decrypt_private_key(user: dict, password: Optional[str] = None) -> bytes:
    """
    STEP 7.4: Get or Decrypt Private Key
    -------------------------------------
    Attempts to get cached private key, or decrypts it if password provided.
    
    Args:
        user: User document from database (dict)
        password: User's password (optional, needed if not cached)
    
    Returns:
        private_key: Decrypted post-quantum private key (bytes)
    
    Raises:
        ValueError: If key not cached and password not provided
    """
    user_id = str(user["_id"])
    
    # Try cache first
    private_key = _key_cache.get(user_id)
    if private_key is not None:
        return private_key
    
    # If not cached, need password
    if password is None:
        raise ValueError(
            "Private key not cached. Password required for decryption. "
            "Please ensure you've logged in recently."
        )
    
    # Decrypt and cache
    return decrypt_and_cache_private_key(user, password)

