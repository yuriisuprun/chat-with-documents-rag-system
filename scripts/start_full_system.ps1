# Start the complete Chat With Documents system (Backend + Frontend + Ollama)
# PowerShell version - Smart: checks if services already running

param(
    [switch]$SkipOllama = $false,
    [string]$OllamaModel = "qwen3:8b"
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
        Write-Host "[OK] Ollama already running on port 11434" -ForegroundColor Green
        $ollamaRunning = $true
    }
}
catch {
    # Ollama not running
}

if (-not $ollamaRunning) {
    Write-Host "Starting Ollama..."
    Start-Process ollama -ArgumentList "serve" -NoNewWindow
    Start-Sleep -Seconds 3
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
Write-Host 'Installing dependencies...' -ForegroundColor Yellow
pip install -q -r requirements.txt 2>$null; if (`$?) { Write-Host '[OK] Dependencies installed' -ForegroundColor Green } else { pip install -r requirements.txt }
Write-Host 'Starting uvicorn...' -ForegroundColor Cyan
python -m uvicorn app.main:app --reload --port 8000
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript
Start-Sleep -Seconds 4
Write-Host "[OK] Backend started" -ForegroundColor Green

Write-Host ""

# Start Frontend
Write-Host "Starting Streamlit Frontend..." -ForegroundColor Cyan
$frontendScript = @"
cd '$frontendPath'
Write-Host 'Installing Streamlit...' -ForegroundColor Yellow
pip install -q streamlit 2>$null; if (`$?) { Write-Host '[OK] Streamlit ready' -ForegroundColor Green } else { pip install streamlit }
Write-Host 'Starting Streamlit...' -ForegroundColor Cyan
streamlit run app.py
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript
Start-Sleep -Seconds 3
Write-Host "[OK] Frontend started" -ForegroundColor Green

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "[OK] System startup complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend: http://localhost:8501" -ForegroundColor Yellow
Write-Host "Backend API: http://localhost:8000" -ForegroundColor Yellow
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "Documentation: Check README.md" -ForegroundColor Cyan
Write-Host "To stop: Close the terminal windows or press Ctrl+C" -ForegroundColor Cyan
Write-Host ""
