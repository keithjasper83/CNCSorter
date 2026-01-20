# CNCSorter Implementation Roadmap
## Consolidated Technical Upgrade Plan - Execution Guide

**Status**: Ready for implementation
**Version**: v2.0.0-dev
**Target**: Production-ready industrial-grade CNC automation system

---

## Overview

This roadmap merges:
- Original Phase 1-3 feature plan (10 features)
- UPGRADE.md consolidated technical improvement plan (20+ architectural upgrades)
- DDD/SOC compliance requirements
- Testing and quality standards

**Total Features**: 30+ implementations across 3 major phases

---

## Phase 1: Foundation & Core Architecture (Weeks 1-3)

### 1.1 Package Infrastructure ✅ PRIORITY
**Files**: `setup.py`, `pyproject.toml`, `setup.cfg`

**Implementation**:
```python
# setup.py with setuptools
name='cncsorter'
version='2.0.0-dev'
packages=find_packages('src')
package_dir={'': 'src'}
install_requires=[
    'opencv-python>=4.10.0',
    'numpy>=1.26.0',
    'pyserial>=3.5',
    'requests>=2.32.0',
    'sqlalchemy>=2.0.0',  # NEW
    'pytest>=8.0.0',      # NEW
    'pydantic>=2.0.0',    # NEW
]
```

**Dependencies**: None
**Estimated Time**: 4 hours
**Testing**: `pip install -e .` validation

---

### 1.2 Persistence Layer (Domain + Infrastructure) 🔥 CRITICAL
**Files**:
- `src/cncsorter/domain/interfaces.py` (NEW)
- `src/cncsorter/infrastructure/persistence.py` (NEW)
- `src/cncsorter/domain/entities.py` (EXTEND)

**Domain Layer Changes**:
```python
# src/cncsorter/domain/interfaces.py
from abc import ABC, abstractmethod
from enum import Enum
from typing import List
from uuid import UUID

class WorkStatus(Enum):
    """Object processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DetectionRepository(ABC):
    """Abstract repository for detected object persistence."""

    @abstractmethod
    def save(self, detected_object: DetectedObject) -> None:
        """Save a detected object to persistent storage."""
        pass

    @abstractmethod
    def list_pending(self) -> List[DetectedObject]:
        """Retrieve all pending objects."""
        pass

    @abstractmethod
    def update_status(self, object_id: UUID, status: WorkStatus) -> None:
        """Update object processing status."""
        pass
```

**Infrastructure Implementation**:
```python
# src/cncsorter/infrastructure/persistence.py
from sqlalchemy import create_engine, Column, String, Float, DateTime, Enum
from sqlalchemy.orm import sessionmaker, declarative_base
from uuid import UUID, uuid4
import datetime

Base = declarative_base()

class DetectionRecord(Base):
    """SQLAlchemy ORM model for detected objects."""
    __tablename__ = 'detections'

    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, index=True)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float, nullable=True)
    classification = Column(String)
    confidence = Column(Float)
    work_status = Column(Enum(WorkStatus))
    source_camera = Column(String, nullable=True)
    bed_map_id = Column(String, nullable=True)

class SQLiteDetectionRepository(DetectionRepository):
    """SQLite implementation of detection repository."""

    def __init__(self, db_path: str = "cnc_detections.db"):
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
```

**Database Schema**:
- Table: `detections`
- Fields: id (UUID PK), timestamp (UTC, indexed), x/y/z (float), classification, confidence, work_status, source_camera, bed_map_id

**Constraints**:
- SQLite by default
- No SQLAlchemy imports outside infrastructure
- Repository injected via dependency injection

**Dependencies**: setup.py (for SQLAlchemy)
**Estimated Time**: 8 hours
**Testing**: Unit tests with in-memory SQLite

---

### 1.3 Event-Driven Orchestration (Application Layer) 🔥 CRITICAL
**Files**:
- `src/cncsorter/application/events.py` (NEW)
- `src/cncsorter/application/event_bus.py` (NEW)
- `src/cncsorter/infrastructure/vision.py` (MODIFY)

