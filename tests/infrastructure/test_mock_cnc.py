"""Tests for MockCNCController."""
import pytest
import time
from unittest.mock import MagicMock

from cncsorter.infrastructure.mock_cnc_controller import MockCNCController
from cncsorter.domain.entities import CNCCoordinate
from cncsorter.application.events import EventBus, CNCPositionUpdated


class TestMockCNCController:
    def test_connection(self):
        # Use a non-standard port to avoid conflicts
        cnc = MockCNCController(port=5001)
        assert not cnc.is_connected()

        # We won't actually start the server to avoid threading issues in tests
        # or port binding issues. We mock the server thread start.
        cnc.app.run = MagicMock()

        cnc.connect()
        assert cnc.is_connected()

        cnc.disconnect()
        assert not cnc.is_connected()

    def test_initial_position(self):
        cnc = MockCNCController(port=5002)
        cnc.connect()
        pos = cnc.get_position()
        assert pos.x == 0.0
        assert pos.y == 0.0
        assert pos.z == 0.0
        cnc.disconnect()

    def test_movement_validation(self):
        validator = MagicMock()
        cnc = MockCNCController(port=5003, motion_validator=validator)
        cnc.connect()

        target = CNCCoordinate(x=100, y=100, z=10)
        cnc.move_to(target)

        validator.validate_coordinate.assert_called_with(target)
        cnc.disconnect()

    def test_movement_simulation(self):
        # Use high speed for fast test
        cnc = MockCNCController(port=5004, speed=1000.0)
        cnc.connect()

        target = CNCCoordinate(x=10, y=0, z=0)
        cnc.move_to(target)

        # Should be moving shortly after call
        # Note: Thread timing makes this tricky, but for unit test we can
        # wait a tiny bit or just check final state after delay
        time.sleep(0.1)

        # Eventually should be at target
        time.sleep(0.1)
        pos = cnc.get_position()
        assert pos.x == 10.0

        cnc.disconnect()
