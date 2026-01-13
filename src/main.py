"""Main application entry point with live status display."""
import time
from typing import Optional

from cncsorter.infrastructure.vision import VisionSystem, ImageStitcher
from cncsorter.infrastructure.cnc_controller import FluidNCSerial, FluidNCHTTP, CNCController
from cncsorter.application.bed_mapping import BedMappingService
from cncsorter.presentation.live_display import LiveStatusDisplay


class CNCSorterApp:
    """Main CNCSorter application with live monitoring."""
    
    def __init__(
        self,
        camera_index: int = 0,
        cnc_mode: str = "none",  # "serial", "http", or "none"
        cnc_config: Optional[dict] = None
    ):
        """
        Initialize CNCSorter application.
        
        Args:
            camera_index: Camera device index
            cnc_mode: CNC connection mode ("serial", "http", or "none")
            cnc_config: CNC configuration dictionary
        """
        self.camera_index = camera_index
        self.cnc_mode = cnc_mode
        self.cnc_config = cnc_config or {}
        
        # Initialize components
        self.vision_system: Optional[VisionSystem] = None
        self.cnc_controller: Optional[CNCController] = None
        self.bed_mapping_service: Optional[BedMappingService] = None
        self.display: Optional[LiveStatusDisplay] = None
        
        # Settings
        self.threshold = 127
        self.min_area = 150
        
        # Performance tracking
        self.last_frame_time = time.time()
        self.fps = 0.0
    
    def initialize(self) -> bool:
        """
        Initialize all components.
        
        Returns:
            True if initialization successful
        """
        print("=" * 50)
        print("CNCSorter - Initializing...")
        print("=" * 50)
        
        # Initialize display
        self.display = LiveStatusDisplay()
        self.display.update(status="Initializing components...", stage="STARTUP", progress=10)
        self.display.wait_key(100)
        
        # Initialize vision system
        print(f"Initializing vision system (camera {self.camera_index})...")
        self.vision_system = VisionSystem(self.camera_index)
        if not self.vision_system.open_camera():
            print("\n" + "!"*60)
            print("INITIALIZATION FAILED: Cannot open camera")
            print("!"*60)
            print("\nThe application cannot start without a working camera.")
            print("Please fix the camera issue and try again.")
            print("!"*60 + "\n")
            
            if self.display:
                self.display.update(
                    status=f"FATAL: Cannot open camera {self.camera_index}",
                    stage="ERROR"
                )
                self.display.wait_key(5000)
            return False
        
        self.display.update(status="Camera initialized", stage="STARTUP", progress=30)
        self.display.wait_key(100)
        
        # Initialize CNC controller if requested
        if self.cnc_mode != "none":
            print(f"Initializing CNC controller ({self.cnc_mode})...")
            
            if self.cnc_mode == "serial":
                port = self.cnc_config.get('port', '/dev/ttyUSB0')
                baudrate = self.cnc_config.get('baudrate', 115200)
                self.cnc_controller = FluidNCSerial(port, baudrate)
            elif self.cnc_mode == "http":
                host = self.cnc_config.get('host', '192.168.1.100')
                http_port = self.cnc_config.get('http_port', 80)
                self.cnc_controller = FluidNCHTTP(host, http_port)
            
            if self.cnc_controller:
                self.display.update(status="Connecting to CNC...", stage="STARTUP", progress=50)
                self.display.wait_key(100)
                
                if not self.cnc_controller.connect():
                    print("Warning: Failed to connect to CNC controller")
                    self.display.update(
                        status="Warning: CNC not connected (continuing without)",
                        stage="STARTUP",
                        progress=60
                    )
                    self.cnc_controller = None
                    self.display.wait_key(2000)
                else:
                    self.display.update(status="CNC connected", stage="STARTUP", progress=70)
                    self.display.wait_key(100)
        
        # Initialize bed mapping service
        print("Initializing bed mapping service...")
        image_stitcher = ImageStitcher()
        self.bed_mapping_service = BedMappingService(
            self.vision_system,
            self.cnc_controller,
            image_stitcher
        )
        
        self.display.update(status="Ready to start", stage="READY", progress=100)
        self.display.wait_key(500)
        
        print("Initialization complete!")
        return True
    
    def update_fps(self):
        """Update FPS calculation."""
        current_time = time.time()
        delta = current_time - self.last_frame_time
        if delta > 0:
            self.fps = 1.0 / delta
        self.last_frame_time = current_time
    
    def run(self):
        """Run the main application loop."""
        if not self.initialize():
            print("\n" + "="*60)
            print("APPLICATION STARTUP FAILED")
            print("="*60)
            print("\nInitialization did not complete successfully.")
            print("Please resolve the issues above and try again.")
            print("="*60 + "\n")
            return
        
        print("\n" + "=" * 50)
        print("CNCSorter - Running")
        print("=" * 50)
        print("Controls:")
        print("  [SPACE] - Capture image and add to map")
        print("  [S]     - Start new bed map")
        print("  [M]     - Stitch current map images")
        print("  [V]     - Save current map")
        print("  [Q]     - Quit application")
        print("=" * 50 + "\n")
        
        current_map = None
        
        try:
            while True:
                self.update_fps()
                
                # Capture frame
                frame = self.vision_system.capture_frame()
                
                if frame is None:
                    self.display.update(
                        status="Error: No camera feed",
                        stage="ERROR",
                        fps=self.fps
                    )
                    key = self.display.wait_key(1)
                    if key == ord('q'):
                        break
                    continue
                
                # Detect objects in current frame
                detected_objects = self.vision_system.detect_objects(
                    frame,
                    self.threshold,
                    self.min_area
                )
                
                # Get CNC position if available
                cnc_pos = None
                if self.cnc_controller and self.cnc_controller.is_connected():
                    cnc_pos = self.cnc_controller.get_position()
                
                # Update display
                images_count = len(current_map.images) if current_map else 0
                total_objects = len(current_map.all_objects) if current_map else 0
                
                self.display.update(
                    frame=frame,
                    detected_objects=detected_objects,
                    status=f"Live view - {len(detected_objects)} objects in frame",
                    stage="READY" if current_map is None else "MAPPING",
                    cnc_pos=cnc_pos,
                    images_count=images_count,
                    objects_count=total_objects,
                    fps=self.fps
                )
                
                # Handle key press
                key = self.display.wait_key(1)
                
                if key == ord('q'):
                    print("Quit requested")
                    break
                
                elif key == ord('s'):
                    # Start new map
                    print("\n[KEY: S] Starting new bed map...")
                    current_map = self.bed_mapping_service.start_new_map()
                    self.display.update(
                        status="✓ New bed map started - Press SPACE to capture images",
                        stage="MAPPING",
                        progress=0
                    )
                    print("✓ Bed map started successfully")
                    time.sleep(1.5)
                
                elif key == ord(' '):
                    if current_map is None:
                        print("\n[KEY: SPACE] ERROR: No active map! Press 'S' to start a new map first")
                        self.display.update(
                            status="⚠ Cannot capture: Start a map first (Press S)",
                            stage="ERROR"
                        )
                        time.sleep(2)
                    else:
                        # Capture image
                        print(f"\n[KEY: SPACE] Capturing image {len(current_map.images) + 1}...")
                        self.display.update(status="📷 Capturing image...", stage="CAPTURING")
                        self.display.wait_key(100)
                        
                        captured = self.bed_mapping_service.capture_and_add_image(
                            threshold=self.threshold,
                            min_area=self.min_area,
                            progress_callback=lambda msg: self.display.update(status=msg)
                        )
                        
                        if captured:
                            progress = min(90, len(current_map.images) * 10)
                            status_msg = f"✓ Image {len(current_map.images)} captured: {len(captured.detected_objects)} objects"
                            self.display.update(
                                status=status_msg,
                                stage="MAPPING",
                                progress=progress
                            )
                            print(status_msg)
                        else:
                            print("✗ Failed to capture image")
                        time.sleep(1)
                
                elif key == ord('m'):
                    if current_map is None:
                        print("\n[KEY: M] ERROR: No active map! Press 'S' to start a new map first")
                        self.display.update(
                            status="⚠ Cannot stitch: Start a map first (Press S)",
                            stage="ERROR"
                        )
                        time.sleep(2)
                    elif len(current_map.images) < 2:
                        print(f"\n[KEY: M] ERROR: Need at least 2 images, currently have {len(current_map.images)}")
                        self.display.update(
                            status=f"⚠ Need at least 2 images to stitch (have {len(current_map.images)})",
                            stage="ERROR"
                        )
                        time.sleep(2)
                    else:
                        # Stitch images
                        print(f"\n[KEY: M] Stitching {len(current_map.images)} images...")
                        self.display.update(
                            status=f"🔗 Stitching {len(current_map.images)} images...",
                            stage="STITCHING",
                            progress=50
                        )
                        self.display.wait_key(100)
                        
                        success = self.bed_mapping_service.stitch_current_map(
                            progress_callback=lambda msg: self.display.update(status=msg)
                        )
                        
                        if success:
                            self.display.update(
                                status="✓ Stitching complete!",
                                stage="COMPLETE",
                                progress=100
                            )
                            print("✓ Stitching completed successfully")
                        else:
                            self.display.update(
                                status="✗ Stitching failed",
                                stage="ERROR"
                            )
                            print("✗ Stitching failed")
                        time.sleep(2)
                
                elif key == ord('v'):
                    if current_map is None:
                        print("\n[KEY: V] ERROR: No active map! Press 'S' to start a new map first")
                        self.display.update(
                            status="⚠ Cannot save: No active map (Press S to start)",
                            stage="ERROR"
                        )
                        time.sleep(2)
                    elif len(current_map.images) == 0:
                        print("\n[KEY: V] ERROR: No images to save!")
                        self.display.update(
                            status="⚠ Cannot save: No images captured yet",
                            stage="ERROR"
                        )
                        time.sleep(2)
                    else:
                        # Save map
                        print(f"\n[KEY: V] Saving map with {len(current_map.images)} images...")
                        self.display.update(status="💾 Saving map to disk...", stage="PROCESSING")
                        self.display.wait_key(100)
                        
                        if self.bed_mapping_service.save_map_images():
                            self.display.update(
                                status=f"✓ Map saved! ({len(current_map.images)} images)",
                                stage="COMPLETE"
                            )
                            print("✓ Map saved successfully")
                        else:
                            self.display.update(
                                status="✗ Failed to save map",
                                stage="ERROR"
                            )
                            print("✗ Failed to save map")
                        time.sleep(2)
        
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        print("\n" + "="*60)
        print("SHUTTING DOWN")
        print("="*60)
        
        if self.display:
            self.display.update(status="Shutting down...", stage="SHUTDOWN")
            self.display.wait_key(500)
        
        if self.vision_system:
            print("Closing camera...")
            self.vision_system.close_camera()
        
        if self.cnc_controller:
            print("Disconnecting CNC controller...")
            self.cnc_controller.disconnect()
        
        if self.display:
            print("Closing display...")
            self.display.close()
        
        print("="*60)
        print("Application closed successfully")
        print("="*60 + "\n")


