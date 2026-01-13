import pytest
from unittest.mock import patch
import json

# Add src to python path if not already
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from desktop_interface import DesktopInterface

class TestDesktopInterface:
    """Tests for the Desktop Operator Interface."""

    @pytest.fixture
    def mock_ui(self):
        """Mock NiceGUI ui module."""
        with patch('desktop_interface.ui') as mock_ui:
            yield mock_ui

    @pytest.fixture
    def mock_event_bus(self):
        """Mock EventBus."""
        with patch('desktop_interface.EventBus') as mock_bus:
            yield mock_bus

    @pytest.fixture
    def mock_repo(self):
        """Mock Repository."""
        with patch('desktop_interface.SQLiteDetectionRepository') as mock_repo:
            yield mock_repo

    def test_initialization_default_config(self, mock_ui, mock_event_bus, mock_repo):
        """Test initialization falls back to default config if file missing."""
        with patch('pathlib.Path.exists', return_value=False):
            interface = DesktopInterface()

            assert interface.system_config is not None
            assert interface.system_config.num_cameras == 1
            assert len(interface.system_config.cameras) == 1
            assert interface.system_config.cameras[0].name == "Camera 0"

    def test_load_configuration_success(self, mock_ui, mock_event_bus, mock_repo, tmp_path):
        """Test loading configuration from JSON file."""
        # Create a temp config file
        config_data = {
            "cameras": [
                {"camera_id": 0, "camera_name": "Test Cam 1"},
                {"camera_id": 1, "camera_name": "Test Cam 2"}
            ]
        }
        config_file = tmp_path / "test_config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('desktop_interface.Path', return_value=config_file):
            interface = DesktopInterface()

            assert interface.system_config.num_cameras == 2
            assert interface.system_config.cameras[0].name == "Test Cam 1"
            assert interface.system_config.cameras[1].name == "Test Cam 2"

    def test_log_message(self, mock_ui, mock_event_bus, mock_repo):
        """Test logging mechanism."""
        with patch('pathlib.Path.exists', return_value=False):
            interface = DesktopInterface()

            interface.log_message("Test info message")
            assert len(interface.logs) == 1
            assert "Test info message" in interface.logs[0]

            interface.log_message("Test error message", type='error')
            assert len(interface.logs) == 2
            assert "Test error message" in interface.logs[0]

    def test_event_subscription(self, mock_ui, mock_event_bus, mock_repo):
        """Test that event handlers are subscribed."""
        with patch('pathlib.Path.exists', return_value=False):
            DesktopInterface()

            # Verify subscribe was called
            assert mock_event_bus.return_value.subscribe.call_count >= 2
