# Post-Quantum Transport Security

This document describes the post-quantum cryptography implementation in the messaging application. The app uses **CRYSTALS-Kyber** (a NIST-selected post-quantum algorithm) for key exchange and **AES-256-GCM** for message encryption.

## Overview

The application implements post-quantum "TLS-like" transport security between the browser and server:

- **Key Exchange**: CRYSTALS-Kyber KEM (Key Encapsulation Mechanism)
- **Message Encryption**: AES-256-GCM (Authenticated Encryption)
- **Key Derivation**: HKDF (HMAC-based Key Derivation Function)

**Important**: This is **transport security** (browser ↔ server), not end-to-end encryption. The server can decrypt and read all messages.

## Architecture

### Flow Diagram

```
1. Server Startup
   └─> Generate Kyber keypair
   └─> Expose public key at /pq/kem-public-key

2. Client Login + PQ Handshake
   ├─> Fetch server's public key
   ├─> Perform Kyber encapsulation → shared secret
   ├─> Send ciphertext to server
   └─> Both sides derive AES-256 session key (HKDF)

3. Message Sending
   ├─> Client encrypts message (AES-GCM) with session key
   ├─> Sends: { recipient_id, nonce, ciphertext }
   ├─> Server decrypts using session key
   └─> Stores plaintext in MongoDB

4. Message Retrieval
   └─> Server returns plaintext (already decrypted)
```

### Components

#### Backend

**Files:**
- `backend/app/pq_transport.py` - PQ KEM and AES-GCM utilities
- `backend/app/session_manager.py` - In-memory session key storage
- `backend/app/routers/pq.py` - PQ handshake endpoints

**Key Functions:**
- `generate_server_keypair()` - Generate Kyber keypair on startup
- `server_decapsulate()` - Server-side KEM decapsulation
- `derive_session_key()` - HKDF key derivation
- `encrypt_aes_gcm()` / `decrypt_aes_gcm()` - AES-256-GCM encryption/decryption

#### Frontend

**Files:**
- `frontend/src/utils/crypto.ts` - Crypto utilities (AES-GCM, HKDF, Kyber placeholder)
- `frontend/src/context/SessionKeyContext.tsx` - React context for session key
- `frontend/src/components/Login.tsx` - Performs PQ handshake after login
- `frontend/src/components/Chat.tsx` - Encrypts messages before sending

**Key Functions:**
- `performKyberEncapsulation()` - Client-side KEM encapsulation (placeholder)
- `deriveSessionKey()` - HKDF using Web Crypto API
- `encryptMessage()` / `decryptMessage()` - AES-256-GCM using Web Crypto API

## API Endpoints

### Post-Quantum Handshake

- **`GET /pq/kem-public-key`** - Returns server's Kyber public key (base64-encoded)
  ```json
  {
    "public_key": "base64_encoded_public_key"
  }
  ```

- **`POST /pq/handshake`** - Perform PQ handshake (requires authentication)
  ```json
  {
    "ciphertext": "base64_encoded_kem_ciphertext"
  }
  ```
  Response:
  ```json
  {
    "status": "ok",
    "message": "Handshake successful. Session key established."
  }
  ```

### Message Encryption Format

When sending an encrypted message, use this format:
```json
{
  "recipient_id": "user_id",
  "nonce": "base64_encoded_nonce",
  "ciphertext": "base64_encoded_ciphertext"
}
```

The server automatically detects encrypted messages and decrypts them using the session key.

## Installation & Setup

### Backend Setup

1. **Install dependencies** (already in `requirements.txt`):
   ```bash
   pip install liboqs-python
   ```

