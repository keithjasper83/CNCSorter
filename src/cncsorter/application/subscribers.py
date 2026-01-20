"""Event subscribers for CNCSorter application.

This module contains concrete event handlers that react to domain events.
Subscribers implement the application's orchestration logic while maintaining
loose coupling through the event bus.
"""
import logging
from typing import Optional, Any

from cncsorter.application.events import (
    ObjectsDetected,
    BedMapCompleted,
    CNCPositionUpdated,
    PickTaskCreated,
    BoundaryViolationDetected,
)
from cncsorter.domain.interfaces import DetectionRepository, RepositoryError


class PersistenceSubscriber:
    """Subscriber that persists detected objects to storage.

    This subscriber listens to ObjectsDetected events and saves all detected
    objects using the DetectionRepository. This decouples the vision system
    from storage concerns.
    """

    def __init__(self, repository: DetectionRepository):
        """Initialize subscriber with repository.

        Args:
            repository: Repository for persisting detected objects.
        """
        self.repository = repository
        self.logger = logging.getLogger(__name__)

    def on_objects_detected(self, event: ObjectsDetected) -> None:
        """Handle ObjectsDetected event by persisting objects.

        Args:
            event: Event containing detected objects.
        """
        for obj in event.detected_objects:
            try:
                # Enrich object with event metadata
                obj.image_id = event.image_id
                obj.source_camera = event.camera_index

                # Save to repository
                uuid = self.repository.save(obj)
                self.logger.info(f"Saved object {uuid} (camera {event.camera_index})")
            except RepositoryError as e:
                self.logger.error(f"Failed to save object: {e}")


class GUISubscriber:
    """Subscriber that updates GUI with detection events.

    This subscriber listens to various events and updates the live display.
    In current implementation, it prints status messages. In future, this
    will update actual GUI components.
    """

    def __init__(self, display: Optional[Any] = None):
        """Initialize subscriber with optional display component.

        Args:
            display: Optional display component to update (LiveStatusDisplay).
        """
        self.display = display
        self.logger = logging.getLogger(__name__)

    def on_objects_detected(self, event: ObjectsDetected) -> None:
        """Handle ObjectsDetected event by updating display.

        Args:
            event: Event containing detected objects.
        """
        count = len(event.detected_objects)
        self.logger.debug(f"GUI updated: {count} objects detected")
        # Future: self.display.update_object_count(count)

    def on_bed_map_completed(self, event: BedMapCompleted) -> None:
        """Handle BedMapCompleted event by updating display.

        Args:
            event: Event containing bed map completion info.
        """
        self.logger.info(f"Bed map completed: {event.total_objects} objects, {event.image_count} images")
        # Future: self.display.show_completion_status(event)

    def on_boundary_violation(self, event: BoundaryViolationDetected) -> None:
        """Handle BoundaryViolationDetected event by showing warning.

        Args:
            event: Event containing boundary violation details.
        """
        self.logger.warning(f"BOUNDARY VIOLATION: {event.message}")
        # Future: self.display.show_error_message(event.message)


class LoggingSubscriber:
    """Subscriber that logs all events for audit trail.

    This subscriber logs all domain events to provide a complete audit trail.
    Useful for debugging, replay, and compliance.
    """

    def __init__(self, log_level: str = "INFO"):
        """Initialize subscriber with log level.

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
        """
        self.log_level = log_level
        self.logger = logging.getLogger("audit")

    def on_objects_detected(self, event: ObjectsDetected) -> None:
        """Log ObjectsDetected event."""
        self.logger.info(f"ObjectsDetected: {len(event.detected_objects)} objects, "
                         f"camera={event.camera_index}, image={event.image_id}")

    def on_bed_map_completed(self, event: BedMapCompleted) -> None:
        """Log BedMapCompleted event."""
        self.logger.info(f"BedMapCompleted: map_id={event.bed_map_id}, "
                         f"objects={event.total_objects}, images={event.image_count}")

    def on_cnc_position_updated(self, event: CNCPositionUpdated) -> None:
        """Log CNCPositionUpdated event."""
        self.logger.info(f"CNCPositionUpdated: position=({event.position.x:.2f}, "
                         f"{event.position.y:.2f}, {event.position.z:.2f})")

    def on_pick_task_created(self, event: PickTaskCreated) -> None:
        """Log PickTaskCreated event."""
        self.logger.info(f"PickTaskCreated: task={event.task_id}, "
                         f"object={event.object_id}, position=({event.target_position.x:.2f}, "
                         f"{event.target_position.y:.2f}, {event.target_position.z:.2f})")

    def on_boundary_violation(self, event: BoundaryViolationDetected) -> None:
        """Log BoundaryViolationDetected event."""
        self.logger.warning(f"BoundaryViolation: type={event.boundary_type}, "
                            f"attempted=({event.attempted_position.x:.2f}, {event.attempted_position.y:.2f}, "
                            f"{event.attempted_position.z:.2f}), message={event.message}")
