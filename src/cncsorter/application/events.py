"""Event-driven orchestration for CNCSorter.

This module implements a lightweight synchronous EventBus for decoupling
system components. Following DDD principles, domain events represent
significant state changes that other parts of the system may care about.
"""
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Type
from datetime import datetime
from uuid import UUID

from cncsorter.domain.entities import DetectedObject, CNCCoordinate


# Domain Events

@dataclass
class DomainEvent:
    """Base class for all domain events."""
    
    timestamp: datetime
    
    def __post_init__(self):
        if not hasattr(self, 'timestamp') or self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ObjectsDetected(DomainEvent):
    """Event fired when objects are detected by vision system.

    Args:
        detected_objects: List of objects detected in current frame/capture.
        image_id: Identifier of the source image.
        camera_index: Index of camera that detected the objects.
        timestamp: When detection occurred.
    """
    
    detected_objects: List[DetectedObject]
    image_id: str
    camera_index: int
    timestamp: datetime = None


@dataclass
class BedMapCompleted(DomainEvent):
    """Event fired when bed mapping process completes.

    Args:
        bed_map_id: Unique identifier for this bed map.
        total_objects: Total number of objects detected.
        image_count: Number of images stitched.
        timestamp: When mapping completed.
    """
    
    bed_map_id: str
    total_objects: int
    image_count: int
    timestamp: datetime = None


@dataclass
class CNCPositionUpdated(DomainEvent):
    """Event fired when CNC machine position changes.

    Args:
        position: New CNC position.
        previous_position: Previous position (optional).
        timestamp: When position was updated.
    """
    
    position: CNCCoordinate
    previous_position: CNCCoordinate = None
    timestamp: datetime = None


@dataclass
class PickTaskCreated(DomainEvent):
    """Event fired when a pick task is generated for CNC.

    Args:
        task_id: Unique identifier for the pick task.
        object_id: UUID of object to be picked.
        target_position: CNC coordinates for pick operation.
        timestamp: When task was created.
    """
    
    task_id: str
    object_id: UUID
    target_position: CNCCoordinate
    timestamp: datetime = None


@dataclass
class BoundaryViolationDetected(DomainEvent):
    """Event fired when a boundary violation is detected.

    Args:
        attempted_position: Position that would violate boundaries.
        boundary_type: Type of boundary violated (workspace, keep-out, etc.).
        message: Human-readable description of violation.
        timestamp: When violation was detected.
    """
    
    attempted_position: CNCCoordinate
    boundary_type: str
    message: str
    timestamp: datetime = None


# Event Bus

EventHandler = Callable[[DomainEvent], None]


class EventBus:
    """Lightweight synchronous event bus for publish-subscribe pattern.

    This implementation is intentionally simple and synchronous to avoid
    complexity. Handlers are called in subscription order on the same thread.
    For async behavior, handlers can delegate to background workers.
    """

    def __init__(self):
        """Initialize empty event bus."""
        self._subscribers: Dict[Type[DomainEvent], List[EventHandler]] = {}

    def subscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
        """Subscribe a handler to an event type.

        Args:
            event_type: Class of event to subscribe to.
            handler: Callable that receives events of this type.

        Example:
            def on_objects_detected(event: ObjectsDetected):
                print(f"Detected {len(event.detected_objects)} objects")

            bus = EventBus()
            bus.subscribe(ObjectsDetected, on_objects_detected)
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
        """Unsubscribe a handler from an event type.

        Args:
            event_type: Class of event to unsubscribe from.
            handler: Handler to remove.
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
            except ValueError:
                pass  # Handler wasn't subscribed

    def publish(self, event: DomainEvent) -> None:
        """Publish an event to all subscribed handlers.

        Handlers are called synchronously in subscription order.
        If a handler raises an exception, it is logged but does not
        prevent other handlers from running.

        Args:
            event: Event instance to publish.

        Example:
            bus.publish(ObjectsDetected(
                detected_objects=[obj1, obj2],
                image_id="img_001",
                camera_index=0
            ))
        """
        event_type = type(event)
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    # Log error but don't stop other handlers
                    print(f"[EventBus] Handler error for {event_type.__name__}: {e}")

    def clear_all(self) -> None:
        """Remove all subscriptions. Useful for testing."""
        self._subscribers.clear()

    def subscriber_count(self, event_type: Type[DomainEvent]) -> int:
        """Get number of subscribers for an event type.

        Args:
            event_type: Class of event to count subscribers for.

        Returns:
            Number of subscribers.
        """
        return len(self._subscribers.get(event_type, []))
