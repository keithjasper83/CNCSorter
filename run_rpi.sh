#!/bin/bash
# CNCSorter - Raspberry Pi launcher with virtual environment
# Optimized for Raspberry Pi with performance considerations

echo "========================================"
echo "CNCSorter - Raspberry Pi Edition"
echo "Object Detection System"
echo "========================================"
echo ""

# Set environment variables for display operation
# Allow Qt to use X11 display while preventing Windows-specific video I/O
export OPENCV_VIDEOIO_PRIORITY_MSMF=0

# Optional: Uncomment below ONLY if running truly headless (SSH without X forwarding)
# export QT_QPA_PLATFORM=offscreen

# Check if running on Raspberry Pi
if [ -f /proc/device-tree/model ]; then
    MODEL=$(cat /proc/device-tree/model 2>/dev/null | tr -d '\0')
    echo "Detected: $MODEL"
    echo ""
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment."
        echo "Please ensure Python 3 is installed."
        echo "Try: sudo apt-get install python3-venv"
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
echo "Note: OpenCV installation on Raspberry Pi may take several minutes..."
python -m pip install --upgrade pip > /dev/null 2>&1

# Install package in editable mode (makes cncsorter importable)
echo "Installing cncsorter package in development mode..."
pip install -e . 2>&1 | grep -v "Requirement already satisfied" || true

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
    echo "If OpenCV installation fails, you may need to install system packages:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install -y python3-opencv python3-numpy"
    echo ""
    read -p "Do you want to continue anyway? (y/n): " choice
    if [ "$choice" != "y" ] && [ "$choice" != "Y" ]; then
        deactivate
        exit 1
    fi
fi

echo ""
echo "Starting CNCSorter application..."
echo "Press 's' to save a snapshot, 'q' to quit."
echo ""
echo "Raspberry Pi Performance Tips:"
echo "- Reduce camera resolution if performance is slow"
echo "- Lower the threshold and min area for faster processing"
echo "- Ensure adequate cooling for sustained operation"
echo "========================================"
echo ""

# Run the application
python -m src.main

# Deactivate virtual environment
deactivate

echo ""
echo "Application closed."
