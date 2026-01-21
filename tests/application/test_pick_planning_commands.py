import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
import threading

# Import project modules
from cncsorter.application.pick_planning import PickPlanningService
from cncsorter.infrastructure.mock_cnc_controller import MockCNCController
from cncsorter.domain.entities import DetectedObject, CNCCoordinate
from cncsorter.domain.interfaces import WorkStatus, DetectionRepository
from cncsorter.config import SORTING

@pytest.mark.asyncio
async def test_tool_activation_deactivation():
    # Setup Mock Controller
    # Use a high port to avoid conflict, or patch connect
    cnc_controller = MockCNCController(port=5999, speed=1000.0)

    # Patch connect to avoid starting web server
    with patch.object(cnc_controller, 'connect', return_value=True) as mock_connect:
        cnc_controller._connected = True

        # Spy on send_command
        # We need to wrap the real method or just replace it since the real method just returns True and logs
        cnc_controller.send_command = MagicMock(return_value=True)

        # Also patch get_position to return valid coordinate immediately
        cnc_controller.get_position = MagicMock(return_value=CNCCoordinate(0,0,0))

        # Patch is_moving to return False so _move_and_wait doesn't wait forever
        # Actually MockCNCController doesn't have is_moving property that returns bool, it has is_moving attribute
        cnc_controller.is_moving = False

        # Setup Mock Repository
        repository = MagicMock(spec=DetectionRepository)

        # Create a test object
        obj_uuid = uuid4()
        # Create a partial mock for detected object if constructor is complex
        # But data class is simple
        test_obj = DetectedObject(
            object_id=1,
            contour_points=[],
            bounding_box=(0,0,10,10),
            area=100,
            center=MagicMock(x=10, y=10),
            cnc_coordinate=CNCCoordinate(x=100, y=100, z=0),
            uuid=obj_uuid
        )

        # Configure repository to return this object
        repository.list_pending.return_value = [test_obj]

        # Setup Service
        service = PickPlanningService(repository, cnc_controller)

        # Make move_and_wait faster by mocking move_to and avoiding sleep
        # However, _move_and_wait calls asyncio.sleep(0.1).
        # We can patch asyncio.sleep to be instant?
        # Or just let it run, 100mm move at 1000mm/s is 0.1s.

        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
             # Execute
            await service.execute_pick_and_place()

        # Verify M8 (activation) and M9 (deactivation) were sent
        calls = cnc_controller.send_command.call_args_list
        print(f"Calls: {calls}")

        # Check if M8 and M9 are in the calls
        assert any(call.args[0] == 'M8' for call in calls), "M8 (Activation) not sent"
        assert any(call.args[0] == 'M9' for call in calls), "M9 (Deactivation) not sent"

        # Verify order: M8 before M9
        m8_idx = -1
        m9_idx = -1
        for i, call in enumerate(calls):
            if call.args[0] == 'M8':
                m8_idx = i
            elif call.args[0] == 'M9':
                m9_idx = i

        assert m8_idx != -1
        assert m9_idx != -1
        assert m8_idx < m9_idx, "M8 should be sent before M9"

        # Verify status update
        repository.update_status.assert_called_with(obj_uuid, WorkStatus.COMPLETED)
