# Multi-Camera Setup Guide

## Why Multiple Camera Angles?

### Key Advantages

#### 1. **Complete Coverage - No Blind Spots**
- Single camera can miss objects hidden behind others
- Multiple angles ensure every object is visible from at least one camera
- Critical for densely packed CNC beds

#### 2. **Occlusion Handling**
- If one camera's view is blocked, other cameras still see the object
- Robustness against temporary obstructions (tool, hand, debris)
- Better detection in cluttered environments

#### 3. **3D Reconstruction & Depth Perception**
- Multiple angles enable triangulation for 3D position
- Calculate object height and orientation
- Essential for robotic pick-and-place operations
- Determine if objects are stacked

#### 4. **Accuracy & Cross-Validation**
- Detect same object in multiple views = high confidence
- Reduce false positives by requiring multi-camera agreement
- More accurate object counting

#### 5. **Redundancy & Reliability**
- System continues working if one camera fails
- IP cameras may drop connection - others keep running
- Mission-critical for production environments

#### 6. **Better Lighting & Reflections**
- Different angles handle shadows differently
- Glossy objects that reflect light badly from one angle work from another
- Matte vs. reflective surfaces benefit from multiple viewpoints

#### 7. **Object Orientation for Pick & Place**
- Single camera cannot determine rotation
- Multiple views reveal object orientation (0°, 90°, 180°, 270°)
- Critical for robotic gripper alignment

## Your Multi-Device Setup

### Available Cameras

| Device | Recommended Position | Resolution | Connection | Best For |
|--------|---------------------|------------|------------|----------|
| **Webcam** | Top-down (overhead) | 720p-1080p | USB | Primary view, overall layout |
| **iPhone** | Side view (90°) | 1080p-4K | IP Camera app | Object profiles, height |
| **GoPro** | Front view | 1080p-4K | IP/USB | Wide angle, full bed coverage |
| **iPad** | 45° angle | 1080p-4K | IP Camera app | Combined perspective, 3D |

### Recommended Camera Placement

```
                    TOP VIEW OF CNC BED
    ┌─────────────────────────────────────────┐
    │                                         │
    │         [Webcam - Overhead]             │
    │                 ↓                       │
    │    ┌─────────────────────────┐         │
    │    │                         │         │
    │    │      CNC BED            │ ← [iPhone - Side]
    │    │                         │         │
    │    │                         │         │
    │    └─────────────────────────┘         │
    │              ↑                          │
    │      [GoPro - Front]                    │
    │                                         │
    │              [iPad - 45° Angle]         │
    │                   ↗                     │
    └─────────────────────────────────────────┘
```

### Physical Setup Tips

1. **Webcam (Overhead)**:
   - Mount directly above CNC bed center
   - Height: 30-50cm for best coverage
   - Provides grid-like view for mapping

2. **iPhone (Side)**:
   - Mount on tripod at bed height
   - Perpendicular to X-axis
   - Shows object profiles and heights

3. **GoPro (Front)**:
   - Wide-angle lens captures entire bed
   - Mount at Y-axis end
   - Good for workflow documentation

4. **iPad (45° Angle)**:
   - Mount at corner, angled down
   - Best compromise for 3D reconstruction
   - Balances overhead and profile views

## Setup Instructions

### 1. IP Camera Apps

For iPhone and iPad:
- **Recommended**: "IP Webcam" or "EpocCam"
- Install app and note the IP address shown
- Enable video streaming
- Default URL format: `http://192.168.1.XXX:8080/video`

For GoPro:
- Use GoPro app with live stream feature
- Or connect via USB for direct feed
- Check GoPro Labs for custom firmware options

### 2. Network Configuration

```bash
# Find device IP addresses
# On Raspberry Pi:
ping iphone.local
ping ipad.local

# Or check router's connected devices
# Note down IP addresses for configuration
```

### 3. Configure Multi-Camera System

Edit `vision_multi_camera.py` configuration:

```python
cameras = [
    CameraConfig(
        name="Webcam",
        source=0,  # USB webcam index
        position="top",
        enabled=True
    ),
    CameraConfig(
        name="iPhone",
        source="http://192.168.1.100:8080/video",  # Your iPhone's IP
        position="side",
        enabled=True  # Set to True when ready
    ),
    CameraConfig(
        name="GoPro",
        source=1,  # Or HTTP URL if using IP streaming
        position="front",
        enabled=True
    ),
    CameraConfig(
        name="iPad",
        source="http://192.168.1.102:8080/video",  # Your iPad's IP
        position="angle45",
        enabled=True
    ),
]
```

### 4. Test Individual Cameras First

```bash
# Test each camera separately using enhanced vision
cd src/infrastructure
python vision_enhanced.py
# Change CONFIG['SOURCE'] to test each device
```

### 5. Run Multi-Camera System

```bash
python vision_multi_camera.py
```

## Display Layouts

The system supports 4 different view layouts:

### 1. Grid Layout (Default) - Press '1'
```
┌─────────┬─────────┐
│ Webcam  │ iPhone  │
│  (Top)  │ (Side)  │
├─────────┼─────────┤
│ GoPro   │  iPad   │
│ (Front) │ (45°)   │
└─────────┴─────────┘
```
Best for: Monitoring all angles simultaneously