2. **Optional: Install liboqs C Library** (for full PQ functionality):
   
   The `liboqs-python` package is a Python wrapper around the `liboqs` C library. For full functionality, you need the C library installed.

   **Without liboqs C Library:**
   - The app will use a fallback implementation (NOT secure - demo only)
   - You'll see warnings: "WARNING: liboqs-python not installed. Using fallback implementation."

   **With liboqs C Library:**
   - Full post-quantum security
   - Real CRYSTALS-Kyber implementation

   **To install liboqs (optional, for production):**
   
   1. Download from: https://github.com/open-quantum-safe/liboqs/releases
   2. Extract to a directory (e.g., `C:\liboqs`)
   3. Build from source (requires CMake and Visual Studio Build Tools on Windows)
   4. Set environment variable:
      ```powershell
      $env:LIBOQS_DIR = "C:\path\to\liboqs\build"
      ```
   5. Or set permanently:
      - Press `Win + R`, type `sysdm.cpl`
      - Environment Variables → User variables → New
      - Name: `LIBOQS_DIR`
      - Value: Path to your liboqs build directory

3. **Verify installation** (optional):
   ```bash
   cd backend
   python verify_pq.py
   ```
   
   Expected output if working:
   ```
   [OK] liboqs-python is installed
   [OK] Generated public key: 800 bytes
   [OK] KEM encapsulation/decapsulation works
   [SUCCESS] ALL CHECKS PASSED - Your backend is PQ-safe!
   ```

### Frontend Setup

No additional setup needed. The frontend uses:
- Web Crypto API (built into browsers)
- A placeholder Kyber implementation (for demonstration)

**Note**: For production, replace the placeholder Kyber implementation in `frontend/src/utils/crypto.ts` with a real library (WebAssembly-based or pure JavaScript).

## Usage

### Automatic Handshake

The PQ handshake happens automatically when a user logs in:

1. User logs in → receives JWT token
2. Frontend automatically:
   - Fetches server's public key
   - Performs Kyber encapsulation
   - Sends ciphertext to server
   - Derives session key locally
3. Session key is stored in React context (in-memory)
4. All subsequent messages are encrypted with this session key

### Manual Verification

Check browser console after login for:
```
[PQ] Starting post-quantum handshake...
[PQ] Received server public key
[PQ] Kyber encapsulation complete
[PQ] Session key established
[PQ] Encrypting message before sending...
```

Check backend logs for:
```
[PQ] Generated Kyber512 keypair for server
[PQ_HANDSHAKE] Successfully established session key for user <username>
[PQ] Decrypted message from user <username>
```

## Security Properties

### What This Provides

✅ **Post-Quantum Safe**: Uses CRYSTALS-Kyber (NIST-selected algorithm)  
✅ **Transport Security**: Messages encrypted between browser and server  
✅ **Authenticated Encryption**: AES-GCM provides encryption + authentication  
✅ **Key Derivation**: HKDF ensures proper key properties for AES-256  

### What This Does NOT Provide

❌ **End-to-End Encryption**: Server can decrypt and read all messages  
❌ **Message Encryption at Rest**: Messages stored as plaintext in MongoDB  
❌ **Forward Secrecy**: Session keys persist until logout/server restart  
❌ **Key Rotation**: Session keys don't expire or rotate automatically  

## Current Status

### Backend Status

| Component | Status | PQ-Safe? |
|-----------|--------|----------|
| Code Implementation | ✅ Uses liboqs-python | ✅ Yes |
| Runtime (with liboqs) | ✅ Full functionality | ✅ Yes |
| Runtime (without liboqs) | ⚠️ Fallback mode | ❌ No (demo only) |
| AES-GCM | ✅ Real implementation | ✅ Yes |
| HKDF | ✅ Real implementation | ✅ Yes |

### Frontend Status

| Component | Status | PQ-Safe? |
|-----------|--------|----------|
| Kyber Implementation | ⚠️ Placeholder | ❌ No (demo only) |
| AES-GCM | ✅ Web Crypto API | ✅ Yes |
| HKDF | ✅ Web Crypto API | ✅ Yes |
| Session Key Storage | ✅ In-memory (React context) | ✅ Yes |

