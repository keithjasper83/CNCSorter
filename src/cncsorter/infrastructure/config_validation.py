"""Configuration validation using Pydantic.

This module provides validation models for the configuration dictionary
in config.py using Pydantic, ensuring type safety and constraints.
"""
from typing import Tuple, List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class HardwareConfig(BaseModel):
    platform: str
    cpu_cores: int = Field(ge=1)
    ram_gb: int = Field(ge=1)
    local_storage_gb: int
    network_storage_tb: int
    network_speed_mbps: int


class WorkspaceConfig(BaseModel):
    width_mm: float = Field(gt=0)
    depth_mm: float = Field(gt=0)
    height_mm: float = Field(gt=0)
    bed_height_mm: float


class VisionConfig(BaseModel):
    default_camera_index: int = Field(ge=0)
    resolution: Tuple[int, int]
    fps_target: int = Field(gt=0)
    preview_scale: float = Field(gt=0, le=1)
    min_object_area_px: int = Field(ge=0)
    max_object_area_px: int = Field(ge=0)
    threshold_value: int = Field(ge=0, le=255)
    frame_skip: int = Field(ge=1)
    max_objects_per_frame: int = Field(gt=0)
    multi_camera_enabled: bool = True
    camera_count: int = Field(ge=1)

    @field_validator('max_object_area_px')
    @classmethod
    def check_max_area(cls, v: int, info: Any) -> int:
        values = info.data
        if 'min_object_area_px' in values and v < values['min_object_area_px']:
            raise ValueError('max_object_area_px must be greater than min_object_area_px')
        return v


class BedMappingConfig(BaseModel):
    capture_grid_x: int = Field(ge=1)
    capture_grid_y: int = Field(ge=1)
    total_captures: int = Field(ge=1)
    overlap_percent: int = Field(ge=0, le=90)
    capture_width_mm: float = Field(gt=0)
    capture_height_mm: float = Field(gt=0)
    local_output_dir: str
    network_output_dir: str
    use_network_storage: bool
    local_retention_days: int
    max_local_maps: int

    @model_validator(mode='after')
    def check_total_captures(self) -> 'BedMappingConfig':
        expected = self.capture_grid_x * self.capture_grid_y
        if self.total_captures != expected:
            raise ValueError(f'total_captures ({self.total_captures}) does not match grid ({expected})')
        return self


class GimbalConfig(BaseModel):
    enabled: bool
    type: str
    pan_gpio_pin: int
    tilt_gpio_pin: int
    roll_gpio_pin: Optional[int] = None
    pan_range_degrees: Tuple[float, float]
    tilt_range_degrees: Tuple[float, float]
    roll_range_degrees: Optional[Tuple[float, float]] = None
    movement_speed: float = Field(gt=0)
    scan_positions_overhead: List[Dict[str, float]]
    scan_positions_sides: List[Dict[str, float]]

    @model_validator(mode='after')
    def check_pins(self) -> 'GimbalConfig':
        if self.enabled:
            if self.pan_gpio_pin == self.tilt_gpio_pin:
                raise ValueError('Pan and tilt pins cannot be the same')
        return self


class CNCConfig(BaseModel):
    mode: str
    serial_port: str
    serial_baudrate: int
    http_host: str
    http_port: int
    x_min_mm: float
    x_max_mm: float
    y_min_mm: float
    y_max_mm: float
    z_min_mm: float
    z_max_mm: float
    feed_rate_mm_min: float = Field(gt=0)
    safe_z_height_mm: float


class ToolConfig(BaseModel):
    id: str
    offset_mm: Tuple[float, float, float]
    handling_types: List[str]
    tool_change_location: Dict[str, float]


class BinConfig(BaseModel):
    id: str
    location: Dict[str, float]
    accepts: List[str]
    size_range: List[str]


class SortingConfig(BaseModel):
    tools: Dict[str, ToolConfig]
    bins: List[BinConfig]
    default_tool: str
    default_bin: str
    path_optimization: str


class ConfigModel(BaseModel):
    HARDWARE: HardwareConfig
    WORKSPACE: WorkspaceConfig
    VISION: VisionConfig
    BED_MAPPING: BedMappingConfig
    GIMBAL: GimbalConfig
    CNC: CNCConfig
    SORTING: SortingConfig

    @model_validator(mode='after')
    def check_cnc_workspace_match(self) -> 'ConfigModel':
        if self.CNC.x_max_mm != self.WORKSPACE.width_mm:
            raise ValueError("CNC X max does not match Workspace width")
        if self.CNC.y_max_mm != self.WORKSPACE.depth_mm:
            raise ValueError("CNC Y max does not match Workspace depth")
        return self


def validate_config_dict(config_module: Any) -> ConfigModel:
    """Validate configuration module/dict against Pydantic models."""
    config_data = {
        "HARDWARE": config_module.HARDWARE,
        "WORKSPACE": config_module.WORKSPACE,
        "VISION": config_module.VISION,
        "BED_MAPPING": config_module.BED_MAPPING,
        "GIMBAL": config_module.GIMBAL,
        "CNC": config_module.CNC,
        "SORTING": config_module.SORTING
    }
    return ConfigModel(**config_data)
