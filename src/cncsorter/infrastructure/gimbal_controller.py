"""
Gimbal Controller for automated camera positioning in CNCSorter.

This module provides control over a 2-axis or 3-axis gimbal system to allow
the CNC system to automatically position cameras for optimal object detection
from multiple angles.

Supports:
- GPIO-based servo control (Raspberry Pi)
- 2-axis (pan/tilt) and 3-axis (pan/tilt/roll) configurations
- Preset positions for common angles
- Smooth motion with configurable speed
- Position memory and calibration
"""

import time
import warnings
from typing import Optional, Tuple, List
from dataclasses import dataclass
from abc import ABC, abstractmethod

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False
    warnings.warn("RPi.GPIO not available. Gimbal control will be simulated.", RuntimeWarning)


@dataclass
class GimbalPosition:
    """Represents a gimbal position in degrees."""
    pan: float  # Horizontal rotation (-90 to +90 degrees)
    tilt: float  # Vertical rotation (-90 to +90 degrees)
    roll: Optional[float] = 0.0  # Camera rotation (only for 3-axis)

    def __str__(self):
        if self.roll is not None and self.roll != 0.0:
            return f"Pan: {self.pan}°, Tilt: {self.tilt}°, Roll: {self.roll}°"
        return f"Pan: {self.pan}°, Tilt: {self.tilt}°"


class ServoController:
    """
    Controls a single servo motor via GPIO PWM.

    Standard RC servos expect pulses:
    - 1.0 ms = -90° (full left/down)
    - 1.5 ms = 0° (center)
    - 2.0 ms = +90° (full right/up)
    - 50 Hz frequency (20ms period)
    """

    def __init__(self, gpio_pin: int, min_pulse_ms: float = 1.0,
                 max_pulse_ms: float = 2.0, frequency: int = 50):
        """
        Initialize servo controller.

        Args:
            gpio_pin: GPIO pin number (BCM numbering)
            min_pulse_ms: Pulse width for -90° position
            max_pulse_ms: Pulse width for +90° position
            frequency: PWM frequency in Hz
        """
        self.gpio_pin = gpio_pin
        self.min_pulse_ms = min_pulse_ms
        self.max_pulse_ms = max_pulse_ms
        self.frequency = frequency
        self.current_angle = 0.0
        self.pwm = None

        if GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.OUT)
            self.pwm = GPIO.PWM(self.gpio_pin, self.frequency)
            self.pwm.start(0)

    def _angle_to_duty_cycle(self, angle: float) -> float:
        """
        Convert angle (-90 to +90) to PWM duty cycle.

        Args:
            angle: Angle in degrees (-90 to +90)

        Returns:
            Duty cycle percentage (0-100)
        """
        # Clamp angle to valid range
        angle = max(-90.0, min(90.0, angle))

        # Map angle to pulse width
        pulse_range = self.max_pulse_ms - self.min_pulse_ms
        pulse_width = self.min_pulse_ms + ((angle + 90) / 180) * pulse_range

        # Convert to duty cycle (pulse_width / period * 100)
        period_ms = 1000.0 / self.frequency
        duty_cycle = (pulse_width / period_ms) * 100.0

        return duty_cycle

    def move_to(self, angle: float, smooth: bool = True, speed: float = 30.0):
        """
        Move servo to specified angle.

        Args:
            angle: Target angle in degrees (-90 to +90)
            smooth: If True, move smoothly; if False, jump directly
            speed: Movement speed in degrees per second (for smooth motion)
        """
        angle = max(-90.0, min(90.0, angle))

        if smooth and abs(angle - self.current_angle) > 1.0:
            # Smooth motion - move in small steps
            steps = int(abs(angle - self.current_angle) / (speed * 0.02))
            steps = max(1, min(steps, 100))  # Limit steps

            for i in range(steps + 1):
                intermediate = self.current_angle + (angle - self.current_angle) * (i / steps)
                if GPIO_AVAILABLE and self.pwm:
                    duty = self._angle_to_duty_cycle(intermediate)
                    self.pwm.ChangeDutyCycle(duty)
                time.sleep(0.02)
        else:
            # Direct movement
            if GPIO_AVAILABLE and self.pwm:
                duty = self._angle_to_duty_cycle(angle)
                self.pwm.ChangeDutyCycle(duty)

        self.current_angle = angle
        time.sleep(0.1)  # Allow servo to reach position

    def get_current_angle(self) -> float:
        """Get current servo angle."""
        return self.current_angle

    def center(self):
        """Move servo to center position (0°)."""
        self.move_to(0.0)

    def cleanup(self):
        """Clean up GPIO resources."""
        if GPIO_AVAILABLE and self.pwm:
            self.pwm.stop()
            GPIO.cleanup(self.gpio_pin)


