# OQS-OpenSSL 3 Integration Guide

This guide covers everything you need to know about integrating OQS-OpenSSL 3 for post-quantum TLS connections in this application.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Migration Plan](#migration-plan)
4. [Building OQS-OpenSSL 3 on Windows](#building-oqs-openssl-3-on-windows)
5. [Setup Guide](#setup-guide)
6. [Migration Progress](#migration-progress)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

## Overview

To satisfy the project requirement of using "OQS-OpenSSL 3", we need to integrate the official **oqs-openssl** fork to terminate TLS connections with post-quantum cipher suites.

Your current implementation already uses liboqs-python and CRYSTALS-Kyber for post-quantum transport security. This guide explains how to add OQS-OpenSSL 3 TLS termination on top of the existing implementation.

### Why OQS-OpenSSL 3?

- **Project Requirement**: Explicitly requires OQS-OpenSSL 3
- **TLS Integration**: Provides post-quantum TLS/HTTPS connections
- **Industry Standard**: Uses standard TLS protocol with PQ enhancements
- **Same Underlying Library**: Both OQS-OpenSSL and liboqs-python use the same liboqs C library

## Architecture

### Target Architecture

```
Client (browser or custom client)
   │
   │  HTTPS (TLS 1.3) with OQS-OpenSSL 3
   ▼
OQS-enabled TLS proxy (nginx/apache/stunnel built with oqs-openssl)
   │
   │  Plain HTTP (internal)
   ▼
FastAPI backend (existing application)
   │
   ▼
MongoDB
```

### Rationale

- We keep FastAPI/React logic intact
- A reverse proxy compiled with oqs-openssl handles TLS termination using post-quantum algorithms
- Clients connect via HTTPS and therefore "use OQS-OpenSSL 3" for the protected channel
- The existing application-layer post-quantum encryption (liboqs-python) can remain as an additional layer

## Migration Plan

### Required Components

1. **oqs-openssl 3** (OpenSSL fork with PQC support)
2. **oqs-provider** or preconfigured cipher suites (e.g., `pqc_kyber512` + classical hybrid)
3. **nginx** or **stunnel** compiled against oqs-openssl
4. **Client** using oqs-openssl (CLI or custom executable) to demonstrate PQ TLS handshake

### Migration Steps

1. **Build oqs-openssl** - Clone and build the OQS-OpenSSL 3 fork
2. **Build TLS Proxy** - Compile nginx/stunnel against oqs-openssl
3. **Generate Certificates** - Create TLS certificates with post-quantum signature algorithms
4. **Configure Proxy** - Set up the proxy to forward to FastAPI backend
5. **Test Connection** - Verify post-quantum TLS handshake works

## Building OQS-OpenSSL 3 on Windows

### Prerequisites

1. **Visual Studio 2022** (or Build Tools)
   - Download: https://visualstudio.microsoft.com/downloads/
   - Install "Desktop development with C++" workload

2. **CMake** (3.20+)
   - Download: https://cmake.org/download/
   - Install and add to PATH

3. **Git**
   - Download: https://git-scm.com/download/win
   - Or use: `winget install Git.Git`

4. **Perl** (for OpenSSL build scripts)
   - Download: https://strawberryperl.com/
   - Install and add to PATH

5. **NASM** (optional, for better performance)
   - Download: https://www.nasm.us/pub/nasm/releasebuilds/

### Step 1: Clone OQS-OpenSSL Repository

```powershell
cd C:\
git clone --branch OQS-OpenSSL_3_0-stable https://github.com/open-quantum-safe/oqs-openssl.git
cd oqs-openssl
```

### Step 2: Initialize and Update Submodules

```powershell
git submodule update --init --recursive
```

This will download:
- liboqs (Open Quantum Safe library)
- OpenSSL 3.0 source code

### Step 3: Build liboqs First

```powershell
cd oqs
mkdir build
cd build
cmake .. -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
```

This will take 10-30 minutes. After building, note the build directory path (e.g., `C:\oqs-openssl\oqs\build`).

### Step 4: Configure OQS-OpenSSL Build

```powershell
cd C:\oqs-openssl
mkdir build
cd build

# Configure with liboqs path
cmake .. -G "Visual Studio 17 2022" -A x64 ^
  -DCMAKE_BUILD_TYPE=Release ^
  -DOQS_BUILD_ONLY_LIB=OFF ^
  -DOQS_USE_OPENSSL=ON
```

### Step 5: Build OQS-OpenSSL

```powershell
cmake --build . --config Release
```

This will take another 10-20 minutes.

### Step 6: Install (Optional)

```powershell
cmake --install . --config Release --prefix C:\oqs-openssl\install
```

### Step 7: Set Environment Variables

```powershell
# Temporary (current session)
$env:OQS_OPENSSL_DIR = "C:\oqs-openssl\build"
$env:PATH = "C:\oqs-openssl\build\bin\Release;$env:PATH"

# Or set permanently:
[System.Environment]::SetEnvironmentVariable('OQS_OPENSSL_DIR', 'C:\oqs-openssl\build', 'User')
[System.Environment]::SetEnvironmentVariable('PATH', "C:\oqs-openssl\build\bin\Release;$env:PATH", 'User')
```

### Step 8: Verify Installation

```powershell
# Test openssl binary
C:\oqs-openssl\build\bin\Release\openssl.exe version

# Should show: OpenSSL 3.x.x with OQS support

# Test s_client
C:\oqs-openssl\build\bin\Release\openssl.exe s_client -help
```

## Setup Guide

### Quick Start Options

Since building OQS-OpenSSL on Windows can be complex, we provide multiple approaches:

#### Option 1: Use Pre-built Binaries (If Available)

Check the OQS-OpenSSL releases page for Windows binaries:
- https://github.com/open-quantum-safe/oqs-openssl/releases
- Look for Windows x64 builds

#### Option 2: Build from Source

Follow the instructions in [Building OQS-OpenSSL 3 on Windows](#building-oqs-openssl-3-on-windows) above.

#### Option 3: Use WSL/Docker (Easier)

If you have WSL2 or Docker:
1. Use Linux-based build (much easier)
2. Run the TLS proxy in WSL/container
3. Forward ports to Windows

### What We've Already Set Up

✅ **Document Serving** - Added `/documents` endpoint to serve HTML pages  
✅ **Certificate Generation Script** - `backend/generate_pq_certificate.ps1`  
✅ **Stunnel Configuration** - `backend/create_stunnel_config.ps1`  
✅ **Build Instructions** - This consolidated guide

### Next Steps

1. **Build or download OQS-OpenSSL 3**
2. **Generate certificates**: Run `backend/generate_pq_certificate.ps1`
3. **Set up TLS proxy**: Choose one:
   - Build nginx with OQS-OpenSSL
   - Build stunnel with OQS-OpenSSL
   - Use Python TLS server (simpler)
4. **Test connection**: Use `oqs_openssl s_client` to verify PQ TLS

## Migration Progress

### ✅ Completed

1. **Document Serving Feature** ✅
   - Added `/documents` router to serve HTML documents
   - Created sample HTML documents in `backend/documents/`
   - Documents are now available via API endpoints

2. **Build Documentation** ✅
   - Consolidated all OQS-OpenSSL documentation into this file
   - Created detailed build instructions
   - Created architecture and migration plan

3. **Scripts & Configuration** ✅
   - Certificate generation script: `backend/generate_pq_certificate.ps1`
   - Stunnel configuration script: `backend/create_stunnel_config.ps1`
   - TLS proxy placeholder: `backend/app/tls_proxy.py`

### ⏳ In Progress / Next Steps

1. **Build OQS-OpenSSL 3** 
   - Follow instructions in [Building OQS-OpenSSL 3 on Windows](#building-oqs-openssl-3-on-windows)
   - Or download pre-built binaries if available
   - Set environment variables

2. **Generate Certificates**
   - Run `backend/generate_pq_certificate.ps1` after OQS-OpenSSL is installed
   - Certificates will be stored in `backend/certs/`

3. **Set Up TLS Proxy**
   - Option A: Build nginx with OQS-OpenSSL
   - Option B: Build stunnel with OQS-OpenSSL  
   - Option C: Use Python TLS server (simpler)

4. **Test Post-Quantum TLS**
   - Use `oqs_openssl s_client` to verify PQ TLS handshake
   - Document the process with screenshots/logs

### Current Architecture

```
Client → HTTPS (OQS-OpenSSL TLS) → TLS Proxy → FastAPI Backend → MongoDB
                                            ↓
                                   Documents API (/documents)
```

## Testing

### Testing Post-Quantum TLS

After setup, test with:

```powershell
# Using OQS-OpenSSL s_client
C:\oqs-openssl\build\bin\Release\openssl.exe s_client `
  -connect localhost:8443 `
  -groups kyber512 `
  -showcerts

# You should see post-quantum key exchange in the output
```

### Testing Document Serving

1. Start the backend server
2. Visit: http://localhost:8000/documents
3. You should see a list of available documents
4. Click on any document to view it

Documents are stored in: `backend/documents/`

### Documentation for Project

For your project report, document:

1. **Architecture**: How OQS-OpenSSL 3 is integrated (TLS proxy)
2. **Post-Quantum Algorithms**: CRYSTALS-Kyber for key exchange, Dilithium for signatures
3. **Testing**: Screenshots/logs from `s_client` showing PQ TLS handshake
4. **Certificate Generation**: How PQ certificates were created

## Troubleshooting

### Build Fails

1. **Missing dependencies**: Ensure all prerequisites are installed
2. **CMake errors**: Check CMake version (needs 3.20+)
3. **Visual Studio not found**: Open "Developer Command Prompt for VS 2022"

### DLL Errors

- Copy DLLs to the build directory
- Add build directory to PATH
- Ensure all dependencies are in the same directory

### Certificate Generation Issues

- Make sure OQS-OpenSSL is properly installed and in PATH
- Check that the certificate generation script has the correct paths
- Verify environment variables are set correctly

## Additional Enhancements

1. **Serve Static Documents**  
   - Add a directory of HTML/PDF documents served under `/docs` via FastAPI or nginx.
   - Demonstrates "server maintains a database of web pages/documents."

2. **Client Authentication**  
   - Use PQ signature suites (e.g., Dilithium) for mutual TLS or signed tokens.

3. **Testing Script**  
   - Provide a script that runs `oqs_openssl s_client` and hits your endpoints.

## Current Status

- ✅ Document serving implemented
- ✅ Certificate generation script ready
- ✅ Build instructions documented
- ⏳ OQS-OpenSSL build (in progress)
- ⏳ TLS proxy configuration (pending OQS-OpenSSL)

Once OQS-OpenSSL is built, the TLS proxy can be configured to provide post-quantum secure HTTPS connections.

## Project Requirements Alignment

### Requirements vs Implementation

| Requirement | Status | Notes |
|------------|--------|-------|
| **OQS-OpenSSL 3 specifically** | ⏳ In Progress | Building and integrating TLS proxy |
| **Post-quantum secure** | ✅ Complete | CRYSTALS-Kyber (NIST-selected) |
| **Protected channel** | ✅ Complete | Post-quantum transport security |
| **Post-quantum key exchange** | ✅ Complete | CRYSTALS-Kyber KEM |
| **Database of documents** | ✅ Complete | `/documents` endpoint serves HTML pages |
| **Secure against quantum attacks** | ✅ Complete | Uses NIST PQC algorithms |

### Library Comparison

**OQS-OpenSSL 3:**
- Fork of OpenSSL 3 with post-quantum algorithms integrated
- Provides TLS/SSL with post-quantum support
- Uses liboqs C library underneath
- Commonly used for HTTPS/TLS connections

**liboqs-python (Current Implementation):**
- Python bindings for liboqs C library
- Direct access to post-quantum algorithms
- Uses the **same underlying liboqs library** as OQS-OpenSSL
- More flexible for custom protocols

**Key Point**: Both use the same underlying liboqs C library and CRYSTALS-Kyber algorithm. The difference is the interface (OpenSSL TLS vs direct API).

## Summary

This guide consolidates all information about integrating OQS-OpenSSL 3 into your messaging application. The integration involves:

1. Building OQS-OpenSSL 3 from source (or using pre-built binaries)
2. Setting up a TLS proxy (nginx/stunnel) compiled against OQS-OpenSSL
3. Generating post-quantum TLS certificates
4. Configuring the proxy to forward to your FastAPI backend
5. Testing the post-quantum TLS connection

Once complete, your application will use OQS-OpenSSL 3 for the TLS layer, satisfying the project requirement while maintaining your existing application logic.

