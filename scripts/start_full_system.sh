#!/bin/bash

# Start the complete Chat With Documents system (Backend + React Frontend)
# Bash version for macOS and Linux
# Requires: Python 3.11+, Node.js 18+, npm

set -e

BACKEND_PORT=${1:-8000}
FRONTEND_PORT=${2:-5173}
SKIP_OLLAMA=${SKIP_OLLAMA:-false}
OLLAMA_MODEL=${OLLAMA_MODEL:-qwen3:8b}

cat << "EOF"
==========================================
Chat With Documents - Full System Startup
==========================================
EOF
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "[FAIL] Python 3 not found. Please install Python 3.11+"
    exit 1
fi
echo "[OK] $(python3 --version)"

if ! command -v node &> /dev/null; then
    echo "[FAIL] Node.js not found. Please install Node.js 18+"
    exit 1
fi
echo "[OK] Node.js $(node --version)"

if ! command -v npm &> /dev/null; then
    echo "[FAIL] npm not found. Please install npm"
    exit 1
fi
echo "[OK] npm $(npm --version)"

echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PATH="$PROJECT_ROOT/backend"
FRONTEND_PATH="$PROJECT_ROOT/frontend-react"

# Check if Ollama is running
echo "Checking Ollama..."
if curl -s http://localhost:11434/api/status > /dev/null 2>&1; then
    echo "[OK] Ollama already running on port 11434"
else
    if [ "$SKIP_OLLAMA" = "false" ]; then
        echo "Starting Ollama with $OLLAMA_MODEL..."
        if command -v ollama &> /dev/null; then
            ollama serve &
            sleep 3
            echo "[OK] Ollama started"
        else
            echo "[WARN] Ollama not found. Skipping Ollama startup."
            echo "       Install from: https://ollama.ai"
        fi
    fi
fi

echo ""

# Start Backend
echo "Starting Backend API..."
(
    cd "$BACKEND_PATH"
    
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    echo "Activating virtual environment..."
    # Detect OS and use appropriate activation script
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OS" == "Windows_NT" ]]; then
        # Windows (Git Bash or WSL)
        source venv/Scripts/activate
    else
        # macOS and Linux
        source venv/bin/activate
    fi
    
    echo "Upgrading pip..."
    python -m pip install --upgrade pip >/dev/null 2>&1
    
    echo "Installing build tools..."
    pip install --upgrade setuptools wheel >/dev/null 2>&1
    
    echo "Installing dependencies..."
    if ! pip install -r requirements.txt 2>/dev/null; then
        echo "[ERROR] Dependency installation failed!"
        exit 1
    fi
    
    echo "[OK] Dependencies installed"
    echo "Starting FastAPI on 0.0.0.0:$BACKEND_PORT..."
    export ENVIRONMENT=development
    python -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload
) &
BACKEND_PID=$!
sleep 8
echo "[OK] Backend started on http://localhost:$BACKEND_PORT"

echo ""

# Start Frontend
echo "Starting React Frontend..."
(
    cd "$FRONTEND_PATH"
    
    echo "Checking Node dependencies..."
    if [ ! -d "node_modules" ]; then
        echo "Installing npm dependencies (this may take a minute)..."
        npm install
        if [ $? -ne 0 ]; then
            echo "[ERROR] npm install failed!"
            exit 1
        fi
    fi
    
    echo "[OK] Dependencies ready"
    echo "Starting Vite dev server on http://localhost:$FRONTEND_PORT..."
    npm run dev
) &
FRONTEND_PID=$!
sleep 3
echo "[OK] Frontend started"

echo ""
cat << "EOF"
=========================================
[OK] System startup complete!
=========================================

Frontend (React): http://localhost:5173
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs

The React dev server will open in your browser automatically.
If not, navigate to http://localhost:5173 in your browser.

To stop: Press Ctrl+C in this terminal or close the windows.

EOF

# Wait for both processes
wait
