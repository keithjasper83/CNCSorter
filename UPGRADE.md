
⸻

CNCSorter Consolidated Technical Improvement and Implementation Plan

Objective
Upgrade CNCSorter from a session based prototype to a persistent event driven industrial grade system while preserving strict DDD SOC boundaries safety and long term extensibility

This plan merges
Your original Phase 1 to Phase 3 roadmap
Architectural and capability recommendations
The CNCSorter Technical Implementation Brief

This document is intended to be copied reviewed and handed to Copilot for stepwise execution

CORE ARCHITECTURAL UPGRADES FOUNDATION

Persistence Layer Domain and Infrastructure

Purpose
Enable traceability replay auditing regression testing and future ML
Remove session only object tracking

Domain Layer
File src cncsorter domain interfaces py

Define abstract repository
class DetectionRepository
save detected object returns none
list pending returns list of detected objects
update status object id status returns none

Introduce WorkStatus enum
PENDING
PROCESSING
COMPLETED
FAILED

Infrastructure Layer
File src cncsorter infrastructure persistence py
Implement SQLiteDetectionRepository using SQLAlchemy

Database Schema minimum
id UUID primary key
timestamp UTC indexed
x y z float
classification string
confidence float
work status enum
source camera optional
bed map id optional

Constraints
SQLite by default
Repository injected via application services
No SQLAlchemy imports outside infrastructure

Event Driven Orchestration Application Layer

Purpose
Decouple vision persistence UI and future automation
Prepare system for async pipelines and Web API extensions

Application Layer
File src cncsorter application events py

Implement
Lightweight synchronous EventBus
publish event
subscribe event type handler

Domain Events new
ObjectsDetected
BedMapCompleted
CNCPositionUpdated
PickTaskCreated
BoundaryViolationDetected

Vision System Changes
VisionSystem must not directly
write to storage
update GUI
control CNC

VisionSystem publishes ObjectsDetected event with DetectedObject entities

Subscribers
PersistenceSubscriber
Saves detected objects via DetectionRepository

GUISubscriber
Updates live overlay and counters

Future AutomationSubscriber
Generates pick tasks

Safety Interceptor Infrastructure CNC Protection

Purpose
Prevent physical damage
Enforce hard workspace limits

File
src cncsorter infrastructure cnc controller py

Implement
MotionValidator class

Behavior
Intercepts all G code movement commands
Extracts target X Y Z
Validates against config defined workspace
X less than or equal 800
Y less than or equal 400
Z less than or equal 300

On Violation
Raise BoundaryViolationError
Publish BoundaryViolationDetected event
Block command transmission

Rules
Validator is mandatory and non bypassable
Applies to both real and mock CNC controllers

Hardware Abstraction Digital Twin

Purpose
Enable CI testing
Allow development without physical CNC
Support replay and simulation

Infrastructure Layer
Implement MockCNCController

Behavior
Implements same interface as serial or HTTP CNC controller
Logs all moves to structured log file JSON
Simulates position updates

Configuration
config py
CNC_MODE serial or http or mock

Rules
Application layer must not know which controller is active
Dependency injected at startup

VISION SYSTEM IMPROVEMENTS

Automatic Camera Calibration High Priority

Implement
ChArUco or chessboard calibration wizard
Per camera intrinsic calibration
Extrinsic alignment to CNC coordinates

Artifacts
Calibration profiles stored on disk
Versioned and selectable via config
GUI and CLI access

Outcome
Eliminates manual alignment errors
Stabilizes multi camera stitching

Lighting Normalization Pipeline

Add preprocessing steps
CLAHE
Auto white balance
Exposure lock after first frame

Goal
Improve detection reliability in real workshop lighting

Hybrid CV and ML Classification Optional Modular

Pipeline
OpenCV contour detection fast filter
Optional ML refinement stage
ONNX runtime
MobileNet or YOLO Nano

Rules
ML layer is optional
Domain classification logic remains ML agnostic
Confidence scores fused not replaced

CNC INTELLIGENCE AND AUTONOMY

CNC Capability Model

Domain Entity
CNCCapabilities
max feed rate
acceleration
backlash
safe z height
probe support

Used by
Motion planner
Pick path optimizer
Safety validation

Pick Path Optimization

Implement
Nearest neighbor or TSP based ordering
Z safe batching
Tool change awareness future

Result
30 to 60 percent cycle time reduction for bulk sorting

Collision and Keep Out Zones

Extend BedMap
Polygon based exclusion zones
Clamps fixtures occlusions

Enforced by
MotionValidator
Pick planner

DATA DEBUGGING AND TRACEABILITY

Replay and Time Travel Debugging

Enable
Full session replay from SQLite
Algorithm version comparison
Offline tuning without hardware

API AND INTEGRATION

Minimal REST and WebSocket API

Endpoints
health
status
objects
bedmap latest
pick start
stream WebSocket

Use Cases
Remote monitoring
Headless operation
Factory dashboard
External robot integration

TESTING AND QUALITY

Synthetic Vision Test Harness

Generate
Artificial beds
Known object layouts
Noise blur lighting variations

Validate
Detection accuracy
Classification drift
Performance regressions

Hardware In The Loop HIL Mocks

Mock
CNC controller
Camera feeds
GPIO PWM

Allows
CI testing of motion logic
Safe regression testing

OPERATIONAL HARDENING

Structured Logging

JSON logs
Correlation ID per run
Log rotation
Machine readable diagnostics

Health and Self Diagnostics

Expose
FPS
Detection count
Camera latency
CNC latency
Storage IO

Trigger warnings on degradation

CODING STANDARDS MANDATORY

100 percent type hint coverage mypy clean
Google style docstrings pydocstyle clean
Cyclomatic complexity less than 10
Infrastructure depends on Domain only
No framework imports in Domain layer
Event driven where decoupling is possible

RECOMMENDED IMPLEMENTATION ORDER

Immediate Phase 1 plus
Setup py or pyproject toml
SQLite persistence and repository
EventBus and ObjectsDetected flow
MotionValidator safety interceptor
MockCNCController
Structured logging

Near Term
Camera calibration wizard
Pick path optimization
REST health endpoint
CNC capability modeling

Strategic
Hybrid CV and ML classifier
Adaptive scanning
Replay and regression framework

END OF CONSOLIDATED PLAN
