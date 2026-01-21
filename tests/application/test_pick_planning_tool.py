import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
import asyncio

# Assuming the imports in pick_planning.py are fixed or we will fix them
from cncsorter.application.pick_planning import PickPlanningService
from cncsorter.domain.entities import CNCCoordinate, PickTask, DetectedObject, Point2D
from cncsorter.domain.interfaces import DetectionRepository, WorkStatus
from cncsorter.infrastructure.cnc_controller import CNCController
from cncsorter.config import SORTING

class TestPickPlanningTool:
    @pytest.fixture
    def mock_repo(self):
        return MagicMock(spec=DetectionRepository)

    @pytest.fixture
    def mock_controller(self):
        controller = MagicMock(spec=CNCController)
        controller.is_connected.return_value = True
        controller.connect.return_value = True
        controller.get_position.return_value = CNCCoordinate(0, 0, 0)
        controller.move_to.return_value = True
        controller.send_command.return_value = True
        # PickPlanningService checks is_moving if it exists
        controller.is_moving = False
        return controller

    @pytest.mark.asyncio
    async def test_execute_single_pick_activates_tool(self, mock_repo, mock_controller):
        # Setup
        service = PickPlanningService(mock_repo, mock_controller)
        service.is_running = True

        object_id = uuid4()
        task = PickTask(
            task_id="task-1",
            object_id=object_id,
            target_position=CNCCoordinate(100, 100, 0)
        )

        # Mock repository to return an object
        mock_obj = DetectedObject(
            object_id=1,
            contour_points=[],
            bounding_box=(0,0,10,10),
            area=100,
            center=Point2D(100, 100),
            uuid=object_id,
            classification="nut"
        )
        mock_repo.get_by_id.return_value = mock_obj

        # Act
        result = await service._execute_single_pick(task)

        # Assert
        assert result is True

        # Verify M8 (Magnet On) and M9 (Off) are sent
        # Note: This relies on default_tool being magnet_tool in config

        # We expect send_command to be called with M8 then later M9
        mock_controller.send_command.assert_any_call("M8")
        mock_controller.send_command.assert_any_call("M9")

        # Verify call count
        assert mock_controller.send_command.call_count >= 2
