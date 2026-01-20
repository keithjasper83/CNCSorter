# Desktop/Operator Console Guide

## Overview

The Desktop/Operator Console provides a full-featured development and testing environment that uses **real camera detection** (Mac webcam, iPhone, iPad) with **simulated CNC movements**. This enables rapid development cycles without needing physical CNC hardware.

## Key Features

✅ **Real Object Detection**: Uses your Mac's built-in webcam or external cameras
✅ **Live Camera Feed**: See real-time object detection with bounding boxes
✅ **Simulated CNC**: CNC movements are simulated (no hardware needed)
✅ **Full Data Pipeline**: Objects are saved to SQLite database
✅ **EventBus Integration**: Uses the same event system as production
✅ **Perfect Testing Environment**: Test complete workflows on your Mac

## Quick Start

### Mac (Recommended for Development)

```bash
# Clone repository
git clone https://github.com/keithjasper83/CNCSorter.git
cd CNCSorter

# Run desktop console (auto-creates venv, installs dependencies)
./run_desktop.sh

# Access at http://localhost:8080
```

### Advanced Options

```bash
# Use external camera (camera index 1)
./run_desktop.sh --camera 1

# Use real CNC instead of simulation
./run_desktop.sh --real-cnc

# Change port
./run_desktop.sh --port 8090

# Run in fullscreen/native mode
./run_desktop.sh --fullscreen

# Combine options
./run_desktop.sh --camera 1 --port 8090
```

### Direct Python Execution

```bash
# Activate venv first
source venv/bin/activate

# Run directly
python -m src.desktop_console

# With options
python -m src.desktop_console --camera 0 --port 8080
```

## What You Can Test

### 1. Object Detection
- **Real Detection**: Uses OpenCV to detect objects from your webcam
- **Live Feed**: See detected objects with green bounding boxes and red center points
- **Object Counting**: Real-time count of detected objects
- **Classification Ready**: Detected objects are saved with all metadata

### 2. Scanning Workflow
- **Start Scan Cycle**: Simulates CNC moving through grid positions
- **Real-Time Detection**: Captures and counts objects at each position
- **Progress Tracking**: Visual progress bar shows scan completion
- **Data Persistence**: All objects saved to SQLite database

### 3. Camera Management
- **Start/Stop Camera**: Full camera lifecycle control
- **Camera Selection**: Choose from built-in or external cameras
- **iPhone/iPad**: Connect iPhone/iPad as external camera
- **Resolution**: Auto-configured to 1280x720 for best quality

### 4. System Integration
- **EventBus**: Publishes ObjectsDetected and BedMapCompleted events
- **SQLite Database**: Full persistence with DetectionRepository
- **Configuration**: Same config system as production
- **Emergency Stop**: Safety feature works in testing mode

## Interface Guide

### Main Screen

```
┌─────────────────────────────────────────────────────────┐
│ CNCSorter - Desktop/Operator Console                   │
│ [🛑 EMERGENCY STOP]                                     │
├─────────────────────────────────────────────────────────┤
│ 🖥️ macOS - Desktop Console with Real Camera Detection │
│    (CNC Simulated)                                      │
├──────────────────────┬──────────────────────────────────┤
│ SYSTEM CONTROL       │ LIVE CAMERA FEED                 │
│                      │                                  │
│ Hardware Control:    │ [Real-time video with          │
│ • Camera: ○ Inactive │  detection overlays]            │
│ • CNC: ○ Disconnected│                                  │
│                      │                                  │
│ System Status:       │                                  │
│ • Status: IDLE       │                                  │
│ • Detected: 0        │                                  │
│ • Progress: [░░░░]   │                                  │
│                      │                                  │
│ [▶️ START SCAN]      │                                  │
│ [🔧 PICK & PLACE]    │                                  │
│ [⏹ STOP] [🔄 RESET] │                                  │
└──────────────────────┴──────────────────────────────────┘
```

### Workflow Steps

1. **Click "START CAMERA"**
   - Activates your Mac webcam
   - Status changes to "Camera: ✓ Active"
   - Live feed appears on right side

2. **Click "CONNECT CNC"** (optional)
   - Simulates CNC connection
   - Status changes to "CNC: ✓ Connected (Simulated)"
   - Not required for testing detection

3. **Click "START SCAN CYCLE"**
   - Begins simulated scanning
   - Camera detects objects at each position
   - Progress bar shows completion
   - All objects saved to database