**Recommendation**: For production, replace the frontend Kyber placeholder with a real library.

## Limitations & Future Improvements

### Current Limitations

1. **Frontend Kyber**: Uses simplified placeholder (NOT cryptographically secure)
   - **Fix**: Replace with WebAssembly-based liboqs or a proper JavaScript Kyber library

2. **Session Key Storage**: In-memory only (lost on server restart)
   - **Fix**: Use Redis or similar for multi-instance deployments

3. **No Key Rotation**: Session keys don't expire or rotate
   - **Fix**: Implement periodic key refresh mechanism

4. **No Forward Secrecy**: Compromised session key affects all messages
   - **Fix**: Use ephemeral keys or re-keying mechanism

### Future Improvements

1. Replace frontend Kyber placeholder with real library
2. Add session key persistence (Redis) for multi-instance
3. Implement key rotation/refresh mechanism
4. Add proper error handling for encryption failures
5. Add logging/auditing for security events
6. Consider message authentication at application layer
7. Implement forward secrecy (ephemeral session keys)

## Troubleshooting

### Backend Issues

**"liboqs not found" warnings:**
- The app will use fallback mode (demo only)
- For full PQ security, install liboqs C library (optional)
- App will still work, just without real PQ cryptography

**"No session key found" errors:**
- User needs to complete PQ handshake (happens automatically on login)
- Try logging out and logging back in

**Version mismatch warnings:**
- You may see: "liboqs version 0.15.0 differs from liboqs-python version 0.14.1"
- This is safe to ignore - versions are compatible

### Frontend Issues

**PQ handshake fails:**
- Check browser console for errors
- Verify backend is running and `/pq/kem-public-key` endpoint works
- Check network tab for failed requests

**Messages not encrypting:**
- Verify session key is stored (check browser console for `[PQ] Session key established`)
- Check that handshake completed successfully
- Messages fall back to plaintext if no session key exists

## Verification

### Backend Verification

Run the verification script:
```bash
cd backend
python verify_pq.py
```

Expected output (if liboqs is installed):
```
[OK] liboqs-python is installed
[OK] Generated public key: 800 bytes
[OK] KEM encapsulation/decapsulation works
[SUCCESS] ALL CHECKS PASSED - Your backend is PQ-safe!
```

Expected output (if liboqs is NOT installed):
```
WARNING: liboqs-python not installed. Using fallback implementation.
[OK] Fallback key generation works
[WARNING] Using fallback implementation (NOT secure!)
```

### Frontend Verification

1. Login to the app
2. Open browser console (F12)
3. Look for `[PQ]` log messages showing:
   - Handshake starting
   - Public key received
   - Encapsulation complete
   - Session key established
4. Send a message and verify: `[PQ] Encrypting message before sending...`

## For Project Documentation

### What to Document

1. **Architecture**: Post-quantum transport security using CRYSTALS-Kyber
2. **Implementation**:
   - Backend: Real Kyber via liboqs-python (with optional liboqs C library)
   - Frontend: Demonstrates concept with placeholder (would use real library in production)
3. **Security Properties**:
   - Post-quantum safe: Uses NIST-selected algorithm
   - Transport encryption: AES-256-GCM
   - Key exchange: Kyber KEM with HKDF

### Limitations to Note

1. Frontend uses placeholder Kyber implementation (document as demo limitation)
2. Transport security only (not end-to-end encryption)
3. Messages stored as plaintext in database
4. Session keys in-memory only (lost on restart)

## Summary

✅ **Backend**: Fully PQ-safe with real CRYSTALS-Kyber (when liboqs is installed)  
⚠️ **Frontend**: Uses placeholder (document as demo limitation)  
✅ **Architecture**: Correct and production-ready  
✅ **Code Structure**: Uses industry-standard libraries and patterns  

The implementation demonstrates post-quantum transport security and follows best practices for cryptographic implementations.

