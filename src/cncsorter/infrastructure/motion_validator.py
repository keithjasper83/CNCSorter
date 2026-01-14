"""Motion safety validator for CNC operations.

This module implements mandatory safety validation to prevent physical damage
by enforcing workspace boundaries. All G-code movement commands are intercepted
and validated before transmission to the CNC controller.
"""
import re
from typing import Optional

from cncsorter.domain.entities import CNCCoordinate
from cncsorter.application.events import EventBus, BoundaryViolationDetected


class BoundaryViolationError(Exception):
    """Raised when a movement command would violate workspace boundaries."""

    pass


class MotionValidator:
    """Validates CNC movements against workspace boundaries.

    This validator intercepts all G-code movement commands and validates
    target coordinates against configured workspace limits. Violations
    result in:
    1. BoundaryViolationError raised (blocks command)
    2. BoundaryViolationDetected event published (alerts system)

    The validator is mandatory and non-bypassable for safety.
    """

    def __init__(
        self,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        z_min: float,
        z_max: float,
        event_bus: Optional[EventBus] = None,
    ):
        """Initialize motion validator with workspace boundaries.

        Args:
            x_min: Minimum X coordinate (mm).
            x_max: Maximum X coordinate (mm).
            y_min: Minimum Y coordinate (mm).
            y_max: Maximum Y coordinate (mm).
            z_min: Minimum Z coordinate (mm).
            z_max: Maximum Z coordinate (mm).
            event_bus: Optional event bus for publishing violation events.
        """
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.z_min = z_min
        self.z_max = z_max
        self.event_bus = event_bus

        # Validation statistics
        self.validations_performed = 0
        self.violations_detected = 0

    def validate_coordinate(self, coordinate: CNCCoordinate) -> None:
        """Validate a coordinate against workspace boundaries.

        Args:
            coordinate: CNC coordinate to validate.

        Raises:
            BoundaryViolationError: If coordinate violates boundaries.
        """
        self.validations_performed += 1

        # Check X boundaries
        if coordinate.x < self.x_min or coordinate.x > self.x_max:
            self._handle_violation(
                coordinate,
                "workspace",
                f"X coordinate {coordinate.x:.2f}mm out of bounds "
                f"[{self.x_min:.2f}, {self.x_max:.2f}]",
            )

        # Check Y boundaries
        if coordinate.y < self.y_min or coordinate.y > self.y_max:
            self._handle_violation(
                coordinate,
                "workspace",
                f"Y coordinate {coordinate.y:.2f}mm out of bounds "
                f"[{self.y_min:.2f}, {self.y_max:.2f}]",
            )

        # Check Z boundaries
        if coordinate.z < self.z_min or coordinate.z > self.z_max:
            self._handle_violation(
                coordinate,
                "workspace",
                f"Z coordinate {coordinate.z:.2f}mm out of bounds "
                f"[{self.z_min:.2f}, {self.z_max:.2f}]",
            )

    def validate_gcode(self, gcode: str) -> str:
        """Validate and return G-code command if safe.

        Extracts target coordinates from G-code movement commands (G0, G1)
        and validates them against workspace boundaries.

        Args:
            gcode: G-code command string (e.g., "G1 X100 Y50 Z10 F1000").

        Returns:
            Original G-code if valid.

        Raises:
            BoundaryViolationError: If command would violate boundaries.
        """
        # Extract coordinates from G-code
        coordinate = self._extract_coordinates_from_gcode(gcode)

        if coordinate:
            # Validate if this is a movement command
            self.validate_coordinate(coordinate)

        return gcode

    def _extract_coordinates_from_gcode(self, gcode: str) -> Optional[CNCCoordinate]:
        """Extract X, Y, Z coordinates from G-code command.

        Args:
            gcode: G-code command string.

        Returns:
            CNCCoordinate if movement command, None otherwise.
        """
        gcode = gcode.strip().upper()

        # Check if this is a movement command (G0 or G1)
        if not (gcode.startswith("G0 ") or gcode.startswith("G1 ") or
                gcode.startswith("G0") or gcode.startswith("G1")):
            return None

        # Extract X, Y, Z using regex
        x_match = re.search(r"X\s*(-?\d+\.?\d*)", gcode)
        y_match = re.search(r"Y\s*(-?\d+\.?\d*)", gcode)
        z_match = re.search(r"Z\s*(-?\d+\.?\d*)", gcode)

        # If no coordinates found, not a position command
        if not (x_match or y_match or z_match):
            return None

        # Build coordinate with extracted values (use 0 for missing axes)
        x = float(x_match.group(1)) if x_match else 0.0
        y = float(y_match.group(1)) if y_match else 0.0
        z = float(z_match.group(1)) if z_match else 0.0

        return CNCCoordinate(x=x, y=y, z=z)

    def _handle_violation(
        self, coordinate: CNCCoordinate, boundary_type: str, message: str
    ) -> None:
        """Handle boundary violation by raising exception and publishing event.

        Args:
            coordinate: Attempted coordinate that violated boundaries.
            boundary_type: Type of boundary violated (e.g., "workspace").
            message: Human-readable violation message.

        Raises:
            BoundaryViolationError: Always raised to block the command.
        """
        self.violations_detected += 1

        # Publish event if event bus available
        if self.event_bus:
            self.event_bus.publish(
                BoundaryViolationDetected(
                    attempted_position=coordinate,
                    boundary_type=boundary_type,
                    message=message,
                    timestamp=None,  # Auto-generated
                )
            )

        # Always raise exception to block command
        raise BoundaryViolationError(message)

    def get_statistics(self) -> dict:
        """Get validation statistics.

        Returns:
            Dictionary with validation statistics.
        """
        return {
            "validations_performed": self.validations_performed,
            "violations_detected": self.violations_detected,
            "violation_rate": (
                self.violations_detected / self.validations_performed
                if self.validations_performed > 0
                else 0.0
            ),
        }

    def get_boundaries(self) -> dict:
        """Get current workspace boundaries.

        Returns:
            Dictionary with boundary limits.
        """
        return {
            "x_min": self.x_min,
            "x_max": self.x_max,
            "y_min": self.y_min,
            "y_max": self.y_max,
            "z_min": self.z_min,
            "z_max": self.z_max,
        }
