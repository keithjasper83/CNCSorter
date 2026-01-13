# CNCSorter

CNC object identification and mapping system with pick and place capabilities based on computer vision.

## Features

- **Real-time Object Detection**: Advanced OpenCV-based detection with adjustable parameters
- **CNC Integration**: Support for FluidNC via Serial or HTTP communication
- **Image Mapping**: Capture multiple images and stitch them into a complete bed map
- **Live Status Display**: Full-screen monitoring optimized for Raspberry Pi
- **Coordinate Mapping**: Map detected objects to real-world CNC coordinates
- **Modular Architecture**: DDD (Domain-Driven Design) with clear separation of concerns
- **Interactive Testing**: Test individual functions without running the full automation
- **Touchscreen GUI**: Simple, large-button interface optimized for small Raspberry Pi touchscreens

## Installation

For detailed installation instructions, see **[INSTALL_GUIDE.md](INSTALL_GUIDE.md)**.

### Quick Install

```bash
# Using launcher scripts (automatic installation)
./run.sh          # Mac/Linux
./run_rpi.sh      # Raspberry Pi
run.bat           # Windows

# Manual installation
pip install -e .  # From repository root
```

## Quick Start

### Touchscreen GUI Mode (Raspberry Pi)

For Raspberry Pi with touchscreen, use the simplified GUI:

```bash
./run_gui.sh
```

The touchscreen interface provides:
- **Large, touch-friendly buttons** for all operations
- **Real-time status** display
- **CNC position** monitoring
- **Simple workflow**: Start Camera → Connect CNC → New Map → Capture → Stitch → Save

