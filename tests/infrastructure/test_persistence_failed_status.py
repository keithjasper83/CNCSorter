import pytest
from cncsorter.domain.entities import DetectedObject, Point2D
from cncsorter.domain.interfaces import WorkStatus
from cncsorter.infrastructure.persistence import SQLiteDetectionRepository

def test_list_failed():
    # Setup in-memory repository
    repo = SQLiteDetectionRepository("sqlite:///:memory:")

    # Create objects
    obj_pending = DetectedObject(
        object_id=1,
        contour_points=[],
        bounding_box=(0,0,10,10),
        area=100.0,
        center=Point2D(10,10)
    )
    obj_failed = DetectedObject(
        object_id=2,
        contour_points=[],
        bounding_box=(20,20,10,10),
        area=100.0,
        center=Point2D(20,20)
    )
    obj_completed = DetectedObject(
        object_id=3,
        contour_points=[],
        bounding_box=(30,30,10,10),
        area=100.0,
        center=Point2D(30,30)
    )

    # Save objects
    repo.save(obj_pending)
    repo.save(obj_failed)
    repo.save(obj_completed)

    # Update statuses
    # Default is PENDING, so obj_pending is fine
    repo.update_status(obj_failed.uuid, WorkStatus.FAILED)
    repo.update_status(obj_completed.uuid, WorkStatus.COMPLETED)

    # Verify counts using existing methods
    assert len(repo.list_pending()) == 1

    # Verify list_failed
    # This assumes list_failed exists on the repo object
    if hasattr(repo, 'list_failed'):
        failed_objects = repo.list_failed()
        assert len(failed_objects) == 1
        assert failed_objects[0].uuid == obj_failed.uuid
    else:
        pytest.fail("list_failed method not implemented in repository")
