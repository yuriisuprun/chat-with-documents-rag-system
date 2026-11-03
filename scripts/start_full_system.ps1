# Start the complete Chat With Documents system (Backend + Frontend + Ollama)
# PowerShell version - Includes production Uvicorn setup for Windows

param(
    [switch]$SkipOllama = $false,
    [string]$OllamaModel = "qwen3:8b",
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 8501
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Chat With Documents - Full System Startup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check for required tools
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] $pythonVersion"

Write-Host ""

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$backendPath = Join-Path $projectRoot "backend"
$frontendPath = Join-Path $projectRoot "frontend"

# Check if Ollama is already running
Write-Host "Checking Ollama..."
$ollamaRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/status" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        [OK] Ollama already running on port 11434" -ForegroundColor Green
        $ollamaRunning = $true
    }
}
catch {
    # Ollama not running
}

if (-not $ollamaRunning -and -not $SkipOllama) {
    Write-Host "Starting Ollama with $OllamaModel..."
    Start-Process ollama -ArgumentList "serve" -NoNewWindow
    Start-Sleep -Seconds 3
    Write-Host "[OK] Ollama started" -ForegroundColor Green
}

Write-Host ""

# Start Backend
Write-Host "Starting Backend API..." -ForegroundColor Cyan
$backendScript = @"
cd '$backendPath'
if (-not (Test-Path 'venv')) {
    Write-Host 'Creating virtual environment...' -ForegroundColor Yellow
    python -m venv venv
}
Write-Host 'Activating virtual environment...' -ForegroundColor Yellow
. '.\venv\Scripts\Activate.ps1'
Write-Host 'Upgrading pip...' -ForegroundColor Yellow
python -m pip install --upgrade pip 2>&1 | Out-Null
Write-Host 'Installing build tools...' -ForegroundColor Yellow
pip install --upgrade setuptools wheel --quiet 2>&1 | Out-Null
Write-Host 'Installing dependencies...' -ForegroundColor Yellow
`$result = pip install -r requirements.txt 2>&1
if (`$LASTEXITCODE -ne 0) {
    Write-Host 'ERROR: Dependency installation failed!' -ForegroundColor Red
    Write-Host `$result -ForegroundColor Red
    Write-Host 'Please run: .\scripts\fix_and_install.ps1' -ForegroundColor Yellow
    Read-Host 'Press Enter to exit'
    exit 1
}
Write-Host '[OK] Dependencies installed' -ForegroundColor Green
Write-Host 'Starting uvicorn on 0.0.0.0:$BackendPort...' -ForegroundColor Cyan
`$env:ENVIRONMENT = 'production'
python -m uvicorn app.main:app --host 0.0.0.0 --port $BackendPort --loop asyncio
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript
Start-Sleep -Seconds 10
Write-Host "[OK] Backend started" -ForegroundColor Green

Write-Host ""

# Start Frontend
Write-Host "Starting Streamlit Frontend..." -ForegroundColor Cyan
$frontendScript = @"
cd '$frontendPath'
Write-Host 'Installing Streamlit...' -ForegroundColor Yellow
pip install -q streamlit 2>$null; if (`$?) { Write-Host '[OK] Streamlit ready' -ForegroundColor Green } else { pip install streamlit }
Write-Host 'Starting Streamlit on port $FrontendPort...' -ForegroundColor Cyan
streamlit run app.py --server.port $FrontendPort
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript
Start-Sleep -Seconds 3
Write-Host "[OK] Frontend started" -ForegroundColor Green

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "[OK] System startup complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend: http://localhost:$FrontendPort" -ForegroundColor Yellow
Write-Host "Backend API: http://localhost:$BackendPort" -ForegroundColor Yellow
Write-Host "API Docs: http://localhost:$BackendPort/docs" -ForegroundColor Yellow
Write-Host "Metrics: http://localhost:$BackendPort/metrics" -ForegroundColor Yellow
Write-Host ""
Write-Host "Documentation: Check README.md" -ForegroundColor Cyan
Write-Host "To stop: Close the terminal windows or press Ctrl+C" -ForegroundColor Cyan
Write-Host ""
