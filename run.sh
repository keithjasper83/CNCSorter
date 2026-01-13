#!/bin/bash
# CNCSorter - Automatic launcher with virtual environment (Mac/Linux)
# This script creates a virtual environment if needed and runs main.py

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================"
echo "CNCSorter - Object Detection System"
echo "========================================"
echo ""

# Detect platform
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="Mac"
    echo -e "${BLUE}Platform: macOS${NC}"
else
    PLATFORM="Linux"
    echo "Platform: Linux"
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    echo "Please install Python 3.8 or higher and try again."
    read -p "Press enter to exit..."
    exit 1
fi

echo "Python version: $(python3 --version)"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to create virtual environment.${NC}"
        echo "This could be because:"
        echo "  1. python3-venv is not installed (run: sudo apt install python3-venv)"
        echo "  2. Insufficient disk space"
        echo "  3. Permission issues"
        read -p "Press enter to exit..."
        exit 1
    fi
    echo -e "${GREEN}✓ Virtual environment created successfully.${NC}"
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
else
    echo -e "${RED}Error: Virtual environment activation script not found.${NC}"
    echo "The virtual environment may be corrupted. Try deleting 'venv' folder and run again."
    read -p "Press enter to exit..."
    exit 1
fi

# Install/update dependencies
echo ""
echo "Checking and installing dependencies..."
python -m pip install --upgrade pip --quiet

# Install package in editable mode (makes cncsorter importable)
echo "Installing cncsorter package in development mode..."
pip install -e . --quiet

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Package installed successfully${NC}"
else
    echo -e "${RED}✗ Package installation failed${NC}"
    echo "Please check error messages above."
    read -p "Press enter to exit..."
    exit 1
fi

# Use pinned requirements for security
if [ -f "requirements-lock.txt" ]; then
    echo "Installing from pinned requirements for security..."
    pip install -r requirements-lock.txt --quiet
else
    echo "Installing from requirements.txt..."
    pip install -r requirements.txt --quiet
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencies installed successfully${NC}"
else
    echo -e "${YELLOW}Warning: Some dependencies may not have installed correctly.${NC}"
    echo ""
fi

echo ""
echo "Starting CNCSorter application..."
echo "Press 's' to save a snapshot, 'q' to quit."
echo "========================================"
echo ""

# Run the application
python -m src.main

# Deactivate virtual environment
deactivate

echo ""
echo "Application closed."
read -p "Press enter to exit..."
