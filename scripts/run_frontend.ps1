# Run the Streamlit frontend for Chat With Documents (PowerShell)

param(
    [string]$ApiUrl = "http://localhost:8000"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Chat With Documents - Frontend Startup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if backend is running
Write-Host "Checking backend connectivity..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$ApiUrl/health" -ErrorAction SilentlyContinue
    Write-Host "✅ Backend is responding" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Warning: Backend API not responding at $ApiUrl" -ForegroundColor Yellow
    Write-Host "   Make sure the backend is running:" -ForegroundColor Yellow
    Write-Host "   cd backend" -ForegroundColor Yellow
    Write-Host "   python -m uvicorn app.main:app --reload" -ForegroundColor Yellow
    Write-Host ""
}

# Navigate to frontend directory
$frontendPath = Split-Path -Parent $PSScriptRoot
$frontendPath = Join-Path $frontendPath "frontend"

Push-Location $frontendPath

# Load environment if exists
if (Test-Path ".env") {
    Write-Host "Loading .env configuration..." -ForegroundColor Yellow
    Get-Content .env | foreach-object {
        if ($_ -and !$_.StartsWith("#")) {
            $parts = $_.Split("=", 2)
            if ($parts.Count -eq 2) {
                [System.Environment]::SetEnvironmentVariable($parts[0], $parts[1], "Process")
            }
        }
    }
}

# Start Streamlit
Write-Host ""
Write-Host "Starting Streamlit frontend..." -ForegroundColor Green
Write-Host "Frontend will be available at: http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

streamlit run app.py

Pop-Location