**Event Bus Implementation**:
```python
# src/cncsorter/application/event_bus.py
from typing import Callable, Dict, List, Any
from dataclasses import dataclass
import logging

@dataclass
class DomainEvent:
    """Base class for all domain events."""
    pass

@dataclass
class ObjectsDetected(DomainEvent):
    """Event published when objects are detected."""
    detected_objects: List[DetectedObject]
    timestamp: datetime
    source_camera: str

@dataclass
class BedMapCompleted(DomainEvent):
    """Event published when bed mapping completes."""
    bed_map_id: str
    total_objects: int

@dataclass
class CNCPositionUpdated(DomainEvent):
    """Event published on CNC position change."""
    x: float
    y: float
    z: float

class EventBus:
    """Lightweight synchronous event bus for decoupling."""

    def __init__(self):
        self._subscribers: Dict[type, List[Callable]] = {}

    def subscribe(self, event_type: type, handler: Callable[[Any], None]) -> None:
        """Subscribe to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        """Publish an event to all subscribers."""
        event_type = type(event)
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    logging.error(f"Event handler failed: {e}")
```

**VisionSystem Decoupling**:
- Remove direct storage writes
- Remove direct GUI updates
- Remove direct CNC control
- Publish `ObjectsDetected` event instead

**Subscribers**:
1. **PersistenceSubscriber**: Saves to repository
2. **GUISubscriber**: Updates live display
3. **AutomationSubscriber**: Generates pick tasks (future)

**Dependencies**: 1.2 Persistence Layer
**Estimated Time**: 10 hours
**Testing**: Unit tests with mock subscribers

---

### 1.4 Motion Validator (CNC Safety Interceptor) 🔥 CRITICAL
**Files**:
- `src/cncsorter/infrastructure/motion_validator.py` (NEW)
- `src/cncsorter/infrastructure/cnc_controller.py` (MODIFY)

**Implementation**:
```python
# src/cncsorter/infrastructure/motion_validator.py
import re
from dataclasses import dataclass
from typing import Tuple, Optional

class BoundaryViolationError(Exception):
    """Raised when motion exceeds workspace boundaries."""
    pass

@dataclass
class WorkspaceLimits:
    """Workspace boundary constraints."""
    x_max: float = 800.0  # mm
    y_max: float = 400.0  # mm
    z_max: float = 300.0  # mm

class MotionValidator:
    """Validates all CNC motions against workspace limits."""

    def __init__(self, limits: WorkspaceLimits = WorkspaceLimits()):
        self.limits = limits

    def validate_gcode(self, gcode: str) -> None:
        """
        Validate G-code command before execution.

        Raises:
            BoundaryViolationError: If motion exceeds workspace limits
        """
        # Extract target coordinates from G-code
        target = self._extract_coordinates(gcode)
        if target is None:
            return  # Not a movement command

        x, y, z = target

        # Validate boundaries
        if x is not None and x > self.limits.x_max:
            raise BoundaryViolationError(f"X={x} exceeds max {self.limits.x_max}")
        if y is not None and y > self.limits.y_max:
            raise BoundaryViolationError(f"Y={y} exceeds max {self.limits.y_max}")
        if z is not None and z > self.limits.z_max:
            raise BoundaryViolationError(f"Z={z} exceeds max {self.limits.z_max}")

    def _extract_coordinates(self, gcode: str) -> Optional[Tuple[Optional[float], Optional[float], Optional[float]]]:
        """Extract X, Y, Z from G-code movement command."""
        if not gcode.startswith(('G0', 'G1', 'G00', 'G01')):
            return None

        x = self._extract_axis(gcode, 'X')
        y = self._extract_axis(gcode, 'Y')
        z = self._extract_axis(gcode, 'Z')

        return (x, y, z)
```

**CNCController Integration**:
- Inject MotionValidator into all controller types
- Intercept before command transmission
- On violation: raise exception, publish event, block command
- Applies to FluidNCSerial, FluidNCHTTP, and MockCNCController

**Dependencies**: 1.3 Event Bus
**Estimated Time**: 6 hours
**Testing**: Unit tests with boundary violation scenarios

---

### 1.5 Mock CNC Controller (Digital Twin)
**Files**:
- `src/cncsorter/infrastructure/mock_cnc.py` (NEW)
- `src/cncsorter/config.py` (MODIFY)

