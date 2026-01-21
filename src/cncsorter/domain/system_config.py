from dataclasses import dataclass
from typing import List

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