4. **View Results**
   - Detected items counter updates in real-time
   - See bounding boxes on live feed
   - Objects saved to `cncsorter.db` SQLite database

## Camera Setup

### Using Mac Built-in Camera

**Default (camera index 0):**
```bash
./run_desktop.sh
```

The built-in camera works perfectly for testing object detection algorithms.

### Using External Camera

**USB Camera (usually camera index 1):**
```bash
./run_desktop.sh --camera 1
```

**Check available cameras:**
```bash
# On Mac
system_profiler SPCameraDataType

# Or try each index
./run_desktop.sh --camera 0  # Usually built-in
./run_desktop.sh --camera 1  # Usually external USB
./run_desktop.sh --camera 2  # If you have multiple cameras
```

### Using iPhone/iPad as Camera

You can use your iPhone or iPad as an external camera:

**Option 1: Continuity Camera (macOS Ventura+)**
1. iPhone/iPad must be on same Apple ID
2. iPhone/iPad should automatically appear as camera option
3. May show up as camera index 1 or 2

**Option 2: Third-party apps**
- **EpocCam**: Turn iPhone into webcam
- **iVCam**: Similar functionality
- Install app on iPhone and Mac
- Follow app instructions to connect
- Then use `./run_desktop.sh --camera X` where X is the new camera index

### Camera Troubleshooting

**Camera not detected:**
```bash
# Check camera permissions (Mac)
System Preferences → Security & Privacy → Camera
# Make sure Terminal/iTerm has camera access

# Test camera directly
python3 -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

**Camera permission denied:**
- Grant camera permission to Terminal/iTerm in System Preferences
- Restart Terminal after granting permission

**Wrong camera selected:**
- Try different camera indices (0, 1, 2)
- Check which cameras are available: `system_profiler SPCameraDataType`

## Detection at 0,0 Coordinates

As mentioned, you can place objects at a fixed position (0,0 coordinates) and detect them without CNC movement:

```bash
# Start desktop console
./run_desktop.sh

# In the interface:
1. Click "START CAMERA"
2. Place objects in view of camera
3. Click "START SCAN CYCLE"

# Objects will be detected and saved with coordinates
# Even though CNC is simulated, you get real detection data
```

**Benefits:**
- Test detection algorithms without CNC
- Verify object counting accuracy
- Check classification readiness
- Build up detection database for training
- Fast iteration on vision improvements

## Data Access

### SQLite Database

All detected objects are saved to `cncsorter.db`:

```bash
# View database
sqlite3 cncsorter.db

# List all detected objects
sqlite> SELECT uuid, classification, confidence, center_x, center_y FROM detected_objects;

# Count total detections
sqlite> SELECT COUNT(*) FROM detected_objects;

# View pending objects (ready for pick & place)
sqlite> SELECT * FROM detected_objects WHERE work_status='pending';
```

### Database Schema

```sql
CREATE TABLE detected_objects (
    uuid VARCHAR(36) PRIMARY KEY,
    object_id INTEGER,
    timestamp DATETIME,
    center_x FLOAT,
    center_y FLOAT,
    area FLOAT,
    classification VARCHAR(100),
    confidence FLOAT,
    work_status VARCHAR(20),  -- pending, processing, completed, failed
    camera_index INTEGER,
    image_id VARCHAR(100)
);
```

## Development Workflow

### Typical Development Cycle

1. **Start Desktop Console**: `./run_desktop.sh`
2. **Test Detection**: Point camera at objects, start camera
3. **Iterate on Code**: Make changes to detection algorithms
4. **Reload**: Stop and restart console to test changes
5. **Verify Data**: Check SQLite database for correct detections
6. **Deploy to Pi**: Once satisfied, deploy to Raspberry Pi with real CNC

### Benefits Over Direct Pi Testing

✅ **Faster Iteration**: No need to deploy to Pi for each change
✅ **Easier Debugging**: Full Mac development tools available
✅ **No Hardware Risk**: Can't damage CNC during development
✅ **Full Data Access**: Easy SQLite access for verification
✅ **Real Detection**: Uses actual camera, not simulated objects

## Integration with Other Interfaces

### Touchscreen Interface

The Desktop Console shares the same backend as the touchscreen interface:

```bash
# Run both simultaneously (different ports)
./run_desktop.sh --port 8080        # Desktop console
./run_touchscreen.sh --port 8081    # Touchscreen UI