def main():
    """Main entry point."""
    # Parse command line arguments for CNC configuration
    import argparse
    
    parser = argparse.ArgumentParser(description='CNCSorter - CNC Object Detection and Mapping')
    parser.add_argument('--camera', type=int, default=0, help='Camera device index')
    parser.add_argument('--cnc-mode', choices=['none', 'serial', 'http'], default='none',
                       help='CNC connection mode')
    parser.add_argument('--cnc-port', type=str, default='/dev/ttyUSB0',
                       help='Serial port for CNC (serial mode)')
    parser.add_argument('--cnc-baudrate', type=int, default=115200,
                       help='Serial baudrate for CNC (serial mode)')
    parser.add_argument('--cnc-host', type=str, default='192.168.1.100',
                       help='IP address for CNC (http mode)')
    parser.add_argument('--cnc-http-port', type=int, default=80,
                       help='HTTP port for CNC (http mode)')
    
    args = parser.parse_args()
    
    # Build CNC config
    cnc_config = {
        'port': args.cnc_port,
        'baudrate': args.cnc_baudrate,
        'host': args.cnc_host,
        'http_port': args.cnc_http_port
    }
    
    # Create and run application
    app = CNCSorterApp(
        camera_index=args.camera,
        cnc_mode=args.cnc_mode,
        cnc_config=cnc_config
    )
    
    app.run()


if __name__ == "__main__":
    main()
