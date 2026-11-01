# Start the complete Chat With Documents system (Backend + Frontend + Ollama)
# PowerShell version

param(
    [switch]$SkipOllama = $false,
    [string]$OllamaModel = "qwen2.5:3b"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Chat With Documents - Full System Startup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check for required tools
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}
Write-Host "✅ $pythonVersion"

# Check for ollama
if (-not $SkipOllama) {
    $ollamaVersion = ollama --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Ollama not found in PATH" -ForegroundColor Yellow
        Write-Host "   Install from: https://ollama.ai" -ForegroundColor Yellow
        $SkipOllama = $true
    } else {
        Write-Host "✅ $ollamaVersion"
    }
}

Write-Host ""

# Function to start process
function Start-ProcessAndWait {
    param(
        [string]$Name,
        [string]$CommandLine,
        [string]$WorkingDirectory,
        [int]$WaitSeconds = 5
    )
    
    Write-Host "Starting $Name..." -ForegroundColor Green
    
    $process = Start-Process `
        -FilePath "powershell" `
        -ArgumentList "-NoExit", "-Command", $CommandLine `
        -WorkingDirectory $WorkingDirectory `
        -PassThru
    
    Write-Host "  PID: $($process.Id)" -ForegroundColor Gray
    Start-Sleep -Seconds $WaitSeconds
}

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
        Write-Host "✅ $OllamaModel is available" -ForegroundColor Green
    } else {
        Write-Host "⚠️  $OllamaModel not found, pulling..." -ForegroundColor Yellow
        ollama pull $OllamaModel
    }
}

# Start Backend
Write-Host ""
Write-Host "Starting Backend API..." -ForegroundColor Cyan
$backendCmd = "cd '$backendPath'; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Start-ProcessAndWait -Name "Backend API" -CommandLine $backendCmd -WorkingDirectory $backendPath -WaitSeconds 5

# Start Frontend
Write-Host ""
Write-Host "Starting Streamlit Frontend..." -ForegroundColor Cyan
$frontendCmd = "cd '$frontendPath'; streamlit run app.py"
Start-ProcessAndWait -Name "Frontend" -CommandLine $frontendCmd -WorkingDirectory $frontendPath -WaitSeconds 3

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "✅ System startup complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Frontend: http://localhost:8501" -ForegroundColor Yellow
Write-Host "🔌 Backend API: http://localhost:8000" -ForegroundColor Yellow
Write-Host "📚 API Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "📖 Documentation: Check README.md" -ForegroundColor Cyan
Write-Host "🛑 To stop: Close the terminal windows or press Ctrl+C" -ForegroundColor Cyan
Write-Host ""
