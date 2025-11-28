# Startup script for FastAPI server with PQ support
# This sets the OQS_INSTALL_PATH before starting uvicorn

Write-Host "Setting up post-quantum environment..." -ForegroundColor Cyan

# Set OQS_INSTALL_PATH to point to your liboqs build
$env:OQS_INSTALL_PATH = "C:\Users\xxcbj\Desktop\liboqs-0.15.0\liboqs-0.15.0\build"

# Verify DLL exists
$dllPath = "$env:OQS_INSTALL_PATH\bin\oqs.dll"
if (Test-Path $dllPath) {
    Write-Host "[OK] Found liboqs DLL at: $dllPath" -ForegroundColor Green
} else {
    Write-Host "[WARNING] DLL not found at: $dllPath" -ForegroundColor Yellow
    Write-Host "Copying from Release directory..." -ForegroundColor Yellow
    $releaseDll = "$env:OQS_INSTALL_PATH\bin\Release\oqs.dll"
    if (Test-Path $releaseDll) {
        Copy-Item $releaseDll -Destination $dllPath -Force
        Write-Host "[OK] DLL copied" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] DLL not found in Release directory either!" -ForegroundColor Red
        exit 1
    }
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

# Test liboqs import
Write-Host "Testing liboqs import..." -ForegroundColor Cyan
try {
    python -c "import oqs; print('[OK] liboqs loaded successfully')" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] liboqs is ready!" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] liboqs import failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[ERROR] Failed to import liboqs: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Starting FastAPI server..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Start uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

