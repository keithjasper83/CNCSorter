import unittest
import os
from uuid import uuid4
from datetime import datetime

from cncsorter.infrastructure.persistence import SQLiteDetectionRepository
from cncsorter.domain.entities import DetectedObject, Point2D
from cncsorter.domain.interfaces import WorkStatus, RepositoryError

class TestSQLitePersistenceStatus(unittest.TestCase):
    def setUp(self):
        self.db_path = f"test_db_{uuid4()}.sqlite"
        self.db_url = f"sqlite:///{self.db_path}"
        self.repo = SQLiteDetectionRepository(self.db_url)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def create_dummy_object(self, object_id):
        return DetectedObject(
            object_id=object_id,
            contour_points=[(0, 0), (1, 1)],
            bounding_box=(0, 0, 10, 10),
            area=100.0,
            center=Point2D(x=5.0, y=5.0),
            classification="bolt",
            confidence=0.9
        )

    def test_list_by_status(self):
        # Create objects
        obj_pending = self.create_dummy_object(1)
        obj_failed = self.create_dummy_object(2)
        obj_completed = self.create_dummy_object(3)

        # Save them (defaults to PENDING)
        self.repo.save(obj_pending)
        self.repo.save(obj_failed)
        self.repo.save(obj_completed)

        # Update statuses
        self.repo.update_status(obj_failed.uuid, WorkStatus.FAILED)
        self.repo.update_status(obj_completed.uuid, WorkStatus.COMPLETED)
        # obj_pending remains PENDING

        # Verify we can list by status
        # Note: list_by_status is not yet implemented, so this test expects the method to exist
        try:
            failed_objects = self.repo.list_by_status(WorkStatus.FAILED)
            self.assertEqual(len(failed_objects), 1)
            self.assertEqual(failed_objects[0].object_id, 2)

            completed_objects = self.repo.list_by_status(WorkStatus.COMPLETED)
            self.assertEqual(len(completed_objects), 1)
            self.assertEqual(completed_objects[0].object_id, 3)

            pending_objects = self.repo.list_by_status(WorkStatus.PENDING)
            # There might be old objects if I didn't clean up, but I use a unique DB per test
            self.assertEqual(len(pending_objects), 1)
            self.assertEqual(pending_objects[0].object_id, 1)

        except AttributeError:
            self.fail("list_by_status method not implemented yet")

if __name__ == '__main__':
    unittest.main()
