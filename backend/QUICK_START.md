# Quick Start Guide - Running the Server

## The Problem

When you start uvicorn, it needs the `OQS_INSTALL_PATH` environment variable to find liboqs. If it's not set, it tries to auto-install (and fails).

## Solution: Use the Startup Script

I've created a startup script that sets everything up automatically:

```powershell
cd PostQuantumMessagingApp\backend
.\start_server.ps1
```

This script:
- Sets `OQS_INSTALL_PATH` automatically
- Verifies the DLL exists
- Tests liboqs import
- Starts uvicorn

## Or Set It Manually

If you prefer to start uvicorn manually:

```powershell
cd PostQuantumMessagingApp\backend
.\venv\Scripts\Activate.ps1

# Set the environment variable for this session
$env:OQS_INSTALL_PATH = "C:\Users\xxcbj\Desktop\liboqs-0.15.0\liboqs-0.15.0\build"

# Now start uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Why This Happens

The environment variable `OQS_INSTALL_PATH` was set **permanently**, but:
- You need to **restart your terminal** for permanent variables to take effect
- OR set it in the current session before starting uvicorn

## Quick Fix for Current Session

Just run this before starting uvicorn:

```powershell
$env:OQS_INSTALL_PATH = "C:\Users\xxcbj\Desktop\liboqs-0.15.0\liboqs-0.15.0\build"
```

Then start uvicorn normally.

## Verify It's Working

When uvicorn starts, you should see:
```
[PQ] Generated Kyber512 keypair for server
```

If you see "liboqs not found" or "Error installing liboqs", the environment variable isn't set in that process.

