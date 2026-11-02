#!/bin/bash
# Fix pip and install dependencies

echo "=========================================="
echo "Fixing pip and installing dependencies..."
echo "=========================================="
echo ""

cd backend || exit 1

# Remove old venv
if [ -d "venv" ]; then
    echo "Removing old venv..."
    rm -rf venv
fi

# Create fresh venv
echo "Creating fresh virtual environment..."
python -m venv venv

# Activate venv
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Upgrade pip
echo ""
echo "Upgrading pip..."
python -m pip install --upgrade pip --quiet

# Clear pip cache
echo ""
echo "Clearing pip cache..."
pip cache purge

# Install wheel and setuptools first
echo ""
echo "Installing build tools..."
pip install --upgrade setuptools wheel --quiet

# Install requirements
echo ""
echo "Installing dependencies (this may take 5-10 minutes)..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "Now run: python -m uvicorn app.main:app --reload --port 8000"
