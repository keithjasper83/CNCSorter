@echo off
REM CNCSorter - Automatic launcher with virtual environment
REM This script creates a virtual environment if needed and runs main.py

echo ========================================
echo CNCSorter - Object Detection System
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment.
        echo Please ensure Python is installed and added to PATH.
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Install/update dependencies
echo Checking and installing dependencies...
python -m pip install --upgrade pip >nul 2>&1

REM Install package in editable mode (makes cncsorter importable)
echo Installing cncsorter package in development mode...
pip install -e . >nul 2>&1

REM Use pinned requirements for security
if exist requirements-lock.txt (
    echo Installing from pinned requirements for security...
    pip install -r requirements-lock.txt
) else (
    echo Installing from requirements.txt...
    pip install -r requirements.txt
)
if errorlevel 1 (
    echo Warning: Some dependencies may not have installed correctly.
    echo.
)

echo.
echo Starting CNCSorter application...
echo Press 's' to save a snapshot, 'q' to quit.
echo ========================================
echo.

REM Run the application
python -m src.main

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat

echo.
echo Application closed.
pause
