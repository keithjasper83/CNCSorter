"""Domain interfaces for CNCSorter.

This module defines abstract interfaces that infrastructure layer must implement.
Following DDD principles, domain layer defines contracts without implementation details.
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional
from uuid import UUID

from cncsorter.domain.entities import DetectedObject


class WorkStatus(Enum):
    """Status of detected object processing workflow."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DetectionRepository(ABC):
    """Abstract repository for persisting detected objects.

    This interface defines the contract for object persistence without
    specifying implementation details (e.g., SQLite, PostgreSQL, etc.).
    Infrastructure layer provides concrete implementations.
    """

    @abstractmethod
    def save(self, detected_object: DetectedObject) -> UUID:
        """Save a detected object to persistent storage.

        Args:
            detected_object: The detected object entity to persist.

        Returns:
            UUID of the saved object.

        Raises:
            RepositoryError: If save operation fails.
        """
        pass

    @abstractmethod
    def list_pending(self) -> List[DetectedObject]:
        """Retrieve all objects with PENDING status.

        Returns:
            List of detected objects awaiting processing.

        Raises:
            RepositoryError: If retrieval fails.
        """
        pass

    @abstractmethod
    def update_status(self, object_id: UUID, status: WorkStatus) -> None:
        """Update the processing status of a detected object.

        Args:
            object_id: UUID of the object to update.
            status: New status to assign.

        Raises:
            RepositoryError: If update fails or object not found.
        """
        pass

    @abstractmethod
    def get_by_id(self, object_id: UUID) -> Optional[DetectedObject]:
        """Retrieve a detected object by its UUID.

        Args:
            object_id: UUID of the object to retrieve.

        Returns:
            DetectedObject if found, None otherwise.

        Raises:
            RepositoryError: If retrieval fails.
        """
        pass

    @abstractmethod
    def list_all(self, limit: Optional[int] = None) -> List[DetectedObject]:
        """Retrieve all detected objects, optionally limited.

        Args:
            limit: Maximum number of objects to return. None for all.

        Returns:
            List of all detected objects.

        Raises:
            RepositoryError: If retrieval fails.
        """
        pass


class RepositoryError(Exception):
    """Base exception for repository operations."""

    pass