# They share:
- Same SQLite database
- Same EventBus events
- Same configuration files
```

### Operator Tablet Interface

When @jules builds the tablet interface, it will integrate with the desktop console:

```bash
# Desktop console for development
./run_desktop.sh --port 8080

# Tablet interface for operators (future)
./run_tablet.sh --port 8090

# Both access same data and events
```

## Advanced Features

### Custom Camera Settings

Modify camera resolution or other settings:

```python
# Edit src/cncsorter/infrastructure/vision.py
# In VisionSystem.open_camera():

self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)   # Higher resolution
self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
self.capture.set(cv2.CAP_PROP_FPS, 30)              # Frame rate
```

### Detection Thresholds

Adjust detection sensitivity:

```python
# Edit src/desktop_console.py
# In _detection_loop():

objects = self.vision_system.detect_objects(
    frame,
    threshold=100,   # Lower = more sensitive (default 127)
    min_area=100     # Lower = detect smaller objects (default 150)
)
```

### Event Handling

Subscribe to custom events:

```python
# Edit src/desktop_console.py
# In __init__():

# Add custom event handler
self.event_bus.subscribe(ObjectsDetected, self._my_custom_handler)

def _my_custom_handler(self, event):
    print(f"Detected {len(event.detected_objects)} objects!")
    # Your custom logic here
```

## Troubleshooting

### "Camera already in use"

```bash
# Another application is using the camera
# Close other apps using camera (Zoom, Skype, etc.)
# Or use external camera: ./run_desktop.sh --camera 1
```

### "Module not found" errors

```bash
# Ensure dependencies are installed
source venv/bin/activate
pip install -e .

# Or delete venv and let script recreate:
rm -rf venv
./run_desktop.sh
```

### Poor detection quality

```bash
# 1. Improve lighting
# 2. Adjust thresholds (see Advanced Features above)
# 3. Use higher resolution camera
# 4. Clean camera lens
```

### Database locked

```bash
# Close other SQLite connections
# Check for hanging Python processes:
ps aux | grep python
kill <process_id>
```

## Command Reference

### run_desktop.sh Options

```bash
./run_desktop.sh [OPTIONS]

--camera INDEX     Camera device index (default: 0)
--real-cnc        Use real CNC instead of simulation
--port PORT       Port number (default: 8080)
--fullscreen      Run in fullscreen/native mode
-h, --help        Show help message
```

### Python Module Options

```bash
python -m src.desktop_console [OPTIONS]

--camera INDEX     Camera device index (default: 0)
--real-cnc        Use real CNC instead of simulation
--port PORT       Port number (default: 8080)
--fullscreen      Run in fullscreen/native mode
-h, --help        Show help message
```

## Network Access

### Access from Other Devices

```bash
# Find your Mac's IP address
ipconfig getifaddr en0   # WiFi
ipconfig getifaddr en1   # Ethernet

# Access from other device on same network
http://<your-mac-ip>:8080

# Example:
http://192.168.1.100:8080
```

This allows you to:
- View detection on tablet/phone
- Share development progress
- Test responsive design
- Remote monitoring

## Next Steps

### After Testing on Mac

1. **Verify Detection Accuracy**: Check database for correct object counts
2. **Tune Thresholds**: Adjust for your specific objects
3. **Test Edge Cases**: Various lighting, angles, object sizes
4. **Deploy to Pi**: Transfer working code to Raspberry Pi
5. **Connect Real CNC**: Switch from simulation to real hardware

### Production Deployment

Once testing is complete on Mac:

```bash
# On Raspberry Pi
git pull origin main
./run_touchscreen.sh  # Full production mode with real CNC
```

The desktop console ensures your detection algorithms work perfectly before risking real hardware!

## Support

For issues or questions:
- Check this guide first
- Review MAC_SETUP.md for Mac-specific issues
- Check TOUCHSCREEN_INTERFACE.md for UI features
- Open GitHub issue with details of your setup

## Summary

The Desktop/Operator Console provides the perfect development environment:
- **Real camera detection** from Mac webcam/iPhone/iPad
- **Simulated CNC** movements (no hardware needed)
- **Full data pipeline** with SQLite persistence
- **Fast iteration** cycle for development
- **Production-ready** code that transfers to Pi

Start developing and testing today with just your Mac! 🚀