class GimbalController(ABC):
    """Abstract base class for gimbal controllers."""

    @abstractmethod
    def move_to(self, position: GimbalPosition, smooth: bool = True):
        """Move gimbal to specified position."""
        pass

    @abstractmethod
    def get_current_position(self) -> GimbalPosition:
        """Get current gimbal position."""
        pass

    @abstractmethod
    def center(self):
        """Move gimbal to center position."""
        pass

    @abstractmethod
    def cleanup(self):
        """Clean up resources."""
        pass


class TwoAxisGimbal(GimbalController):
    """
    2-axis gimbal controller (pan and tilt).

    Hardware requirements:
    - 2x RC servo motors (e.g., SG90, MG90S)
    - Raspberry Pi GPIO pins
    - 5V power supply (separate from Pi if using high-torque servos)
    - 3D printed gimbal mount
    """

    # Preset positions for common viewing angles
    PRESETS = {
        "center": GimbalPosition(pan=0, tilt=0),
        "overhead": GimbalPosition(pan=0, tilt=-90),
        "front": GimbalPosition(pan=0, tilt=-45),
        "left": GimbalPosition(pan=-60, tilt=-45),
        "right": GimbalPosition(pan=60, tilt=-45),
        "back_left": GimbalPosition(pan=-135, tilt=-30),
        "back_right": GimbalPosition(pan=135, tilt=-30),
        "low_angle": GimbalPosition(pan=0, tilt=-15),
    }

    def __init__(self, pan_pin: int = 17, tilt_pin: int = 18,
                 pan_limits: Tuple[float, float] = (-90, 90),
                 tilt_limits: Tuple[float, float] = (-90, 90)):
        """
        Initialize 2-axis gimbal.

        Args:
            pan_pin: GPIO pin for pan servo (BCM numbering)
            tilt_pin: GPIO pin for tilt servo (BCM numbering)
            pan_limits: (min, max) pan angles in degrees
            tilt_limits: (min, max) tilt angles in degrees
        """
        self.pan_servo = ServoController(pan_pin)
        self.tilt_servo = ServoController(tilt_pin)
        self.pan_limits = pan_limits
        self.tilt_limits = tilt_limits

        # Initialize to center position
        self.center()

    def move_to(self, position: GimbalPosition, smooth: bool = True, speed: float = 30.0):
        """
        Move gimbal to specified position.

        Args:
            position: Target position
            smooth: Enable smooth motion
            speed: Movement speed in degrees/second
        """
        # Clamp to limits
        pan = max(self.pan_limits[0], min(self.pan_limits[1], position.pan))
        tilt = max(self.tilt_limits[0], min(self.tilt_limits[1], position.tilt))

        # Move both servos simultaneously (non-blocking)
        self.pan_servo.move_to(pan, smooth, speed)
        self.tilt_servo.move_to(tilt, smooth, speed)

    def get_current_position(self) -> GimbalPosition:
        """Get current gimbal position."""
        return GimbalPosition(
            pan=self.pan_servo.get_current_angle(),
            tilt=self.tilt_servo.get_current_angle()
        )

    def center(self):
        """Move gimbal to center position."""
        self.move_to(GimbalPosition(pan=0, tilt=0), smooth=False)

    def move_to_preset(self, preset_name: str, smooth: bool = True):
        """
        Move to a preset position.

        Args:
            preset_name: Name of preset (e.g., "overhead", "front", "left")
            smooth: Enable smooth motion
        """
        if preset_name in self.PRESETS:
            self.move_to(self.PRESETS[preset_name], smooth)
        else:
            print(f"Warning: Unknown preset '{preset_name}'")

    def scan_area(self, positions: List[GimbalPosition], dwell_time: float = 1.0):
        """
        Scan through multiple positions sequentially.

        Args:
            positions: List of positions to visit
            dwell_time: Time to pause at each position (seconds)
        """
        for pos in positions:
            self.move_to(pos, smooth=True)
            time.sleep(dwell_time)

    def panorama_scan(self, tilt: float = -45, pan_range: Tuple[float, float] = (-90, 90),
                      steps: int = 5, dwell_time: float = 1.0) -> List[GimbalPosition]:
        """
        Perform a panoramic scan at fixed tilt angle.

        Args:
            tilt: Tilt angle to maintain
            pan_range: (start_pan, end_pan) in degrees
            steps: Number of positions to capture
            dwell_time: Time at each position

        Returns:
            List of positions visited
        """
        positions = []
        pan_start, pan_end = pan_range
        pan_step = (pan_end - pan_start) / (steps - 1) if steps > 1 else 0

        for i in range(steps):
            pan = pan_start + i * pan_step
            pos = GimbalPosition(pan=pan, tilt=tilt)
            positions.append(pos)
            self.move_to(pos, smooth=True)
            time.sleep(dwell_time)

        return positions

    def cleanup(self):
        """Clean up GPIO resources."""
        self.pan_servo.cleanup()
        self.tilt_servo.cleanup()


