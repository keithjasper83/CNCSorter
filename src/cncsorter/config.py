"""
CNCSorter System Configuration

Centralized configuration for hardware specifications, workspace dimensions,
and performance parameters optimized for Pi 5 with high-capacity storage.
"""

# ============================================================================
# HARDWARE CONFIGURATION
# ============================================================================

HARDWARE = {
    "platform": "raspberry_pi_5",
    "cpu_cores": 4,
    "ram_gb": 8,
    "local_storage_gb": 128,  # SSD
    "network_storage_tb": 8,
    "network_speed_mbps": 1000,
}

# ============================================================================
# WORKSPACE DIMENSIONS (in millimeters)
# ============================================================================

WORKSPACE = {
    "width_mm": 800,    # X-axis
    "depth_mm": 400,    # Y-axis
    "height_mm": 300,   # Z-axis (above bed)
    "bed_height_mm": 0, # Reference plane
}

# Derived workspace properties
WORKSPACE["area_mm2"] = WORKSPACE["width_mm"] * WORKSPACE["depth_mm"]  # 320,000 mm²
WORKSPACE["volume_mm3"] = WORKSPACE["area_mm2"] * WORKSPACE["height_mm"]  # 96,000,000 mm³

# ============================================================================
# VISION SYSTEM CONFIGURATION
# ============================================================================

VISION = {
    # Camera settings optimized for Pi 5 performance
    "default_camera_index": 0,
    "resolution": (1920, 1080),  # Full HD - Pi 5 can handle this
    "fps_target": 30,
    "preview_scale": 0.3,  # 30% scale for display, full res for processing
    
    # Object detection parameters
    # Calibrated for M2-M12 nuts, bolts, washers, spring washers
    "min_object_area_px": 50,  # M2 nuts (~2mm diameter) visible at 1080p
    "max_object_area_px": 80000,  # M12 bolts with washers
    "threshold_value": 127,
    
    # Frame processing
    "frame_skip": 1,  # Process every frame (Pi 5 can handle it)
    "max_objects_per_frame": 400,  # Pi 5 capacity
    
    # Multi-camera support
    "multi_camera_enabled": True,
    "camera_count": 4,  # Webcam, GoPro, iPhone, iPad
}

# ============================================================================
# OBJECT SPECIFICATIONS
# ============================================================================

