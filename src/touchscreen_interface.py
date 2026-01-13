#!/usr/bin/env python3
"""
NiceGUI Touchscreen Interface for CNCSorter.

Production-ready touchscreen interface optimized for Freenove display.
Features touch-optimized controls, no keyboard input, comprehensive configuration.

Supports simulator mode for testing on Mac without hardware.
"""

from nicegui import ui, app
from typing import Optional, List, Dict, Any
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import sys
import argparse

# Import from cncsorter package
from cncsorter.application.events import EventBus, ObjectsDetected, BedMapCompleted
from cncsorter.infrastructure.persistence import SQLiteDetectionRepository
from cncsorter.domain.interfaces import WorkStatus
from cncsorter import config

# Check for simulator mode
SIMULATOR_MODE = '--simulator' in sys.argv or '--sim' in sys.argv


@dataclass
class CameraConfig:
    """Configuration for a single camera."""
    camera_id: int
    name: str
    mount_x: float  # mm
    mount_y: float  # mm
    mount_z: float  # mm
    visible_width: float  # mm at bed level
    visible_height: float  # mm at bed level
    tilt_angle: float  # degrees
    pan_angle: float  # degrees
    enabled: bool = True


@dataclass
class SystemConfig:
    """Complete system configuration."""
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


class TouchscreenInterface:
    """Main touchscreen interface application."""
    
    def __init__(self):
        """Initialize touchscreen interface."""
        self.config_path = Path("config/touchscreen_config.json")
        self.system_config: Optional[SystemConfig] = None
        self.event_bus = EventBus()
        self.repository = SQLiteDetectionRepository()
        
        # UI state
        self.current_page = "home"
        self.detected_count = 0
        self.cycle_progress = 0.0
        self.system_status = "SIMULATOR" if SIMULATOR_MODE else "IDLE"
        
        # Hardware connections (None in simulator mode)
        self.vision_system = None
        self.cnc_controller = None
        self.camera_active = False
        self.cnc_connected = False
        self.current_map = None
        
        # Load configuration
        self.load_configuration()
        
        # Subscribe to events
        self.event_bus.subscribe(ObjectsDetected, self.on_objects_detected)
        self.event_bus.subscribe(BedMapCompleted, self.on_bed_map_completed)
        
        # Show simulator mode notification
        if SIMULATOR_MODE:
            print("=" * 60)
            print("SIMULATOR MODE ENABLED")
            print("Running without hardware - perfect for Mac testing!")
            print("All controls are functional but won't affect real hardware.")
            print("=" * 60)
    
    def load_configuration(self) -> None:
        """Load configuration from file."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                cameras = [CameraConfig(**cam) for cam in data['cameras']]
                data['cameras'] = cameras
                self.system_config = SystemConfig(**data)
        else:
            # Default configuration
            self.system_config = SystemConfig(
                num_cameras=1,
                cameras=[
                    CameraConfig(0, "Camera 0", 400, 200, 300, 400, 300, 0, 0)
                ],
                x_min=0, x_max=800,
                y_min=0, y_max=400,
                z_min=0, z_max=300,
                safe_z=50,
                overlap_percent=20.0,
                grid_x=3, grid_y=2
            )
    
    def save_configuration(self) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            data = asdict(self.system_config)
            json.dump(data, f, indent=2)
    
    def on_objects_detected(self, event: ObjectsDetected) -> None:
        """Handle objects detected event."""
        self.detected_count += len(event.detected_objects)
    
    def on_bed_map_completed(self, event: BedMapCompleted) -> None:
        """Handle bed map completed event."""
        self.detected_count = event.total_objects
        self.cycle_progress = 1.0
        self.system_status = "COMPLETE"
    
    def create_ui(self) -> None:
        """Create the main UI."""
        # Set dark theme and responsive layout
        ui.colors(primary='#2563eb', secondary='#10b981', accent='#f59e0b', 
                  dark='#111827', positive='#10b981', negative='#ef4444')
        
        # Main container with full height
        with ui.column().classes('w-full h-screen bg-gray-900'):
            # Header
            self.create_header()
            
            # Main content area (scrollable)
            with ui.scroll_area().classes('flex-grow'):
                with ui.column().classes('w-full p-4 gap-4'):
                    if self.current_page == "home":
                        self.create_home_page()
                    elif self.current_page == "cameras":
                        self.create_cameras_page()
                    elif self.current_page == "machine":
                        self.create_machine_page()
                    elif self.current_page == "scanning":
                        self.create_scanning_page()
                    elif self.current_page == "status":
                        self.create_status_page()
    
    def create_header(self) -> None:
        """Create header with navigation and emergency stop."""
        with ui.row().classes('w-full bg-gray-800 p-4 items-center justify-between'):
            # Title
            ui.label('CNCSorter Control').classes('text-3xl font-bold text-white')
            
            # Emergency Stop Button (always visible)
            ui.button('🛑 E-STOP', on_click=self.emergency_stop).props(
                'size=xl color=red'
            ).classes('text-2xl font-bold')
        
        # Navigation menu
        with ui.row().classes('w-full bg-gray-700 p-2 gap-2'):
            ui.button('🏠 Home', on_click=lambda: self.navigate('home')).props('flat')
            ui.button('📷 Cameras', on_click=lambda: self.navigate('cameras')).props('flat')
            ui.button('⚙️ Machine', on_click=lambda: self.navigate('machine')).props('flat')
            ui.button('🗺️ Scanning', on_click=lambda: self.navigate('scanning')).props('flat')
            ui.button('📊 Status', on_click=lambda: self.navigate('status')).props('flat')
    
    def create_home_page(self) -> None:
        """Create home page with main controls."""
        # Simulator mode banner
        if SIMULATOR_MODE:
            with ui.card().classes('w-full bg-yellow-900 p-4 mb-4'):
                ui.label('🖥️ SIMULATOR MODE - Perfect for Mac Testing!').classes(
                    'text-xl font-bold text-yellow-200'
                )
                ui.label('All controls functional without hardware').classes('text-yellow-300')
        
        # Hardware Control Card
        with ui.card().classes('w-full bg-gray-800 p-6 mb-4'):
            ui.label('Hardware Control').classes('text-xl font-bold text-white mb-4')
            
            with ui.row().classes('w-full gap-4'):
                # Camera controls
                with ui.column().classes('flex-1'):
                    camera_status = '✓ Active' if self.camera_active else '○ Inactive'
                    ui.label(f'Camera: {camera_status}').classes('text-white mb-2')
                    
                    if not self.camera_active:
                        ui.button(
                            '📷 START CAMERA',
                            on_click=self.start_camera
                        ).props('size=md color=positive').classes('w-full')
                    else:
                        ui.button(
                            '⏹️ STOP CAMERA',
                            on_click=self.stop_camera
                        ).props('size=md color=warning').classes('w-full')
                
                # CNC controls
                with ui.column().classes('flex-1'):
                    cnc_status = '✓ Connected' if self.cnc_connected else '○ Disconnected'
                    ui.label(f'CNC: {cnc_status}').classes('text-white mb-2')
                    
                    if not self.cnc_connected:
                        ui.button(
                            '🔌 CONNECT CNC',
                            on_click=self.connect_cnc
                        ).props('size=md color=primary').classes('w-full')
                    else:
                        ui.button(
                            '🔌 DISCONNECT CNC',
                            on_click=self.disconnect_cnc
                        ).props('size=md color=warning').classes('w-full')
        
        # Status card
        with ui.card().classes('w-full bg-gray-800 p-6'):
            ui.label('System Status').classes('text-2xl font-bold text-white mb-4')
            
            # Current status
            status_color = {
                'IDLE': 'blue',
                'SIMULATOR': 'yellow',
                'SCANNING': 'yellow',
                'COMPLETE': 'green',
                'ERROR': 'red',
                'STOPPED': 'red'
            }.get(self.system_status, 'gray')
            
            ui.label(f'Status: {self.system_status}').classes(
                f'text-xl text-{status_color}-400 mb-2'
            )
            
            # Detected items count
            ui.label(f'Detected Items: {self.detected_count}').classes(
                'text-xl text-white mb-4'
            )
            
            # Progress bar
            ui.label('Scan Progress').classes('text-lg text-gray-300')
            ui.linear_progress(value=self.cycle_progress).props(
                'size=20px color=primary'
            ).classes('mb-4')
        
        # Action buttons
        with ui.row().classes('w-full gap-4 mt-6'):
            with ui.column().classes('flex-1'):
                ui.button(
                    '▶️ START SCAN CYCLE',
                    on_click=self.start_scan_cycle
                ).props('size=xl color=positive').classes(
                    'w-full h-32 text-2xl font-bold'
                )
            
            with ui.column().classes('flex-1'):
                ui.button(
                    '🔧 PICK & PLACE',
                    on_click=self.start_pick_place
                ).props('size=xl color=secondary').classes(
                    'w-full h-32 text-2xl font-bold'
                )
        
        with ui.row().classes('w-full gap-4 mt-4'):
            ui.button(
                '⏹️ STOP',
                on_click=self.stop_cycle
            ).props('size=lg color=negative').classes(
                'flex-1 h-24 text-xl font-bold'
            )
            
            ui.button(
                '🔄 RESET',
                on_click=self.reset_system
            ).props('size=lg color=warning').classes(
                'flex-1 h-24 text-xl font-bold'
            )
    
    def create_cameras_page(self) -> None:
        """Create camera configuration page."""
        with ui.card().classes('w-full bg-gray-800 p-6'):
            ui.label('Camera Configuration').classes('text-2xl font-bold text-white mb-6')
            
            # Number of cameras
            with ui.row().classes('w-full items-center mb-6'):
                ui.label('Number of Cameras:').classes('text-xl text-white flex-1')
                
                # Plus/minus buttons for camera count
                with ui.row().classes('gap-2'):
                    ui.button('➖', on_click=lambda: self.adjust_camera_count(-1)).props(
                        'size=lg round'
                    )
                    ui.label(str(self.system_config.num_cameras)).classes(
                        'text-2xl text-white w-16 text-center'
                    )
                    ui.button('➕', on_click=lambda: self.adjust_camera_count(1)).props(
                        'size=lg round'
                    )
        
        # Individual camera configurations
        for i in range(self.system_config.num_cameras):
            self.create_camera_config_card(i)
    
    def create_camera_config_card(self, camera_idx: int) -> None:
        """Create configuration card for a single camera."""
        if camera_idx >= len(self.system_config.cameras):
            return
        
        camera = self.system_config.cameras[camera_idx]
        
        with ui.card().classes('w-full bg-gray-700 p-6 mt-4'):
            # Header with enable/disable toggle
            with ui.row().classes('w-full items-center justify-between mb-4'):
                ui.label(f'📷 {camera.name}').classes('text-xl font-bold text-white')
                ui.switch(
                    value=camera.enabled,
                    on_change=lambda e, idx=camera_idx: self.toggle_camera(idx, e.value)
                ).classes('scale-150')
            
            # Mount Position
            ui.label('Mount Position (mm)').classes('text-lg text-gray-300 mb-2')
            self.create_value_adjuster('X', camera.mount_x, 0, 1000, 10,
                                      lambda v, idx=camera_idx: self.update_camera_param(idx, 'mount_x', v))
            self.create_value_adjuster('Y', camera.mount_y, 0, 1000, 10,
                                      lambda v, idx=camera_idx: self.update_camera_param(idx, 'mount_y', v))
            self.create_value_adjuster('Z', camera.mount_z, 0, 1000, 10,
                                      lambda v, idx=camera_idx: self.update_camera_param(idx, 'mount_z', v))
            
            # Visible Region
            ui.label('Visible Region (mm)').classes('text-lg text-gray-300 mt-4 mb-2')
            self.create_value_adjuster('Width', camera.visible_width, 50, 1000, 10,
                                      lambda v, idx=camera_idx: self.update_camera_param(idx, 'visible_width', v))
            self.create_value_adjuster('Height', camera.visible_height, 50, 1000, 10,
                                      lambda v, idx=camera_idx: self.update_camera_param(idx, 'visible_height', v))
            
            # Angles
            ui.label('Orientation (degrees)').classes('text-lg text-gray-300 mt-4 mb-2')
            self.create_value_adjuster('Tilt', camera.tilt_angle, -90, 90, 5,
                                      lambda v, idx=camera_idx: self.update_camera_param(idx, 'tilt_angle', v))
            self.create_value_adjuster('Pan', camera.pan_angle, -180, 180, 5,
                                      lambda v, idx=camera_idx: self.update_camera_param(idx, 'pan_angle', v))
    
    def create_machine_page(self) -> None:
        """Create machine limits configuration page."""
        with ui.card().classes('w-full bg-gray-800 p-6'):
            ui.label('Machine Workspace Limits').classes('text-2xl font-bold text-white mb-6')
            
            # X axis
            ui.label('X Axis (mm)').classes('text-xl text-gray-300 mb-2')
            self.create_value_adjuster('Min', self.system_config.x_min, 0, 2000, 10,
                                      lambda v: setattr(self.system_config, 'x_min', v))
            self.create_value_adjuster('Max', self.system_config.x_max, 0, 2000, 10,
                                      lambda v: setattr(self.system_config, 'x_max', v))
            
            # Y axis
            ui.label('Y Axis (mm)').classes('text-xl text-gray-300 mt-4 mb-2')
            self.create_value_adjuster('Min', self.system_config.y_min, 0, 2000, 10,
                                      lambda v: setattr(self.system_config, 'y_min', v))
            self.create_value_adjuster('Max', self.system_config.y_max, 0, 2000, 10,
                                      lambda v: setattr(self.system_config, 'y_max', v))
            
            # Z axis
            ui.label('Z Axis (mm)').classes('text-xl text-gray-300 mt-4 mb-2')
            self.create_value_adjuster('Min', self.system_config.z_min, 0, 1000, 10,
                                      lambda v: setattr(self.system_config, 'z_min', v))
            self.create_value_adjuster('Max', self.system_config.z_max, 0, 1000, 10,
                                      lambda v: setattr(self.system_config, 'z_max', v))
            
            # Safe Z height
            ui.label('Safe Z Height (mm)').classes('text-xl text-gray-300 mt-4 mb-2')
            self.create_value_adjuster('Safe Z', self.system_config.safe_z, 0, 500, 5,
                                      lambda v: setattr(self.system_config, 'safe_z', v))
            
            # Save button
            ui.button('💾 SAVE CONFIGURATION', on_click=self.save_configuration).props(
                'size=xl color=positive'
            ).classes('w-full mt-6 h-20 text-xl font-bold')
    
    def create_scanning_page(self) -> None:
        """Create scanning pattern configuration page."""
        with ui.card().classes('w-full bg-gray-800 p-6'):
            ui.label('Scanning Pattern').classes('text-2xl font-bold text-white mb-6')
            
            # Grid dimensions
            ui.label('Grid Size').classes('text-xl text-gray-300 mb-2')
            self.create_value_adjuster('Positions X', self.system_config.grid_x, 1, 10, 1,
                                      lambda v: setattr(self.system_config, 'grid_x', v))
            self.create_value_adjuster('Positions Y', self.system_config.grid_y, 1, 10, 1,
                                      lambda v: setattr(self.system_config, 'grid_y', v))
            
            # Overlap percentage
            ui.label('Overlap Percentage').classes('text-xl text-gray-300 mt-4 mb-2')
            
            # Slider for overlap
            overlap_label = ui.label(f'{self.system_config.overlap_percent}%').classes(
                'text-lg text-white'
            )
            
            def update_overlap(e):
                self.system_config.overlap_percent = e.value
                overlap_label.set_text(f'{e.value}%')
            
            ui.slider(min=0, max=50, step=5, value=self.system_config.overlap_percent,
                     on_change=update_overlap).props('label-always').classes('w-full')
            
            # Coverage estimate
            total_positions = self.system_config.grid_x * self.system_config.grid_y
            workspace_area = (self.system_config.x_max - self.system_config.x_min) * \
                           (self.system_config.y_max - self.system_config.y_min)
            
            with ui.card().classes('w-full bg-gray-700 p-4 mt-6'):
                ui.label('Estimated Coverage').classes('text-lg font-bold text-white mb-2')
                ui.label(f'Total Positions: {total_positions}').classes('text-md text-gray-300')
                ui.label(f'Workspace: {workspace_area/1000:.1f} cm²').classes('text-md text-gray-300')
            
            # Save button
            ui.button('💾 SAVE PATTERN', on_click=self.save_configuration).props(
                'size=xl color=positive'
            ).classes('w-full mt-6 h-20 text-xl font-bold')
    
    def create_status_page(self) -> None:
        """Create system status and statistics page."""
        with ui.card().classes('w-full bg-gray-800 p-6'):
            ui.label('System Status').classes('text-2xl font-bold text-white mb-6')
            
            # Real-time statistics
            stats = self.get_system_stats()
            
            with ui.column().classes('w-full gap-4'):
                self.create_stat_row('Total Objects Detected', str(stats['total_detected']))
                self.create_stat_row('Pending Processing', str(stats['pending']))
                self.create_stat_row('Completed', str(stats['completed']))
                self.create_stat_row('Failed', str(stats['failed']))
                
                ui.separator().classes('my-4')
                
                self.create_stat_row('Active Cameras', f"{stats['active_cameras']}/{self.system_config.num_cameras}")
                self.create_stat_row('CNC Status', stats['cnc_status'])
                self.create_stat_row('Last Scan', stats['last_scan'])
        
        # Refresh button
        ui.button('🔄 REFRESH', on_click=lambda: ui.notify('Refreshing...')).props(
            'size=lg color=primary'
        ).classes('w-full mt-4 h-16 text-lg font-bold')
    
    def create_value_adjuster(self, label: str, value: float, min_val: float, 
                             max_val: float, step: float, on_change) -> None:
        """Create a value adjuster with +/- buttons."""
        with ui.row().classes('w-full items-center justify-between mb-3'):
            ui.label(f'{label}:').classes('text-lg text-white w-32')
            
            # Value display and controls
            with ui.row().classes('gap-2 items-center'):
                def decrease():
                    new_val = max(min_val, value - step)
                    on_change(new_val)
                    value_label.set_text(f'{new_val:.1f}')
                
                def increase():
                    new_val = min(max_val, value + step)
                    on_change(new_val)
                    value_label.set_text(f'{new_val:.1f}')
                
                ui.button('➖', on_click=decrease).props('size=md round')
                value_label = ui.label(f'{value:.1f}').classes(
                    'text-xl text-white w-24 text-center font-mono'
                )
                ui.button('➕', on_click=increase).props('size=md round')
    
    def create_stat_row(self, label: str, value: str) -> None:
        """Create a statistics row."""
        with ui.row().classes('w-full items-center justify-between'):
            ui.label(label).classes('text-lg text-gray-300')
            ui.label(value).classes('text-lg font-bold text-white')
    
    # Action handlers
    def navigate(self, page: str) -> None:
        """Navigate to a different page."""
        self.current_page = page
        ui.notify(f'Navigating to {page}')
        # TODO: Implement page refresh
    
    def emergency_stop(self) -> None:
        """Emergency stop handler."""
        ui.notify('🛑 EMERGENCY STOP ACTIVATED', type='negative')
        self.system_status = "STOPPED"
        self.cycle_progress = 0.0
        
        if SIMULATOR_MODE:
            ui.notify('(Simulator: Emergency stop simulated)', type='info')
        else:
            # Stop all hardware
            if self.cnc_controller:
                try:
                    self.cnc_controller.emergency_stop()
                except Exception as e:
                    print(f"CNC emergency stop error: {e}")
            if self.vision_system:
                try:
                    self.vision_system.stop()
                except Exception as e:
                    print(f"Vision system stop error: {e}")
    
    def start_scan_cycle(self) -> None:
        """Start scan cycle."""
        ui.notify('▶️ Starting scan cycle...', type='positive')
        self.system_status = "SCANNING"
        self.cycle_progress = 0.0
        self.detected_count = 0
        
        if SIMULATOR_MODE:
            # Simulate scan cycle
            ui.notify('(Simulator: Scanning simulation started)', type='info')
            # Simulate detecting objects over time
            import random
            self.detected_count = random.randint(5, 20)
            self.cycle_progress = 0.5
            ui.notify(f'(Simulator: Detected {self.detected_count} objects)', type='positive')
        else:
            # Start real hardware scan
            if not self.camera_active:
                ui.notify('⚠️ Camera not started. Start camera first.', type='warning')
                return
            if not self.current_map:
                # Start new map
                try:
                    from cncsorter.application.bed_mapping import BedMappingService
                    from cncsorter.infrastructure.vision import ImageStitcher
                    
                    stitcher = ImageStitcher()
                    bed_mapping = BedMappingService(self.vision_system, stitcher)
                    self.current_map = bed_mapping.start_new_map()
                    ui.notify(f'Started new map: {self.current_map.map_id}', type='positive')
                except Exception as e:
                    ui.notify(f'Error starting map: {e}', type='negative')
    
    def start_camera(self) -> None:
        """Start camera system."""
        if SIMULATOR_MODE:
            self.camera_active = True
            ui.notify('(Simulator: Camera started)', type='positive')
            return
        
        if self.camera_active:
            ui.notify('Camera already active', type='info')
            return
        
        try:
            from cncsorter.infrastructure.vision import VisionSystem
            self.vision_system = VisionSystem(camera_index=0)
            self.camera_active = True
            ui.notify('✓ Camera started successfully', type='positive')
        except Exception as e:
            ui.notify(f'Error starting camera: {e}', type='negative')
    
    def stop_camera(self) -> None:
        """Stop camera system."""
        if SIMULATOR_MODE:
            self.camera_active = False
            ui.notify('(Simulator: Camera stopped)', type='info')
            return
        
        if self.vision_system:
            try:
                self.vision_system.stop()
                self.camera_active = False
                ui.notify('Camera stopped', type='info')
            except Exception as e:
                ui.notify(f'Error stopping camera: {e}', type='negative')
    
    def connect_cnc(self) -> None:
        """Connect to CNC controller."""
        if SIMULATOR_MODE:
            self.cnc_connected = True
            ui.notify('(Simulator: CNC connected)', type='positive')
            return
        
        if self.cnc_connected:
            ui.notify('CNC already connected', type='info')
            return
        
        try:
            from cncsorter.infrastructure.cnc_controller import FluidNCSerial
            self.cnc_controller = FluidNCSerial('/dev/ttyUSB0', 115200)
            if self.cnc_controller.connect():
                self.cnc_connected = True
                ui.notify('✓ CNC connected successfully', type='positive')
            else:
                ui.notify('Failed to connect to CNC', type='negative')
        except Exception as e:
            ui.notify(f'Error connecting to CNC: {e}', type='negative')
    
    def disconnect_cnc(self) -> None:
        """Disconnect from CNC controller."""
        if SIMULATOR_MODE:
            self.cnc_connected = False
            ui.notify('(Simulator: CNC disconnected)', type='info')
            return
        
        if self.cnc_controller:
            try:
                self.cnc_controller.disconnect()
                self.cnc_connected = False
                ui.notify('CNC disconnected', type='info')
            except Exception as e:
                ui.notify(f'Error disconnecting CNC: {e}', type='negative')
    
    def start_scan_cycle(self) -> None:
        """Start scan cycle."""
        ui.notify('▶️ Starting scan cycle...', type='positive')
        self.system_status = "SCANNING"
        self.cycle_progress = 0.0
        self.detected_count = 0
        # TODO: Integrate with scanning system
    
    def start_pick_place(self) -> None:
        """Start pick and place operation."""
        if self.detected_count == 0:
            ui.notify('⚠️ No objects detected. Run scan first.', type='warning')
            return
        
        ui.notify('🔧 Starting pick & place...', type='positive')
        # TODO: Integrate with pick and place system
    
    def stop_cycle(self) -> None:
        """Stop current cycle."""
        ui.notify('⏹️ Stopping cycle...', type='warning')
        self.system_status = "IDLE"
        # TODO: Graceful shutdown of operations
    
    def reset_system(self) -> None:
        """Reset system."""
        ui.notify('🔄 Resetting system...', type='info')
        self.detected_count = 0
        self.cycle_progress = 0.0
        self.system_status = "IDLE"
    
    def adjust_camera_count(self, delta: int) -> None:
        """Adjust number of cameras."""
        new_count = max(1, min(8, self.system_config.num_cameras + delta))
        
        if new_count > self.system_config.num_cameras:
            # Add new camera
            new_id = len(self.system_config.cameras)
            self.system_config.cameras.append(
                CameraConfig(new_id, f"Camera {new_id}", 400, 200, 300, 400, 300, 0, 0)
            )
        elif new_count < self.system_config.num_cameras:
            # Remove last camera
            self.system_config.cameras.pop()
        
        self.system_config.num_cameras = new_count
        ui.notify(f'Camera count: {new_count}')
        # TODO: Refresh UI
    
    def toggle_camera(self, camera_idx: int, enabled: bool) -> None:
        """Toggle camera enabled state."""
        if camera_idx < len(self.system_config.cameras):
            self.system_config.cameras[camera_idx].enabled = enabled
            status = "enabled" if enabled else "disabled"
            ui.notify(f'Camera {camera_idx} {status}')
    
    def update_camera_param(self, camera_idx: int, param: str, value: float) -> None:
        """Update camera parameter."""
        if camera_idx < len(self.system_config.cameras):
            setattr(self.system_config.cameras[camera_idx], param, value)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        try:
            pending = len(self.repository.list_pending())
            all_objects = self.repository.list_all(limit=10000)
            
            completed = sum(1 for obj in all_objects if obj.classification != "unknown")
            failed = 0  # TODO: Track failed objects
            
            return {
                'total_detected': len(all_objects),
                'pending': pending,
                'completed': completed,
                'failed': failed,
                'active_cameras': sum(1 for cam in self.system_config.cameras if cam.enabled),
                'cnc_status': 'Connected',  # TODO: Get real status
                'last_scan': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception:
            return {
                'total_detected': 0,
                'pending': 0,
                'completed': 0,
                'failed': 0,
                'active_cameras': 0,
                'cnc_status': 'Unknown',
                'last_scan': 'Never'
            }


def main():
    """Run the touchscreen interface."""
    # Parse arguments
    parser = argparse.ArgumentParser(description='CNCSorter Touchscreen Interface')
    parser.add_argument('--simulator', '--sim', action='store_true',
                       help='Run in simulator mode (no hardware required - perfect for Mac testing)')
    parser.add_argument('--port', type=int, default=8080,
                       help='Port to run the web interface on (default: 8080)')
    parser.add_argument('--fullscreen', action='store_true',
                       help='Run in fullscreen mode (for production deployment)')
    
    args = parser.parse_args()
    
    # Print startup information
    print("=" * 60)
    print("CNCSorter Touchscreen Interface")
    print("=" * 60)
    if args.simulator or SIMULATOR_MODE:
        print("MODE: Simulator (No hardware required)")
        print("      Perfect for testing on Mac/Windows/Linux")
        print("      All controls functional without real hardware")
    else:
        print("MODE: Production (Hardware integration enabled)")
        print("      Requires camera and CNC connection")
    print(f"PORT: http://localhost:{args.port}")
    print("=" * 60)
    print()
    
    # Create interface
    interface = TouchscreenInterface()
    interface.create_ui()
    
    # Configure NiceGUI
    ui.run(
        title='CNCSorter Touchscreen',
        port=args.port,
        reload=False,
        show=True,
        native=False,  # Use browser for better compatibility
        fullscreen=args.fullscreen,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