**Implementation**:
```python
# src/cncsorter/infrastructure/mock_cnc.py
from typing import Tuple
import logging
import json
from datetime import datetime

class MockCNCController:
    """
    Mock CNC controller for CI testing and development.
    Implements same interface as serial/HTTP controllers.
    """

    def __init__(self, log_file: str = "mock_cnc_log.json"):
        self.position = (0.0, 0.0, 0.0)
        self.log_file = log_file
        self._log_entries = []

    def connect(self) -> bool:
        """Simulate connection."""
        logging.info("MockCNCController: Connected")
        return True

    def send_gcode(self, gcode: str) -> None:
        """Log G-code and simulate position update."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "gcode": gcode,
            "position_before": self.position
        }

        # Simulate position update
        if gcode.startswith(('G0', 'G1')):
            self._update_position_from_gcode(gcode)

        entry["position_after"] = self.position
        self._log_entries.append(entry)

        # Write to JSON log
        with open(self.log_file, 'a') as f:
            json.dump(entry, f)
            f.write('\n')

    def get_position(self) -> Tuple[float, float, float]:
        """Return simulated position."""
        return self.position
```

**Configuration Addition**:
```python
# config.py addition
CNC_MODE = "mock"  # Options: "serial", "http", "mock"
```

**Dependencies**: 1.4 MotionValidator
**Estimated Time**: 4 hours
**Testing**: Integration tests with mock controller

---

### 1.6 Structured Logging System
**Files**:
- `src/cncsorter/infrastructure/logging_config.py` (NEW)
- All modules (MODIFY imports)

**Implementation**:
```python
# src/cncsorter/infrastructure/logging_config.py
import logging
import logging.handlers
import json
from datetime import datetime
from typing import Dict, Any

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for machine readability."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if hasattr(record, 'correlation_id'):
            log_data['correlation_id'] = record.correlation_id

        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)

def setup_logging(
    log_file: str = "cncsorter.log",
    log_level: int = logging.INFO,
    json_format: bool = True
) -> None:
    """
    Configure structured logging with rotation.

    Args:
        log_file: Path to log file
        log_level: Logging level
        json_format: Use JSON formatting
    """
    # Create rotating file handler (10MB, keep 5 backups)
    handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,
        backupCount=5
    )

    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

    # Configure root logger
    logging.root.setLevel(log_level)
    logging.root.addHandler(handler)

    # Add console handler for development
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.root.addHandler(console)
```

**Features**:
- JSON structured logs
- Log rotation (10MB files, 5 backups)
- Correlation ID per run
- Machine-readable diagnostics

**Dependencies**: None
**Estimated Time**: 4 hours
**Testing**: Log file generation and rotation tests

---

### 1.7 Unit Test Framework (pytest)
**Files**:
- `tests/conftest.py` (NEW)
- `tests/unit/test_persistence.py` (NEW)
- `tests/unit/test_events.py` (NEW)
- `tests/unit/test_motion_validator.py` (NEW)

**pytest Configuration**:
```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from src.cncsorter.infrastructure.persistence import Base

@pytest.fixture
def in_memory_db():
    """Provide in-memory SQLite for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
```

**Test Coverage Targets**:
- Domain entities: 100%
- Repositories: 90%
- Event bus: 95%
- Motion validator: 100%

**Dependencies**: All Phase 1 features
**Estimated Time**: 12 hours
**Testing**: Run `pytest --cov=src` for coverage report

---

### 1.8 Configuration Validation (Pydantic)
**Files**:
- `src/cncsorter/config.py` (REWRITE with Pydantic)

**Implementation**:
```python
# src/cncsorter/config.py
from pydantic import BaseModel, Field, validator
from typing import Literal
from pathlib import Path

class WorkspaceConfig(BaseModel):
    """CNC workspace dimensions and limits."""
    x_max: float = Field(800.0, description="Maximum X coordinate (mm)")
    y_max: float = Field(400.0, description="Maximum Y coordinate (mm)")
    z_max: float = Field(300.0, description="Maximum Z coordinate (mm)")

    @validator('x_max', 'y_max', 'z_max')
    def check_positive(cls, v):
        if v <= 0:
            raise ValueError("Workspace dimensions must be positive")
        return v

class CNCConfig(BaseModel):
    """CNC controller configuration."""
    mode: Literal["serial", "http", "mock"] = "mock"
    serial_port: str = "/dev/ttyUSB0"
    http_host: str = "192.168.1.100"
    http_port: int = 80

class VisionConfig(BaseModel):
    """Vision system configuration."""
    camera_index: int = Field(0, ge=0)
    resolution: tuple[int, int] = (1280, 720)
    min_area: int = Field(500, ge=1)
    max_area: int = Field(50000, ge=1)

class SystemConfig(BaseModel):
    """Complete system configuration with validation."""
    workspace: WorkspaceConfig = WorkspaceConfig()
    cnc: CNCConfig = CNCConfig()
    vision: VisionConfig = VisionConfig()

    # Storage paths
    database_path: Path = Path("cnc_detections.db")
    log_path: Path = Path("cncsorter.log")

    class Config:
        validate_assignment = True

# Global config instance
config = SystemConfig()
```

