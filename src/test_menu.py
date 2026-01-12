"""Interactive test menu for CNCSorter - Test individual functions without running full automation."""
import sys
import os
import time
import cv2
from typing import Optional

# Add parent directory to path for imports (relative to this file)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from domain.entities import CNCCoordinate
from infrastructure.vision import VisionSystem, ImageStitcher
from infrastructure.cnc_controller import FluidNCSerial, FluidNCHTTP, CNCController
from application.bed_mapping import BedMappingService
from presentation.live_display import LiveStatusDisplay


class InteractiveTestMenu:
    """Interactive menu for testing CNCSorter functions individually."""
    
    def __init__(self):
        """Initialize the test menu."""
        self.vision_system: Optional[VisionSystem] = None
        self.cnc_controller: Optional[CNCController] = None
        self.bed_mapping_service: Optional[BedMappingService] = None
        self.display: Optional[LiveStatusDisplay] = None
        
        # Test settings
        self.threshold = 127
        self.min_area = 150
        self.camera_index = 0
    
    def show_main_menu(self):
        """Display the main menu."""
        print("\n" + "=" * 60)
        print("CNCSorter - Interactive Test Menu")
        print("=" * 60)
        print("\nTest Individual Functions:")
        print("  1. Test Camera/Vision System")
        print("  2. Test Object Detection")
        print("  3. Test CNC Controller (Serial)")
        print("  4. Test CNC Controller (HTTP)")
        print("  5. Test Image Capture & Detection")
        print("  6. Test Image Stitching")
        print("  7. Test Bed Mapping Service")
        print("  8. Test Live Status Display")
        print("  9. Run Full Application")
        print("  0. Exit")
        print("=" * 60)
    
    def get_user_choice(self) -> str:
        """Get user menu choice."""
        try:
            choice = input("\nEnter your choice (0-9): ").strip()
            return choice
        except (KeyboardInterrupt, EOFError):
            return '0'
    
    def test_camera_vision(self):
        """Test 1: Camera and vision system initialization."""
        print("\n" + "=" * 60)
        print("TEST 1: Camera/Vision System")
        print("=" * 60)
        
        print(f"\nOpening camera {self.camera_index}...")
        vision = VisionSystem(self.camera_index)
        
        if not vision.open_camera():
            print("❌ FAILED: Could not open camera")
            return
        
        print("✓ Camera opened successfully")
        print("  Press 'q' to quit, 's' to save snapshot")
        
        try:
            while True:
                frame = vision.capture_frame()
                if frame is None:
                    print("❌ Failed to capture frame")
                    break
                
                # Display frame info
                print(f"\rFrame size: {frame.shape[1]}x{frame.shape[0]}", end='', flush=True)
                
                cv2.imshow("Camera Test", frame)
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    filename = f"camera_test_{int(time.time())}.jpg"
                    cv2.imwrite(filename, frame)
                    print(f"\n✓ Snapshot saved: {filename}")
        
        finally:
            vision.close_camera()
            cv2.destroyAllWindows()
            print("\n✓ Camera closed")
    
    def test_object_detection(self):
        """Test 2: Object detection algorithm."""
        print("\n" + "=" * 60)
        print("TEST 2: Object Detection")
        print("=" * 60)
        
        vision = VisionSystem(self.camera_index)
        if not vision.open_camera():
            print("❌ FAILED: Could not open camera")
            return
        
        # Create trackbars for threshold and min_area
        cv2.namedWindow("Object Detection Test")
        cv2.createTrackbar("Threshold", "Object Detection Test", self.threshold, 255, lambda x: None)
        cv2.createTrackbar("Min Area", "Object Detection Test", self.min_area, 5000, lambda x: None)
        
        print("✓ Detection system ready")
        print("  Adjust sliders to tune detection")
        print("  Press 'q' to quit")
        
        try:
            while True:
                frame = vision.capture_frame()
                if frame is None:
                    break
                
                # Get current settings
                threshold = cv2.getTrackbarPos("Threshold", "Object Detection Test")
                min_area = cv2.getTrackbarPos("Min Area", "Object Detection Test")
                
                # Detect objects
                objects = vision.detect_objects(frame, threshold, min_area)
                
                # Draw objects on frame
                result = vision.draw_objects_on_frame(frame, objects)
                
                # Add stats overlay
                cv2.putText(
                    result,
                    f"Objects: {len(objects)}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 255, 0),
                    2
                )
                
                cv2.imshow("Object Detection Test", result)
                
                print(f"\rDetected {len(objects)} objects | Threshold: {threshold} | Min Area: {min_area}", end='', flush=True)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        finally:
            vision.close_camera()
            cv2.destroyAllWindows()
            print("\n✓ Test complete")
    
    def test_cnc_serial(self):
        """Test 3: CNC controller via serial."""
        print("\n" + "=" * 60)
        print("TEST 3: CNC Controller (Serial)")
        print("=" * 60)
        
        port = input("Enter serial port [/dev/ttyUSB0]: ").strip() or '/dev/ttyUSB0'
        baudrate = input("Enter baudrate [115200]: ").strip() or '115200'
        
        try:
            baudrate = int(baudrate)
        except ValueError:
            print("❌ Invalid baudrate")
            return
        
        print(f"\nConnecting to {port} at {baudrate} baud...")
        cnc = FluidNCSerial(port, baudrate)
        
        if not cnc.connect():
            print("❌ FAILED: Could not connect to CNC")
            return
        
        print("✓ Connected to CNC")
        
        # Test getting position
        print("\nGetting CNC position...")
        pos = cnc.get_position()
        if pos:
            print(f"✓ Position: X={pos.x:.3f} Y={pos.y:.3f} Z={pos.z:.3f}")
        else:
            print("⚠ Could not get position")
        
        # Ask if user wants to test movement
        test_move = input("\nTest movement? (y/n): ").strip().lower()
        if test_move == 'y':
            x = float(input("  Enter X: "))
            y = float(input("  Enter Y: "))
            z = float(input("  Enter Z [0]: ") or "0")
            
            coord = CNCCoordinate(x, y, z)
            print(f"\nMoving to {coord.to_dict()}...")
            if cnc.move_to(coord):
                print("✓ Move command sent")
            else:
                print("❌ Move command failed")
        
        cnc.disconnect()
        print("\n✓ Disconnected from CNC")
    
    def test_cnc_http(self):
        """Test 4: CNC controller via HTTP."""
        print("\n" + "=" * 60)
        print("TEST 4: CNC Controller (HTTP)")
        print("=" * 60)
        
        host = input("Enter host IP [192.168.1.100]: ").strip() or '192.168.1.100'
        port = input("Enter port [80]: ").strip() or '80'
        
        try:
            port = int(port)
        except ValueError:
            print("❌ Invalid port")
            return
        
        print(f"\nConnecting to http://{host}:{port}...")
        cnc = FluidNCHTTP(host, port)
        
        if not cnc.connect():
            print("❌ FAILED: Could not connect to CNC via HTTP")
            return
        
        print("✓ Connected to CNC via HTTP")
        
        # Test getting position
        print("\nGetting CNC position...")
        pos = cnc.get_position()
        if pos:
            print(f"✓ Position: X={pos.x:.3f} Y={pos.y:.3f} Z={pos.z:.3f}")
        else:
            print("⚠ Could not get position")
        
        cnc.disconnect()
        print("\n✓ Disconnected from CNC")
    
    def test_image_capture_detection(self):
        """Test 5: Image capture with detection."""
        print("\n" + "=" * 60)
        print("TEST 5: Image Capture & Detection")
        print("=" * 60)
        
        vision = VisionSystem(self.camera_index)
        if not vision.open_camera():
            print("❌ FAILED: Could not open camera")
            return
        
        print("✓ Camera ready")
        print("  Press SPACE to capture, 'q' to quit")
        
        capture_count = 0
        
        try:
            while True:
                frame = vision.capture_frame()
                if frame is None:
                    break
                
                cv2.imshow("Capture Test - Press SPACE to capture", frame)
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    break
                elif key == ord(' '):
                    capture_count += 1
                    img_id = f"test_{capture_count:03d}"
                    
                    print(f"\nCapturing image {img_id}...")
                    captured = vision.create_captured_image(
                        frame, img_id, None, self.threshold, self.min_area
                    )
                    
                    print(f"✓ Captured: {len(captured.detected_objects)} objects detected")
                    
                    # Show detected objects
                    result = vision.draw_objects_on_frame(frame, captured.detected_objects)
                    cv2.imshow(f"Captured - {img_id}", result)
                    
                    # Save
                    filename = f"{img_id}_detected.jpg"
                    cv2.imwrite(filename, result)
                    print(f"✓ Saved: {filename}")
        
        finally:
            vision.close_camera()
            cv2.destroyAllWindows()
            print(f"\n✓ Test complete - {capture_count} images captured")
    
    def test_image_stitching(self):
        """Test 6: Image stitching."""
        print("\n" + "=" * 60)
        print("TEST 6: Image Stitching")
        print("=" * 60)
        
        vision = VisionSystem(self.camera_index)
        if not vision.open_camera():
            print("❌ FAILED: Could not open camera")
            return
        
        stitcher = ImageStitcher()
        images = []
        
        print("✓ Ready to capture images for stitching")
        print("  Press SPACE to capture image (need at least 2)")
        print("  Press 's' to stitch collected images")
        print("  Press 'q' to quit")
        
        try:
            while True:
                frame = vision.capture_frame()
                if frame is None:
                    break
                
                cv2.putText(
                    frame,
                    f"Images collected: {len(images)}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 255, 0),
                    2
                )
                
                cv2.imshow("Stitching Test", frame)
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    break
                elif key == ord(' '):
                    images.append(frame.copy())
                    print(f"✓ Image {len(images)} captured")
                elif key == ord('s') and len(images) >= 2:
                    print(f"\nStitching {len(images)} images...")
                    stitched = stitcher.stitch_images(images)
                    
                    if stitched is not None:
                        print("✓ Stitching successful!")
                        cv2.imshow("Stitched Result", stitched)
                        cv2.imwrite("stitched_test.jpg", stitched)
                        print("✓ Saved: stitched_test.jpg")
                    else:
                        print("❌ Stitching failed")
        
        finally:
            vision.close_camera()
            cv2.destroyAllWindows()
            print("\n✓ Test complete")
    
    def test_bed_mapping_service(self):
        """Test 7: Bed mapping service."""
        print("\n" + "=" * 60)
        print("TEST 7: Bed Mapping Service")
        print("=" * 60)
        
        vision = VisionSystem(self.camera_index)
        if not vision.open_camera():
            print("❌ FAILED: Could not open camera")
            return
        
        service = BedMappingService(vision, None, ImageStitcher())
        
        print("✓ Bed mapping service initialized")
        print("\nStarting new bed map...")
        bed_map = service.start_new_map()
        print(f"✓ Bed map created: {bed_map.map_id}")
        
        print("\n  Press SPACE to add image to map")
        print("  Press 's' to stitch map")
        print("  Press 'v' to save map")
        print("  Press 'q' to quit")
        
        try:
            while True:
                frame = vision.capture_frame()
                if frame is None:
                    break
                
                cv2.putText(
                    frame,
                    f"Images: {len(bed_map.images)} | Objects: {len(bed_map.all_objects)}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2
                )
                
                cv2.imshow("Bed Mapping Test", frame)
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    break
                elif key == ord(' '):
                    print(f"\nCapturing image {len(bed_map.images) + 1}...")
                    captured = service.capture_and_add_image(
                        self.threshold,
                        self.min_area,
                        lambda msg: print(f"  {msg}")
                    )
                    if captured:
                        print(f"✓ Added to map")
                elif key == ord('s') and len(bed_map.images) >= 2:
                    print("\nStitching map...")
                    if service.stitch_current_map(lambda msg: print(f"  {msg}")):
                        print("✓ Map stitched successfully")
                        if bed_map.stitched_image is not None:
                            cv2.imshow("Stitched Map", bed_map.stitched_image)
                    else:
                        print("❌ Stitching failed")
                elif key == ord('v'):
                    print("\nSaving map...")
                    if service.save_map_images():
                        print("✓ Map saved successfully")
                    else:
                        print("❌ Failed to save map")
        
        finally:
            vision.close_camera()
            cv2.destroyAllWindows()
            print("\n✓ Test complete")
    
    def test_live_display(self):
        """Test 8: Live status display."""
        print("\n" + "=" * 60)
        print("TEST 8: Live Status Display")
        print("=" * 60)
        
        vision = VisionSystem(self.camera_index)
        if not vision.open_camera():
            print("❌ FAILED: Could not open camera")
            return
        
        display = LiveStatusDisplay()
        
        print("✓ Display initialized")
        print("  Press 'q' to quit")
        print("  Watch the live status display update in real-time")
        
        stages = ["STARTUP", "READY", "CAPTURING", "PROCESSING", "STITCHING", "COMPLETE"]
        stage_idx = 0
        frame_count = 0
        last_time = time.time()
        
        try:
            while True:
                frame = vision.capture_frame()
                if frame is None:
                    break
                
                # Detect objects
                objects = vision.detect_objects(frame, self.threshold, self.min_area)
                
                # Calculate FPS
                current_time = time.time()
                fps = 1.0 / (current_time - last_time) if (current_time - last_time) > 0 else 0
                last_time = current_time
                
                # Cycle through stages every 60 frames
                frame_count += 1
                if frame_count % 60 == 0:
                    stage_idx = (stage_idx + 1) % len(stages)
                
                # Update display
                progress = (frame_count % 100)
                display.update(
                    frame=frame,
                    detected_objects=objects,
                    status=f"Testing display - Stage {stages[stage_idx]}",
                    stage=stages[stage_idx],
                    progress=progress,
                    cnc_pos=CNCCoordinate(10.5, 20.3, 5.0),
                    images_count=frame_count // 10,
                    objects_count=len(objects) * (frame_count // 10),
                    fps=fps
                )
                
                if display.wait_key(1) == ord('q'):
                    break
        
        finally:
            vision.close_camera()
            display.close()
            print("\n✓ Test complete")
    
    def run_full_application(self):
        """Test 9: Run the full application."""
        print("\n" + "=" * 60)
        print("TEST 9: Full Application")
        print("=" * 60)
        print("\nLaunching full CNCSorter application...")
        
        try:
            from main import main as app_main
        except ImportError as e:
            print("❌ Failed to import the main application module 'main'.")
            print(f"   Details: {e}")
            print("   Make sure that 'main.py' is present and importable.")
            return
        except Exception as e:
            # Catch any other unexpected errors during import (e.g., runtime errors in module code)
            print("❌ An unexpected error occurred while importing the main application module.")
            print(f"   Details: {e}")
            return

        try:
            app_main()
        except Exception as e:
            print("❌ An error occurred while running the full CNCSorter application.")
            print(f"   Details: {e}")
    
    def run(self):
        """Run the interactive test menu."""
        while True:
            self.show_main_menu()
            choice = self.get_user_choice()
            
            if choice == '0':
                print("\nExiting test menu. Goodbye!")
                break
            elif choice == '1':
                self.test_camera_vision()
            elif choice == '2':
                self.test_object_detection()
            elif choice == '3':
                self.test_cnc_serial()
            elif choice == '4':
                self.test_cnc_http()
            elif choice == '5':
                self.test_image_capture_detection()
            elif choice == '6':
                self.test_image_stitching()
            elif choice == '7':
                self.test_bed_mapping_service()
            elif choice == '8':
                self.test_live_display()
            elif choice == '9':
                self.run_full_application()
            else:
                print("❌ Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    menu = InteractiveTestMenu()
    menu.run()
