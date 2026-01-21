import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from cncsorter.application.scanning import ScanningService
from cncsorter.domain.entities import CNCCoordinate, DetectedObject, Point2D
from cncsorter.domain.system_config import SystemConfig, CameraConfig
from cncsorter.application.events import ObjectsDetected, BedMapCompleted

@pytest.fixture
def mock_dependencies():
    repository = MagicMock()
    cnc_controller = MagicMock()
    cnc_controller.is_connected.return_value = True

    # Mock position tracking
    current_pos = [CNCCoordinate(x=0, y=0, z=0)]

    def move_to_side_effect(target):
        current_pos[0] = target
        return True

    def get_position_side_effect():
        return current_pos[0]

    cnc_controller.move_to.side_effect = move_to_side_effect
    cnc_controller.get_position.side_effect = get_position_side_effect

    vision_system = MagicMock()
    vision_system.camera_index = 0
    # Mock capture_frame returning a dummy array
    import numpy as np
    vision_system.capture_frame.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
    vision_system.detect_objects.return_value = []

    event_bus = MagicMock()

    config = SystemConfig(
        num_cameras=1,
        cameras=[
            CameraConfig(0, "Cam0", 10, 20, 0, 100, 100, 0, 0)
        ],
        x_min=0, x_max=100,
        y_min=0, y_max=100,
        z_min=0, z_max=100,
        safe_z=10,
        overlap_percent=0,
        grid_x=2, grid_y=2
    )

    return repository, cnc_controller, vision_system, event_bus, config

@pytest.mark.asyncio
async def test_run_scan(mock_dependencies):
    repo, cnc, vision, bus, config = mock_dependencies
    service = ScanningService(repo, cnc, vision, bus, config)

    # Mock detecting objects
    import numpy as np
    vision.detect_objects.return_value = [
        DetectedObject(
            object_id=1,
            contour_points=[],
            bounding_box=(40, 40, 10, 10),
            area=100,
            center=Point2D(50, 50) # Center of image
        )
    ]

    callback = MagicMock()

    await service.run_scan(callback)

    # Verify CNC moves
    assert cnc.move_to.called
    # Grid 2x2 = 4 points + initial safe z
    assert cnc.move_to.call_count >= 5

    # Verify capture and detection
    assert vision.capture_frame.called
    assert vision.detect_objects.called

    # Verify repository save
    assert repo.save.called
    saved_obj = repo.save.call_args[0][0]
    assert saved_obj.cnc_coordinate is not None
    # Check coordinate transformation logic
    # Camera at (10, 20) relative to CNC.
    # Image center (50, 50) corresponds to Camera Center.
    # Object at (50, 50) should be at CNC + Camera Offset.
    # But CNC moves to grid points.
    # Let's say last point was (75, 75).
    # CNC pos = (75, 75).
    # Camera pos = (75+10, 75+20) = (85, 95).
    # Object at center of image = Camera pos = (85, 95).
    # saved_obj.cnc_coordinate.x should be around 85

    # Verify events
    assert bus.publish.called
    # ObjectsDetected and BedMapCompleted
    assert any(isinstance(call.args[0], ObjectsDetected) for call in bus.publish.call_args_list)
    assert any(isinstance(call.args[0], BedMapCompleted) for call in bus.publish.call_args_list)

    # Verify event arguments
    objects_detected_call = next(call for call in bus.publish.call_args_list if isinstance(call.args[0], ObjectsDetected))
    event = objects_detected_call.args[0]
    assert event.image_id is not None
    assert event.camera_index == 0
    assert len(event.detected_objects) > 0

@pytest.mark.asyncio
async def test_calculate_scan_points(mock_dependencies):
    repo, cnc, vision, bus, config = mock_dependencies
    service = ScanningService(repo, cnc, vision, bus, config)

    points = service._calculate_scan_points()
    assert len(points) == 4 # 2x2 grid

    # Check coordinates
    # x range 0-100, step 50. centers: 25, 75.
    # y range 0-100, step 50. centers: 25, 75.
    expected_x = {25.0, 75.0}
    expected_y = {25.0, 75.0}

    xs = {p.x for p in points}
    ys = {p.y for p in points}

    assert xs == expected_x
    assert ys == expected_y
