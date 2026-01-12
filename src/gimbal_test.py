#!/usr/bin/env python3
"""
Interactive test program for gimbal control system.

Tests all gimbal functionality without requiring the full CNCSorter application.
"""

import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.gimbal_controller import (
    TwoAxisGimbal, ThreeAxisGimbal, GimbalPosition,
    AutomatedScanController, GPIO_AVAILABLE
)


def print_menu():
    """Print test menu."""
    print("\n" + "=" * 60)
    print(" GIMBAL CONTROL TEST MENU")
    print("=" * 60)
    print("1. Initialize 2-Axis Gimbal")
    print("2. Initialize 3-Axis Gimbal")
    print("3. Test Manual Positioning")
    print("4. Test Preset Positions")
    print("5. Test Panorama Scan")
    print("6. Test Full Coverage Scan")
    print("7. Test Adaptive Scan (Simulated)")
    print("8. Test Smooth Motion")
    print("9. Continuous Pan Test")
    print("10. Get Current Position")
    print("11. Center Gimbal")
    print("0. Exit and Cleanup")
    print("=" * 60)
    if not GPIO_AVAILABLE:
        print("⚠️  WARNING: GPIO not available - running in simulation mode")
    print()


def test_manual_positioning(gimbal):
    """Test manual positioning with user input."""
    print("\n--- Manual Positioning Test ---")
    try:
        pan = float(input("Enter pan angle (-90 to 90): "))
        tilt = float(input("Enter tilt angle (-90 to 90): "))
        
        position = GimbalPosition(pan=pan, tilt=tilt)
        print(f"Moving to: {position}")
        gimbal.move_to(position, smooth=True)
        print("✓ Movement complete")
        
        current = gimbal.get_current_position()
        print(f"Current position: {current}")
        
    except ValueError:
        print("❌ Invalid input. Please enter numeric values.")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_presets(gimbal):
    """Test all preset positions."""
    if not hasattr(gimbal, 'PRESETS'):
        print("❌ Presets not available for this gimbal type")
        return
    
    print("\n--- Testing Preset Positions ---")
    presets = list(gimbal.PRESETS.keys())
    
    print(f"Available presets: {', '.join(presets)}")
    print("\nTesting each preset with 2-second pause...")
    
    for preset_name in presets:
        position = gimbal.PRESETS[preset_name]
        print(f"\n→ {preset_name}: {position}")
        gimbal.move_to_preset(preset_name, smooth=True)
        time.sleep(2)
    
    print("\n✓ All presets tested")
    gimbal.center()


def test_panorama_scan(gimbal):
    """Test panorama scanning."""
    if not hasattr(gimbal, 'panorama_scan'):
        print("❌ Panorama scan not available for this gimbal type")
        return
    
    print("\n--- Panorama Scan Test ---")
    print("Scanning from -90° to +90° pan at -45° tilt")
    print("7 positions, 1 second each\n")
    
    positions = gimbal.panorama_scan(
        tilt=-45,
        pan_range=(-90, 90),
        steps=7,
        dwell_time=1.0
    )
    
    print(f"\n✓ Scanned {len(positions)} positions:")
    for i, pos in enumerate(positions, 1):
        print(f"  {i}. {pos}")
    
    gimbal.center()


def test_full_coverage(gimbal):
    """Test full coverage scan."""
    print("\n--- Full Coverage Scan Test ---")
    scanner = AutomatedScanController(gimbal)
    
    print("Scanning multiple tilt angles...")
    print("Tilt angles: -90°, -60°, -30°")
    print("Pan range: -75° to +75°")
    print("5 positions per tilt angle\n")
    
    positions = scanner.full_coverage_scan(
        tilt_angles=[-90, -60, -30],
        pan_range=(-75, 75),
        pan_steps=5
    )
    
    print(f"\n✓ Scanned {len(positions)} total positions")
    gimbal.center()


def test_adaptive_scan(gimbal):
    """Test adaptive scan with simulated detection."""
    print("\n--- Adaptive Scan Test (Simulated) ---")
    scanner = AutomatedScanController(gimbal)
    
    # Simulated detection callback
    detection_count = 0
    def simulated_detection():
        nonlocal detection_count
        detection_count = (detection_count + 1) % 10  # Cycle 0-9
        return detection_count
    
    initial_positions = [
        GimbalPosition(pan=-60, tilt=-45),
        GimbalPosition(pan=0, tilt=-45),
        GimbalPosition(pan=60, tilt=-45),
    ]
    
    print("Initial positions to scan:")
    for pos in initial_positions:
        print(f"  • {pos}")
    print("\nAreas with 5+ detected objects will trigger detailed scans\n")
    
    positions = scanner.adaptive_scan(
        initial_positions=initial_positions,
        detection_callback=simulated_detection,
        threshold=5
    )
    
    print(f"\n✓ Adaptive scan complete: {len(positions)} total positions")
    
    # Show scan history
    print("\nScan history (position, object count):")
    for pos, count in scanner.scan_history:
        marker = "🔍" if count >= 5 else "  "
        print(f"{marker} {pos}: {count} objects")
    
    best_pos = scanner.return_to_best_position()
    if best_pos:
        print(f"\n✓ Returned to best position: {best_pos}")
    
    gimbal.center()


