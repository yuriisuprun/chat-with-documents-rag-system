#!/bin/bash

# Run the Streamlit frontend for Chat With Documents (Bash)

API_URL="${1:-http://localhost:8000}"

echo "=========================================="
echo "Chat With Documents - Frontend Startup"
echo "=========================================="
echo ""

# Check if backend is running
echo "Checking backend connectivity..."
if curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo "✅ Backend is responding"
else
    echo "⚠️  Warning: Backend API not responding at $API_URL"
    echo "   Make sure the backend is running:"
    echo "   cd backend"
    echo "   python -m uvicorn app.main:app --reload"
    echo ""
fi

# Navigate to frontend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$(dirname "$SCRIPT_DIR")/frontend"

cd "$FRONTEND_DIR" || exit 1

# Load environment if exists
if [ -f ".env" ]; then
    echo "Loading .env configuration..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start Streamlit
echo ""
echo "Starting Streamlit frontend..."
echo "Frontend will be available at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop"
echo ""

streamlit run app.py
