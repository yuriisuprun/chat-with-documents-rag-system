#!/bin/bash
# Chat With Documents - Complete System Startup
# Works on: Windows Git Bash, Linux, macOS
# Smart: Checks if services already running

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
if ! python --version 2>/dev/null; then
    echo "ERROR: Python not found"
    exit 1
fi

# Check if Ollama is already running
echo ""
echo "Checking Ollama..."
if curl -s http://localhost:11434/api/status >/dev/null 2>&1; then
    echo "✓ Ollama already running on port 11434"
else
    echo "Starting Ollama..."
    ollama serve &
    OLLAMA_PID=$!
    echo "Ollama PID: $OLLAMA_PID"
    sleep 3
fi

# Start Backend
echo ""
echo "Starting Backend..."
cd "$BACKEND" || exit 1

if [ ! -d "venv" ]; then
    echo "Creating venv..."
    python -m venv venv 2>/dev/null || python3 -m venv venv
fi

# Activate venv
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install deps
echo "Upgrading pip..."
pip install --upgrade pip 2>&1 >/dev/null
echo "Installing build tools..."
pip install --upgrade setuptools wheel --quiet 2>&1 >/dev/null
echo "Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Dependency installation failed!"
    echo "Please run: bash scripts/fix_and_install.sh"
    echo ""
    exit 1
fi
echo "[OK] Dependencies installed"

# Start backend
echo "Backend starting on http://localhost:8000"
python -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
sleep 2

# Start Frontend
echo ""
echo "Starting Frontend..."
cd "$FRONTEND" || exit 1

echo "Installing Streamlit..."
pip install -q streamlit 2>/dev/null || pip install streamlit

echo "Frontend starting on http://localhost:8501"
streamlit run app.py &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

echo ""
echo "=========================================="
echo "System Started!"
echo "=========================================="
echo ""
echo "UI:   http://localhost:8501"
echo "API:  http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for all processes
wait
