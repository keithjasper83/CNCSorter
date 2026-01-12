# CNCSorter

CNC object identification and eventually pick and place based on computer vision.

## Features

- Real-time object detection using OpenCV
- Adjustable threshold and minimum area settings
- Live camera feed with visual feedback
- Automatic object counting and labeling
- Snapshot capability for documentation

## Quick Start

### Windows
Simply double-click `run.bat` to automatically:
- Create a virtual environment (if needed)
- Install required dependencies
- Launch the application

### Mac/Linux (Development)
```bash
./run.sh
```

### Raspberry Pi (Production)
```bash
./run_rpi.sh
```

All launchers will automatically:
- Create a virtual environment (if needed)
- Install required dependencies
- Launch the application

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

- **'s' key**: Save a snapshot of the current frame
- **'q' key**: Quit the application
- **Threshold slider**: Adjust detection sensitivity
- **Min Area slider**: Filter objects by minimum size

## Project Structure

```
CNCSorter/
├── src/              # Source code
│   └── main.py       # Main application
├── requirements.txt  # Python dependencies
├── run.bat          # Automatic launcher (Windows)
├── run.sh           # Automatic launcher (Mac/Linux)
├── run_rpi.sh       # Automatic launcher (Raspberry Pi)
├── LICENSE          # MIT License
├── agents.md        # Development rules and guidelines
└── README.md        # This file
```

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
 
