#!/usr/bin/env python3
"""
Generate a secure 32-byte encryption key for APP_ENCRYPTION_KEY.
"""
import secrets
import base64

def generate_key():
    """Generate a 32-byte key and return it in base64 format."""
    key = secrets.token_bytes(32)
    key_b64 = base64.b64encode(key).decode()
    key_hex = key.hex()
    
    print("=" * 60)
    print("Generated Encryption Key (32 bytes)")
    print("=" * 60)
    print(f"\nBase64 (recommended):")
    print(key_b64)
    print(f"\nHex format:")
    print(key_hex)
    print("\n" + "=" * 60)
    print("Add this to your .env file:")
    print(f"APP_ENCRYPTION_KEY={key_b64}")
    print("=" * 60)
    
    return key_b64

if __name__ == "__main__":
    generate_key()

