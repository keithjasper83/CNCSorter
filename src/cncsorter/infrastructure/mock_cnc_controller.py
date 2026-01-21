"""Mock CNC Controller for development and testing.

This module provides a visual "Digital Twin" of the CNC machine that runs
locally via a web interface, allowing developers to see and "feel" the
system's operation without physical hardware.
"""
import threading
import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from flask import Flask, jsonify, request, Response

from cncsorter.domain.entities import CNCCoordinate
from cncsorter.infrastructure.cnc_controller import CNCController
from cncsorter.infrastructure.motion_validator import MotionValidator
from cncsorter.application.events import EventBus,CNCPositionUpdated

# Configure logging
logger = logging.getLogger(__name__)

# Embedded HTML for the visualization
# This provides a real-time view of the bed and toolhead
VISUALIZATION_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>CNCSorter Digital Twin</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #2c3e50;
            color: #ecf0f1;
            display: flex;
            flex-direction: column;
            align-items: center;
            margin: 0;
            padding: 20px;
        }
        h1 { margin-bottom: 10px; }
        .container {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            justify-content: center;
        }
        .panel {
            background-color: #34495e;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        #canvas-container {
            position: relative;
            background-color: #fff;
            border: 2px solid #95a5a6;
            cursor: crosshair;
        }
        canvas { display: block; }
        .stats {
            min-width: 250px;
        }
        .stat-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 1px solid #7f8c8d;
        }
        .stat-label { color: #bdc3c7; }
        .stat-value { font-weight: bold; font-family: monospace; font-size: 1.2em; }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-idle { background-color: #2ecc71; }
        .status-moving { background-color: #f1c40f; box-shadow: 0 0 8px #f1c40f; }
        .status-error { background-color: #e74c3c; }

        /* Grid lines on canvas */
        .grid-line { stroke: #eee; stroke-width: 1; }
        .axis-line { stroke: #333; stroke-width: 2; }
    </style>
</head>
<body>
    <h1>CNCSorter Digital Twin</h1>

    <div class="container">
        <div class="panel">
            <div id="canvas-container">
                <canvas id="bedCanvas" width="800" height="600"></canvas>
            </div>
            <div style="margin-top: 10px; text-align: center; color: #95a5a6; font-size: 0.9em;">
                Bed Size: 800mm x 600mm | Scale: 1px = 1mm
            </div>
        </div>

        <div class="panel stats">
            <h2>Machine Status</h2>
            <div class="stat-row">
                <span class="stat-label">State</span>
                <span class="stat-value">
                    <span id="status-dot" class="status-indicator status-idle"></span>
                    <span id="status-text">IDLE</span>
                </span>
            </div>
            <div class="stat-row">
                <span class="stat-label">X Position</span>
                <span class="stat-value" id="pos-x">0.00</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Y Position</span>
                <span class="stat-value" id="pos-y">0.00</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Z Position</span>
                <span class="stat-value" id="pos-z">0.00</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Target X</span>
                <span class="stat-value" id="target-x">0.00</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Target Y</span>
                <span class="stat-value" id="target-y">0.00</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Target Z</span>
                <span class="stat-value" id="target-z">0.00</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Speed</span>
                <span class="stat-value" id="speed">0 mm/s</span>
            </div>

            <div style="margin-top: 20px;">
                <button onclick="home()" style="padding: 10px; width: 100%; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">
                    🏠 HOME MACHINE
                </button>
            </div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('bedCanvas');
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        let currentState = {
            x: 0, y: 0, z: 0,
            target_x: 0, target_y: 0, target_z: 0,
            is_moving: false,
            speed: 0
        };

        // Draw the machine bed
        function drawBed() {
            ctx.clearRect(0, 0, width, height);

            // Draw grid
            ctx.strokeStyle = '#eee';
            ctx.lineWidth = 1;

            // Vertical lines (every 50mm)
            for(let x = 0; x <= width; x += 50) {
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, height);
                ctx.stroke();
            }

            // Horizontal lines (every 50mm)
            for(let y = 0; y <= height; y += 50) {
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(width, y);
                ctx.stroke();
            }

            // Coordinate origin
            ctx.fillStyle = '#333';
            ctx.font = '12px Arial';
            ctx.fillText('(0,0)', 5, height - 5);
        }

        // Draw the toolhead
        function drawToolhead(x, y, z, isMoving) {
            // Coordinate system flip: Canvas Y increases downwards, CNC Y typically increases "away" or "up"
            // Assuming standard CNC: (0,0) is bottom-left. Canvas (0,0) is top-left.
            // So visual Y = height - CNC Y
            const visualX = x;
            const visualY = height - y;

            // Draw path from previous if moving (simplified)
            if (isMoving) {
                const targetVisualX = currentState.target_x;
                const targetVisualY = height - currentState.target_y;

                ctx.strokeStyle = 'rgba(46, 204, 113, 0.3)';
                ctx.lineWidth = 2;
                ctx.setLineDash([5, 5]);
                ctx.beginPath();
                ctx.moveTo(visualX, visualY);
                ctx.lineTo(targetVisualX, targetVisualY);
                ctx.stroke();
                ctx.setLineDash([]);

                // Draw target ghost
                ctx.strokeStyle = 'rgba(46, 204, 113, 0.5)';
                ctx.beginPath();
                ctx.arc(targetVisualX, targetVisualY, 5, 0, Math.PI * 2);
                ctx.stroke();
            }

            // Toolhead body
            ctx.fillStyle = isMoving ? '#f1c40f' : '#e74c3c';
            ctx.beginPath();
            ctx.arc(visualX, visualY, 15, 0, Math.PI * 2);
            ctx.fill();

            // Toolhead center
            ctx.fillStyle = '#fff';
            ctx.beginPath();
            ctx.arc(visualX, visualY, 3, 0, Math.PI * 2);
            ctx.fill();

            // Z-height indicator (circle size or shadow)
            ctx.strokeStyle = '#2c3e50';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(visualX, visualY, 15 + (z/10), 0, Math.PI * 2);
            ctx.stroke();

            // Label
            ctx.fillStyle = '#2c3e50';
            ctx.font = 'bold 12px Arial';
            ctx.fillText(`Z: ${z.toFixed(1)}`, visualX + 20, visualY);
        }

        function updateDisplay() {
            drawBed();
            drawToolhead(currentState.x, currentState.y, currentState.z, currentState.is_moving);

            // Update stats
            document.getElementById('pos-x').textContent = currentState.x.toFixed(2);
            document.getElementById('pos-y').textContent = currentState.y.toFixed(2);
            document.getElementById('pos-z').textContent = currentState.z.toFixed(2);

            document.getElementById('target-x').textContent = currentState.target_x.toFixed(2);
            document.getElementById('target-y').textContent = currentState.target_y.toFixed(2);
            document.getElementById('target-z').textContent = currentState.target_z.toFixed(2);

            document.getElementById('speed').textContent = currentState.speed.toFixed(0) + ' mm/s';

            const statusText = document.getElementById('status-text');
            const statusDot = document.getElementById('status-dot');

            if (currentState.is_moving) {
                statusText.textContent = 'MOVING';
                statusText.style.color = '#f1c40f';
                statusDot.className = 'status-indicator status-moving';
            } else {
                statusText.textContent = 'IDLE';
                statusText.style.color = '#2ecc71';
                statusDot.className = 'status-indicator status-idle';
            }
        }

        function pollStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    currentState = data;
                    updateDisplay();
                })
                .catch(err => console.error('Error polling status:', err));
        }

        function home() {
            fetch('/api/home', { method: 'POST' })
                .then(response => console.log('Homing command sent'))
                .catch(err => console.error('Error homing:', err));
        }

        // Poll every 100ms
        setInterval(pollStatus, 100);
        updateDisplay();
    </script>
</body>
</html>
"""

class MockCNCController(CNCController):
    """
    Mock CNC Controller that simulates machine movement and provides a web interface.

    This controller:
    1. Tracks virtual position
    2. Simulates movement time based on speed
    3. Runs a lightweight Flask server to visualize state
    4. Integrates with MotionValidator and EventBus
    """

    def __init__(self, port: int = 5000, speed: float = 100.0,
                 motion_validator: Optional[MotionValidator] = None,
                 event_bus: Optional[EventBus] = None):
        """
        Initialize the Mock CNC Controller.

        Args:
            port: Web server port (default 5000)
            speed: Movement speed in units/sec (default 100.0)
            motion_validator: Optional validator for safety checks
            event_bus: Optional event bus for publishing updates
        """
        self.web_port = port
        self.move_speed = speed
        self.motion_validator = motion_validator
        self.event_bus = event_bus

        # State
        self.current_pos = CNCCoordinate(x=0.0, y=0.0, z=0.0)
        self.target_pos = CNCCoordinate(x=0.0, y=0.0, z=0.0)
        self.is_moving = False
        self._connected = False

        # Web server setup
        self.app = Flask(__name__)
        self._setup_routes()

        # Thread control
        self._stop_event = threading.Event()
        self._server_thread = None
        self._movement_thread = None

        # Suppress Flask logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

    def _setup_routes(self):
        """Configure Flask routes."""

        @self.app.route('/')
        def index():
            return VISUALIZATION_HTML

        @self.app.route('/api/status')
        def status():
            return jsonify({
                'x': self.current_pos.x,
                'y': self.current_pos.y,
                'z': self.current_pos.z,
                'target_x': self.target_pos.x,
                'target_y': self.target_pos.y,
                'target_z': self.target_pos.z,
                'is_moving': self.is_moving,
                'speed': self.move_speed,
                'connected': self._connected
            })

        @self.app.route('/api/home', methods=['POST'])
        def home_machine():
            if self.is_moving:
                return jsonify({'status': 'busy'}), 409

            # Trigger homing in background
            threading.Thread(target=self._simulate_move,
                             args=(CNCCoordinate(x=0, y=0, z=0),)).start()
            return jsonify({'status': 'homing_started'})

    def connect(self) -> bool:
        """Connect to the mock controller (start web server)."""
        if self._connected:
            return True

        self._connected = True
        self._stop_event.clear()

        # Start web server in background thread
        self._server_thread = threading.Thread(
            target=self.app.run,
            kwargs={'host': '0.0.0.0', 'port': self.web_port, 'use_reloader': False},
            daemon=True
        )
        self._server_thread.start()

        print(f"Mock CNC Controller started on http://localhost:{self.web_port}")
        return True

    def disconnect(self):
        """Disconnect and stop server."""
        self._connected = False
        self._stop_event.set()
        # Flask server doesn't have a clean stop method without request context,
        # but daemon thread will die when main process exits.
        print("Mock CNC Controller disconnected")

    def get_position(self) -> Optional[CNCCoordinate]:
        """Get current virtual position."""
        if not self._connected:
            return None
        return self.current_pos

    def move_to(self, coordinate: CNCCoordinate) -> bool:
        """
        Move to target coordinate with simulated delay.

        This method returns immediately (asynchronous command) in real hardware,
        but for simple scripts we might want to block. However, the interface
        implies immediate return of success/fail of the command sent.

        To properly simulate, we should start a background movement.
        """
        if not self._connected:
            return False

        # Validate
        if self.motion_validator:
            self.motion_validator.validate_coordinate(coordinate)

        if self.is_moving:
            print("Mock CNC: Busy, ignoring command")
            return False

        # Start movement simulation in background
        self._movement_thread = threading.Thread(
            target=self._simulate_move,
            args=(coordinate,)
        )
        self._movement_thread.start()

        return True

    def _simulate_move(self, target: CNCCoordinate):
        """Simulate physical movement over time."""
        self.is_moving = True
        self.target_pos = target

        start_pos = self.current_pos

        # Calculate distance
        dx = target.x - start_pos.x
        dy = target.y - start_pos.y
        dz = target.z - start_pos.z
        distance = (dx**2 + dy**2 + dz**2) ** 0.5

        if distance == 0:
            self.is_moving = False
            return

        # Calculate duration
        duration = distance / self.move_speed
        start_time = time.time()

        while time.time() - start_time < duration:
            if self._stop_event.is_set():
                break

            elapsed = time.time() - start_time
            progress = elapsed / duration

            # Update current position (linear interpolation)
            new_x = start_pos.x + (dx * progress)
            new_y = start_pos.y + (dy * progress)
            new_z = start_pos.z + (dz * progress)

            prev_pos = self.current_pos
            self.current_pos = CNCCoordinate(x=new_x, y=new_y, z=new_z)

            # Publish event if changed significantly
            if self.event_bus:
                # Basic rate limiting done by sleep
                self.event_bus.publish(CNCPositionUpdated(
                    position=self.current_pos,
                    previous_position=prev_pos
                ))

            time.sleep(0.05)  # 20Hz update rate

        # Finalize
        self.current_pos = target
        self.is_moving = False

        if self.event_bus:
            self.event_bus.publish(CNCPositionUpdated(
                position=self.current_pos,
                timestamp=datetime.now()
            ))

    def is_connected(self) -> bool:
        """Check connection status."""
        return self._connected

    def send_command(self, command: str) -> bool:
        """Send a raw command to the mock controller."""
        if not self._connected:
            return False

        # Handle soft reset
        if command == '\x18':
            self.is_moving = False
            # We could also reset other state if needed
            print("Mock CNC: Soft reset received")

        return True
