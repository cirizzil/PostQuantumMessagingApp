# Create stunnel configuration for OQS-OpenSSL TLS proxy
# This creates a configuration file for stunnel compiled with OQS-OpenSSL

param(
    [int]$LISTEN_PORT = 8443,
    [string]$BACKEND_HOST = "localhost",
    [int]$BACKEND_PORT = 8000,
    [string]$CERT_DIR = "$PSScriptRoot\certs",
    [string]$CONFIG_FILE = "$PSScriptRoot\stunnel.conf"
)

Write-Host "Creating stunnel configuration for OQS-OpenSSL..." -ForegroundColor Cyan

$cert_file = Join-Path $CERT_DIR "server.crt"
$key_file = Join-Path $CERT_DIR "server.key"

# Check if certificates exist
if (-not (Test-Path $cert_file) -or -not (Test-Path $key_file)) {
    Write-Host "ERROR: Certificates not found. Generate them first:" -ForegroundColor Red
    Write-Host "  .\generate_pq_certificate.ps1" -ForegroundColor Yellow
    exit 1
}

# Create stunnel configuration
$config = @"
# Stunnel configuration for OQS-OpenSSL TLS Proxy
# This forwards TLS connections from port $LISTEN_PORT to FastAPI backend on port $BACKEND_PORT

# PID file
pid = stunnel.pid

# Debugging (set to 7 for verbose, 5 for normal, 0 for none)
debug = 5

# Output file
output = stunnel.log

# TLS Proxy Service
[oqs-fastapi-proxy]
accept = $LISTEN_PORT
connect = ${BACKEND_HOST}:${BACKEND_PORT}
cert = $cert_file
key = $key_file

# TLS Options
options = NO_SSLv2
options = NO_SSLv3
options = NO_TLSv1
options = NO_TLSv1_1
options = NO_TLSv1_2

# Use TLS 1.3 only
sslVersion = TLSv1.3

# Post-quantum cipher suites (if supported)
# ciphers = TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256

# Enable post-quantum groups (Kyber)
# This requires stunnel compiled with OQS-OpenSSL support
"@

$config | Out-File -FilePath $CONFIG_FILE -Encoding UTF8

Write-Host "[SUCCESS] Stunnel configuration created: $CONFIG_FILE" -ForegroundColor Green
Write-Host ""
Write-Host "To use this configuration:" -ForegroundColor Cyan
Write-Host "1. Build stunnel with OQS-OpenSSL (see OQS_OPENSSL_MIGRATION.md)" -ForegroundColor Yellow
Write-Host "2. Run: stunnel.exe `"$CONFIG_FILE`"" -ForegroundColor Yellow
Write-Host "3. Clients can connect via: https://localhost:$LISTEN_PORT" -ForegroundColor Yellow

