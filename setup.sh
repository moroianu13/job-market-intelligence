#!/bin/bash
# Quick setup script for Job Market Intelligence project

set -e  # Exit on error

echo "=========================================="
echo "Job Market Intelligence - Quick Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p data/raw/adzuna data/curated logs

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  Warning: .env file not found!"
    echo "Please create .env file with:"
    echo "  ADZUNA_APP_ID=your_app_id"
    echo "  ADZUNA_APP_KEY=your_app_key"
    echo ""
else
    echo "✓ .env file found"
fi

# Run tests
echo ""
echo "Running tests..."
pytest tests/ -v

echo ""
echo "=========================================="
echo "✓ Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Activate venv: source venv/bin/activate"
echo "  2. Configure .env with API credentials"
echo "  3. Run pipeline: python orchestration/run_pipeline.py"
echo ""
