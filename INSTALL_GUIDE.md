# CNCSorter Installation and Usage Guide

## Quick Start

### Option 1: Using Launcher Scripts (Recommended)

The package is automatically installed when using the launcher scripts:

```bash
# Linux/Mac
./run.sh

# Raspberry Pi
./run_rpi.sh

# Windows
run.bat

# Touchscreen GUI
./run_gui.sh
```

### Option 2: Manual Installation

Install the package in development mode from the repository root:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package in editable mode
pip install -e .

# Run the application
python -m src.main
```

### Option 3: Direct Python Command

After installation, you can run directly:

```bash
python -m src.main --camera 0
python -m src.main --cnc-mode serial --cnc-port /dev/ttyUSB0
python -m src.main --cnc-mode http --cnc-host 192.168.1.100
```

## What Changed

**Problem**: `ModuleNotFoundError: No module named 'cncsorter'`

**Root Cause**: The `cncsorter` package wasn't properly installed, so Python couldn't find it when importing.

**Solution**: Added proper Python packaging infrastructure:
- `pyproject.toml` - Modern Python package configuration
- `setup.py` - Backward compatibility for editable installs
- `MANIFEST.in` - Package file inclusion rules
- `src/cncsorter/py.typed` - Type checking support marker

**Benefits**:
1. ✅ Package can be installed with `pip install -e .`
2. ✅ Works from any directory after installation
3. ✅ Proper dependency management
4. ✅ Type checking support
5. ✅ Follows PEP 517/518 standards

## Package Structure

```
CNCSorter/
├── pyproject.toml          # Package configuration
├── setup.py                # Editable install support
├── MANIFEST.in             # File inclusion rules
├── src/
│   └── cncsorter/         # Python package
│       ├── py.typed       # Type hint marker
│       ├── domain/
│       ├── application/
│       ├── infrastructure/
│       └── presentation/
└── run scripts automatically install package
```

## For Raspberry Pi Users

The `run_rpi.sh` script now:
1. Creates virtual environment
2. **Installs cncsorter package in editable mode** (NEW)
3. Installs dependencies
4. Runs the application

This fixes the `ModuleNotFoundError` you encountered.

## Development Workflow

```bash
# Clone repository
git clone https://github.com/keithjasper83/CNCSorter.git
cd CNCSorter

# Install in development mode
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Run application
python -m src.main

# Run tests (when implemented)
pytest

# Type checking (when configured)
mypy src/cncsorter

# Code formatting (when configured)
black src/cncsorter
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'cncsorter'"

**Solution 1**: Use the launcher scripts - they handle installation automatically
**Solution 2**: Install manually: `pip install -e .` from repository root
**Solution 3**: Check you're running from repository root, not src/

### "pip install -e . fails"

Ensure you have setuptools:
```bash
pip install --upgrade setuptools wheel
pip install -e .
```

### Virtual Environment Not Activating

**Linux/Mac**: `source venv/bin/activate`
**Windows**: `venv\Scripts\activate`

## Next Steps

This implementation completed **Feature 1.1** from IMPLEMENTATION_ROADMAP.md (Phase 1).

The package installation infrastructure is now in place, enabling:
- Proper imports of `cncsorter` package
- Development mode installations
- Future test framework integration
- CI/CD pipeline setup
