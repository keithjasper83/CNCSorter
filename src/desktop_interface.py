#!/usr/bin/env python3
"""
Desktop Operator Interface for CNCSorter.

Feature-rich NiceGUI interface for desktop/tablet control.
Integrates the Touchscreen Interface via an "Eye Frame" (IFrame) for unified control.
"""

from nicegui import ui, app
from typing import Optional, List, Dict, Any
import json
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

# Import from cncsorter package
from cncsorter.application.events import (
    EventBus, ObjectsDetected, BedMapCompleted,
    CNCPositionUpdated, BoundaryViolationDetected
)
from cncsorter.infrastructure.persistence import SQLiteDetectionRepository
# Reuse configuration classes
from cncsorter import config


@dataclass
class CameraConfig:
    """Configuration for a single camera."""
    camera_id: int
    name: str
    enabled: bool = True

@dataclass
class SystemConfig:
    """System configuration subset for display."""
    num_cameras: int = 1
    cameras: List[CameraConfig] = field(default_factory=list)


class DesktopInterface:
    """Main desktop interface application."""

    def __init__(self):
        """Initialize desktop interface."""
        self.config_path = Path("config/machine_config.json")
        self.system_config: Optional[SystemConfig] = None
        self.event_bus = EventBus()
        self.repository = SQLiteDetectionRepository()

        # State
        self.logs: List[str] = []
        self.connection_status = "Connected" # Placeholder
        self.system_status = "IDLE"

        # UI Elements ref
        self.log_container = None

        # Load config
        self.load_configuration()

        # Subscribe to events
        self.event_bus.subscribe(BoundaryViolationDetected, self.on_boundary_violation)
        self.event_bus.subscribe(ObjectsDetected, self.on_objects_detected)

        # Setup UI
        self.setup_ui()

    def load_configuration(self) -> None:
        """Load minimal configuration for dashboard display."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    cameras_data = data.get('cameras', [])
                    cameras = [
                        CameraConfig(
                            camera_id=c.get('camera_id', i),
                            name=c.get('camera_name', f"Camera {i}"),
                            enabled=True
                        ) for i, c in enumerate(cameras_data)
                    ]
                    self.system_config = SystemConfig(num_cameras=len(cameras), cameras=cameras)
            except Exception:
                self.create_default_config()
        else:
            self.create_default_config()

    def create_default_config(self):
        self.system_config = SystemConfig(
            num_cameras=1,
            cameras=[CameraConfig(0, "Camera 0")]
        )

    # Event Handlers
    def on_boundary_violation(self, event: BoundaryViolationDetected):
        self.log_message(f"VIOLATION: {event.message}", type='error')
        ui.notify(f"Boundary Violation: {event.message}", type='negative')

    def on_objects_detected(self, event: ObjectsDetected):
        self.log_message(f"Detected {len(event.detected_objects)} objects")

    def log_message(self, message: str, type: str = 'info'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.insert(0, log_entry)
        if len(self.logs) > 100: self.logs.pop()

        if self.log_container:
            with self.log_container:
                color = 'text-red-500' if type == 'error' else 'text-gray-300'
                ui.label(log_entry).classes(f'text-sm font-mono {color}')

    # UI Construction
    def setup_ui(self):
        ui.colors(primary='#3b82f6', secondary='#10b981', accent='#8b5cf6', dark='#111827')

        # Main Layout: Sidebar + Content
        with ui.row().classes('w-full h-screen bg-gray-900 no-wrap gap-0'):
            # Sidebar
            self.create_sidebar()

            # Content Area
            with ui.column().classes('flex-grow h-full p-0 gap-0'):
                # Header
                self.create_header()

                # Tab Panels
                with ui.tabs().classes('w-full text-white bg-gray-800') as tabs:
                    t_dashboard = ui.tab('Dashboard', icon='dashboard')
                    t_control = ui.tab('Control (Eye Frame)', icon='touch_app')
                    t_jobs = ui.tab('Jobs', icon='work')
                    t_logs = ui.tab('Logs', icon='list')

                with ui.tab_panels(tabs, value=t_dashboard).classes('w-full flex-grow bg-gray-900 p-0'):
                    # Dashboard Panel
                    with ui.tab_panel(t_dashboard).classes('p-6'):
                        self.create_dashboard_page()

                    # Control Panel (Eye Frame / IFrame)
                    with ui.tab_panel(t_control).classes('w-full h-full p-0'):
                        # This IFrame embeds the Touchscreen Interface
                        # Use Javascript to determine current host to support remote access
                        # iframe source will be http://<hostname>:8080

                        iframe_html = """
                        <iframe id="control-frame" class="w-full h-full border-none"></iframe>
                        <script>
                            // Dynamically set iframe source to same host but port 8080
                            const host = window.location.hostname;
                            const frame = document.getElementById('control-frame');
                            frame.src = `http://${host}:8080`;
                        </script>
                        """
                        ui.html(iframe_html).classes('w-full h-full')

                    # Jobs Panel
                    with ui.tab_panel(t_jobs).classes('p-6'):
                        self.create_jobs_page()

                    # Logs Panel
                    with ui.tab_panel(t_logs).classes('p-6'):
                        self.create_logs_page()

    def create_sidebar(self):
        with ui.column().classes('w-64 h-full bg-gray-800 p-4 border-r border-gray-700'):
            ui.label('CNCSorter Pro').classes('text-2xl font-bold text-white mb-6')

            with ui.card().classes('w-full bg-gray-700 p-4 mb-4'):
                ui.label('STATUS').classes('text-xs text-gray-400 font-bold')
                ui.label(self.system_status).classes('text-lg font-bold text-green-400')

            ui.label('Cameras').classes('text-xs text-gray-400 font-bold mt-4 mb-2')
            for cam in self.system_config.cameras:
                with ui.row().classes('items-center gap-2'):
                    ui.icon('videocam', color='green' if cam.enabled else 'gray')
                    ui.label(cam.name).classes('text-white')

    def create_header(self):
        with ui.row().classes('w-full bg-gray-800 p-2 px-4 justify-between items-center border-b border-gray-700'):
            ui.label('Desktop Operator Station').classes('text-gray-400')
            ui.button(icon='logout', on_click=lambda: ui.notify('Logout')).props('flat round color=white')

    def create_dashboard_page(self):
        ui.label('System Dashboard').classes('text-2xl font-bold text-white mb-6')

        # Camera Grid
        with ui.grid(columns=2).classes('w-full gap-4 mb-6'):
            for cam in self.system_config.cameras:
                if cam.enabled:
                    with ui.card().classes('bg-black aspect-video relative group'):
                         ui.label(cam.name).classes('absolute top-2 left-2 text-white bg-black/50 px-2 rounded')
                         ui.label('Live Feed Placeholder').classes('text-gray-500 m-auto')

    def create_jobs_page(self):
        ui.label('Job Queue').classes('text-2xl font-bold text-white mb-6')
        ui.label('Job management interface here...').classes('text-gray-400')

    def create_logs_page(self):
        ui.label('System Logs').classes('text-2xl font-bold text-white mb-4')
        self.log_container = ui.column().classes('w-full bg-black p-4 rounded h-full overflow-auto')
        for log in self.logs:
             ui.label(log).classes('text-sm font-mono text-gray-300')


def main():
    """Run the desktop interface."""
    # Run on port 8081, assuming Touchscreen runs on 8080
    ui.run(title='CNCSorter Desktop', port=8081, show=False, dark=True)

if __name__ in {"__main__", "__mp_main__"}:
    main()
