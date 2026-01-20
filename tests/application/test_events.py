"""Tests for EventBus."""
from dataclasses import dataclass
from datetime import datetime
from cncsorter.application.events import EventBus, DomainEvent


@dataclass
class TestEvent(DomainEvent):
    payload: str = None
    timestamp: datetime = None


class TestEventBus:
    def test_subscribe_publish(self):
        bus = EventBus()
        received = []

        def handler(event: TestEvent):
            received.append(event.payload)

        bus.subscribe(TestEvent, handler)

        bus.publish(TestEvent(payload="hello"))
        bus.publish(TestEvent(payload="world"))

        assert len(received) == 2
        assert received[0] == "hello"
        assert received[1] == "world"

    def test_unsubscribe(self):
        bus = EventBus()
        received = []

        def handler(event: TestEvent):
            received.append(event.payload)

        bus.subscribe(TestEvent, handler)
        bus.publish(TestEvent(payload="one"))

        bus.unsubscribe(TestEvent, handler)
        bus.publish(TestEvent(payload="two"))

        assert len(received) == 1
        assert received[0] == "one"

    def test_handler_exception_isolation(self):
        """Ensure one handler failing doesn't stop others."""
        bus = EventBus()
        received = []

        def failing_handler(event):
            raise ValueError("Boom")

        def working_handler(event):
            received.append(event.payload)

        bus.subscribe(TestEvent, failing_handler)
        bus.subscribe(TestEvent, working_handler)

        # Should not raise exception
        bus.publish(TestEvent(payload="test"))

        assert len(received) == 1
        assert received[0] == "test"
