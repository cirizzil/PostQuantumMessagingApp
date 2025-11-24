"""
Post-Quantum Message Encryption Module
======================================

STEP 2: Integration of Post-Quantum Cryptography with Message Encryption
------------------------------------------------------------------------
This module replaces the old encryption.py functionality with post-quantum
key exchange while maintaining AES-GCM for symmetric encryption.

Encryption Flow:
1. Sender retrieves recipient's public key
2. Sender performs KEM encapsulation → shared secret
3. Shared secret → AES-256 key (via HKDF)
4. Message encrypted with AES-256-GCM
5. Store: encrypted message + KEM ciphertext

Decryption Flow:
1. Recipient retrieves their private key (decrypts with password)
2. Recipient performs KEM decapsulation → shared secret
3. Shared secret → AES-256 key (via HKDF)
4. Message decrypted with AES-256-GCM
"""

import os
import base64
from typing import Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.post_quantum import PostQuantumKEM


def encrypt_message_pq(plaintext: str, recipient_public_key: bytes) -> Tuple[bytes, bytes, bytes, bytes]:
    """
    STEP 2.1: Post-Quantum Message Encryption
    ------------------------------------------
    Encrypts a message using post-quantum key exchange and AES-GCM.
    
    Args:
        plaintext: Message content to encrypt (string)
        recipient_public_key: Recipient's post-quantum public key (bytes)
    
    Returns:
        (ciphertext, nonce, auth_tag, kem_ciphertext): Tuple of bytes
        - ciphertext: Encrypted message content
        - nonce: AES-GCM nonce
        - auth_tag: AES-GCM authentication tag
        - kem_ciphertext: Post-quantum KEM ciphertext (needed for decryption)
    
    Process:
        1. Perform KEM encapsulation with recipient's public key
        2. Derive AES-256 key from shared secret
        3. Encrypt message with AES-256-GCM
        4. Return all necessary components
    """
    # Step 1: Perform post-quantum key encapsulation
    shared_secret, kem_ciphertext = PostQuantumKEM.encapsulate(recipient_public_key)
    
    # Step 2: Derive AES-256 key from shared secret
    aes_key = PostQuantumKEM.derive_aes_key(shared_secret, info=b"message_encryption")
    
    # Step 3: Encrypt message with AES-GCM
    aesgcm = AESGCM(aes_key)
    nonce = os.urandom(12)  # 12 bytes for GCM
    
    plaintext_bytes = plaintext.encode('utf-8')
    encrypted = aesgcm.encrypt(nonce, plaintext_bytes, None)
    
    # AESGCM.encrypt returns ciphertext + auth_tag concatenated
    # For GCM, auth_tag is 16 bytes
    auth_tag = encrypted[-16:]
    ciphertext_only = encrypted[:-16]
    
    return ciphertext_only, nonce, auth_tag, kem_ciphertext


def decrypt_message_pq(
    ciphertext: bytes,
    nonce: bytes,
    auth_tag: bytes,
    kem_ciphertext: bytes,
    recipient_private_key: bytes
) -> str:
    """
    STEP 2.2: Post-Quantum Message Decryption
    ------------------------------------------
    Decrypts a message using post-quantum key exchange and AES-GCM.
    
    Args:
        ciphertext: Encrypted message content (bytes)
        nonce: AES-GCM nonce (bytes)
        auth_tag: AES-GCM authentication tag (bytes)
        kem_ciphertext: Post-quantum KEM ciphertext (bytes)
        recipient_private_key: Recipient's post-quantum private key (bytes)
    
    Returns:
        plaintext: Decrypted message content (string)
    
    Process:
        1. Perform KEM decapsulation with recipient's private key
        2. Derive AES-256 key from shared secret
        3. Decrypt message with AES-256-GCM
        4. Return plaintext
    """
    # Step 1: Perform post-quantum key decapsulation
    shared_secret = PostQuantumKEM.decapsulate(recipient_private_key, kem_ciphertext)
    
    # Step 2: Derive AES-256 key from shared secret (must match encryption)
    aes_key = PostQuantumKEM.derive_aes_key(shared_secret, info=b"message_encryption")
    
    # Step 3: Decrypt message with AES-GCM
    aesgcm = AESGCM(aes_key)
    
    # Reconstruct the full ciphertext (ciphertext + auth_tag)
    full_ciphertext = ciphertext + auth_tag
    
    plaintext_bytes = aesgcm.decrypt(nonce, full_ciphertext, None)
    return plaintext_bytes.decode('utf-8')


def get_user_public_key(user: dict) -> bytes:
    """
    STEP 2.3: Retrieve User Public Key
    -----------------------------------
    Extracts and decodes a user's public key from the database.
    
    Args:
        user: User document from database (dict)
    
    Returns:
        public_key: User's post-quantum public key (bytes)
    
    Raises:
        ValueError: If user doesn't have a public key
    """
    if "pq_public_key" not in user:
        raise ValueError(f"User {user.get('username', 'unknown')} does not have a post-quantum public key")
    
    public_key_b64 = user["pq_public_key"]
    return base64.b64decode(public_key_b64)


def get_user_private_key(user: dict, password: str) -> bytes:
    """
    STEP 2.4: Retrieve and Decrypt User Private Key
    ------------------------------------------------
    Retrieves and decrypts a user's private key using their password.
    
    Args:
        user: User document from database (dict)
        password: User's password (string)
    
    Returns:
        private_key: Decrypted post-quantum private key (bytes)
    
    Raises:
        ValueError: If user doesn't have a private key or decryption fails
    """
    from app.post_quantum import decrypt_private_key
    
    if "pq_private_key_encrypted" not in user:
        raise ValueError(f"User {user.get('username', 'unknown')} does not have a post-quantum private key")
    
    encrypted_private_key_b64 = user["pq_private_key_encrypted"]
    encrypted_private_key = base64.b64decode(encrypted_private_key_b64)
    
    try:
        private_key = decrypt_private_key(encrypted_private_key, password)
        return private_key
    except Exception as e:
        raise ValueError(f"Failed to decrypt private key: {e}")