class ThreeAxisGimbal(GimbalController):
    """
    3-axis gimbal controller (pan, tilt, and roll).

    Hardware requirements:
    - 3x RC servo motors
    - Raspberry Pi GPIO pins
    - 5V power supply
    - 3D printed 3-axis gimbal mount
    """

    def __init__(self, pan_pin: int = 17, tilt_pin: int = 18, roll_pin: int = 27,
                 pan_limits: Tuple[float, float] = (-90, 90),
                 tilt_limits: Tuple[float, float] = (-90, 90),
                 roll_limits: Tuple[float, float] = (-45, 45)):
        """
        Initialize 3-axis gimbal.

        Args:
            pan_pin: GPIO pin for pan servo
            tilt_pin: GPIO pin for tilt servo
            roll_pin: GPIO pin for roll servo
            pan_limits: (min, max) pan angles
            tilt_limits: (min, max) tilt angles
            roll_limits: (min, max) roll angles
        """
        self.pan_servo = ServoController(pan_pin)
        self.tilt_servo = ServoController(tilt_pin)
        self.roll_servo = ServoController(roll_pin)
        self.pan_limits = pan_limits
        self.tilt_limits = tilt_limits
        self.roll_limits = roll_limits

        self.center()

    def move_to(self, position: GimbalPosition, smooth: bool = True, speed: float = 30.0):
        """Move gimbal to specified position."""
        # Clamp to limits
        pan = max(self.pan_limits[0], min(self.pan_limits[1], position.pan))
        tilt = max(self.tilt_limits[0], min(self.tilt_limits[1], position.tilt))
        roll = max(self.roll_limits[0], min(self.roll_limits[1], position.roll or 0.0))

        # Move all servos
        self.pan_servo.move_to(pan, smooth, speed)
        self.tilt_servo.move_to(tilt, smooth, speed)
        self.roll_servo.move_to(roll, smooth, speed)

    def get_current_position(self) -> GimbalPosition:
        """Get current gimbal position."""
        return GimbalPosition(
            pan=self.pan_servo.get_current_angle(),
            tilt=self.tilt_servo.get_current_angle(),
            roll=self.roll_servo.get_current_angle()
        )

    def center(self):
        """Move gimbal to center position."""
        self.move_to(GimbalPosition(pan=0, tilt=0, roll=0), smooth=False)

    def cleanup(self):
        """Clean up GPIO resources."""
        self.pan_servo.cleanup()
        self.tilt_servo.cleanup()
        self.roll_servo.cleanup()


