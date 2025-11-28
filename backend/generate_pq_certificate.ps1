# Generate Post-Quantum Certificate using OQS-OpenSSL
# This script generates a self-signed certificate with post-quantum signature algorithms

param(
    [string]$OQS_OPENSSL_DIR = "C:\oqs-openssl\build\bin\Release",
    [string]$CERT_DIR = "$PSScriptRoot\certs",
    [string]$COMMON_NAME = "localhost"
)

Write-Host "Generating Post-Quantum Certificate..." -ForegroundColor Cyan

# Check if OQS-OpenSSL is available
$openssl_exe = Join-Path $OQS_OPENSSL_DIR "openssl.exe"

if (-not (Test-Path $openssl_exe)) {
    Write-Host "ERROR: OQS-OpenSSL not found at: $openssl_exe" -ForegroundColor Red
    Write-Host "Please install OQS-OpenSSL first. See BUILD_OQS_OPENSSL_WINDOWS.md" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Found OQS-OpenSSL at: $openssl_exe" -ForegroundColor Green

# Create certificate directory
if (-not (Test-Path $CERT_DIR)) {
    New-Item -ItemType Directory -Path $CERT_DIR | Out-Null
}

$cert_file = Join-Path $CERT_DIR "server.crt"
$key_file = Join-Path $CERT_DIR "server.key"

# Check if certificate already exists
if ((Test-Path $cert_file) -and (Test-Path $key_file)) {
    Write-Host "[INFO] Certificate already exists. Use -Force to regenerate." -ForegroundColor Yellow
    exit 0
}

Write-Host "Generating certificate with post-quantum signature algorithm..." -ForegroundColor Cyan

# Generate certificate using OQS-OpenSSL with post-quantum signature
# Using Dilithium3 (NIST-selected post-quantum signature algorithm)
$openssl_args = @(
    "req",
    "-x509",
    "-new",
    "-newkey", "dilithium3",
    "-keyout", $key_file,
    "-out", $cert_file,
    "-nodes",
    "-days", "365",
    "-subj", "/CN=$COMMON_NAME"
)

try {
    & $openssl_exe $openssl_args
    Write-Host "[SUCCESS] Certificate generated successfully!" -ForegroundColor Green
    Write-Host "  Certificate: $cert_file" -ForegroundColor Green
    Write-Host "  Private Key: $key_file" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now use these certificates with your TLS proxy." -ForegroundColor Cyan
} catch {
    Write-Host "ERROR: Failed to generate certificate: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Make sure OQS-OpenSSL is built correctly" -ForegroundColor Yellow
    Write-Host "2. Check that dilithium3 algorithm is available:" -ForegroundColor Yellow
    Write-Host "   $openssl_exe list -signature-algorithms" -ForegroundColor Yellow
    exit 1
}

