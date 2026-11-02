#!/bin/bash
# Chat With Documents - Complete System Startup
# Works on: Windows Git Bash, Linux, macOS

set -e

echo "=========================================="
echo "Chat With Documents - Starting..."
echo "=========================================="
echo ""

# Get paths
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
BACKEND="$PROJECT_ROOT/backend"
FRONTEND="$PROJECT_ROOT/frontend"

echo "Project: $PROJECT_ROOT"
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

echo "Backend: $(which python)"
echo ""

# Start backend server
echo "Starting uvicorn on http://localhost:8000"
python -m uvicorn app.main:app --reload --port 8000 2>&1 &
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

echo "Starting Streamlit on http://localhost:8501"
streamlit run "$STREAMLIT_FILE" --server.port 8501 --logger.level=warning 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"
sleep 2

echo ""
echo "=========================================="
echo "✓ System Started!"
echo "=========================================="
echo ""
echo "📱 UI:   http://localhost:8501"
echo "🔧 API:  http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"
echo ""
echo "Ollama: Make sure ollama serve is running"
echo "        (or start: ollama serve)"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Wait for processes
wait
