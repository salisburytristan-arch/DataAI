# Deploy ArcticCodex to Vercel
# Run from arctic-site directory

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "     ArcticCodex - Vercel Deployment                 " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in arctic-site directory
if (-not (Test-Path "package.json")) {
    Write-Host "[!] Error: Must run from arctic-site directory" -ForegroundColor Red
    Write-Host "[*] Run: cd arctic-site" -ForegroundColor Yellow
    exit 1
}

# Check if Vercel CLI is installed
Write-Host "[*] Checking Vercel CLI..." -ForegroundColor Yellow
$vercelInstalled = Get-Command vercel -ErrorAction SilentlyContinue

if (-not $vercelInstalled) {
    Write-Host "[!] Vercel CLI not found. Installing..." -ForegroundColor Yellow
    npm install -g vercel
}

# Check .env.local
Write-Host "[*] Checking environment configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env.local")) {
    Write-Host "[!] Warning: .env.local not found" -ForegroundColor Yellow
    Write-Host "[*] Creating default .env.local..." -ForegroundColor Yellow
    
    @"
NEXT_PUBLIC_API_URL=https://arcticcodex-studio.fly.dev
NEXT_PUBLIC_LLM_ENDPOINT=https://arcticcodex-studio.fly.dev
NEXT_PUBLIC_SITE_URL=https://arcticcodex.vercel.app
"@ | Out-File -Encoding UTF8 .env.local
    
    Write-Host "[OK] Created .env.local with default values" -ForegroundColor Green
    Write-Host "[*] Update NEXT_PUBLIC_API_URL with your Fly.io URL" -ForegroundColor Cyan
}

# Show current config
Write-Host ""
Write-Host "[*] Current configuration:" -ForegroundColor Cyan
Get-Content .env.local | ForEach-Object {
    if ($_ -match "^NEXT_PUBLIC_") {
        Write-Host "    $_" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "[?] Deploy to Vercel? (y/n): " -ForegroundColor Yellow -NoNewline
$response = Read-Host

if ($response -ne "y") {
    Write-Host "[*] Deployment cancelled" -ForegroundColor Yellow
    exit 0
}

# Deploy
Write-Host ""
Write-Host "[*] Deploying to Vercel..." -ForegroundColor Green
Write-Host "[*] Follow the prompts to configure your project" -ForegroundColor Cyan
Write-Host ""

vercel --prod

Write-Host ""
Write-Host "[OK] Deployment complete!" -ForegroundColor Green
Write-Host "[*] View your site at the URL shown above" -ForegroundColor Cyan
Write-Host "[*] Chat will be available at: /chat" -ForegroundColor Cyan
Write-Host ""
Write-Host "[*] To update environment variables:" -ForegroundColor Yellow
Write-Host "    vercel env add NEXT_PUBLIC_API_URL" -ForegroundColor Gray
Write-Host ""
