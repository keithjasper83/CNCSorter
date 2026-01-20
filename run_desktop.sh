#!/bin/bash

# CNCSorter Desktop/Operator Console Launcher
# Works on Mac, Linux, and Windows (Git Bash)
# Uses real webcam for object detection with simulated CNC movements

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "========================================"
echo "CNCSorter - Desktop/Operator Console"
echo "========================================"
echo

# Detect platform
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="Mac"
    echo -e "${BLUE}Platform: macOS${NC}"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="Linux"
    echo -e "${BLUE}Platform: Linux${NC}"
else
    PLATFORM="Other"
    echo -e "${BLUE}Platform: $OSTYPE${NC}"
fi

# Check Python 3
echo -e "${BLUE}Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    echo "Please install Python 3.8 or higher:"
    if [[ "$PLATFORM" == "Mac" ]]; then
        echo "  brew install python@3.11"
    else
        echo "  sudo apt-get install python3"
    fi
    exit 1
fi

echo -e "${GREEN}✓ Python version: $(python3 --version)${NC}"

# Check/create virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv

    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to create virtual environment.${NC}"
        echo "This could be because:"
        echo "  1. python3-venv is not installed"
        echo "  2. Insufficient disk space"
        echo "  3. Permission issues"
        exit 1
    fi

    if [ ! -d "venv" ]; then
        echo -e "${RED}Error: Virtual environment directory not created.${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
else
    echo -e "${RED}Error: Virtual environment activation script not found.${NC}"
    echo "The virtual environment may be corrupted."
    echo "Try deleting 'venv' folder and run again:"
    echo "  rm -rf venv"
    echo "  ./run_desktop.sh"
    exit 1
fi

# Install/update dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -e . --quiet
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}Error: Failed to install dependencies${NC}"
    exit 1
fi

echo
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Starting Desktop Console...${NC}"
echo -e "${GREEN}========================================${NC}"
echo
echo -e "${YELLOW}💡 Features:${NC}"
echo "  • Real webcam detection (Mac built-in camera works!)"
echo "  • Simulated CNC movements (no hardware needed)"
echo "  • Full object counting and classification"
echo "  • SQLite database persistence"
echo "  • Perfect for rapid development!"
echo
echo -e "${BLUE}📱 Access at: http://localhost:8080${NC}"
echo
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo

# Run desktop console
python -m src.desktop_console "$@"

# Deactivate venv on exit
deactivate 2>/dev/null || true
