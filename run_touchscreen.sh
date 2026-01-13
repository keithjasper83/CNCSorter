#!/bin/bash
#
# CNCSorter Touchscreen Interface Launcher (Raspberry Pi / Freenove / Mac)
# Supports simulator mode for testing without hardware
#

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
SIMULATOR_MODE=false
for arg in "$@"; do
    case $arg in
        --simulator|--sim)
            SIMULATOR_MODE=true
            shift
            ;;
    esac
done

echo "========================================"
echo "CNCSorter Touchscreen Interface"
echo "========================================"

# Check platform
if [ -f /proc/device-tree/model ]; then
    MODEL=$(cat /proc/device-tree/model | tr -d '\0')
    echo "Device: $MODEL"
    PLATFORM="Raspberry Pi"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Device: macOS"
    PLATFORM="Mac"
    SIMULATOR_MODE=true  # Force simulator on Mac
    echo -e "${BLUE}Note: Simulator mode auto-enabled on Mac${NC}"
else
    echo "Device: Linux/Other"
    PLATFORM="Linux"
fi

# Show mode
if [ "$SIMULATOR_MODE" = true ]; then
    echo -e "${YELLOW}MODE: Simulator (No hardware required)${NC}"
    echo "      Perfect for testing on Mac/Windows/Linux"
else
    echo -e "${GREEN}MODE: Production (Hardware integration)${NC}"
    echo "      Requires camera and CNC hardware"
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

# Set environment variables (only for Pi with display)
if [ "$PLATFORM" = "Raspberry Pi" ]; then
    export QT_QPA_PLATFORM_PLUGIN_PATH=""
    export DISPLAY=:0
    
    # Check for Freenove display
    if xrandr | grep -q "HDMI"; then
        echo "Display detected"
    fi
fi

echo "========================================"
echo "Starting Touchscreen Interface..."
echo "Access at: http://localhost:8080"
echo "Press Ctrl+C to stop"
echo "========================================"
echo ""

# Run touchscreen interface with appropriate flags
if [ "$SIMULATOR_MODE" = true ]; then
    python -m src.touchscreen_interface --simulator "$@"
else
    python -m src.touchscreen_interface "$@"
fi

echo ""
echo "Touchscreen interface stopped."
