# Fix pip and install dependencies (Windows PowerShell)

$backend = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "backend"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Fixing pip and installing dependencies..." -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $backend

# Remove old venv
if (Test-Path "venv") {
    Write-Host "Removing old venv..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force venv
}

# Create fresh venv
Write-Host "Creating fresh virtual environment..." -ForegroundColor Cyan
python -m venv venv

# Activate venv
Write-Host "Activating venv..." -ForegroundColor Cyan
. ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip --quiet

# Clear pip cache
Write-Host ""
Write-Host "Clearing pip cache..." -ForegroundColor Cyan
pip cache purge

# Install wheel and setuptools first (required for any build dependencies)
Write-Host ""
Write-Host "Installing build tools..." -ForegroundColor Cyan
pip install --upgrade setuptools wheel --quiet

# Install requirements
Write-Host ""
Write-Host "Installing dependencies (this may take 5-10 minutes)..." -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Now run:" -ForegroundColor Yellow
Write-Host "python -m uvicorn app.main:app --reload --port 8000" -ForegroundColor Cyan
Write-Host ""