OBJECTS = {
    # Component types and approximate physical dimensions (in millimeters)
    "types": {
        "M2": {
            "nut_diameter": 4.0,
            "bolt_head_diameter": 3.8,
            "washer_outer_diameter": 5.0,
            "min_pixel_area": 50,  # At 1920x1080 from ~300mm height
        },
        "M3": {
            "nut_diameter": 5.5,
            "bolt_head_diameter": 5.5,
            "washer_outer_diameter": 7.0,
            "min_pixel_area": 80,
        },
        "M4": {
            "nut_diameter": 7.0,
            "bolt_head_diameter": 7.0,
            "washer_outer_diameter": 9.0,
            "min_pixel_area": 120,
        },
        "M5": {
            "nut_diameter": 8.0,
            "bolt_head_diameter": 8.0,
            "washer_outer_diameter": 10.0,
            "min_pixel_area": 150,
        },
        "M6": {
            "nut_diameter": 10.0,
            "bolt_head_diameter": 10.0,
            "washer_outer_diameter": 12.5,
            "min_pixel_area": 200,
        },
        "M8": {
            "nut_diameter": 13.0,
            "bolt_head_diameter": 13.0,
            "washer_outer_diameter": 17.0,
            "min_pixel_area": 350,
        },
        "M10": {
            "nut_diameter": 16.0,
            "bolt_head_diameter": 16.0,
            "washer_outer_diameter": 21.0,
            "min_pixel_area": 550,
        },
        "M12": {
            "nut_diameter": 18.0,
            "bolt_head_diameter": 18.0,
            "washer_outer_diameter": 24.0,
            "min_pixel_area": 800,
        },
    },
    
    # Size classification ranges
    "size_ranges": {
        "tiny": {"min_px": 50, "max_px": 150, "typical": "M2-M3"},
        "small": {"min_px": 150, "max_px": 350, "typical": "M4-M6"},
        "medium": {"min_px": 350, "max_px": 800, "typical": "M8-M10"},
        "large": {"min_px": 800, "max_px": 80000, "typical": "M12+"},
    },
    
    # Detection confidence thresholds
    "confidence_thresholds": {
        "high_confidence": 0.85,  # Clear, well-lit, unobscured
        "medium_confidence": 0.65,  # Partial occlusion or poor lighting
        "low_confidence": 0.45,  # Barely visible, flag for review
    },
    
    # Component categories
    "categories": [
        "nut",
        "bolt",
        "washer",
        "spring_washer",
        "lock_washer",
        "hex_bolt",
        "socket_head_cap_screw",
        "unknown",  # Requires manual classification
    ],
    
    # Shape-based classification for "guessing" unknown objects
    "shape_features": {
        "circular": {
            "aspect_ratio_range": (0.85, 1.15),  # Nearly square bounding box
            "circularity_min": 0.7,  # High circularity
            "likely_types": ["washer", "nut", "coin", "bearing", "o-ring"],
        },
        "hexagonal": {
            "aspect_ratio_range": (0.9, 1.1),
            "corner_count": 6,
            "likely_types": ["nut", "hex_bolt_head"],
        },
        "rectangular": {
            "aspect_ratio_range": (1.5, 4.0),  # Elongated
            "circularity_max": 0.5,
            "likely_types": ["bolt", "screw", "pin", "nail", "tie_wrap"],
        },
        "small_circular": {
            "aspect_ratio_range": (0.85, 1.15),
            "area_max": 200,  # pixels
            "likely_types": ["small_washer", "spring_washer", "tiny_nut", "rivet"],
        },
        "irregular": {
            "circularity_max": 0.6,
            "aspect_ratio_range": (0.5, 2.0),
            "likely_types": ["clip", "spring", "bracket", "wire_piece", "debris"],
        },
    },
}

# ============================================================================
# PICK AND PLACE DATA EXPORT CONFIGURATION
# ============================================================================

PICK_AND_PLACE = {
    # Data output format for pick and place stage
    "output_format": "csv",  # csv, json, or both
    "csv_delimiter": ",",
    "include_confidence": True,
    "include_size_estimate": True,
    "include_shape_classification": True,
    
    # CSV column structure for pick and place
    "csv_columns": [
        "object_id",           # Unique identifier
        "x_mm",                # X coordinate in millimeters
        "y_mm",                # Y coordinate in millimeters
        "z_mm",                # Z coordinate (usually 0 for bed level)
        "area_px",             # Area in pixels
        "estimated_size",      # M2, M3, ..., M12, or "unknown"
        "shape_type",          # circular, hexagonal, rectangular, irregular
        "likely_category",     # Best guess: nut, bolt, washer, etc.
        "confidence",          # 0.0-1.0 confidence score
        "needs_review",        # Boolean: True if manual review suggested
        "rotation_degrees",    # Estimated rotation for gripper alignment
        "capture_image_id",    # Source image reference
    ],
    
    # Export settings
    "export_path_local": "/home/pi/pick_and_place_data",
    "export_path_network": "/mnt/network_storage/pick_and_place_data",
    "use_network_export": True,
    
    # Sorting and filtering
    "sort_by": "size",  # size, position, confidence, or capture_order
    "filter_low_confidence": False,  # Set True to exclude uncertain objects
    "min_confidence_threshold": 0.45,
    
    # Grouping for batch processing
    "group_by_size": True,  # Group M2s together, M3s together, etc.
    "group_by_type": True,  # Group nuts together, bolts together, etc.
}

# ============================================================================
# BED MAPPING CONFIGURATION
# ============================================================================