### 2. Horizontal Layout - Press '2'
```
┌────┬────┬────┬────┐
│Web │iPhone│Go │iPad│
│cam │      │Pro│    │
└────┴────┴────┴────┘
```
Best for: Ultrawide displays, comparing side-by-side

### 3. Vertical Layout - Press '3'
```
┌──────────┐
│ Webcam   │
├──────────┤
│ iPhone   │
├──────────┤
│ GoPro    │
├──────────┤
│ iPad     │
└──────────┘
```
Best for: Portrait displays, detailed inspection

### 4. Picture-in-Picture - Press '4'
```
┌─────────────────────────┐
│                     ┌─┐ │
│                     │i│ │
│    Webcam (Main)    ├─┤ │
│                     │G│ │
│                     ├─┤ │
│                     │iP│ │
└─────────────────────┴─┘ │
```
Best for: Focusing on primary view with context

## Performance Optimization

### For Raspberry Pi

```python
# Reduce resolution for IP cameras
CameraConfig(
    name="iPhone",
    source="http://192.168.1.100:8080/video",
    resolution=(1280, 720),  # Force lower resolution
    preview_scale=0.3,       # Smaller preview
    frame_skip=2,            # Process every 2nd frame
)
```

### Network Tips

1. **Use 5GHz WiFi** for IP cameras (less interference)
2. **Static IP addresses** prevent connection drops
3. **Same subnet** as Raspberry Pi for best performance
4. **Reduce streaming quality** in camera apps if laggy

## Advanced Features

### Cross-Camera Object Matching

Future enhancement: Match same object across multiple cameras

```python
# Pseudo-code for object correspondence
def match_objects_across_cameras(multi_frame):
    """
    Match same physical object detected in multiple camera views.
    Uses epipolar geometry and feature matching.
    """
    # 1. Extract features from each detection
    # 2. Find corresponding features across cameras
    # 3. Use camera calibration for 3D position
    # 4. Group detections by physical object
    # 5. Return unique object list with 3D coordinates
```

### 3D Reconstruction

With camera calibration, you can:
- Calculate real-world 3D coordinates
- Measure object dimensions
- Determine object orientation
- Create point clouds

### Calibration Process

1. Print calibration pattern (checkerboard)
2. Capture pattern from all cameras
3. Run OpenCV calibration
4. Save camera intrinsics and extrinsics
5. Use for 3D triangulation

## Troubleshooting

### Camera Not Connecting

```bash
# Test URL directly
curl http://192.168.1.100:8080/video

# Check if streaming
ping 192.168.1.100
```

### Low FPS

- Reduce `preview_scale` to 0.3 or 0.2
- Increase `frame_skip` to 2 or 3
- Lower IP camera resolution in app settings
- Close other programs using camera

### Sync Issues

The system uses threading for independent capture. Small delays are normal.
For precise synchronization, use hardware trigger (advanced).

### IP Camera Drops

- Check WiFi signal strength
- Use closer access point
- Reduce video quality in app
- Enable auto-reconnect (already implemented)

## Integration with CNCSorter

### Using in Main Application

```python
from infrastructure.vision_multi_camera import MultiCameraVisionSystem, CameraConfig

# In CNCSorterApp.__init__:
self.multi_camera = MultiCameraVisionSystem(camera_configs)
self.multi_camera.initialize_cameras()
self.multi_camera.start_capture_threads()

# In main loop:
multi_frame = self.multi_camera.get_synchronized_frames()
multi_frame = self.multi_camera.detect_objects_multi_camera(multi_frame)

# Get results
total_objects = self.multi_camera.get_total_unique_objects(multi_frame)
display = self.multi_camera.create_multi_view_display(multi_frame)
```

### Saving Multi-Camera Data

```python
# Save all camera views
for camera_name, frame in multi_frame.annotated_frames.items():
    filename = f"{map_id}_{camera_name}.jpg"
    cv2.imwrite(filename, frame)

# Save metadata
metadata = {
    'timestamp': multi_frame.timestamp,
    'cameras': list(multi_frame.frames.keys()),
    'object_counts': multi_camera.get_combined_object_count(multi_frame)
}
```

## Production Checklist

- [ ] All cameras physically mounted
- [ ] IP camera apps installed and streaming
- [ ] IP addresses noted and configured
- [ ] Network stable (5GHz WiFi)
- [ ] Lighting adequate from all angles
- [ ] Camera views calibrated (if using 3D)
- [ ] Tested with actual CNC parts
- [ ] Frame rates acceptable on Raspberry Pi
- [ ] Backup camera enabled (redundancy)
- [ ] Auto-reconnect working for IP cameras

## Cost-Effective Alternatives

Don't have all these devices? Try:

1. **Multiple Webcams**: 3-4 USB webcams (~$20-30 each)
2. **Raspberry Pi Camera Modules**: Multiple Pi boards with cameras
3. **Old Android Phones**: Use as IP cameras (free!)
4. **Security Cameras**: IP cameras with RTSP streams

## Summary

Multi-camera setups provide significant advantages for CNC object detection:
- **Reliability**: Redundancy and failover
- **Accuracy**: Cross-validation and 3D positioning
- **Coverage**: No blind spots or occlusions
- **Flexibility**: Multiple workflows (quick check vs. detailed scan)

The investment in additional cameras pays off through:
- Reduced errors in pick-and-place
- Faster detection (parallel processing)
- Better handling of edge cases
- Professional-grade results
