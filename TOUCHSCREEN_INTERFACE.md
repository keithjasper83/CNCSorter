# CNCSorter Touchscreen Interface

## Overview

The CNCSorter touchscreen interface has been consolidated into a single, comprehensive NiceGUI-based implementation that works on **Raspberry Pi (Freenove display)**, **Mac**, **Windows**, and **Linux**.

## Key Features

✅ **Touch-Optimized**: Large buttons (80px+ height), no keyboard input required  
✅ **Multi-Platform**: Raspberry Pi, Mac, Windows, Linux  
✅ **Simulator Mode**: Test on Mac without hardware  
✅ **Web-Based**: Access from any device on network  
✅ **Python-Native**: Single codebase, no separate frontend  
✅ **Lightweight**: ~2MB total (vs React's 100MB+)  
✅ **Hardware Integration**: Direct camera and CNC control  
✅ **EventBus Integration**: Real-time updates  
✅ **Persistent Configuration**: JSON-based settings  

## Quick Start

### On Raspberry Pi (Production Mode)

```bash
./run_touchscreen.sh
```

Access at: http://localhost:8080

### On Mac/Windows/Linux (Simulator Mode)

```bash
./run_touchscreen.sh --simulator
```

Or directly:

```bash
python -m src.touchscreen_interface --simulator
```

The simulator mode automatically enables on Mac and provides full UI functionality without requiring camera or CNC hardware.

## Command-Line Options

```bash
python -m src.touchscreen_interface [OPTIONS]

Options:
  --simulator, --sim    Run in simulator mode (no hardware)
  --port PORT          Port number (default: 8080)
  --fullscreen         Run in fullscreen mode
  -h, --help          Show help message
```

## Interface Pages

### Home Page
- **Hardware Control**: Start/stop camera, connect/disconnect CNC
- **System Status**: Real-time status indicator, detected items count
- **Scan Progress**: Visual progress bar
- **Action Buttons**: 
  - START SCAN CYCLE (green, 100px height)
  - PICK & PLACE (blue, 100px height)
  - STOP (red)
  - RESET (orange)
- **Emergency Stop**: Always visible (red, top-right)

### Cameras Page
- **Camera Count**: +/- adjusters (1-8 cameras)
- **Per-Camera Configuration**:
  - Enable/disable toggle
  - Mount position (X, Y, Z) with +/- controls
  - Visible region (Width, Height) with +/- controls
  - Orientation (Tilt, Pan angles) with +/- controls
- **No Keyboard Input**: All values adjustable via touch

### Machine Page
- **Workspace Limits**: X/Y/Z min/max with +/- adjusters
- **Safe Z Height**: Parking height configuration
- **Workspace Volume**: Auto-calculated
- **Save Configuration**: Persist to JSON

### Scanning Page
- **Grid Size**: X × Y positions with +/- controls
- **Overlap Percentage**: Slider (0-50%)
- **Coverage Estimation**: Visual feedback
- **Total Positions**: Auto-calculated
- **Save Pattern**: Persist scanning settings

### Status Page
- **Live Statistics**: Total/pending/completed objects
- **Active Cameras**: Count of enabled cameras
- **CNC Status**: Connection state
- **Last Scan**: Timestamp
- **Refresh Button**: Update statistics

## Simulator Mode

Simulator mode is perfect for development and testing on Mac without hardware:

**What Works**:
- ✓ All UI controls functional
- ✓ Configuration saving/loading
- ✓ Simulated camera start/stop
- ✓ Simulated CNC connection
- ✓ Simulated scan cycle with random object detection
- ✓ Full navigation between pages
- ✓ All +/- adjusters, sliders, toggles
- ✓ Emergency stop simulation

**What's Simulated**:
- Camera operations (no actual camera access)
- CNC operations (no serial/HTTP communication)
- Object detection (random values generated)
- Scan progress (simulated timing)

**Notifications**:
All simulated actions show "(Simulator: ...)" notifications so you know what's being simulated.

## Hardware Integration (Production Mode)

When running on Raspberry Pi without `--simulator` flag:

**Camera Integration**:
- Direct integration with `VisionSystem`
- Uses configured camera index
- Real-time object detection
- Frame capture and processing

**CNC Integration**:
- Connects to FluidNC via serial or HTTP
- Motion validation with MotionValidator
- Position tracking
- Emergency stop support

**EventBus Integration**:
- Subscribes to `ObjectsDetected` events
- Subscribes to `BedMapCompleted` events
- Real-time UI updates based on events

## Configuration

Configuration is saved to `config/touchscreen_config.json`:

```json
{
  "num_cameras": 1,
  "cameras": [
    {
      "camera_id": 0,
      "name": "Camera 0",
      "mount_x": 400.0,
      "mount_y": 200.0,
      "mount_z": 300.0,
      "visible_width": 400.0,
      "visible_height": 300.0,
      "tilt_angle": 0.0,
      "pan_angle": 0.0,
      "enabled": true
    }
  ],
  "x_min": 0.0,
  "x_max": 800.0,
  "y_min": 0.0,
  "y_max": 400.0,
  "z_min": 0.0,
  "z_max": 300.0,
  "safe_z": 50.0,
  "overlap_percent": 20.0,
  "grid_x": 3,
  "grid_y": 2
}
```

## Touch Optimization

All UI elements are optimized for touch:

- **Button Size**: Minimum 80px height (WCAG AAA compliant)
- **Tap Targets**: Large, well-spaced for easy touch
- **No Keyboard**: +/- adjusters for all numeric values
- **Sliders**: Visual feedback for ranges/percentages
- **Toggles**: Large switches for enable/disable
- **Scrolling**: Smooth scroll areas for long content
- **Gestures**: Native swipe, tap, scroll support

## Color Coding

- **Red**: Emergency stop, errors, critical actions
- **Green**: Start actions, success states
- **Blue**: Primary actions, information
- **Yellow**: Warnings, caution states, simulator mode
- **Gray**: Inactive/disabled states

## Consolidation Notes

**Previous Implementations**:
1. **NiceGUI version** (`touchscreen_interface.py`) - Web-based, comprehensive configuration
2. **Tkinter version** (`gui_touchscreen.py`) - Native GUI, direct hardware control

**Consolidation Decision**:
- Kept **NiceGUI** as primary interface
- Added **simulator mode** for Mac testing
- Integrated **hardware control** features from Tkinter version
- Removed duplicate Tkinter interface (backed up as `gui_touchscreen.py.backup`)

**Why NiceGUI**:
- ✓ Works on Mac for testing
- ✓ Web-based (remote access possible)
- ✓ Python-native (no separate frontend)
- ✓ Lightweight (~2MB vs React 100MB+)
- ✓ Built-in TailwindCSS for consistent design
- ✓ Touch-optimized out of the box

## Remote Access

Since the interface is web-based, you can access it from any device on the network:

**From Mac/Windows/Linux**:
```
http://<raspberry-pi-ip>:8080
```

**From Phone/Tablet**:
```
http://<raspberry-pi-ip>:8080
```

This allows operators to monitor and control the system remotely.

## Development

### Running Locally

```bash
# Install dependencies
pip install -e .

# Run with simulator
python -m src.touchscreen_interface --simulator

# Open browser
open http://localhost:8080
```

### Testing on Mac

The simulator mode makes it easy to develop and test on Mac:

```bash
./run_touchscreen.sh --simulator
```

All UI controls work without hardware, making it perfect for:
- UI development and testing
- Configuration testing
- Workflow validation
- Demo purposes

## Support

For issues or questions:
1. Check TOUCHSCREEN_INTERFACE.md (this file)
2. Check RPI_TROUBLESHOOTING.md for Raspberry Pi specific issues
3. Review configuration in `config/touchscreen_config.json`
4. Enable simulator mode for testing: `--simulator`

## Future Enhancements

- [ ] Desktop/tablet operator interface (assigned to @jules)
- [ ] REST API for external integrations
- [ ] Real-time camera feed display
- [ ] Job queue management
- [ ] Historical data visualization
- [ ] Multi-language support
