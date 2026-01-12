# Gimbal Hardware Guide for CNCSorter

This guide covers the hardware requirements, assembly instructions, and wiring for the automated gimbal system that enables intelligent camera positioning in CNCSorter.

## Table of Contents
1. [Why Use a Gimbal?](#why-use-a-gimbal)
2. [Hardware Requirements](#hardware-requirements)
3. [3D Printed Parts](#3d-printed-parts)
4. [Wiring Diagrams](#wiring-diagrams)
5. [Assembly Instructions](#assembly-instructions)
6. [Calibration](#calibration)
7. [Usage Examples](#usage-examples)
8. [Troubleshooting](#troubleshooting)

---

## Why Use a Gimbal?

### Advantages Over Fixed Cameras
- **One Camera, Many Angles**: Replace 3-4 fixed cameras with 1 gimbal-mounted camera
- **Active 3D Scanning**: Programmatically capture views from optimal angles
- **Cost Reduction**: Less hardware = lower cost and complexity
- **Dynamic Coverage**: Automatically adjust to work piece size/position
- **Better for Small Parts**: Focus on specific areas with precision
- **Occlusion Resolution**: If blocked, move to alternate angle automatically

### Use Cases
1. **Full Bed Mapping**: Scan entire CNC bed from multiple angles
2. **Part Inspection**: Circle around objects for complete coverage
3. **Adaptive Detection**: Move to angles with best object visibility
4. **3D Reconstruction**: Capture calibrated views for 3D modeling
5. **Quality Control**: Systematic inspection from standardized angles

---

## Hardware Requirements

### Recommended Components

#### Option 1: Budget Build (2-Axis) - ~$25
Best for: Testing, small objects, overhead scanning

| Component | Specification | Quantity | Approx. Cost |
|-----------|---------------|----------|--------------|
| **Servo Motors** | SG90 (9g micro servo) | 2 | $6 |
| **Power Supply** | 5V 2A USB or DC adapter | 1 | $5 |
| **Wiring** | Jumper wires, breadboard | 1 set | $3 |
| **Hardware** | M3 screws, nuts, bearings | 1 set | $5 |
| **3D Printed Parts** | Pan/tilt mechanism | - | $6 (filament) |

**Notes**: 
- SG90 servos have limited torque (~1.8 kg⋅cm)
- Best for lightweight cameras (Webcam, Pi Camera)
- Not recommended for GoPro or iPhone without case

#### Option 2: Standard Build (2-Axis) - ~$45
Best for: Most applications, iPhone/GoPro support

| Component | Specification | Quantity | Approx. Cost |
|-----------|---------------|----------|--------------|
| **Servo Motors** | MG90S (metal gear, 13g) | 2 | $12 |
| **Power Supply** | 5V 3A DC adapter | 1 | $8 |
| **Buck Converter** | Step-down to 5V from 12V | 1 | $4 |
| **Wiring** | Jumper wires, breadboard | 1 set | $3 |
| **Hardware** | M3/M4 screws, bearings | 1 set | $8 |
| **3D Printed Parts** | Reinforced pan/tilt | - | $10 (filament) |

**Notes**:
- MG90S has higher torque (~2.2 kg⋅cm) and durability
- Metal gears reduce backlash and wear
- Handles iPhone, GoPro, and small webcams

#### Option 3: Pro Build (3-Axis) - ~$85
Best for: Professional setups, heavy cameras, roll stabilization

| Component | Specification | Quantity | Approx. Cost |
|-----------|---------------|----------|--------------|
| **Servo Motors** | MG996R (high-torque, 55g) | 3 | $30 |
| **Power Supply** | 6V 5A DC adapter | 1 | $15 |
| **Buck Converter** | Adjustable 5-6V output | 1 | $5 |
| **Wiring** | Heavy gauge wires, connectors | 1 set | $5 |
| **Hardware** | M4/M5 screws, ball bearings | 1 set | $15 |
| **3D Printed Parts** | 3-axis gimbal frame | - | $15 (filament) |

**Notes**:
- MG996R has excellent torque (~9.4 kg⋅cm at 6V)
- Supports roll axis for horizon stabilization
- Can handle heavier cameras (DSLR with lens cap removed)
- More complex assembly and calibration

### Servo Comparison

| Model | Torque (kg⋅cm) | Speed (sec/60°) | Weight (g) | Price | Best For |
|-------|----------------|-----------------|------------|-------|----------|
| SG90 | 1.8 @ 4.8V | 0.12 | 9 | $3 | Testing, Pi Camera |
| MG90S | 2.2 @ 4.8V | 0.10 | 13 | $6 | Webcam, iPhone |
| MG995 | 10 @ 4.8V | 0.20 | 55 | $10 | GoPro, heavy loads |
| MG996R | 11 @ 6V | 0.17 | 55 | $10 | Professional setups |

### Additional Hardware

**Required**:
- Raspberry Pi 4 (already in system)
- MicroSD card with Raspberry Pi OS
- Camera (Webcam, Pi Camera, iPhone, or GoPro)

**Recommended**:
- Ball bearings (608ZZ, 6mm ID) for smooth rotation
- Heat sinks for servos (reduces thermal drift)
- Cable management (zip ties, cable clips)
- Anti-vibration mounts (foam pads)

**Optional**:
- Position feedback (potentiometers or encoders)
- Slip rings (for 360° pan rotation)
- IMU sensor (MPU6050) for stabilization feedback

---

## 3D Printed Parts

### STL Files to Print

All STL files are in the `hardware/3d_prints/gimbal/` directory:

#### 2-Axis Gimbal (Budget/Standard)
1. **base_mount.stl** - Mounts to CNC or tripod
2. **pan_bracket.stl** - Holds pan servo and tilt mechanism
3. **tilt_bracket.stl** - Holds tilt servo and camera mount
4. **camera_platform.stl** - Universal camera mount with 1/4"-20 thread
5. **servo_horn_adapter.stl** - Connects servo horns to brackets

#### 3-Axis Gimbal (Pro)
1. **base_3axis.stl** - Heavy-duty base
2. **pan_assembly.stl** - Pan mechanism
3. **tilt_assembly.stl** - Tilt mechanism  
4. **roll_assembly.stl** - Roll mechanism
5. **camera_cage.stl** - Adjustable camera cage

### Print Settings

```
Material: PLA or PETG
Layer Height: 0.2mm
Infill: 30-50%
Supports: Yes (for overhangs)
Brim: Recommended for large parts
Print Speed: 50-60 mm/s
Temperature: PLA 200-210°C, PETG 230-240°C
```

**Tips**:
- PETG is stronger and more heat-resistant than PLA
- Use 100% infill for servo mounting holes
- Orient parts to minimize overhangs
- Print reinforcement ribs in the same orientation as stress

### Post-Processing
1. Remove support material carefully
2. Drill out servo mounting holes to 3mm (or tap for M3 threads)
3. Sand contact surfaces for smooth rotation
4. Apply lubricant to bearing surfaces (dry PTFE or silicone)

---

## Wiring Diagrams

### 2-Axis Gimbal Wiring

```
Raspberry Pi GPIO Layout (BCM Numbering):
┌─────────────────────────────────┐
│  3V3  (1) (2)  5V               │
│  GP2  (3) (4)  5V               │
│  GP3  (5) (6)  GND              │
│  GP4  (7) (8)  GP14             │
│  GND  (9) (10) GP15             │
│ GP17 (11) (12) GP18             │  ← Servo PWM pins
│ GP27 (13) (14) GND              │
│ GP22 (15) (16) GP23             │
│  3V3 (17) (18) GP24             │
│ GP10 (19) (20) GND              │
│  GP9 (21) (22) GP25             │
│ GP11 (23) (24) GP8              │
│  GND (25) (26) GP7              │
└─────────────────────────────────┘

Servo Connections:
Pan Servo (GP17):
  - Brown/Black wire → GND (Pin 9 or 20)
  - Red wire → 5V (External power supply)
  - Orange/Yellow wire → GP17 (Pin 11)

Tilt Servo (GP18):
  - Brown/Black wire → GND (Pin 9 or 20)
  - Red wire → 5V (External power supply)
  - Orange/Yellow wire → GP18 (Pin 12)

⚠️ IMPORTANT: Do NOT power servos from Pi's 5V pins!
   Use external 5V power supply with common ground.
```

### Power Supply Wiring

```
External 5V Power Supply:
┌──────────────┐
│   5V 2-3A    │
│   DC Adapter │
└──────┬───────┘
       │
       ├──────────┬──────────────┐
       │          │              │
    (+5V)      (GND)          (GND)
       │          │              │
       │          └──────────────┴─→ Raspberry Pi GND (Pin 9)
       │
       ├─→ Pan Servo (Red wire)
       └─→ Tilt Servo (Red wire)

Common Ground Connection is ESSENTIAL!
```

### 3-Axis Gimbal Wiring

Add the roll servo:
```
Roll Servo (GP27):
  - Brown/Black wire → GND (Pin 14)
  - Red wire → 5V (External power supply)
  - Orange/Yellow wire → GP27 (Pin 13)
```

### Safety Notes
- **Never** connect servo power wires to Pi's 5V output (insufficient current, risk of damage)
- Always use external power supply rated for at least 1A per servo
- Ensure common ground between Pi and external power supply
- Add a 1000µF capacitor across power supply for servo current spikes
- Use 22-24 AWG wire for power connections
- Consider adding a fuse (2A fast-blow) on power supply line

---

## Assembly Instructions

### 2-Axis Gimbal Assembly

#### Step 1: Base Mount
1. Secure `base_mount.stl` to CNC frame or tripod
2. Use M4 or M5 bolts depending on mounting surface
3. Ensure mount is level and stable

#### Step 2: Pan Mechanism
1. Insert pan servo into `pan_bracket.stl`
2. Secure servo with M3 screws (don't overtighten)
3. Attach servo horn to output shaft
4. Connect `servo_horn_adapter.stl` to horn
5. Mount pan bracket to base with M4 bolt through center
6. Test free rotation (should be smooth, no binding)

#### Step 3: Tilt Mechanism
1. Insert tilt servo into `tilt_bracket.stl`
2. Secure servo with M3 screws
3. Attach tilt bracket to pan bracket using servo horn adapter
4. Ensure tilt axis is perpendicular to pan axis

#### Step 4: Camera Mount
1. Attach `camera_platform.stl` to tilt bracket
2. If using webcam: Use webcam's built-in clip/mount
3. If using Pi Camera: Use M2.5 screws through camera mounting holes
4. If using iPhone/GoPro: Use phone holder with 1/4"-20 adapter

#### Step 5: Wiring
1. Route servo wires down through gimbal structure
2. Use cable clips or zip ties to prevent snagging
3. Connect servos to GPIO pins (see wiring diagram)
4. Connect external power supply
5. Double-check all connections before powering on

#### Step 6: Cable Management
1. Leave slack for full range of motion
2. Test pan and tilt movements manually before powering
3. Secure cables with adhesive cable clips
4. Use spiral wrap or braided sleeve for protection

### 3-Axis Gimbal Assembly

Similar to 2-axis, with additional roll mechanism between tilt and camera platform. Requires more precise alignment and balancing.

---

## Calibration

### Initial Calibration

1. **Power On**:
   ```bash
   cd /path/to/CNCSorter
   python3 src/infrastructure/gimbal_test.py
   ```

2. **Center Servos**:
   - Gimbal should move to center position (0°, 0°, 0°)
   - Verify camera is level and facing forward
   - If not, adjust servo horn positions

3. **Test Range of Motion**:
   ```python
   from src.infrastructure.gimbal_controller import TwoAxisGimbal
   
   gimbal = TwoAxisGimbal(pan_pin=17, tilt_pin=18)
   
   # Test pan
   gimbal.move_to(GimbalPosition(pan=-90, tilt=0))
   gimbal.move_to(GimbalPosition(pan=90, tilt=0))
   
   # Test tilt
   gimbal.move_to(GimbalPosition(pan=0, tilt=-90))
   gimbal.move_to(GimbalPosition(pan=0, tilt=90))
   ```

4. **Fine-Tune Limits**:
   - If servos bind at extremes, reduce limits in code:
   ```python
   gimbal = TwoAxisGimbal(
       pan_limits=(-80, 80),  # Reduce from (-90, 90)
       tilt_limits=(-80, 80)
   )
   ```

5. **Save Calibration**:
   - Note any offset corrections needed
   - Update default parameters in your code

### Camera Alignment

1. **Level Check**: Place gimbal at (0°, 0°) and verify camera is level
2. **Centering**: Verify camera points at CNC bed center when at (0°, -45°)
3. **Offset Correction**: If camera is off-center, adjust mounting or add software offset

---

## Usage Examples

### Example 1: Basic Control

```python
from src.infrastructure.gimbal_controller import TwoAxisGimbal, GimbalPosition

# Initialize gimbal
gimbal = TwoAxisGimbal(pan_pin=17, tilt_pin=18)

# Move to specific position
gimbal.move_to(GimbalPosition(pan=45, tilt=-60))

# Use preset positions
gimbal.move_to_preset("overhead")
gimbal.move_to_preset("front")
gimbal.move_to_preset("left")

# Return to center
gimbal.center()

# Clean up
gimbal.cleanup()
```

### Example 2: Panorama Scan

```python
from src.infrastructure.gimbal_controller import TwoAxisGimbal, AutomatedScanController

gimbal = TwoAxisGimbal(pan_pin=17, tilt_pin=18)
scanner = AutomatedScanController(gimbal)

# Scan at -45° tilt, from -90° to +90° pan, 7 steps
positions = gimbal.panorama_scan(
    tilt=-45,
    pan_range=(-90, 90),
    steps=7,
    dwell_time=1.5
)

print(f"Captured {len(positions)} positions")
```

### Example 3: Integrated with Vision System

```python
from src.infrastructure.gimbal_controller import TwoAxisGimbal, AutomatedScanController
from src.infrastructure.vision import VisionSystem
from src.domain.entities import CNCCoordinate

# Initialize systems
gimbal = TwoAxisGimbal(pan_pin=17, tilt_pin=18)
vision = VisionSystem(camera_index=0)
scanner = AutomatedScanController(gimbal)

# Define detection callback
def detect_objects():
    frame = vision.get_frame()
    objects = vision.detect_objects(frame)
    return len(objects)

# Adaptive scan - focuses on areas with objects
positions = scanner.adaptive_scan(
    initial_positions=[
        GimbalPosition(pan=-60, tilt=-45),
        GimbalPosition(pan=0, tilt=-45),
        GimbalPosition(pan=60, tilt=-45),
    ],
    detection_callback=detect_objects,
    threshold=3  # Trigger detailed scan if 3+ objects detected
)

# Return to best viewing angle
best_pos = scanner.return_to_best_position()
print(f"Best position: {best_pos}")

# Cleanup
vision.release()
gimbal.cleanup()
```

### Example 4: Full Bed Mapping

```python
from src.infrastructure.gimbal_controller import TwoAxisGimbal, AutomatedScanController
from src.application.bed_mapping import BedMappingService
from src.infrastructure.vision import VisionSystem, ImageStitcher
from src.infrastructure.cnc_controller import FluidNCSerial

# Initialize all systems
gimbal = TwoAxisGimbal(pan_pin=17, tilt_pin=18)
vision = VisionSystem(camera_index=0)
cnc = FluidNCSerial(port='/dev/ttyUSB0')
stitcher = ImageStitcher()
mapper = BedMappingService(vision, cnc, stitcher)
scanner = AutomatedScanController(gimbal)

# Start new bed map
bed_map = mapper.start_new_map()

# Full coverage scan
scan_positions = scanner.full_coverage_scan(
    tilt_angles=[-90, -60, -30],
    pan_range=(-75, 75),
    pan_steps=5
)

# Capture image at each position
for position in scan_positions:
    gimbal.move_to(position)
    time.sleep(0.5)  # Stabilization
    mapper.capture_and_add_image()  # Captures with CNC coordinate

# Stitch images
mapper.stitch_current_map()
mapper.save_map_images(output_dir="./bed_maps")

# Cleanup
gimbal.cleanup()
vision.release()
cnc.disconnect()
```

---

## Troubleshooting

### Servo Jitter/Vibration
**Symptoms**: Servo oscillates or vibrates at target position
**Solutions**:
- Add 1000µF capacitor across power supply
- Check power supply can provide sufficient current
- Reduce movement speed
- Add small delay after movement
- Check for mechanical binding

### Insufficient Torque
**Symptoms**: Servo can't hold position, droops under load
**Solutions**:
- Upgrade to higher torque servos (MG996R)
- Increase voltage to 6V (check servo specs)
- Reduce camera weight
- Add counterweight for balance
- Check for mechanical friction

### Erratic Movement
**Symptoms**: Servo moves unpredictably or to wrong positions
**Solutions**:
- Verify power supply voltage and current
- Check PWM signal wiring (no loose connections)
- Ensure common ground between Pi and servos
- Update RPi.GPIO library: `pip install --upgrade RPi.GPIO`
- Add signal filtering capacitor (0.1µF on servo signal line)

### Position Drift
**Symptoms**: Gimbal slowly drifts from commanded position
**Solutions**:
- Calibrate servo center position
- Check mechanical friction/binding
- Add position feedback (encoder or potentiometer)
- Increase servo hold torque (higher voltage)
- Balance camera weight evenly

### GPIO Errors
**Symptoms**: `RuntimeError: Not running on a RPi` or GPIO warnings
**Solutions**:
- Verify running on Raspberry Pi (not desktop)
- Run with `sudo` if needed: `sudo python3 script.py`
- Check GPIO permissions: `sudo adduser $USER gpio`
- Log out and back in after adding to gpio group
- Verify BCM pin numbers (not BOARD numbers)

### Overheating Servos
**Symptoms**: Servos get hot, lose accuracy, or burn out
**Solutions**:
- Add heat sinks to servo bodies
- Improve airflow around servos
- Reduce holding time at positions
- Use "park" mode when idle (slight reduction in duty cycle)
- Upgrade to metal-gear servos (better heat dissipation)

### Camera Shake
**Symptoms**: Images are blurry due to vibration
**Solutions**:
- Add stabilization delay after movement (0.5-1.0 seconds)
- Use slower movement speeds
- Add anti-vibration mounts (foam pads)
- Increase gimbal structural rigidity
- Use camera with image stabilization

---

## Advanced Features

### Position Feedback
Add a potentiometer or rotary encoder for closed-loop control:
```python
import RPi.GPIO as GPIO

# Read position from potentiometer via ADC
def read_position():
    # Using MCP3008 ADC
    import spidev
    spi = spidev.SpiDev()
    spi.open(0, 0)
    adc = spi.xfer2([1, (8 + 0) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data * 180 / 1023  # Convert to degrees
```

### IMU Integration
Use an IMU (e.g., MPU6050) for tilt sensing and stabilization:
```python
from mpu6050 import mpu6050

imu = mpu6050(0x68)
accel_data = imu.get_accel_data()

# Calculate tilt angle
import math
tilt = math.atan2(accel_data['y'], accel_data['z']) * 180 / math.pi
```

### Slip Ring for 360° Rotation
For continuous pan rotation (no cable wrapping):
- Install slip ring between pan base and rotating platform
- Allows unlimited rotation in either direction
- Useful for continuous surveillance or automated scanning

---

## Next Steps

1. **Print Components**: Start with 2-axis budget build
2. **Order Hardware**: See hardware list above
3. **Assemble**: Follow assembly instructions
4. **Test**: Run `gimbal_test.py` for basic testing
5. **Integrate**: Add gimbal to your CNCSorter workflow
6. **Optimize**: Fine-tune positioning for your specific CNC setup

For questions or issues, refer to the [GitHub Issues](https://github.com/keithjasper83/CNCSorter/issues) page.