Perfect for:
- Small touchscreens (7" or smaller)
- Quick operations without keyboard
- Production environment on the CNC machine

### Full Application Mode

#### Windows
Simply double-click `run.bat` to automatically:
- Create a virtual environment (if needed)
- **Install cncsorter package** (NEW - fixes import errors)
- Install required dependencies
- Launch the full application

#### Mac/Linux (Development)
```bash
./run.sh
```

#### Raspberry Pi (Production)
```bash
./run_rpi.sh
```

All launchers will automatically:
- Create a virtual environment (if needed)
- Install required dependencies
- Launch the application with live status display

### Interactive Test Mode

To test individual functions without running the full automation:

```bash
# Activate virtual environment first
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate  # Windows

# Run the interactive test menu from project root
python src/test_menu.py
```

The test menu allows you to:
1. Test Camera/Vision System
2. Test Object Detection with live tuning
3. Test CNC Controller (Serial)
4. Test CNC Controller (HTTP)
5. Test Image Capture & Detection
6. Test Image Stitching
7. Test Bed Mapping Service
8. Test Live Status Display
9. Run Full Application

## Manual Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
```bash
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python src/main.py
```

## Usage

### Full Application Mode
- **[SPACE]**: Capture image and add to current map
- **[S]**: Start new bed map
- **[M]**: Stitch all images in current map
- **[V]**: Save current map to disk
- **[Q]**: Quit application

### Command Line Options
```bash
python src/main.py [options]

Options:
  --camera INDEX           Camera device index (default: 0)
  --cnc-mode MODE         CNC connection: none, serial, http (default: none)
  --cnc-port PORT         Serial port (default: /dev/ttyUSB0)
  --cnc-baudrate BAUD     Serial baudrate (default: 115200)
  --cnc-host HOST         CNC IP address (default: 192.168.1.100)
  --cnc-http-port PORT    HTTP port (default: 80)
```

### Example: Connect to CNC via Serial
```bash
python src/main.py --cnc-mode serial --cnc-port /dev/ttyUSB0 --cnc-baudrate 115200
```

### Example: Connect to CNC via HTTP
```bash
python src/main.py --cnc-mode http --cnc-host 192.168.1.100
```

## Project Structure

Following Domain-Driven Design (DDD) principles with clear separation between code organization and package structure:

```
CNCSorter/
├── src/                      # Source code directory (standard convention)
│   ├── cncsorter/           # Python package (the actual application)
│   │   ├── __init__.py      # Package initialization
│   │   ├── domain/          # Core business entities and logic
│   │   │   └── entities.py  # Domain models (CNCCoordinate, DetectedObject, BedMap)
│   │   ├── application/     # Use cases and orchestration
│   │   │   └── bed_mapping.py  # Bed mapping service
│   │   ├── infrastructure/  # Technical implementations
│   │   │   ├── vision.py    # Vision system and image stitcher
│   │   │   ├── cnc_controller.py  # CNC communication (Serial/HTTP)
│   │   │   ├── gimbal_controller.py  # Gimbal control with GPIO
│   │   │   ├── object_classifier.py  # Shape-based classification
│   │   │   ├── vision_enhanced.py    # Multi-source vision
│   │   │   └── vision_multi_camera.py  # Multi-camera system
│   │   ├── presentation/    # UI and user interaction
│   │   │   └── live_display.py  # Live status display
│   │   └── config.py        # System configuration
│   ├── main.py             # Main application entry point
│   ├── gui_touchscreen.py  # Touchscreen GUI for Raspberry Pi
│   ├── gimbal_test.py      # Gimbal testing utility
│   └── test_menu.py        # Interactive test menu
├── tests/                   # Tests and reference code
├── maps/                    # Saved bed maps (created at runtime)
├── requirements.txt         # Python dependencies (flexible versions)
├── requirements-lock.txt    # Pinned dependencies (security)
├── run.bat                 # Automatic launcher (Windows)
├── run.sh                  # Automatic launcher (Mac/Linux)
├── run_rpi.sh              # Automatic launcher (Raspberry Pi)
├── run_gui.sh              # Touchscreen GUI launcher (Raspberry Pi)
├── LICENSE                 # MIT License
├── agents.md               # Development rules (DDD/SOC)
└── README.md               # This file
```

**Key Points**:
- `src/` is a directory for source code organization (standard Python convention)
- `src/cncsorter/` is the actual Python package with all the application code
- Entry points (`main.py`, `test_menu.py`, etc.) are in `src/` for easy access
- The package name `cncsorter` is meaningful and describes the application

## Troubleshooting

### Running the Application

The application should always be run from the **repository root** using one of these methods:

```bash
# ✅ Method 1: Use the launcher scripts (recommended):
./run.sh               # Mac/Linux
./run_rpi.sh           # Raspberry Pi  
run.bat                # Windows
./run_gui.sh           # Touchscreen GUI

# ✅ Method 2: Run as a Python module:
python3 -m src.main

# ✅ Method 3: With arguments:
python3 -m src.main --camera 0
python3 -m src.main --cnc-mode serial --cnc-port /dev/ttyUSB0
```

**Why?** The code is organized with:
- `src/` - Source code directory (standard convention)
- `src/cncsorter/` - The actual Python package with domain, application, infrastructure, and presentation layers
- `src/main.py` - Entry point that imports from the `cncsorter` package

The launcher scripts automatically handle the correct execution from the repository root.

### Camera Not Found

- **Mac**: Check System Preferences → Security & Privacy → Camera
- **Raspberry Pi**: Enable camera with `sudo raspi-config` → Interface Options → Camera
- Try different camera indices: `python3 -m src.main --camera 1`

### CNC Connection Failed

- **Serial**: Check port name and permissions (`ls /dev/tty*`)
- **HTTP**: Verify FluidNC IP address and port
- Test connection without CNC: Use `--cnc-mode none`

For more detailed documentation, see:
- [README_FULL.md](README_FULL.md) - Complete system guide
- [INSTALL.md](INSTALL.md) - Installation and setup
- [GIMBAL_HARDWARE_GUIDE.md](GIMBAL_HARDWARE_GUIDE.md) - Hardware assembly
- [MULTI_CAMERA_GUIDE.md](MULTI_CAMERA_GUIDE.md) - Multi-camera setup

## Platform-Specific Notes

### Mac Development
- Requires Python 3.6 or higher
- OpenCV will be installed via pip
- Camera access may require permissions in System Preferences

### Raspberry Pi Production
- Tested on Raspberry Pi 3B+ and newer
- OpenCV installation may take 10-15 minutes on first run
- For better performance on older Pi models, consider installing `python3-opencv` from apt:
  ```bash
  sudo apt-get install python3-opencv python3-numpy
  ```
- Ensure camera module is enabled: `sudo raspi-config` → Interface Options → Camera

## Development Guidelines

See [agents.md](agents.md) for coding standards, DDD principles, and SOC guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
 
