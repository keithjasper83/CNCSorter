#!/usr/bin/env python3
"""
CNCSorter Interface Launcher.

Launches both the Touchscreen Interface (Port 8080) and
Desktop Operator Interface (Port 8081) concurrently.
"""

import multiprocessing
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from touchscreen_interface import main as run_touchscreen
from desktop_interface import main as run_desktop

def start_touchscreen():
    print("Starting Touchscreen Interface on port 8080...")
    sys.argv = [sys.argv[0]] # Reset args for NiceGUI
    run_touchscreen()

def start_desktop():
    print("Starting Desktop Interface on port 8081...")
    sys.argv = [sys.argv[0]] # Reset args for NiceGUI
    run_desktop()

if __name__ == "__main__":
    print("="*60)
    print("CNCSorter Multi-Interface Launcher")
    print("="*60)
    print("1. Touchscreen Interface: http://localhost:8080")
    print("2. Desktop Interface:     http://localhost:8081")
    print("="*60)

    # Start processes
    p_touch = multiprocessing.Process(target=start_touchscreen)
    p_desktop = multiprocessing.Process(target=start_desktop)

    try:
        p_touch.start()
        time.sleep(1) # Small delay to separate startup logs
        p_desktop.start()

        p_touch.join()
        p_desktop.join()
    except KeyboardInterrupt:
        print("\nShutting down interfaces...")
        p_touch.terminate()
        p_desktop.terminate()
        p_touch.join()
        p_desktop.join()
        print("Shutdown complete.")
