#!/bin/bash
#
# CNCSorter Touchscreen Interface Launcher (Raspberry Pi / Freenove)
# Optimized for touch display with automatic package installation
#

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "CNCSorter Touchscreen Interface"
echo "========================================"

# Check if running on Raspberry Pi
if [ -f /proc/device-tree/model ]; then
    MODEL=$(cat /proc/device-tree/model | tr -d '\0')
    echo "Device: $MODEL"
fi

# Create config directory
mkdir -p config

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install/update package
echo "Installing cncsorter package..."
pip install -e . > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Package installed successfully${NC}"
else
    echo -e "${RED}✗ Package installation failed${NC}"
    exit 1
fi

# Set environment variables for touchscreen
export QT_QPA_PLATFORM_PLUGIN_PATH=""
export DISPLAY=:0

# Check for Freenove display
if xrandr | grep -q "HDMI"; then
    echo "Display detected"
fi

echo "========================================"
echo "Starting Touchscreen Interface..."
echo "Access at: http://localhost:8080"
echo "Press Ctrl+C to stop"
echo "========================================"

# Run touchscreen interface
python -m src.touchscreen_interface

echo ""
echo "Touchscreen interface stopped."