class AutomatedScanController:
    """
    High-level controller for automated camera positioning and scanning.

    Integrates gimbal control with vision system for intelligent positioning.
    """

    def __init__(self, gimbal: GimbalController):
        """
        Initialize automated scan controller.

        Args:
            gimbal: GimbalController instance
        """
        self.gimbal = gimbal
        self.scan_history: List[Tuple[GimbalPosition, int]] = []  # (position, object_count)

    def full_coverage_scan(self, tilt_angles: List[float] = [-90, -60, -30, 0],
                          pan_range: Tuple[float, float] = (-90, 90),
                          pan_steps: int = 5) -> List[GimbalPosition]:
        """
        Perform a comprehensive scan covering the entire work area.

        Args:
            tilt_angles: List of tilt angles to scan at
            pan_range: Pan range (start, end)
            pan_steps: Number of pan positions per tilt

        Returns:
            List of all positions scanned
        """
        all_positions = []
        pan_start, pan_end = pan_range

        for tilt in tilt_angles:
            for i in range(pan_steps):
                if pan_steps > 1:
                    pan = pan_start + i * (pan_end - pan_start) / (pan_steps - 1)
                else:
                    pan = (pan_start + pan_end) / 2

                pos = GimbalPosition(pan=pan, tilt=tilt)
                self.gimbal.move_to(pos, smooth=True)
                all_positions.append(pos)
                time.sleep(0.5)  # Stabilization time

        return all_positions

    def focus_scan(self, center_position: GimbalPosition,
                   radius: float = 30, steps: int = 8) -> List[GimbalPosition]:
        """
        Scan in a circular pattern around a center position.

        Useful for detailed inspection of a specific area.

        Args:
            center_position: Center of scan pattern
            radius: Scan radius in degrees
            steps: Number of positions around circle

        Returns:
            List of positions scanned
        """
        import math
        positions = [center_position]  # Start at center

        for i in range(steps):
            angle = 2 * math.pi * i / steps
            pan_offset = radius * math.cos(angle)
            tilt_offset = radius * math.sin(angle)

            pos = GimbalPosition(
                pan=center_position.pan + pan_offset,
                tilt=center_position.tilt + tilt_offset
            )
            self.gimbal.move_to(pos, smooth=True)
            positions.append(pos)
            time.sleep(0.5)

        return positions

    def adaptive_scan(self, initial_positions: List[GimbalPosition],
                     detection_callback, threshold: int = 5) -> List[GimbalPosition]:
        """
        Adaptive scanning that focuses on areas with detected objects.

        Args:
            initial_positions: Initial positions to scan
            detection_callback: Function that returns number of detected objects
            threshold: Minimum object count to trigger detailed scan

        Returns:
            List of all positions scanned (including adaptive positions)
        """
        all_positions = []
        interesting_positions = []

        # Initial scan
        for pos in initial_positions:
            self.gimbal.move_to(pos, smooth=True)
            time.sleep(0.5)

            object_count = detection_callback()
            self.scan_history.append((pos, object_count))
            all_positions.append(pos)

            if object_count >= threshold:
                interesting_positions.append(pos)

        # Detailed scan of interesting areas
        for pos in interesting_positions:
            detail_positions = self.focus_scan(pos, radius=15, steps=4)
            all_positions.extend(detail_positions[1:])  # Skip center (already scanned)

        return all_positions

    def return_to_best_position(self) -> Optional[GimbalPosition]:
        """
        Return gimbal to position with most detected objects.

        Returns:
            Best position, or None if no history
        """
        if not self.scan_history:
            return None

        best_pos, _ = max(self.scan_history, key=lambda x: x[1])
        self.gimbal.move_to(best_pos, smooth=True)
        return best_pos

    def clear_history(self):
        """Clear scan history."""
        self.scan_history.clear()