BED_MAPPING = {
    # Capture strategy for 800x400mm bed
    "capture_grid_x": 3,  # 3 columns
    "capture_grid_y": 2,  # 2 rows
    "total_captures": 6,  # 3x2 = 6 captures with overlap
    
    # Overlap for stitching
    "overlap_percent": 20,  # 20% overlap between adjacent captures
    
    # Calculated capture size (with overlap)
    "capture_width_mm": WORKSPACE["width_mm"] / 2.5,  # ~320mm per capture
    "capture_height_mm": WORKSPACE["depth_mm"] / 1.67,  # ~240mm per capture
    
    # Storage paths
    "local_output_dir": "/home/pi/cnc_maps",  # 128GB SSD
    "network_output_dir": "/mnt/network_storage/cnc_maps",  # 8TB NAS
    "use_network_storage": True,  # Prefer network storage for permanent storage
    
    # Retention policy
    "local_retention_days": 7,  # Keep 7 days locally before archiving
    "max_local_maps": 100,  # Auto-cleanup when exceeding this
}

# ============================================================================
# GIMBAL CONFIGURATION
# ============================================================================

GIMBAL = {
    # Hardware setup
    "enabled": True,
    "type": "two_axis",  # or "three_axis"
    "pan_gpio_pin": 17,
    "tilt_gpio_pin": 18,
    "roll_gpio_pin": 27,  # Only for three_axis
    
    # Motion parameters
    "pan_range_degrees": (-90, 90),
    "tilt_range_degrees": (-60, 60),
    "roll_range_degrees": (-30, 30),
    "movement_speed": 0.5,  # seconds per 90 degrees
    
    # Scanning patterns for 800x400mm bed
    "scan_positions_overhead": [
        {"pan": 0, "tilt": -45},  # Center overhead
        {"pan": -45, "tilt": -45},  # Left overhead
        {"pan": 45, "tilt": -45},  # Right overhead
    ],
    
    "scan_positions_sides": [
        {"pan": -60, "tilt": -30},  # Left side
        {"pan": 60, "tilt": -30},  # Right side
        {"pan": 0, "tilt": -60},  # Steep overhead
    ],
}

# ============================================================================
# CNC CONTROLLER CONFIGURATION
# ============================================================================

CNC = {
    # Connection settings
    "mode": "serial",  # or "http"
    "serial_port": "/dev/ttyUSB0",
    "serial_baudrate": 115200,
    "http_host": "192.168.1.100",
    "http_port": 80,
    
    # Workspace limits (safety boundaries)
    "x_min_mm": 0,
    "x_max_mm": WORKSPACE["width_mm"],
    "y_min_mm": 0,
    "y_max_mm": WORKSPACE["depth_mm"],
    "z_min_mm": WORKSPACE["bed_height_mm"],
    "z_max_mm": WORKSPACE["height_mm"],
    
    # Movement parameters
    "feed_rate_mm_min": 1000,  # 1000mm/min
    "safe_z_height_mm": 50,  # Park position for camera/gimbal
}

# ============================================================================
# PERFORMANCE OPTIMIZATION (Pi 5 specific)
# ============================================================================

PERFORMANCE = {
    # Threading
    "enable_multithreading": True,
    "worker_threads": 4,  # Match Pi 5 cores
    
    # Memory management
    "max_memory_usage_gb": 6,  # Leave 2GB for system
    "enable_memory_compression": False,  # Pi 5 has enough RAM
    
    # Processing priorities
    "realtime_detection_priority": True,
    "batch_processing_enabled": True,
    
    # Caching
    "cache_processed_frames": True,
    "max_cache_size_mb": 500,
    
    # Networking
    "async_network_storage": True,  # Don't block on network writes
    "network_timeout_seconds": 10,
}

# ============================================================================
# LOGGING AND MONITORING
# ============================================================================

LOGGING = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "local_log_dir": "/home/pi/cnc_logs",
    "network_log_dir": "/mnt/network_storage/cnc_logs",
    "max_local_log_size_mb": 100,
    "log_rotation_days": 7,
    
    # Performance metrics
    "enable_performance_logging": True,
    "log_fps": True,
    "log_object_count": True,
    "log_memory_usage": True,
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_output_dir():
    """Get the current output directory based on storage configuration."""
    if BED_MAPPING["use_network_storage"]:
        return BED_MAPPING["network_output_dir"]
    return BED_MAPPING["local_output_dir"]


def get_workspace_dimensions():
    """Get workspace dimensions as a tuple (width, depth, height)."""
    return (
        WORKSPACE["width_mm"],
        WORKSPACE["depth_mm"],
        WORKSPACE["height_mm"]
    )