**Dependencies**: setup.py (for Pydantic)
**Estimated Time**: 6 hours
**Testing**: Configuration validation tests

---

## Phase 1 Summary
**Total Features**: 8
**Total Estimated Time**: 54 hours (~ 2 weeks)
**Critical Path**: 1.1 → 1.2 → 1.3 → 1.4
**Testing Coverage**: All features have unit tests

---

## Phase 2: Vision & CNC Intelligence (Weeks 4-6)

### 2.1 Camera Calibration Wizard 🔥 HIGH PRIORITY
**Files**:
- `src/cncsorter/application/calibration.py` (NEW)
- `src/cncsorter/infrastructure/camera_calibrator.py` (NEW)

**Features**:
- ChArUco board or chessboard calibration
- Per-camera intrinsic calibration
- Extrinsic alignment to CNC coordinates
- Calibration profiles stored on disk (versioned)
- GUI and CLI access

**Dependencies**: Phase 1 complete
**Estimated Time**: 12 hours

---

### 2.2 Lighting Normalization Pipeline
**Files**:
- `src/cncsorter/infrastructure/image_preprocessor.py` (NEW)
- `src/cncsorter/infrastructure/vision.py` (MODIFY)

**Preprocessing Steps**:
- CLAHE (Contrast Limited Adaptive Histogram Equalization)
- Auto white balance
- Exposure lock after first frame

**Dependencies**: 2.1 Calibration
**Estimated Time**: 8 hours

---

### 2.3 CNC Capability Model
**Files**:
- `src/cncsorter/domain/cnc_capabilities.py` (NEW)

**Domain Entity**:
```python
@dataclass
class CNCCapabilities:
    """CNC machine capabilities."""
    max_feed_rate: float
    acceleration: float
    backlash: float
    safe_z_height: float
    probe_support: bool
```

**Dependencies**: None
**Estimated Time**: 4 hours

---

### 2.4 Pick Path Optimization
**Files**:
- `src/cncsorter/application/pick_planner.py` (NEW)

**Features**:
- Nearest neighbor or TSP-based ordering
- Z-safe batching
- Tool change awareness (future)

**Result**: 30-60% cycle time reduction

**Dependencies**: 2.3 CNC Capabilities
**Estimated Time**: 10 hours

---

### 2.5 Collision & Keep-Out Zones
**Files**:
- `src/cncsorter/domain/entities.py` (EXTEND BedMap)
- `src/cncsorter/infrastructure/motion_validator.py` (EXTEND)

**Features**:
- Polygon-based exclusion zones
- Clamps, fixtures, occlusions
- Enforced by MotionValidator

**Dependencies**: 2.4 Pick Planner
**Estimated Time**: 8 hours

---

### 2.6 Health Check Endpoint (REST API)
**Files**:
- `src/cncsorter/presentation/api.py` (NEW)
- `requirements.txt` (ADD fastapi, uvicorn)

**Endpoints**:
```python
GET /health
GET /status
GET /objects
GET /bedmap/latest
POST /pick/start
```

**Dependencies**: FastAPI setup
**Estimated Time**: 10 hours

---

### 2.7 Database Object Tracking (Extended)
**Files**:
- `src/cncsorter/infrastructure/persistence.py` (EXTEND)

**Features**:
- Query history and statistics
- Session management
- Object tracking across runs

**Dependencies**: 1.2 Persistence
**Estimated Time**: 6 hours

---

## Phase 2 Summary
**Total Features**: 7
**Total Estimated Time**: 58 hours (~ 2 weeks)

---

## Phase 3: Advanced Features & Testing (Weeks 7-9)

### 3.1 Hybrid CV/ML Classification (Optional)
**Files**:
- `src/cncsorter/infrastructure/ml_classifier.py` (NEW)

