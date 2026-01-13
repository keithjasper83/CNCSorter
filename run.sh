#!/bin/bash
# CNCSorter - Automatic launcher with virtual environment (Mac/Linux)
# This script creates a virtual environment if needed and runs main.py

echo "========================================"
echo "CNCSorter - Object Detection System"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment."
        echo "Please ensure Python 3 is installed."
        read -p "Press enter to exit..."
        exit 1
    fi
    echo "Virtual environment created successfully."
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment."
    read -p "Press enter to exit..."
    exit 1
fi

# Install/update dependencies
echo "Checking and installing dependencies..."
python -m pip install --upgrade pip > /dev/null 2>&1

# Install package in editable mode (makes cncsorter importable)
echo "Installing cncsorter package in development mode..."
pip install -e . > /dev/null 2>&1

# Use pinned requirements for security
if [ -f "requirements-lock.txt" ]; then
    echo "Installing from pinned requirements for security..."
    pip install -r requirements-lock.txt
else
    echo "Installing from requirements.txt..."
    pip install -r requirements.txt
fi
if [ $? -ne 0 ]; then
    echo "Warning: Some dependencies may not have installed correctly."
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
