#!/usr/bin/env python3
"""
Machine Configuration Wizard for CNCSorter
===========================================

Interactive interface for specifying machine limits and camera visible regions
before first live test. Generates custom config files and validates settings.

Usage:
    python configure_machine.py              # Interactive wizard
    python configure_machine.py --validate   # Validate current config
    python configure_machine.py --export     # Export current config to file
"""

import json
import sys
from dataclasses import dataclass, asdict
from typing import Tuple, Optional
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from cncsorter import config


@dataclass
class MachineLimits:
    """Machine workspace limits in millimeters."""
    x_min: float = 0.0
    x_max: float = 800.0
    y_min: float = 0.0
    y_max: float = 400.0
    z_min: float = 0.0
    z_max: float = 300.0
    safe_z_height: float = 50.0

    def validate(self) -> list[str]:
        """Validate machine limits."""
        errors = []

        if self.x_min >= self.x_max:
            errors.append("X minimum must be less than X maximum")
        if self.y_min >= self.y_max:
            errors.append("Y minimum must be less than Y maximum")
        if self.z_min >= self.z_max:
            errors.append("Z minimum must be less than Z maximum")
        if self.safe_z_height < self.z_min or self.safe_z_height > self.z_max:
            errors.append("Safe Z height must be within Z limits")

        if self.x_min < 0 or self.y_min < 0 or self.z_min < 0:
            errors.append("Minimum limits should not be negative")

        if self.x_max > 2000 or self.y_max > 2000 or self.z_max > 1000:
            errors.append("Maximum limits seem unreasonably large (check units are mm)")

        return errors

    def get_workspace_volume(self) -> float:
        """Calculate workspace volume in cubic millimeters."""
        return (self.x_max - self.x_min) * (self.y_max - self.y_min) * (self.z_max - self.z_min)


@dataclass
class CameraVisibleRegion:
    """Camera visible region at a specific height (field of view)."""
    camera_id: int = 0
    camera_name: str = "Camera 0"

    # Camera mounting position in CNC coordinates (mm)
    mount_x: float = 0.0
    mount_y: float = 0.0
    mount_z: float = 300.0  # Height above bed

    # Visible region at bed level (Z=0) in mm
    # This defines the rectangle the camera can see when looking straight down
    visible_width_mm: float = 400.0
    visible_height_mm: float = 300.0

    # Center offset from mount position (for angled cameras)
    center_offset_x: float = 0.0
    center_offset_y: float = 0.0

    # Camera orientation (degrees from vertical)
    tilt_angle: float = 0.0  # 0 = looking straight down, positive = tilting back
    pan_angle: float = 0.0   # 0 = centered, positive = rotating right

    def get_coverage_rectangle(self) -> Tuple[float, float, float, float]:
        """
        Get the coverage rectangle at bed level (Z=0).

        Returns:
            Tuple of (x_min, y_min, x_max, y_max) in mm
        """
        center_x = self.mount_x + self.center_offset_x
        center_y = self.mount_y + self.center_offset_y

        half_width = self.visible_width_mm / 2
        half_height = self.visible_height_mm / 2

        return (
            center_x - half_width,
            center_y - half_height,
            center_x + half_width,
            center_y + half_height
        )

    def get_coverage_area(self) -> float:
        """Get coverage area in square millimeters."""
        return self.visible_width_mm * self.visible_height_mm

    def validate(self, machine_limits: MachineLimits) -> list[str]:
        """Validate camera configuration against machine limits."""
        errors = []

        # Check mount position is within machine limits
        if not (machine_limits.x_min <= self.mount_x <= machine_limits.x_max):
            errors.append(f"{self.camera_name}: Mount X position outside machine limits")
        if not (machine_limits.y_min <= self.mount_y <= machine_limits.y_max):
            errors.append(f"{self.camera_name}: Mount Y position outside machine limits")
        if not (machine_limits.z_min <= self.mount_z <= machine_limits.z_max):
            errors.append(f"{self.camera_name}: Mount Z position outside machine limits")

        # Check visible region doesn't extend beyond machine limits
        x_min, y_min, x_max, y_max = self.get_coverage_rectangle()

        if x_min < machine_limits.x_min:
            errors.append(f"{self.camera_name}: Visible region extends before X minimum")
        if x_max > machine_limits.x_max:
            errors.append(f"{self.camera_name}: Visible region extends past X maximum")
        if y_min < machine_limits.y_min:
            errors.append(f"{self.camera_name}: Visible region extends before Y minimum")
        if y_max > machine_limits.y_max:
            errors.append(f"{self.camera_name}: Visible region extends past Y maximum")

        # Warnings for unusual configurations
        if self.mount_z < 100:
            errors.append(f"{self.camera_name}: WARNING - Camera very close to bed (<100mm)")
        if self.mount_z > 500:
            errors.append(f"{self.camera_name}: WARNING - Camera very high (>500mm), resolution may be poor")

        return errors