def calculate_camera_positions_for_bed():
    """
    Calculate optimal camera positions for full bed coverage.
    Returns list of (x, y, z) positions in millimeters.
    """
    positions = []
    
    grid_x = BED_MAPPING["capture_grid_x"]
    grid_y = BED_MAPPING["capture_grid_y"]
    
    step_x = WORKSPACE["width_mm"] / (grid_x + 0.5)
    step_y = WORKSPACE["depth_mm"] / (grid_y + 0.5)
    
    # Optimal Z height for overhead camera (adjust based on FOV)
    optimal_z = CNC["safe_z_height_mm"]
    
    for i in range(grid_x):
        for j in range(grid_y):
            x = step_x * (i + 0.75)
            y = step_y * (j + 0.75)
            positions.append((x, y, optimal_z))
    
    return positions


def get_max_objects_capacity():
    """Calculate maximum objects system can handle based on hardware."""
    # Pi 5 with 8GB RAM and high-performance storage
    # Conservative estimate: 1KB per object
    available_memory_mb = PERFORMANCE["max_memory_usage_gb"] * 1024
    objects_in_memory = (available_memory_mb * 1024) // 1  # 1KB per object
    
    # Practical limit based on processing speed
    processing_limit = VISION["max_objects_per_frame"] * BED_MAPPING["total_captures"]
    
    return min(objects_in_memory, processing_limit)


def classify_object_by_size(area_pixels):
    """
    Classify a detected object by size based on pixel area.
    Returns tuple: (size_category, likely_size_range)
    """
    for category, range_info in OBJECTS["size_ranges"].items():
        if range_info["min_px"] <= area_pixels <= range_info["max_px"]:
            return (category, range_info["typical"])
    return ("unknown", "out_of_range")


def get_detection_params_for_size(size_type="all"):
    """
    Get optimized detection parameters for specific fastener sizes.
    
    Args:
        size_type: "tiny", "small", "medium", "large", or "all"
    
    Returns:
        dict with min_area and max_area for detection
    """
    if size_type == "all":
        return {
            "min_area": VISION["min_object_area_px"],
            "max_area": VISION["max_object_area_px"],
        }
    
    if size_type in OBJECTS["size_ranges"]:
        range_info = OBJECTS["size_ranges"][size_type]
        return {
            "min_area": range_info["min_px"],
            "max_area": range_info["max_px"],
        }
    
    # Default fallback
    return {
        "min_area": VISION["min_object_area_px"],
        "max_area": VISION["max_object_area_px"],
    }


def estimate_camera_height_for_resolution():
    """
    Calculate optimal camera height above bed for M2-M12 detection.
    Assumes standard webcam FOV (~60-70 degrees).
    
    Returns:
        Recommended Z height in millimeters
    """
    # For 1920x1080 resolution to detect M2 (2mm) objects
    # Typical rule: 1 pixel ≈ 0.5mm at optimal height for small fasteners
    # Optimal height: ~250-350mm for M2-M12 range
    
    return 300  # mm - good balance for M2-M12 detection


def guess_object_type(area_pixels, aspect_ratio, circularity):
    """
    Guess object type based on shape features.
    Used for unknown objects that don't match standard M2-M12 fasteners.
    
    Args:
        area_pixels: Area of detected object in pixels
        aspect_ratio: Width/Height ratio of bounding box
        circularity: 4*pi*area / perimeter^2 (1.0 = perfect circle)
    
    Returns:
        dict with:
            - shape_type: circular, hexagonal, rectangular, irregular
            - likely_types: list of possible object types
            - confidence: how confident the guess is (0.0-1.0)
    """
    shape_features = OBJECTS["shape_features"]
    
    # Check each shape category
    for shape_type, criteria in shape_features.items():
        # Check aspect ratio
        ar_range = criteria.get("aspect_ratio_range", (0, 100))
        if not (ar_range[0] <= aspect_ratio <= ar_range[1]):
            continue
        
        # Check circularity constraints
        if "circularity_min" in criteria and circularity < criteria["circularity_min"]:
            continue
        if "circularity_max" in criteria and circularity > criteria["circularity_max"]:
            continue
        
        # Check area constraints
        if "area_max" in criteria and area_pixels > criteria["area_max"]:
            continue
        
        # Match found
        confidence = 0.7  # Base confidence
        
        # Adjust confidence based on how well it fits
        if "circularity_min" in criteria:
            if circularity > criteria["circularity_min"] + 0.2:
                confidence += 0.15
        
        return {
            "shape_type": shape_type,
            "likely_types": criteria["likely_types"],
            "confidence": min(confidence, 0.95),
        }
    
    # No good match - return irregular with low confidence
    return {
        "shape_type": "irregular",
        "likely_types": ["unknown_object", "debris", "contamination"],
        "confidence": 0.3,
    }


