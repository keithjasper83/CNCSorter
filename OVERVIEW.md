# CNCSorter - System Overview

## Quick Reference

### Running the Application

**Full Application (Raspberry Pi with live display):**
```bash
./run_rpi.sh
# or with CNC:
python src/main.py --cnc-mode serial --cnc-port /dev/ttyUSB0
```

**Interactive Test Menu (for development):**
```bash
source venv/bin/activate
cd src
python test_menu.py
```

### Key Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **Domain Entities** | Core business objects | `src/domain/entities.py` |
| **BedMappingService** | Orchestrates bed scanning | `src/application/bed_mapping.py` |
| **VisionSystem** | Camera & detection | `src/infrastructure/vision.py` |
| **CNCController** | Machine communication | `src/infrastructure/cnc_controller.py` |
| **LiveStatusDisplay** | Real-time UI | `src/presentation/live_display.py` |
| **Main Application** | Entry point | `src/main.py` |
| **Test Menu** | Individual testing | `src/test_menu.py` |

## Architecture

### Domain-Driven Design Layers

```
┌─────────────────────────────────────────┐
│        Presentation Layer               │
│   (UI, Display, User Interaction)       │
│     - LiveStatusDisplay                 │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│        Application Layer                │
│    (Use Cases, Orchestration)           │
│     - BedMappingService                 │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│        Domain Layer                     │
│     (Business Entities & Logic)         │
│  - CNCCoordinate, DetectedObject        │
│  - CapturedImage, BedMap                │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Infrastructure Layer               │
│   (Technical Implementations)           │
│  - VisionSystem, ImageStitcher          │
│  - FluidNCSerial, FluidNCHTTP           │
└─────────────────────────────────────────┘
```

## Workflow

### 1. Initialization
```python
# Create app instance
app = CNCSorterApp(
    camera_index=0,
    cnc_mode="serial",
    cnc_config={'port': '/dev/ttyUSB0', 'baudrate': 115200}
)

# Initialize all components
app.initialize()
```

### 2. Bed Mapping Process

```
1. Start New Map
   └─> [S] key → Creates BedMap entity

2. Capture Images
   └─> [SPACE] key → For each capture:
       ├─ Get CNC position
       ├─ Capture camera frame
       ├─ Detect objects
       └─ Create CapturedImage with DetectedObjects

3. Stitch Images
   └─> [M] key → Combines all images into panorama

4. Save Map
   └─> [V] key → Saves:
       ├─ Individual images
       ├─ Stitched panorama
       └─ Metadata with object coordinates
```

### 3. Live Display Updates

The LiveStatusDisplay continuously shows:
- **Camera Feed**: Real-time video with object overlays
- **Status Panel**: Current operation and progress
- **Statistics**: Images captured, objects detected
- **CNC Position**: Real-time X, Y, Z coordinates
- **FPS**: Performance monitoring

## Testing Individual Functions

The interactive test menu (`test_menu.py`) allows isolated testing:

1. **Camera Test**: Verify camera connectivity
2. **Detection Test**: Tune threshold and min_area parameters
3. **CNC Serial Test**: Test serial communication
4. **CNC HTTP Test**: Test HTTP/REST communication
5. **Capture Test**: Test image capture with detection
6. **Stitching Test**: Test image panorama creation
7. **Mapping Test**: Test complete bed mapping workflow
8. **Display Test**: Test live status display UI
9. **Full App**: Run complete application

## CNC Integration

### Serial Communication (FluidNC)
```python
controller = FluidNCSerial('/dev/ttyUSB0', 115200)
controller.connect()
position = controller.get_position()  # Returns CNCCoordinate
controller.move_to(CNCCoordinate(x=10, y=20, z=5))
```

### HTTP Communication (FluidNC)
```python
controller = FluidNCHTTP('192.168.1.100', 80)
controller.connect()
position = controller.get_position()
```

## Data Flow

```
Camera → VisionSystem.capture_frame()
    ↓
Frame → VisionSystem.detect_objects()
    ↓
DetectedObjects → CapturedImage entity
    ↓
CNC Position → CNCCoordinate entity
    ↓
Multiple CapturedImages → BedMap entity
    ↓
BedMap → ImageStitcher.stitch_images()
    ↓
Stitched Image → Save to disk
```

## Key Entities

### CNCCoordinate
Represents 3D position in CNC machine space:
```python
coord = CNCCoordinate(x=10.5, y=20.3, z=5.0)
```

### DetectedObject
Represents an object found in the image:
```python
obj = DetectedObject(
    object_id=1,
    contour_points=[(x1,y1), (x2,y2), ...],
    bounding_box=(x, y, width, height),
    area=1500.0,
    center=Point2D(100, 150),
    cnc_coordinate=CNCCoordinate(10, 20, 0)
)
```

### CapturedImage
Represents a captured frame with detected objects:
```python
image = CapturedImage(
    image_id="img_001",
    image_data=frame,
    cnc_position=CNCCoordinate(10, 20, 0),
    detected_objects=[obj1, obj2, ...]
)
```

### BedMap
Represents complete mapping session:
```python
bed_map = BedMap(
    map_id="map_20260112_142030",
    images=[img1, img2, ...],
    stitched_image=panorama,
    all_objects=[obj1, obj2, obj3, ...]
)
```

## Configuration

### Camera Settings
- Default camera index: 0
- Resolution: 1280x720 (auto-set)
- Adjustable via `--camera` argument

### Detection Parameters
- Threshold: 127 (adjustable in real-time)
- Min Area: 150 pixels (adjustable in real-time)

### CNC Settings
- Serial port: /dev/ttyUSB0 (configurable)
- Baudrate: 115200 (configurable)
- HTTP host: 192.168.1.100 (configurable)
- HTTP port: 80 (configurable)

## Output Files

### Captured Maps
Location: `maps/<map_id>/`

Files:
- `img_001.jpg`, `img_002.jpg`, ... (individual captures)
- `stitched.jpg` (complete panorama)
- `metadata.txt` (session information)

### Snapshots
Location: Current directory
- `snapshot_<count>_objs.jpg`
- `camera_test_<timestamp>.jpg`
- `<img_id>_detected.jpg`

## Development Guidelines

See `agents.md` for:
- DDD principles
- Separation of Concerns rules
- Code quality standards
- Testing practices
- Design patterns

## Troubleshooting

### Camera Not Opening
```
Error: Could not open camera
```
**Solutions:**
- Check camera is connected
- Verify camera index (try --camera 1)
- Check permissions
- Ensure no other app is using camera

### CNC Connection Failed
```
Warning: Failed to connect to CNC controller
```
**Solutions:**
- Verify serial port or IP address
- Check baudrate setting
- Ensure FluidNC is powered and accessible
- Check network connection (HTTP mode)

### Stitching Failed
```
Stitching failed with status: X
```
**Solutions:**
- Capture more images (minimum 2)
- Ensure sufficient overlap between images
- Images should have matching features
- Try adjusting camera position

## Performance Tips

### Raspberry Pi
- Use lower resolution if needed
- Reduce detection parameters for speed
- Ensure adequate cooling
- Consider using system OpenCV (`apt install python3-opencv`)

### Detection Speed
- Increase min_area to filter small objects
- Adjust threshold to reduce false positives
- Lower camera resolution if needed

## Next Steps

1. **Calibration**: Calibrate camera-to-CNC coordinate transformation
2. **Pick & Place**: Implement object picking logic
3. **Path Planning**: Add optimal movement path generation
4. **Multiple Objects**: Handle multiple object types
5. **Database**: Store mapping history in database
6. **Web Interface**: Add web-based monitoring
