# ArcticCodex Studio - Windows Startup Script
# Run this to start the full conversational chat system

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "     ArcticCodex Studio - Full Chat System           " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Check if venv is activated
if ($null -eq $env:VIRTUAL_ENV) {
    Write-Host "[*] Activating Python virtual environment..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[!] Virtual environment not found. Creating..." -ForegroundColor Yellow
        python -m venv venv
        & ".\venv\Scripts\Activate.ps1"
    }
}

# Load environment
Write-Host "[*] Loading environment configuration..." -ForegroundColor Yellow
$env:PYTHONPATH = (Get-Location).Path
$env:AC_EMBEDDINGS = "1"
$env:AC_EMBEDDINGS_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Create vault directory
if (-not (Test-Path "vault")) {
    Write-Host "[*] Creating vault directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "vault" -Force | Out-Null
}

# Check if vault has data
$chunks = @(Get-ChildItem -Path "vault" -ErrorAction SilentlyContinue).Count
if ($chunks -eq 0) {
    Write-Host ""
    Write-Host "[!] Vault is empty. Seed it with documents?" -ForegroundColor Yellow
    $response = Read-Host "[?] Seed vault now? Enter y or n"
    if ($response -eq "y") {
        Write-Host "[*] Seeding vault from documents..." -ForegroundColor Green
        python run_studio.py seed --vault ./vault
        Write-Host ""
    }
}

# Start Studio Server
Write-Host ""
Write-Host "[OK] Starting ArcticCodex Studio Server..." -ForegroundColor Green
Write-Host "[*] Vault: $(Resolve-Path vault)" -ForegroundColor Cyan
Write-Host "[*] Chat: http://localhost:8080" -ForegroundColor Cyan
Write-Host "[*] Press Ctrl+C to stop" -ForegroundColor Cyan
Write-Host ""

python -m packages.studio.src.studio_server_fly `
    --host 0.0.0.0 `
    --port 8080 `
    --vault ./vault `
    --embeddings on

Write-Host ""
Write-Host "[*] Studio server stopped" -ForegroundColor Yellow
