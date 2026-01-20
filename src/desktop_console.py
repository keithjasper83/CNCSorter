#!/usr/bin/env python3
"""
Desktop/Operator Console for CNCSorter
Integrates real camera with touchscreen interface for full development/testing on Mac.
Simulates CNC movements while using real object detection.
"""

import sys
import platform
import argparse
import cv2
import base64
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from nicegui import ui, app
from typing import Optional, List
import asyncio
from dataclasses import dataclass, asdict
import json
from datetime import datetime

# Import CNCSorter components
from cncsorter.infrastructure.vision import VisionSystem
from cncsorter.application.events import EventBus, ObjectsDetected, BedMapCompleted
from cncsorter.infrastructure.persistence import SQLiteDetectionRepository

@dataclass
class CameraConfig:
    """Camera configuration."""
    camera_id: int
    name: str
    mount_x: float
    mount_y: float
    mount_z: float
    visible_width: float
    visible_height: float
    tilt_angle: float
    pan_angle: float
    enabled: bool

@dataclass
class SystemConfig:
    """System configuration."""
    num_cameras: int
    cameras: List[CameraConfig]
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_min: float
    z_max: float
    safe_z: float
    overlap_percent: float
    grid_x: int
    grid_y: int


class DesktopConsole:
    """Desktop operator console with real camera integration."""

    def __init__(self, camera_index: int = 0, simulate_cnc: bool = True):
        """
        Initialize desktop console.

        Args:
            camera_index: Camera device index (0 for Mac webcam)
            simulate_cnc: True to simulate CNC movements, False for real CNC
        """
        self.camera_index = camera_index
        self.simulate_cnc = simulate_cnc

        # Hardware integration
        self.vision_system: Optional[VisionSystem] = None
        self.camera_active = False
        self.cnc_connected = False

        # System state
        self.system_status = "IDLE"
        self.detected_items = 0
        self.scan_progress = 0.0
        self.scanning = False

        # Configuration
        self.config = self._load_or_create_config()

        # EventBus and persistence
        self.event_bus = EventBus()
        self.repository = SQLiteDetectionRepository()

        # Subscribe to events
        self.event_bus.subscribe(ObjectsDetected, self._on_objects_detected)
        self.event_bus.subscribe(BedMapCompleted, self._on_bed_map_completed)

        # UI elements (will be set during UI creation)
        self.status_label = None
        self.items_label = None
        self.progress_bar = None
        self.camera_status_label = None
        self.cnc_status_label = None
        self.camera_feed_image = None

        # Detection loop
        self.detection_task = None

    def _load_or_create_config(self) -> SystemConfig:
        """Load or create default configuration."""
        config_path = Path("touchscreen_config.json")

        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    cameras = [CameraConfig(**cam) for cam in data['cameras']]
                    data['cameras'] = cameras
                    return SystemConfig(**data)
            except Exception as e:
                print(f"Error loading config: {e}")

        # Default configuration
        return SystemConfig(
            num_cameras=1,
            cameras=[
                CameraConfig(
                    camera_id=0,
                    name="Camera 0",
                    mount_x=400.0,
                    mount_y=200.0,
                    mount_z=300.0,
                    visible_width=400.0,
                    visible_height=300.0,
                    tilt_angle=0.0,
                    pan_angle=0.0,
                    enabled=True
                )
            ],
            x_min=0.0, x_max=800.0,
            y_min=0.0, y_max=400.0,
            z_min=0.0, z_max=300.0,
            safe_z=50.0,
            overlap_percent=20.0,
            grid_x=3, grid_y=2
        )

    def _save_config(self):
        """Save configuration to JSON file."""
        config_path = Path("touchscreen_config.json")
        try:
            data = asdict(self.config)
            with open(config_path, 'w') as f:
                json.dump(data, f, indent=2)
            ui.notify("✓ Configuration saved", type='positive')
        except Exception as e:
            ui.notify(f"✗ Save failed: {e}", type='negative')

    def _on_objects_detected(self, event: ObjectsDetected):
        """Handle ObjectsDetected event."""
        self.detected_items += len(event.detected_objects)
        if self.items_label:
            self.items_label.set_text(f"Detected Items: {self.detected_items}")

        # Save to repository
        for obj in event.detected_objects:
            try:
                self.repository.save(obj)
            except Exception as e:
                print(f"Error saving detection: {e}")

    def _on_bed_map_completed(self, event: BedMapCompleted):
        """Handle BedMapCompleted event."""
        self.system_status = "COMPLETE"
        self.scanning = False
        if self.status_label:
            self.status_label.set_text(f"Status: {self.system_status}")
        ui.notify(f"✓ Bed mapping complete! {event.total_objects} objects detected", type='positive')

    async def _detection_loop(self):
        """Continuous detection loop using real camera."""
        if not self.vision_system or not self.camera_active:
            return

        while self.camera_active:
            try:
                # Capture frame
                ret, frame = self.vision_system.capture.read()
                if not ret:
                    await asyncio.sleep(0.1)
                    continue

                # Detect objects
                objects = self.vision_system.detect_objects(frame, threshold=127, min_area=150)

                # Update camera feed display
                if self.camera_feed_image and frame is not None:
                    # Draw detections on frame
                    display_frame = frame.copy()
                    for obj in objects:
                        # Draw bounding box
                        x, y, w, h = obj.bounding_box
                        cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        # Draw center point
                        cv2.circle(display_frame, (int(obj.center.x), int(obj.center.y)), 5, (0, 0, 255), -1)

                    # Convert to base64 for display
                    _, buffer = cv2.imencode('.jpg', display_frame)
                    img_str = base64.b64encode(buffer).decode()
                    self.camera_feed_image.set_source(f'data:image/jpeg;base64,{img_str}')

                # Publish event if objects detected
                if objects and self.scanning:
                    event = ObjectsDetected(
                        detected_objects=objects,
                        image_id=f"frame_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        camera_index=self.camera_index
                    )
                    self.event_bus.publish(event)

                await asyncio.sleep(0.1)  # ~10 FPS

            except Exception as e:
                print(f"Detection loop error: {e}")
                await asyncio.sleep(1.0)

    def start_camera(self):
        """Start the camera."""
        if self.camera_active:
            ui.notify("Camera already active", type='warning')
            return

        try:
            self.vision_system = VisionSystem(self.camera_index)
            if self.vision_system.open_camera():
                self.camera_active = True
                if self.camera_status_label:
                    self.camera_status_label.set_text("Camera: ✓ Active")
                ui.notify("✓ Camera started successfully", type='positive')

                # Start detection loop
                self.detection_task = asyncio.create_task(self._detection_loop())
            else:
                ui.notify("✗ Failed to open camera", type='negative')
        except Exception as e:
            ui.notify(f"✗ Camera error: {e}", type='negative')

    def stop_camera(self):
        """Stop the camera."""
        if not self.camera_active:
            ui.notify("Camera not active", type='warning')
            return

        self.camera_active = False
        if self.detection_task:
            self.detection_task.cancel()
            self.detection_task = None

        if self.vision_system and self.vision_system.capture:
            self.vision_system.capture.release()

        if self.camera_status_label:
            self.camera_status_label.set_text("Camera: ○ Inactive")

        ui.notify("Camera stopped", type='info')

    def connect_cnc(self):
        """Connect to CNC (simulated on Mac)."""
        if self.cnc_connected:
            ui.notify("CNC already connected", type='warning')
            return

        if self.simulate_cnc:
            # Simulated CNC connection
            self.cnc_connected = True
            if self.cnc_status_label:
                self.cnc_status_label.set_text("CNC: ✓ Connected (Simulated)")
            ui.notify("✓ CNC connected (simulated mode)", type='positive')
        else:
            # Real CNC connection would go here
            ui.notify("Real CNC connection not yet implemented", type='warning')

    def disconnect_cnc(self):
        """Disconnect from CNC."""
        if not self.cnc_connected:
            ui.notify("CNC not connected", type='warning')
            return

        self.cnc_connected = False
        if self.cnc_status_label:
            self.cnc_status_label.set_text("CNC: ○ Disconnected")
        ui.notify("CNC disconnected", type='info')

    def start_scan_cycle(self):
        """Start scanning cycle with real detection."""
        if not self.camera_active:
            ui.notify("⚠ Start camera first", type='warning')
            return

        if self.scanning:
            ui.notify("Scan already in progress", type='warning')
            return

        self.scanning = True
        self.system_status = "SCANNING"
        self.detected_items = 0
        self.scan_progress = 0.0

        if self.status_label:
            self.status_label.set_text(f"Status: {self.system_status}")
        if self.progress_bar:
            self.progress_bar.set_value(0.0)

        ui.notify("▶ Scan cycle started - detecting objects from live camera", type='positive')

        # Simulate scanning progress
        asyncio.create_task(self._simulate_scan_progress())

    async def _simulate_scan_progress(self):
        """Simulate scan progress (CNC movements simulated)."""
        total_positions = self.config.grid_x * self.config.grid_y

        for i in range(total_positions):
            if not self.scanning:
                break

            # Simulate CNC movement to next position
            progress = (i + 1) / total_positions
            self.scan_progress = progress

            if self.progress_bar:
                self.progress_bar.set_value(progress)

            await asyncio.sleep(2.0)  # 2 seconds per position

        # Complete scan
        if self.scanning:
            self.scanning = False
            event = BedMapCompleted(
                bed_map_id=f"map_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                total_objects=self.detected_items,
                image_count=total_positions
            )
            self.event_bus.publish(event)

    def stop_scan(self):
        """Stop scanning cycle."""
        if not self.scanning:
            ui.notify("No scan in progress", type='warning')
            return

        self.scanning = False
        self.system_status = "IDLE"
        if self.status_label:
            self.status_label.set_text(f"Status: {self.system_status}")
        ui.notify("⏹ Scan stopped", type='info')

    def reset_system(self):
        """Reset system state."""
        self.scanning = False
        self.detected_items = 0
        self.scan_progress = 0.0
        self.system_status = "IDLE"

        if self.status_label:
            self.status_label.set_text(f"Status: {self.system_status}")
        if self.items_label:
            self.items_label.set_text(f"Detected Items: {self.detected_items}")
        if self.progress_bar:
            self.progress_bar.set_value(0.0)

        ui.notify("🔄 System reset", type='info')

    def emergency_stop(self):
        """Emergency stop - halt everything."""
        self.stop_scan()
        self.stop_camera()
        self.disconnect_cnc()

        self.system_status = "EMERGENCY STOP"
        if self.status_label:
            self.status_label.set_text(f"Status: {self.system_status}")

        ui.notify("🛑 EMERGENCY STOP ACTIVATED", type='negative')

    def build_ui(self):
        """Build the desktop console UI."""
        # Platform info banner
        platform_info = f"🖥️ {platform.system()} - Desktop Console with Real Camera Detection"
        if self.simulate_cnc:
            platform_info += " (CNC Simulated)"

        with ui.header().classes('bg-blue-900 text-white'):
            ui.label('CNCSorter - Desktop/Operator Console').classes('text-2xl font-bold')

        # Emergency stop button (always visible)
        with ui.row().classes('w-full justify-end p-2 bg-red-100'):
            ui.button('🛑 EMERGENCY STOP', on_click=self.emergency_stop).props('color=red size=lg').classes('font-bold')

        # Platform banner
        ui.label(platform_info).classes('text-lg bg-blue-100 p-3 rounded')

        # Main content
        with ui.row().classes('w-full gap-4'):
            # Left column - Controls and Status
            with ui.card().classes('w-1/2'):
                ui.label('System Control').classes('text-xl font-bold')

                # Hardware control
                with ui.card().classes('bg-gray-100 p-4'):
                    ui.label('Hardware Control').classes('text-lg font-semibold')

                    self.camera_status_label = ui.label('Camera: ○ Inactive')
                    with ui.row():
                        ui.button('📷 START CAMERA', on_click=self.start_camera).props('color=green')
                        ui.button('⏹ STOP CAMERA', on_click=self.stop_camera).props('color=orange')

                    ui.separator()

                    self.cnc_status_label = ui.label('CNC: ○ Disconnected')
                    with ui.row():
                        ui.button('🔌 CONNECT CNC', on_click=self.connect_cnc).props('color=blue')
                        ui.button('🔌 DISCONNECT', on_click=self.disconnect_cnc).props('color=gray')

                # System status
                with ui.card().classes('bg-blue-50 p-4'):
                    ui.label('System Status').classes('text-lg font-semibold')
                    self.status_label = ui.label(f'Status: {self.system_status}')
                    self.items_label = ui.label(f'Detected Items: {self.detected_items}')
                    ui.label('Scan Progress:')
                    self.progress_bar = ui.linear_progress(value=self.scan_progress).props('size=20px color=primary')

                # Main actions
                with ui.card().classes('p-4'):
                    ui.label('Main Actions').classes('text-lg font-semibold')
                    ui.button('▶️ START SCAN CYCLE', on_click=self.start_scan_cycle).props('color=green size=lg').classes('w-full h-20')
                    ui.button('🔧 PICK & PLACE', on_click=lambda: ui.notify('Pick & place not yet implemented', type='warning')).props('color=blue size=lg').classes('w-full h-20 mt-2')
                    with ui.row().classes('w-full gap-2 mt-2'):
                        ui.button('⏹ STOP', on_click=self.stop_scan).props('color=orange')
                        ui.button('🔄 RESET', on_click=self.reset_system).props('color=gray')

            # Right column - Camera Feed
            with ui.card().classes('w-1/2'):
                ui.label('Live Camera Feed').classes('text-xl font-bold')
                ui.label('Real-time object detection from webcam').classes('text-sm text-gray-600')

                with ui.card().classes('bg-black flex items-center justify-center').style('height: 600px'):
                    self.camera_feed_image = ui.image().classes('max-w-full max-h-full')

        # Footer with tips
        with ui.footer().classes('bg-gray-800 text-white p-4'):
            ui.label('💡 Tips: Start camera → Connect CNC → Start Scan Cycle to detect objects. Mac webcam works perfectly for testing!').classes('text-sm')


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='CNCSorter Desktop/Operator Console')
    parser.add_argument('--camera', type=int, default=0, help='Camera index (default: 0)')
    parser.add_argument('--real-cnc', action='store_true', help='Use real CNC instead of simulation')
    parser.add_argument('--port', type=int, default=8080, help='Port number (default: 8080)')
    parser.add_argument('--fullscreen', action='store_true', help='Run in fullscreen mode')

    args = parser.parse_args()

    print("=" * 70)
    print("CNCSorter - Desktop/Operator Console")
    print("=" * 70)
    print(f"Platform: {platform.system()}")
    print(f"Camera: {args.camera}")
    print(f"CNC Mode: {'Real' if args.real_cnc else 'Simulated'}")
    print(f"Port: {args.port}")
    print("=" * 70)
    print("\n🚀 Starting desktop console...")
    print(f"📱 Access at: http://localhost:{args.port}")
    print("\n💡 This mode uses your Mac webcam for REAL object detection")
    print("   while simulating CNC movements for faster development!\n")

    # Create console
    console = DesktopConsole(
        camera_index=args.camera,
        simulate_cnc=not args.real_cnc
    )

    # Build UI
    console.build_ui()

    # Run
    native_mode = args.fullscreen
    ui.run(
        title='CNCSorter Desktop Console',
        port=args.port,
        reload=False,
        show=True,
        native=native_mode
    )


if __name__ == '__main__':
    main()
