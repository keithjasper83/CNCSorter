#!/bin/bash
# CNCSorter - Touchscreen GUI launcher for Raspberry Pi

echo "========================================"
echo "CNCSorter - Touchscreen GUI"
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
echo "Launching Touchscreen GUI..."
echo "========================================"
echo ""

# Run the touchscreen GUI
python src/gui_touchscreen.py

# Deactivate virtual environment
deactivate

echo ""
echo "GUI closed."
