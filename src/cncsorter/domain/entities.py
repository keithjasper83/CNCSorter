"""Domain entities for CNCSorter."""
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Any
from datetime import datetime
from uuid import UUID, uuid4
import numpy as np


@dataclass
class Point2D:
    """Represents a 2D point in image coordinates."""
    x: float
    y: float


@dataclass
class CNCCoordinate:
    """Represents a 3D coordinate in the CNC machine space."""
    x: float
    y: float
    z: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {"x": self.x, "y": self.y, "z": self.z}


@dataclass
class DetectedObject:
    """Represents an object detected in the vision system."""
    object_id: int
    contour_points: List[Tuple[int, int]]
    bounding_box: Tuple[int, int, int, int]  # x, y, width, height
    area: float
    center: Point2D
    image_id: Optional[str] = None
    cnc_coordinate: Optional[CNCCoordinate] = None
    timestamp: Optional[datetime] = None
    uuid: UUID = field(default_factory=uuid4)
    classification: str = "unknown"
    confidence: float = 0.0
    source_camera: Optional[int] = None
    bed_map_id: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class BinLocation:
    """Represents a physical bin or drop-off location."""
    bin_id: str
    location: CNCCoordinate
    accepted_types: List[str]
    size_ranges: List[str] = field(default_factory=lambda: ["all"])


@dataclass
class PickOperation:
    """Represents a single step in a pick plan (Move, Pick, Place, ChangeTool)."""
    op_type: str  # "MOVE", "PICK", "PLACE", "TOOL_CHANGE"
    target_coordinate: CNCCoordinate
    details: str = ""
    tool_id: Optional[str] = None
    object_id: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "type": self.op_type,
            "x": self.target_coordinate.x,
            "y": self.target_coordinate.y,
            "z": self.target_coordinate.z,
            "details": self.details,
            "tool": self.tool_id,
            "object": self.object_id
        }


@dataclass
class PickPlan:
    """An ordered sequence of operations to clear the bed."""
    plan_id: str
    operations: List[PickOperation]
    estimated_duration_seconds: float
    total_items: int
    tool_changes: int
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class CapturedImage:
    """Represents a captured image from the camera."""
    image_id: str
    image_data: np.ndarray  # numpy array
    cnc_position: Optional[CNCCoordinate] = None
    timestamp: Optional[datetime] = None
    detected_objects: Optional[List[DetectedObject]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.detected_objects is None:
            self.detected_objects = []


@dataclass
class BedMap:
    """Represents the complete map of the CNC bed with all detected objects."""
    map_id: str
    images: List[CapturedImage] = field(default_factory=list)
    stitched_image: Optional[np.ndarray] = None  # numpy array of stitched image
    all_objects: Optional[List[DetectedObject]] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.all_objects is None:
            self.all_objects = []

    def add_image(self, image: CapturedImage):
        """Add a captured image to the bed map."""
        self.images.append(image)
        # Add all detected objects from this image to the map
        for obj in image.detected_objects:
            obj.image_id = image.image_id
            self.all_objects.append(obj)


@dataclass
class PickTask:
    """Represents a task to pick up an object."""
    task_id: str
    object_id: UUID
    target_position: CNCCoordinate
    status: str = "pending"
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