@dataclass
class ScanningPattern:
    """Scanning pattern for multi-position coverage."""
    pattern_name: str = "Grid Pattern"

    # Number of positions in X and Y
    positions_x: int = 3
    positions_y: int = 2

    # Overlap between adjacent positions (percentage)
    overlap_percent: float = 20.0

    # Whether to use serpentine pattern (more efficient)
    serpentine: bool = True

    def calculate_positions(self, machine_limits: MachineLimits,
                           camera_region: CameraVisibleRegion) -> list[Tuple[float, float, float]]:
        """
        Calculate CNC positions for scanning pattern.

        Returns:
            List of (x, y, z) positions in mm for CNC to visit
        """
        positions = []

        workspace_width = machine_limits.x_max - machine_limits.x_min
        workspace_height = machine_limits.y_max - machine_limits.y_min

        # Calculate step size accounting for overlap
        overlap_factor = (100 - self.overlap_percent) / 100
        step_x = (workspace_width / self.positions_x) * overlap_factor
        step_y = (workspace_height / self.positions_y) * overlap_factor

        # Calculate starting position (offset to center coverage)
        start_x = machine_limits.x_min + (camera_region.visible_width_mm / 2)
        start_y = machine_limits.y_min + (camera_region.visible_height_mm / 2)

        z = camera_region.mount_z

        for j in range(self.positions_y):
            y = start_y + (j * step_y)

            # Serpentine pattern alternates direction
            if self.serpentine and j % 2 == 1:
                x_range = range(self.positions_x - 1, -1, -1)
            else:
                x_range = range(self.positions_x)

            for i in x_range:
                x = start_x + (i * step_x)
                positions.append((x, y, z))

        return positions

    def get_total_positions(self) -> int:
        """Get total number of positions in pattern."""
        return self.positions_x * self.positions_y

    def estimate_coverage_percent(self, machine_limits: MachineLimits,
                                  camera_region: CameraVisibleRegion) -> float:
        """Estimate percentage of workspace covered by scan pattern."""
        workspace_area = (machine_limits.x_max - machine_limits.x_min) * \
                        (machine_limits.y_max - machine_limits.y_min)

        # Account for overlaps (approximate)
        overlap_factor = (100 - self.overlap_percent) / 100
        coverage_area = camera_region.get_coverage_area() * self.get_total_positions() * overlap_factor

        return min((coverage_area / workspace_area) * 100, 100)


