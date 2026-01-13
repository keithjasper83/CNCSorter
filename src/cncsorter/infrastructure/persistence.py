"""SQLite persistence implementation for detected objects.

This module implements the DetectionRepository interface using SQLAlchemy and SQLite.
Following DDD principles, this infrastructure layer depends only on domain interfaces.
No SQLAlchemy types leak outside this module.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
import json

from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, Text
from sqlalchemy.orm import declarative_base, Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from cncsorter.domain.interfaces import DetectionRepository, WorkStatus, RepositoryError
from cncsorter.domain.entities import DetectedObject, Point2D, CNCCoordinate


Base = declarative_base()


class DetectedObjectModel(Base):
    """SQLAlchemy model for detected_objects table.

    This is an internal infrastructure concern and should not leak to other layers.
    """

    __tablename__ = "detected_objects"

    # Primary key
    uuid = Column(String(36), primary_key=True)

    # Core detection data
    object_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)

    # Spatial data
    x = Column(Float, nullable=True)
    y = Column(Float, nullable=True)
    z = Column(Float, nullable=True)
    center_x = Column(Float, nullable=False)
    center_y = Column(Float, nullable=False)
    area = Column(Float, nullable=False)

    # Bounding box as JSON
    bounding_box = Column(Text, nullable=False)

    # Contour points as JSON
    contour_points = Column(Text, nullable=False)

    # Classification
    classification = Column(String(100), nullable=False, index=True)
    confidence = Column(Float, nullable=False)

    # Processing status
    work_status = Column(String(20), nullable=False, default=WorkStatus.PENDING.value, index=True)

    # Optional metadata
    source_camera = Column(Integer, nullable=True)
    bed_map_id = Column(String(100), nullable=True, index=True)
    image_id = Column(String(100), nullable=True)


class SQLiteDetectionRepository(DetectionRepository):
    """SQLite implementation of DetectionRepository.

    This repository persists detected objects to a SQLite database using SQLAlchemy.
    Connection management and transactions are handled internally.
    """

    def __init__(self, database_url: str = "sqlite:///cncsorter.db"):
        """Initialize repository with database connection.

        Args:
            database_url: SQLAlchemy database URL. Defaults to local SQLite file.
        """
        self.engine = create_engine(database_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def _to_model(self, detected_object: DetectedObject, status: WorkStatus = WorkStatus.PENDING) -> DetectedObjectModel:
        """Convert domain entity to SQLAlchemy model.

        Args:
            detected_object: Domain entity to convert.
            status: Work status to assign.

        Returns:
            SQLAlchemy model instance.
        """
        cnc_coord = detected_object.cnc_coordinate
        return DetectedObjectModel(
            uuid=str(detected_object.uuid),
            object_id=detected_object.object_id,
            timestamp=detected_object.timestamp or datetime.now(),
            x=cnc_coord.x if cnc_coord else None,
            y=cnc_coord.y if cnc_coord else None,
            z=cnc_coord.z if cnc_coord else None,
            center_x=detected_object.center.x,
            center_y=detected_object.center.y,
            area=detected_object.area,
            bounding_box=json.dumps(detected_object.bounding_box),
            contour_points=json.dumps(detected_object.contour_points),
            classification=detected_object.classification,
            confidence=detected_object.confidence,
            work_status=status.value,
            source_camera=detected_object.source_camera,
            bed_map_id=detected_object.bed_map_id,
            image_id=detected_object.image_id,
        )

    def _from_model(self, model: DetectedObjectModel) -> DetectedObject:
        """Convert SQLAlchemy model to domain entity.

        Args:
            model: SQLAlchemy model instance.

        Returns:
            Domain entity.
        """
        cnc_coord = None
        if model.x is not None and model.y is not None:
            cnc_coord = CNCCoordinate(x=model.x, y=model.y, z=model.z or 0.0)

        return DetectedObject(
            uuid=UUID(model.uuid),
            object_id=model.object_id,
            contour_points=json.loads(model.contour_points),
            bounding_box=tuple(json.loads(model.bounding_box)),
            area=model.area,
            center=Point2D(x=model.center_x, y=model.center_y),
            image_id=model.image_id,
            cnc_coordinate=cnc_coord,
            timestamp=model.timestamp,
            classification=model.classification,
            confidence=model.confidence,
            source_camera=model.source_camera,
            bed_map_id=model.bed_map_id,
        )

    def save(self, detected_object: DetectedObject) -> UUID:
        """Save a detected object to persistent storage.

        Args:
            detected_object: The detected object entity to persist.

        Returns:
            UUID of the saved object.

        Raises:
            RepositoryError: If save operation fails.
        """
        session = self.SessionLocal()
        try:
            model = self._to_model(detected_object)
            session.add(model)
            session.commit()
            return detected_object.uuid
        except SQLAlchemyError as e:
            session.rollback()
            raise RepositoryError(f"Failed to save detected object: {e}") from e
        finally:
            session.close()

    def list_pending(self) -> List[DetectedObject]:
        """Retrieve all objects with PENDING status.

        Returns:
            List of detected objects awaiting processing.

        Raises:
            RepositoryError: If retrieval fails.
        """
        session = self.SessionLocal()
        try:
            models = session.query(DetectedObjectModel).filter(
                DetectedObjectModel.work_status == WorkStatus.PENDING.value
            ).all()
            return [self._from_model(model) for model in models]
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to list pending objects: {e}") from e
        finally:
            session.close()

    def update_status(self, object_id: UUID, status: WorkStatus) -> None:
        """Update the processing status of a detected object.

        Args:
            object_id: UUID of the object to update.
            status: New status to assign.

        Raises:
            RepositoryError: If update fails or object not found.
        """
        session = self.SessionLocal()
        try:
            model = session.query(DetectedObjectModel).filter(
                DetectedObjectModel.uuid == str(object_id)
            ).first()

            if model is None:
                raise RepositoryError(f"Object not found: {object_id}")

            model.work_status = status.value
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise RepositoryError(f"Failed to update object status: {e}") from e
        finally:
            session.close()

    def get_by_id(self, object_id: UUID) -> Optional[DetectedObject]:
        """Retrieve a detected object by its UUID.

        Args:
            object_id: UUID of the object to retrieve.

        Returns:
            DetectedObject if found, None otherwise.

        Raises:
            RepositoryError: If retrieval fails.
        """
        session = self.SessionLocal()
        try:
            model = session.query(DetectedObjectModel).filter(
                DetectedObjectModel.uuid == str(object_id)
            ).first()
            return self._from_model(model) if model else None
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to retrieve object: {e}") from e
        finally:
            session.close()

    def list_all(self, limit: Optional[int] = None) -> List[DetectedObject]:
        """Retrieve all detected objects, optionally limited.

        Args:
            limit: Maximum number of objects to return. None for all.

        Returns:
            List of all detected objects.

        Raises:
            RepositoryError: If retrieval fails.
        """
        session = self.SessionLocal()
        try:
            query = session.query(DetectedObjectModel).order_by(
                DetectedObjectModel.timestamp.desc()
            )
            if limit:
                query = query.limit(limit)
            models = query.all()
            return [self._from_model(model) for model in models]
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to list objects: {e}") from e
        finally:
            session.close()