def create_pick_and_place_record(detected_object, cnc_position, guess_result=None):
    """
    Create a data record for pick and place system.
    
    Args:
        detected_object: DetectedObject entity from detection
        cnc_position: CNCCoordinate with X, Y, Z in mm
        guess_result: Optional result from guess_object_type()
    
    Returns:
        dict formatted for pick and place export
    """
    # Classify by size if not provided
    size_category, size_range = classify_object_by_size(detected_object.area)
    
    # Use guess result if provided, otherwise mark as needs review
    if guess_result:
        shape_type = guess_result["shape_type"]
        likely_category = guess_result["likely_types"][0]  # Best guess
        confidence = guess_result["confidence"]
    else:
        shape_type = "unknown"
        likely_category = "unknown"
        confidence = 0.5
    
    # Calculate rotation from contour (if available)
    rotation = 0.0  # TODO: Implement rotation calculation from contour
    
    record = {
        "object_id": detected_object.object_id,
        "x_mm": cnc_position.x + detected_object.x,  # Convert pixel to mm
        "y_mm": cnc_position.y + detected_object.y,
        "z_mm": cnc_position.z,
        "area_px": detected_object.area,
        "estimated_size": size_range,
        "shape_type": shape_type,
        "likely_category": likely_category,
        "confidence": confidence,
        "needs_review": confidence < PICK_AND_PLACE["min_confidence_threshold"],
        "rotation_degrees": rotation,
        "capture_image_id": getattr(detected_object, "image_id", "unknown"),
    }
    
    return record


def validate_configuration():
    """Validate configuration consistency."""
    errors = []
    
    # Check workspace dimensions are positive
    if WORKSPACE["width_mm"] <= 0 or WORKSPACE["depth_mm"] <= 0:
        errors.append("Workspace dimensions must be positive")
    
    # Check CNC limits match workspace
    if CNC["x_max_mm"] != WORKSPACE["width_mm"]:
        errors.append("CNC X limit doesn't match workspace width")
    
    if CNC["y_max_mm"] != WORKSPACE["depth_mm"]:
        errors.append("CNC Y limit doesn't match workspace depth")
    
    # Check gimbal is properly configured if enabled
    if GIMBAL["enabled"]:
        if GIMBAL["pan_gpio_pin"] == GIMBAL["tilt_gpio_pin"]:
            errors.append("Gimbal pan and tilt pins cannot be the same")
    
    return errors


# Validate on import
_validation_errors = validate_configuration()
if _validation_errors:
    import warnings
    for error in _validation_errors:
        warnings.warn(f"Configuration error: {error}")


# ============================================================================
# EXPORT SUMMARY
# ============================================================================