class MachineConfigurationWizard:
    """Interactive wizard for machine configuration."""

    def __init__(self):
        self.machine_limits = MachineLimits()
        self.cameras: list[CameraVisibleRegion] = []
        self.scanning_pattern = ScanningPattern()

    def run_interactive(self):
        """Run interactive configuration wizard."""
        print("=" * 70)
        print("CNCSorter Machine Configuration Wizard")
        print("=" * 70)
        print()
        print("This wizard will help you configure machine limits and camera")
        print("visible regions for your first live test.")
        print()

        # Configure machine limits
        self._configure_machine_limits()

        # Configure cameras
        self._configure_cameras()

        # Configure scanning pattern
        self._configure_scanning_pattern()

        # Validate and summarize
        self._validate_and_summarize()

        # Save configuration
        self._save_configuration()

    def _configure_machine_limits(self):
        """Configure CNC machine workspace limits."""
        print("\n" + "─" * 70)
        print("STEP 1: Machine Workspace Limits")
        print("─" * 70)
        print()
        print("Define the safe working area for your CNC machine in millimeters.")
        print(f"Current values: X:[{self.machine_limits.x_min}, {self.machine_limits.x_max}] "
              f"Y:[{self.machine_limits.y_min}, {self.machine_limits.y_max}] "
              f"Z:[{self.machine_limits.z_min}, {self.machine_limits.z_max}]")
        print()

        if not self._ask_yes_no("Use current values from config.py?", default=True):
            self.machine_limits.x_min = self._ask_float("X minimum (mm)", default=0.0)
            self.machine_limits.x_max = self._ask_float("X maximum (mm)", default=800.0)
            self.machine_limits.y_min = self._ask_float("Y minimum (mm)", default=0.0)
            self.machine_limits.y_max = self._ask_float("Y maximum (mm)", default=400.0)
            self.machine_limits.z_min = self._ask_float("Z minimum (mm)", default=0.0)
            self.machine_limits.z_max = self._ask_float("Z maximum (mm)", default=300.0)
            self.machine_limits.safe_z_height = self._ask_float("Safe Z parking height (mm)", default=50.0)

        print()
        print(f"✓ Workspace: {self.machine_limits.x_max - self.machine_limits.x_min}mm × "
              f"{self.machine_limits.y_max - self.machine_limits.y_min}mm × "
              f"{self.machine_limits.z_max - self.machine_limits.z_min}mm")
        print(f"✓ Volume: {self.machine_limits.get_workspace_volume() / 1000000:.1f} liters")

    def _configure_cameras(self):
        """Configure camera visible regions."""
        print("\n" + "─" * 70)
        print("STEP 2: Camera Visible Regions")
        print("─" * 70)
        print()
        print("Configure each camera's visible region at bed level (Z=0).")
        print()

        num_cameras = self._ask_int("How many cameras will you use?", default=1, min_val=1, max_val=10)

        for i in range(num_cameras):
            print(f"\n  Camera {i}:")
            print(f"  " + "─" * 60)

            camera = CameraVisibleRegion(camera_id=i, camera_name=f"Camera {i}")

            camera.mount_x = self._ask_float(f"  Mount X position (mm)", default=self.machine_limits.x_max / 2)
            camera.mount_y = self._ask_float(f"  Mount Y position (mm)", default=self.machine_limits.y_max / 2)
            camera.mount_z = self._ask_float(f"  Mount Z height above bed (mm)", default=300.0)

            camera.visible_width_mm = self._ask_float(f"  Visible width at bed level (mm)", default=400.0)
            camera.visible_height_mm = self._ask_float(f"  Visible height at bed level (mm)", default=300.0)

            if self._ask_yes_no(f"  Is camera angled (not looking straight down)?", default=False):
                camera.tilt_angle = self._ask_float(f"  Tilt angle (degrees from vertical)", default=0.0)
                camera.pan_angle = self._ask_float(f"  Pan angle (degrees from center)", default=0.0)
                camera.center_offset_x = self._ask_float(f"  Center offset X (mm)", default=0.0)
                camera.center_offset_y = self._ask_float(f"  Center offset Y (mm)", default=0.0)

            self.cameras.append(camera)

            x_min, y_min, x_max, y_max = camera.get_coverage_rectangle()
            print(f"  ✓ Coverage: [{x_min:.1f}, {y_min:.1f}] to [{x_max:.1f}, {y_max:.1f}] mm")
            print(f"  ✓ Area: {camera.get_coverage_area() / 100:.1f} cm²")

    def _configure_scanning_pattern(self):
        """Configure scanning pattern for coverage."""
        print("\n" + "─" * 70)
        print("STEP 3: Scanning Pattern")
        print("─" * 70)
        print()
        print("Define the scanning pattern for full workspace coverage.")
        print()

        if len(self.cameras) == 0:
            print("No cameras configured. Skipping scanning pattern.")
            return

        primary_camera = self.cameras[0]

        self.scanning_pattern.positions_x = self._ask_int("Number of positions in X direction", default=3, min_val=1)
        self.scanning_pattern.positions_y = self._ask_int("Number of positions in Y direction", default=2, min_val=1)
        self.scanning_pattern.overlap_percent = self._ask_float("Overlap between positions (%)", default=20.0, min_val=0.0, max_val=50.0)
        self.scanning_pattern.serpentine = self._ask_yes_no("Use serpentine pattern (alternating direction)?", default=True)

        print()
        print(f"✓ Total positions: {self.scanning_pattern.get_total_positions()}")

        coverage = self.scanning_pattern.estimate_coverage_percent(self.machine_limits, primary_camera)
        print(f"✓ Estimated coverage: {coverage:.1f}%")

        if coverage < 95:
            print(f"  ⚠ WARNING: Coverage less than 95%. Consider more positions or wider camera FOV.")

    def _validate_and_summarize(self):
        """Validate configuration and show summary."""
        print("\n" + "=" * 70)
        print("Configuration Summary")
        print("=" * 70)

        # Validate machine limits
        print("\n📏 Machine Limits:")
        errors = self.machine_limits.validate()
        if errors:
            print("  ❌ ERRORS:")
            for error in errors:
                print(f"     - {error}")
        else:
            print(f"  ✓ X: {self.machine_limits.x_min} to {self.machine_limits.x_max} mm")
            print(f"  ✓ Y: {self.machine_limits.y_min} to {self.machine_limits.y_max} mm")
            print(f"  ✓ Z: {self.machine_limits.z_min} to {self.machine_limits.z_max} mm")
            print(f"  ✓ Safe Z: {self.machine_limits.safe_z_height} mm")

        # Validate cameras
        print(f"\n📷 Cameras: {len(self.cameras)} configured")
        for camera in self.cameras:
            errors = camera.validate(self.machine_limits)
            if errors:
                print(f"  ❌ {camera.camera_name} ERRORS:")
                for error in errors:
                    print(f"     - {error}")
            else:
                x_min, y_min, x_max, y_max = camera.get_coverage_rectangle()
                print(f"  ✓ {camera.camera_name}: [{x_min:.0f}, {y_min:.0f}] to [{x_max:.0f}, {y_max:.0f}] mm")

        # Summarize scanning pattern
        if self.cameras:
            print(f"\n🗺️  Scanning Pattern:")
            print(f"  ✓ Grid: {self.scanning_pattern.positions_x} × {self.scanning_pattern.positions_y} = {self.scanning_pattern.get_total_positions()} positions")
            print(f"  ✓ Overlap: {self.scanning_pattern.overlap_percent}%")
            print(f"  ✓ Pattern: {'Serpentine' if self.scanning_pattern.serpentine else 'Raster'}")

            coverage = self.scanning_pattern.estimate_coverage_percent(self.machine_limits, self.cameras[0])
            print(f"  ✓ Coverage: {coverage:.1f}%")

    def _save_configuration(self):
        """Save configuration to file."""
        print("\n" + "─" * 70)

        if not self._ask_yes_no("Save this configuration?", default=True):
            print("Configuration not saved.")
            return

        output_dir = Path("config")
        output_dir.mkdir(exist_ok=True)

        filename = self._ask_string("Configuration filename", default="machine_config.json")
        if not filename.endswith(".json"):
            filename += ".json"

        output_path = output_dir / filename

        config_data = {
            "machine_limits": asdict(self.machine_limits),
            "cameras": [asdict(cam) for cam in self.cameras],
            "scanning_pattern": asdict(self.scanning_pattern),
        }

        with open(output_path, 'w') as f:
            json.dump(config_data, f, indent=2)

        print(f"\n✓ Configuration saved to: {output_path}")
        print(f"\nTo use this configuration, run:")
        print(f"  python -m src.main --config {output_path}")

    # Helper methods for user input
    def _ask_float(self, prompt: str, default: float, min_val: Optional[float] = None,
                   max_val: Optional[float] = None) -> float:
        """Ask for float input with validation."""
        while True:
            try:
                response = input(f"{prompt} [{default}]: ").strip()
                value = float(response) if response else default

                if min_val is not None and value < min_val:
                    print(f"  Value must be >= {min_val}")
                    continue
                if max_val is not None and value > max_val:
                    print(f"  Value must be <= {max_val}")
                    continue

                return value
            except ValueError:
                print("  Invalid number. Please try again.")

    def _ask_int(self, prompt: str, default: int, min_val: Optional[int] = None,
                 max_val: Optional[int] = None) -> int:
        """Ask for integer input with validation."""
        while True:
            try:
                response = input(f"{prompt} [{default}]: ").strip()
                value = int(response) if response else default

                if min_val is not None and value < min_val:
                    print(f"  Value must be >= {min_val}")
                    continue
                if max_val is not None and value > max_val:
                    print(f"  Value must be <= {max_val}")
                    continue

                return value
            except ValueError:
                print("  Invalid integer. Please try again.")

    def _ask_string(self, prompt: str, default: str) -> str:
        """Ask for string input."""
        response = input(f"{prompt} [{default}]: ").strip()
        return response if response else default

    def _ask_yes_no(self, prompt: str, default: bool) -> bool:
        """Ask for yes/no input."""
        default_str = "Y/n" if default else "y/N"
        while True:
            response = input(f"{prompt} [{default_str}]: ").strip().lower()
            if not response:
                return default
            if response in ['y', 'yes']:
                return True
            if response in ['n', 'no']:
                return False
            print("  Please answer 'y' or 'n'.")


