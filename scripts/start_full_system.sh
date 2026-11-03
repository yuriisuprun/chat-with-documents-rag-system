#!/bin/bash
# Chat With Documents - Complete System Startup
# Works on: Windows Git Bash, Linux, macOS
# Includes production Uvicorn (or Gunicorn on Linux/macOS) setup

set -e

# Parameters
BACKEND_PORT=${1:-8000}
FRONTEND_PORT=${2:-8501}
USE_GUNICORN=${3:-"auto"}  # auto, true, false

echo "=========================================="
echo "Chat With Documents - Starting..."
echo "=========================================="
echo ""

# Get paths
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
BACKEND="$PROJECT_ROOT/backend"
FRONTEND="$PROJECT_ROOT/frontend"

echo "Project: $PROJECT_ROOT"
echo "Backend Port: $BACKEND_PORT"
echo "Frontend Port: $FRONTEND_PORT"
echo ""

# Check Python
echo "Checking Python..."
python --version || { echo "ERROR: Python not found"; exit 1; }
echo ""

# Start Backend
echo "=========================================="
echo "Starting Backend..."
echo "=========================================="
cd "$BACKEND" || exit 1

# Check/create venv
if [ ! -d "venv" ]; then
    echo "ERROR: venv not found!"
    echo "Run: bash ../scripts/fix_and_install.sh"
    exit 1
fi

# Activate venv
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Disable file watching during startup
export PYTHONDONTWRITEBYTECODE=1
export WATCHFILES_IGNORE_PATHS='venv/*'
export PYTHONUNBUFFERED=1
export ENVIRONMENT="production"

echo "Backend: $(which python)"
echo ""

# Determine if we should use Gunicorn (Linux/macOS) or Uvicorn (Windows)
USE_GUNICORN_CMD="false"
if [ "$USE_GUNICORN" = "auto" ]; then
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        USE_GUNICORN_CMD="false"  # Windows - use Uvicorn
    else
        USE_GUNICORN_CMD="true"   # Linux/macOS - use Gunicorn
    fi
elif [ "$USE_GUNICORN" = "true" ]; then
    USE_GUNICORN_CMD="true"
fi

# Start backend server
if [ "$USE_GUNICORN_CMD" = "true" ]; then
    # Production: Gunicorn + Uvicorn workers (Linux/macOS)
    CORES=$(nproc || sysctl -n hw.ncpu)
    WORKERS=$((CORES * 2))
    echo "Starting Gunicorn with $WORKERS workers on http://0.0.0.0:$BACKEND_PORT"
    gunicorn \
        "app.main:app" \
        --config "gunicorn_config.py" \
        --workers "$WORKERS" \
        --worker-class "uvicorn.workers.UvicornWorker" \
        --bind "0.0.0.0:$BACKEND_PORT" \
        --access-logfile "-" \
        --error-logfile "-" &
else
    # Windows: Single Uvicorn process (async)
    echo "Starting Uvicorn on http://0.0.0.0:$BACKEND_PORT"
    python -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port $BACKEND_PORT \
        --loop asyncio &
fi

BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
sleep 3

# Start Frontend
echo ""
echo "=========================================="
echo "Starting Frontend..."
echo "=========================================="
cd "$FRONTEND" || exit 1

# Ensure streamlit installed in main python
pip install -q streamlit 2>/dev/null || pip install streamlit >/dev/null

# Find app file
STREAMLIT_FILE="app.py"
if [ ! -f "$STREAMLIT_FILE" ]; then
    echo "ERROR: $STREAMLIT_FILE not found"
    exit 1
fi

echo "Starting Streamlit on http://localhost:$FRONTEND_PORT"
streamlit run "$STREAMLIT_FILE" --server.port $FRONTEND_PORT --logger.level=warning 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"
sleep 2

echo ""
echo "=========================================="
echo "✓ System Started!"
echo "=========================================="
echo ""
echo "📱 UI:   http://localhost:$FRONTEND_PORT"
echo "🔧 API:  http://localhost:$BACKEND_PORT"
echo "📚 Docs: http://localhost:$BACKEND_PORT/docs"
echo "📊 Metrics: http://localhost:$BACKEND_PORT/metrics"
echo ""
echo "Ollama: Make sure ollama serve is running"
echo "        (or start: ollama serve)"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Wait for processes
wait
