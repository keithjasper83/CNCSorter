# Raspberry Pi Troubleshooting Guide

## Common Issues and Solutions

### 1. Qt Platform Plugin Error

**Error**: `Could not find the Qt platform plugin "wayland" in ...`

**Cause**: OpenCV tries to find Qt plugins but the warning is usually harmless if you have a display connected.

**Important**: This is typically just a **warning** and does NOT prevent the system from working with a display.

**Solutions**:

#### Option A: Ignore the Warning (Recommended if you have a display)
If you have a monitor connected to your Raspberry Pi, this warning can be safely ignored. The application will still display video feeds and GUIs properly using the default display backend.

#### Option B: For Truly Headless Systems (SSH without X forwarding)
**ONLY use this if you're running without any display:**
```bash
export QT_QPA_PLATFORM=offscreen
./run_rpi.sh
```

**Warning**: Setting `QT_QPA_PLATFORM=offscreen` disables all GUI windows. Only use this for:
- Headless SSH sessions without X11 forwarding
- Systems running without any display hardware
- Automated/batch processing scenarios

#### Option C: Install Qt Platform Plugins (if needed)
```bash
sudo apt-get update
sudo apt-get install -y libqt5gui5 qtwayland5 libqt5widgets5
```

### 2. Missing Fonts (Hershey Bold, etc.)

**Error**: Font loading errors for OpenCV text rendering

**Cause**: OpenCV font constants may not be available or properly loaded.

**Solution**: The code now uses fallback fonts automatically:
- `cv2.FONT_HERSHEY_SIMPLEX` (most compatible, always available)
- `cv2.FONT_HERSHEY_PLAIN` (fallback)

No action needed - this is handled in the code.

### 3. ModuleNotFoundError: No module named 'cncsorter'

**Error**: Python cannot find the cncsorter package

**Causes**:
1. Package not installed
2. Running from wrong directory
3. Virtual environment not activated

**Solutions**:

#### Quick Fix: Use the Launcher Script
```bash
cd CNCSorter
./run_rpi.sh  # Handles everything automatically
```

#### Manual Fix:
```bash
cd CNCSorter
source venv/bin/activate
pip install -e .  # Install package in development mode
python -m src.main
```

#### Verify Installation:
```bash
python -c "import cncsorter; print('✅ Package installed successfully!')"
```

### 4. Camera Access Issues

**Error**: `Failed to open camera` or `No camera feed`

**Solutions**:

#### Check Camera Connection
```bash
ls /dev/video*  # Should show /dev/video0 or similar
```

#### Test Camera:
```bash
sudo apt-get install -y v4l-utils
v4l2-ctl --list-devices
```

#### Fix Permissions:
```bash
sudo usermod -a -G video $USER
sudo reboot
```

### 5. Performance Issues

**Symptoms**: Low FPS, laggy video, system freezing

**Solutions**:

#### 1. Reduce Camera Resolution
Edit `src/cncsorter/config.py`:
```python
CAMERA_WIDTH = 640   # Instead of 1280
CAMERA_HEIGHT = 480  # Instead of 720
```

#### 2. Lower Detection Parameters
```bash
python -m src.main --threshold 150 --min-area 300
```

#### 3. Ensure Cooling
- Attach heatsink or active cooling fan
- Monitor temperature: `vcgencmd measure_temp`

#### 4. Close Background Applications
```bash
# Check CPU usage
htop

# Stop unused services
sudo systemctl stop bluetooth
```

### 6. Display Issues (No Window Shown)

**If running headless (SSH/VNC)**:

#### Option 1: Use Framebuffer (No Display Required)
Set in launcher or before running:
```bash
export OPENCV_VIDEOIO_PRIORITY_MSMF=0
export QT_QPA_PLATFORM=offscreen
```

#### Option 2: Use VNC with X11 Forwarding
```bash
export DISPLAY=:0
./run_rpi.sh
```

#### Option 3: Save Output to Files
The system can save images without displaying them - modify code to use headless mode.

### 7. Dependency Installation Failures

**Error**: pip install fails for opencv-python or numpy

**Solution**: Use system packages
```bash
sudo apt-get update
sudo apt-get install -y \\
    python3-opencv \\
    python3-numpy \\
    python3-serial \\
    python3-requests \\
    python3-pip

# Then install remaining dependencies
pip install pyserial requests
```

### 8. Memory Issues

**Error**: `Killed` or system freezes during operation

**Solutions**:

#### Increase Swap Space
```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Change CONF_SWAPSIZE=100 to CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

#### Enable GPU Memory
```bash
sudo nano /boot/config.txt
# Add or modify:
gpu_mem=256
```

## System Requirements

### Minimum (Raspberry Pi 3B+)
- 1GB RAM
- 16GB SD Card
- Basic USB Camera
- Passive cooling

### Recommended (Raspberry Pi 4/5)
- 4GB+ RAM
- 32GB+ SD Card (Class 10 or better)
- HD USB Camera or Pi Camera Module
- Active cooling (fan)

## Quick Diagnostic Commands

```bash
# Check Python version
python3 --version  # Should be 3.9+

# Check available memory
free -h

# Check disk space
df -h

# Check camera devices
ls -l /dev/video*

# Check OpenCV installation
python3 -c "import cv2; print(cv2.__version__)"

# Check package installation
python3 -c "import cncsorter; print('Package OK')"

# Monitor system resources
htop
```

## Getting Help

If issues persist:

1. Check the log file: `run_rpi.log`
2. Include full error messages
3. Note your Raspberry Pi model and OS version:
   ```bash
   cat /proc/device-tree/model
   cat /etc/os-release
   ```

## Optimized Launch Command

For best results on Raspberry Pi:

```bash
# Set environment variables for headless operation
export QT_QPA_PLATFORM=offscreen
export OPENCV_VIDEOIO_PRIORITY_MSMF=0

# Launch with optimized settings
./run_rpi.sh
```

Or simply use the updated `run_rpi.sh` which now includes these fixes automatically!