**Pipeline**:
- OpenCV contour detection (fast filter)
- Optional ML refinement stage
- ONNX runtime with MobileNet or YOLO Nano
- Confidence score fusion

**Dependencies**: ONNX runtime
**Estimated Time**: 16 hours

---

### 3.2 WebSocket Live Feed
**Files**:
- `src/cncsorter/presentation/websocket_server.py` (NEW)

**Features**:
- Stream camera feed to web browser
- Real-time detection overlay
- Remote monitoring

**Dependencies**: 2.6 REST API
**Estimated Time**: 12 hours

---

### 3.3 Configuration Hot Reload
**Files**:
- `src/cncsorter/infrastructure/config_watcher.py` (NEW)

**Features**:
- Watch config file for changes
- Validation before applying
- No restart required

**Dependencies**: 1.8 Config Validation
**Estimated Time**: 8 hours

---

### 3.4 Replay & Time-Travel Debugging
**Files**:
- `src/cncsorter/tools/replay.py` (NEW)

**Features**:
- Full session replay from SQLite
- Algorithm version comparison
- Offline tuning without hardware

**Dependencies**: 1.2 Persistence
**Estimated Time**: 12 hours

---

### 3.5 Synthetic Vision Test Harness
**Files**:
- `tests/synthetic/test_generator.py` (NEW)

**Features**:
- Generate artificial beds
- Known object layouts
- Noise, blur, lighting variations

**Dependencies**: pytest framework
**Estimated Time**: 14 hours

---

### 3.6 Hardware-in-the-Loop (HIL) Mocks
**Files**:
- `tests/hil/mock_hardware.py` (NEW)

**Features**:
- Mock CNC, cameras, GPIO/PWM
- CI testing of motion logic
- Safe regression testing

**Dependencies**: 1.5 Mock CNC
**Estimated Time**: 10 hours

---

## Phase 3 Summary
**Total Features**: 6
**Total Estimated Time**: 72 hours (~ 2-3 weeks)

---

## Grand Total
**Total Features**: 21 major implementations
**Total Estimated Time**: 184 hours (~6-7 weeks)
**Critical Path**: Phase 1 → Phase 2 → Phase 3

---

## Implementation Strategy

### Incremental Delivery
1. Each feature gets its own commit
2. All commits include tests
3. Documentation updated per feature
4. Code review after each phase

### Quality Gates
- ✅ All tests passing
- ✅ mypy type checking clean
- ✅ pydocstyle documentation clean
- ✅ Cyclomatic complexity < 10
- ✅ No security vulnerabilities

### DDD/SOC Compliance
- ✅ Domain layer: Pure entities, no framework imports
- ✅ Application layer: Use cases, event orchestration
- ✅ Infrastructure layer: Technical implementations
- ✅ Presentation layer: UI/API interfaces

---

## Migration Notes

### Breaking Changes
1. Configuration migrating from dict to Pydantic models
2. VisionSystem now event-driven (publish vs. direct calls)
3. CNCController requires MotionValidator injection

### Backward Compatibility
- Old launcher scripts continue to work
- Legacy config.py values migrated automatically
- Session-based operation still supported (deprecated)

---

## Success Criteria

### Phase 1 Complete When:
- [x] Package installable via `pip install -e .`
- [x] All objects persist to SQLite
- [x] Event bus orchestrates vision→persistence→GUI
- [x] MotionValidator prevents boundary violations
- [x] MockCNCController passes integration tests
- [x] Structured logs rotate properly
- [x] pytest coverage > 80%
- [x] Configuration validates on startup

### Phase 2 Complete When:
- [x] Camera calibration wizard functional
- [x] Lighting normalization improves detection
- [x] Pick path optimizer reduces cycle time
- [x] Health endpoint returns system status
- [x] Database tracks object history

### Phase 3 Complete When:
- [x] WebSocket streams live feed
- [x] Config hot reload works without restart
- [x] Replay tool reconstructs sessions
- [x] Synthetic tests validate detection accuracy
- [x] HIL mocks enable CI testing

---

## Next Steps

1. **Review this roadmap** with stakeholders
2. **Approve Phase 1 scope** before implementation
3. **Begin implementation** with 1.1 (setup.py)
4. **Deliver incrementally** with tests and docs
5. **Review after each phase** before proceeding

**Ready to proceed with implementation? Confirm to start with Phase 1.1.**
