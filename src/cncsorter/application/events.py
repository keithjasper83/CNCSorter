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
    pass


@dataclass
class ObjectsDetected(DomainEvent):
    """Event fired when objects are detected by vision system."""
    
    detected_objects: List[DetectedObject]
    image_id: str
    camera_index: int
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class BedMapCompleted(DomainEvent):
    """Event fired when bed mapping process completes."""
    
    bed_map_id: str
    total_objects: int
    image_count: int
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class CNCPositionUpdated(DomainEvent):
    """Event fired when CNC machine position changes."""
    
    position: CNCCoordinate
    previous_position: CNCCoordinate = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class PickTaskCreated(DomainEvent):
    """Event fired when a pick task is generated for CNC."""
    
    task_id: str
    object_id: UUID
    target_position: CNCCoordinate
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class BoundaryViolationDetected(DomainEvent):
    """Event fired when a boundary violation is detected."""
    
    attempted_position: CNCCoordinate
    boundary_type: str
    message: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


# Event Bus

EventHandler = Callable[[DomainEvent], None]


class EventBus:
    """Lightweight synchronous event bus for publish-subscribe pattern."""

    def __init__(self):
        """Initialize empty event bus."""
        self._subscribers: Dict[Type[DomainEvent], List[EventHandler]] = {}

    def subscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
        """Subscribe a handler to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
        """Unsubscribe a handler from an event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
            except ValueError:
                pass  # Handler wasn't subscribed

    def publish(self, event: DomainEvent) -> None:
        """Publish an event to all subscribed handlers."""
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
        """Get number of subscribers for an event type."""
        return len(self._subscribers.get(event_type, []))