def print_configuration_summary():
    """Print a human-readable summary of the configuration."""
    print("=" * 70)
    print("CNCSorter Configuration Summary")
    print("=" * 70)
    print(f"\n📊 Hardware:")
    print(f"  Platform: {HARDWARE['platform'].replace('_', ' ').title()}")
    print(f"  Local Storage: {HARDWARE['local_storage_gb']}GB SSD")
    print(f"  Network Storage: {HARDWARE['network_storage_tb']}TB @ {HARDWARE['network_speed_mbps']}Mbps")
    
    print(f"\n📏 Workspace: {WORKSPACE['width_mm']}mm × {WORKSPACE['depth_mm']}mm × {WORKSPACE['height_mm']}mm")
    print(f"  Area: {WORKSPACE['area_mm2'] / 1000:.1f} cm²")
    print(f"  Volume: {WORKSPACE['volume_mm3'] / 1000000:.1f} L")
    
    print(f"\n📷 Vision System:")
    print(f"  Resolution: {VISION['resolution'][0]}×{VISION['resolution'][1]}")
    print(f"  FPS Target: {VISION['fps_target']}")
    print(f"  Max Objects/Frame: {VISION['max_objects_per_frame']}")
    
    print(f"\n🗺️  Bed Mapping:")
    print(f"  Capture Grid: {BED_MAPPING['capture_grid_x']}×{BED_MAPPING['capture_grid_y']} = {BED_MAPPING['total_captures']} captures")
    print(f"  Storage: {'Network (8TB)' if BED_MAPPING['use_network_storage'] else 'Local (128GB)'}")
    
    print(f"\n🎮 Gimbal: {'Enabled' if GIMBAL['enabled'] else 'Disabled'}")
    if GIMBAL['enabled']:
        print(f"  Type: {GIMBAL['type'].replace('_', ' ').title()}")
        print(f"  Pan Range: {GIMBAL['pan_range_degrees'][0]}° to {GIMBAL['pan_range_degrees'][1]}°")
    
    print(f"\n🔧 CNC Controller:")
    print(f"  Mode: {CNC['mode'].upper()}")
    print(f"  Workspace: X:{CNC['x_max_mm']}mm Y:{CNC['y_max_mm']}mm Z:{CNC['z_max_mm']}mm")
    
    print(f"\n⚡ Performance:")
    print(f"  Max System Capacity: {get_max_objects_capacity():,} objects")
    print(f"  Multithreading: {PERFORMANCE['worker_threads']} cores")
    
    print("=" * 70)


if __name__ == "__main__":
    print_configuration_summary()

# ============================================================================
# SORTING STRATEGY & TOOLING CONFIGURATION
# ============================================================================

SORTING = {
    # Available tools and which item types they handle
    "tools": {
        "magnet_tool": {
            "id": "magnet_head_v1",
            "offset_mm": (0, 0, 0),  # Offset from spindle center
            "handling_types": ["nut", "bolt", "washer", "spring_washer", "hex_bolt", "M2", "M3", "M4", "M5", "M6", "M8", "M10", "M12"],
            "tool_change_location": {"x": 10, "y": 10, "z": 50},
            "activation_command": "M8",
            "deactivation_command": "M9",
        },
        "suction_tool": {
            "id": "suction_cup_5mm",
            "offset_mm": (20, 0, 0),
            "handling_types": ["plastic", "nylon", "pcb", "unknown"],
            "tool_change_location": {"x": 10, "y": 50, "z": 50},
            "activation_command": "M7",
            "deactivation_command": "M9",
        }
    },

    # Destination bins
    # Location is the center of the bin/drop-off point
    "bins": [
        {
            "id": "bin_nuts_m2_m6",
            "location": {"x": 750, "y": 50, "z": 10},
            "accepts": ["nut"],
            "size_range": ["tiny", "small"]
        },
        {
            "id": "bin_nuts_m8_plus",
            "location": {"x": 750, "y": 150, "z": 10},
            "accepts": ["nut"],
            "size_range": ["medium", "large"]
        },
        {
            "id": "bin_bolts",
            "location": {"x": 750, "y": 250, "z": 10},
            "accepts": ["bolt", "hex_bolt"],
            "size_range": ["all"]
        },
        {
            "id": "bin_washers",
            "location": {"x": 750, "y": 350, "z": 10},
            "accepts": ["washer", "spring_washer"],
            "size_range": ["all"]
        },
        {
            "id": "bin_rejects",
            "location": {"x": 700, "y": 350, "z": 10},
            "accepts": ["unknown", "debris"],
            "size_range": ["all"]
        }
    ],

    # Default behavior
    "default_tool": "magnet_tool",
    "default_bin": "bin_rejects",

    # Optimization
    "path_optimization": "nearest_neighbor",  # tsp_approx, nearest_neighbor
}
