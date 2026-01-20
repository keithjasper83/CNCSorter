# CNCSorter Setup Guide for macOS

This guide will help you set up and run CNCSorter on your Mac for development and testing.

## Prerequisites

### 1. Install Homebrew (if not already installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Install Python 3.8 or higher

```bash
# Install Python 3 via Homebrew
brew install python@3.11

# Verify installation
python3 --version
```

### 3. Install Git (if not already installed)

```bash
brew install git
```

## Installation

### 1. Clone the Repository

```bash
cd ~/Documents  # or your preferred location
git clone https://github.com/keithjasper83/CNCSorter.git
cd CNCSorter
```

### 2. Run the Setup Script

The launcher scripts will automatically:
- Create a virtual environment
- Install all dependencies
- Install the cncsorter package in development mode

```bash
# For the main OpenCV-based interface
./run.sh

# For the touchscreen interface (simulator mode)
./run_touchscreen.sh
```

## Common Issues and Solutions

### Issue: "Permission denied" when running scripts

**Solution**: Make scripts executable

```bash
chmod +x run.sh
chmod +x run_touchscreen.sh
chmod +x run_gui.sh
```

### Issue: "python3: command not found"

**Solution**: Install Python 3 via Homebrew (see Prerequisites above)

### Issue: "venv/bin/activate: No such file or directory"

**Solution**: The virtual environment may not have been created successfully. Try:

```bash
# Delete existing venv folder
rm -rf venv

# Create new virtual environment manually
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install package
pip install -e .
```

### Issue: "Failed to create virtual environment"

**Possible causes**:
1. **Python not properly installed**: Reinstall Python via Homebrew
2. **Insufficient disk space**: Free up at least 500MB
3. **Corrupted Python installation**: Reinstall Python

**Solution**:
```bash
# Reinstall Python
brew reinstall python@3.11

# Try creating venv again
python3 -m venv venv
```

### Issue: Dependencies fail to install

**Solution**: Install dependencies manually

```bash
# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies one by one
pip install opencv-python
pip install numpy
pip install nicegui
pip install sqlalchemy

# Install all from requirements
pip install -r requirements.txt
```

## Running CNCSorter on Mac

### Main Application (OpenCV Interface)

```bash
./run.sh
```

This runs the main application with OpenCV-based object detection interface.

### Touchscreen Interface (Simulator Mode)

```bash
./run_touchscreen.sh
```

**What happens**:
- Automatically detects macOS
- Enables **simulator mode** (no hardware required)
- Opens web interface at http://localhost:8080
- All UI controls work without camera/CNC hardware
- Perfect for testing and configuration

**Simulator mode features**:
- ✓ Full UI navigation
- ✓ Simulated camera operations
- ✓ Simulated CNC control
- ✓ Random object detection for testing
- ✓ Configuration save/load
- ✓ All touch controls functional

### Configuration Wizard

```bash
python src/configure_machine.py
```

Interactive wizard for setting up machine limits and camera FOV.

## Development Workflow on Mac

1. **Test UI changes**: Run `./run_touchscreen.sh` and access http://localhost:8080
2. **Test configuration**: Use simulator mode to test all settings without hardware
3. **Test detection logic**: Mock objects are generated in simulator mode
4. **Deploy to Pi**: Once tested on Mac, deploy code to Raspberry Pi for hardware testing

## Accessing the Interface

### Touchscreen Interface
- **Local**: http://localhost:8080
- **From other devices**: http://<your-mac-ip>:8080

Find your Mac's IP:
```bash
ipconfig getifaddr en0  # WiFi
ipconfig getifaddr en1  # Ethernet
```

## Virtual Environment Management

### Activate virtual environment manually

```bash
source venv/bin/activate
```

### Deactivate virtual environment

```bash
deactivate
```

### Recreate virtual environment from scratch

```bash
# Remove old venv
rm -rf venv

# Create new one
python3 -m venv venv

# Activate
source venv/bin/activate

# Install package
pip install -e .

# Install dependencies
pip install -r requirements.txt
```

## Updating CNCSorter

```bash
# Pull latest changes
git pull

# Run installer again (updates dependencies)
./run_touchscreen.sh
```

## Troubleshooting

### Check Python installation

```bash
which python3
python3 --version
```

Should show Python 3.8 or higher.

### Check virtual environment

```bash
ls -la venv/bin/
```

Should show `activate`, `python`, `pip`, etc.

### Test package import

```bash
source venv/bin/activate
python -c "import cncsorter; print('Success!')"
```

### View detailed error messages

Run commands without the `--quiet` flag:

```bash
source venv/bin/activate
pip install -e .  # Shows all output
```

## Next Steps

1. **Run simulator mode**: Test the full interface on your Mac
2. **Configure settings**: Use the configuration wizard or UI
3. **Test workflows**: Try scan cycle, camera config, etc. in simulator
4. **Deploy to Pi**: Once satisfied, deploy to Raspberry Pi for hardware testing

## Getting Help

- Check `TOUCHSCREEN_INTERFACE.md` for interface documentation
- Check `INSTALL_GUIDE.md` for general installation info
- Check `RPI_TROUBLESHOOTING.md` for Raspberry Pi specific issues
- Open an issue on GitHub if problems persist