def validate_current_config():
    """Validate current configuration from config.py."""
    print("=" * 70)
    print("Validating Current Configuration")
    print("=" * 70)
    print()

    # Create limits from current config
    limits = MachineLimits(
        x_min=config.CNC["x_min_mm"],
        x_max=config.CNC["x_max_mm"],
        y_min=config.CNC["y_min_mm"],
        y_max=config.CNC["y_max_mm"],
        z_min=config.CNC["z_min_mm"],
        z_max=config.CNC["z_max_mm"],
        safe_z_height=config.CNC["safe_z_height_mm"],
    )

    errors = limits.validate()

    if errors:
        print("❌ Configuration Errors:")
        for error in errors:
            print(f"   - {error}")
        return False
    else:
        print("✓ Machine limits are valid")
        print(f"  X: {limits.x_min} to {limits.x_max} mm")
        print(f"  Y: {limits.y_min} to {limits.y_max} mm")
        print(f"  Z: {limits.z_min} to {limits.z_max} mm")
        print(f"  Workspace: {limits.get_workspace_volume() / 1000000:.1f} liters")
        return True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="CNCSorter Machine Configuration")
    parser.add_argument("--validate", action="store_true", help="Validate current config.py")
    parser.add_argument("--export", action="store_true", help="Export current config to file")

    args = parser.parse_args()

    if args.validate:
        success = validate_current_config()
        sys.exit(0 if success else 1)
    elif args.export:
        print("Export functionality not yet implemented.")
        sys.exit(1)
    else:
        # Run interactive wizard
        wizard = MachineConfigurationWizard()
        wizard.run_interactive()


if __name__ == "__main__":
    main()
