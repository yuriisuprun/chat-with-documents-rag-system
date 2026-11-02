# Start the complete Chat With Documents system (Backend + Frontend + Ollama)
# PowerShell version

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

# Check for ollama
if (-not $SkipOllama) {
    $ollamaVersion = ollama --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[WARN] Ollama not found in PATH" -ForegroundColor Yellow
        Write-Host "       Install from: https://ollama.ai" -ForegroundColor Yellow
        $SkipOllama = $true
    } else {
        Write-Host "[OK] $ollamaVersion"
    }
}

Write-Host ""

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$backendPath = Join-Path $projectRoot "backend"
$frontendPath = Join-Path $projectRoot "frontend"

# Start Ollama (if not skipped)
if (-not $SkipOllama) {
    Write-Host ""
    Write-Host "Starting Ollama server..." -ForegroundColor Cyan
    Start-Process "ollama" -ArgumentList "serve" -NoNewWindow -PassThru | Out-Null
    Start-Sleep -Seconds 3
    
    # Check if model is available
    Write-Host "Checking $OllamaModel availability..." -ForegroundColor Yellow
    $models = ollama list 2>&1
    if ($models -like "*$OllamaModel*") {
        Write-Host "[OK] $OllamaModel is available" -ForegroundColor Green
    } else {
        Write-Host "[WARN] $OllamaModel not found, pulling..." -ForegroundColor Yellow
        ollama pull $OllamaModel
    }
}

# Start Backend
Write-Host ""
Write-Host "Starting Backend API..." -ForegroundColor Cyan
$backendCmd = "cd '$backendPath'; python -m pip install -q -r requirements.txt; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
$process = Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", $backendCmd -PassThru
Write-Host "[OK] Backend PID: $($process.Id)" -ForegroundColor Green
Start-Sleep -Seconds 5

# Start Frontend
Write-Host ""
Write-Host "Starting Streamlit Frontend..." -ForegroundColor Cyan
$frontendCmd = "cd '$frontendPath'; python -m pip install -q streamlit; streamlit run app.py"
$process = Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", $frontendCmd -PassThru
Write-Host "[OK] Frontend PID: $($process.Id)" -ForegroundColor Green
Start-Sleep -Seconds 3

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