def test_smooth_motion(gimbal):
    """Test smooth vs instant motion."""
    print("\n--- Smooth Motion Test ---")
    
    print("1. Instant movement (smooth=False)")
    gimbal.move_to(GimbalPosition(pan=-90, tilt=-45), smooth=False)
    time.sleep(1)
    
    print("2. Smooth movement (smooth=True, speed=30°/s)")
    gimbal.move_to(GimbalPosition(pan=90, tilt=-45), smooth=True, speed=30)
    time.sleep(1)
    
    print("3. Slow smooth movement (speed=10°/s)")
    gimbal.move_to(GimbalPosition(pan=0, tilt=0), smooth=True, speed=10)
    
    print("\n✓ Motion test complete")


def test_continuous_pan(gimbal):
    """Test continuous pan movement."""
    print("\n--- Continuous Pan Test ---")
    print("Panning continuously from -90° to +90° and back")
    print("Press Ctrl+C to stop\n")
    
    try:
        direction = 1
        angle = 0
        
        while True:
            angle += direction * 5
            
            if angle >= 90:
                angle = 90
                direction = -1
                print("← Reversing direction (panning left)")
            elif angle <= -90:
                angle = -90
                direction = 1
                print("→ Reversing direction (panning right)")
            
            gimbal.move_to(GimbalPosition(pan=angle, tilt=-45), smooth=False)
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n✓ Continuous pan stopped")
        gimbal.center()


def main():
    """Main test program."""
    gimbal = None
    gimbal_type = None
    
    try:
        while True:
            print_menu()
            choice = input("Select option: ").strip()
            
            if choice == "0":
                print("\nExiting...")
                break
            
            elif choice == "1":
                print("\n--- Initializing 2-Axis Gimbal ---")
                pan_pin = int(input("Enter pan servo GPIO pin (default 17): ") or "17")
                tilt_pin = int(input("Enter tilt servo GPIO pin (default 18): ") or "18")
                
                try:
                    gimbal = TwoAxisGimbal(pan_pin=pan_pin, tilt_pin=tilt_pin)
                    gimbal_type = "2-axis"
                    print(f"✓ 2-axis gimbal initialized (GPIO {pan_pin}, {tilt_pin})")
                except Exception as e:
                    print(f"❌ Failed to initialize gimbal: {e}")
            
            elif choice == "2":
                print("\n--- Initializing 3-Axis Gimbal ---")
                pan_pin = int(input("Enter pan servo GPIO pin (default 17): ") or "17")
                tilt_pin = int(input("Enter tilt servo GPIO pin (default 18): ") or "18")
                roll_pin = int(input("Enter roll servo GPIO pin (default 27): ") or "27")
                
                try:
                    gimbal = ThreeAxisGimbal(pan_pin=pan_pin, tilt_pin=tilt_pin, roll_pin=roll_pin)
                    gimbal_type = "3-axis"
                    print(f"✓ 3-axis gimbal initialized (GPIO {pan_pin}, {tilt_pin}, {roll_pin})")
                except Exception as e:
                    print(f"❌ Failed to initialize gimbal: {e}")
            
            elif choice == "3":
                if gimbal is None:
                    print("❌ Please initialize a gimbal first (option 1 or 2)")
                else:
                    test_manual_positioning(gimbal)
            
            elif choice == "4":
                if gimbal is None:
                    print("❌ Please initialize a gimbal first (option 1 or 2)")
                else:
                    test_presets(gimbal)
            
            elif choice == "5":
                if gimbal is None:
                    print("❌ Please initialize a gimbal first (option 1 or 2)")
                else:
                    test_panorama_scan(gimbal)
            
            elif choice == "6":
                if gimbal is None:
                    print("❌ Please initialize a gimbal first (option 1 or 2)")
                else:
                    test_full_coverage(gimbal)
            
            elif choice == "7":
                if gimbal is None:
                    print("❌ Please initialize a gimbal first (option 1 or 2)")
                else:
                    test_adaptive_scan(gimbal)
            
            elif choice == "8":
                if gimbal is None:
                    print("❌ Please initialize a gimbal first (option 1 or 2)")
                else:
                    test_smooth_motion(gimbal)
            
            elif choice == "9":
                if gimbal is None:
                    print("❌ Please initialize a gimbal first (option 1 or 2)")
                else:
                    test_continuous_pan(gimbal)
            
            elif choice == "10":
                if gimbal is None:
                    print("❌ Please initialize a gimbal first (option 1 or 2)")
                else:
                    pos = gimbal.get_current_position()
                    print(f"\nCurrent position: {pos}")
            
            elif choice == "11":
                if gimbal is None:
                    print("❌ Please initialize a gimbal first (option 1 or 2)")
                else:
                    print("\nCentering gimbal...")
                    gimbal.center()
                    print("✓ Gimbal centered")
            
            else:
                print("❌ Invalid option. Please select 0-11.")
            
            if choice not in ["0", "1", "2"]:
                input("\nPress Enter to continue...")
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if gimbal is not None:
            print("\nCleaning up gimbal...")
            gimbal.cleanup()
            print("✓ Cleanup complete")


if __name__ == "__main__":
    main()
