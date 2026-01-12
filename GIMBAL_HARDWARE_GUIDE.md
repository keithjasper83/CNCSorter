# Gimbal Hardware Guide for CNCSorter

This guide covers the hardware requirements, assembly instructions, and wiring for the automated gimbal system that enables intelligent camera positioning in CNCSorter.

## Table of Contents
1. [Why Use a Gimbal?](#why-use-a-gimbal)
2. [Hardware Requirements](#hardware-requirements)
3. [3D Printed Parts](#3d-printed-parts)
4. [Wiring Diagrams](#wiring-diagrams)
5. [Assembly Instructions](#assembly-instructions)
6. [Slip Ring for 360° Rotation](#slip-ring-for-360-rotation)
7. [Gyroscope Stabilization](#gyroscope-stabilization-optional-enhancement)
8. [Calibration](#calibration)
9. [Usage Examples](#usage-examples)
10. [Troubleshooting](#troubleshooting)

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

For unlimited continuous pan rotation without cable wrapping, a slip ring is essential for professional setups.

#### Recommended Slip Rings

**Option 1: 12-Wire Miniature Slip Ring (PRIMARY RECOMMENDATION)** - £15-20
- **Model**: The Pi Hut Miniature Slip Ring (12mm diameter, 12 wires)
- **Product Link**: https://thepihut.com/products/miniature-slip-ring-12mm-diameter-12-wires-max-240v-2a
- **Specifications**:
  - Diameter: 12mm (most compact option!)
  - Height: 20mm  
  - Circuits: 12 wires (28 AWG, color coded)
  - Current: 2A per circuit (240VAC/DC max)
  - Contact Resistance: < 0.01Ω (gold plated contacts)
  - Rotation Speed: 0-300 RPM (can go faster with reduced lifespan)
  - Operating Temperature: -20°C to +80°C
  - Lifespan: >10 million rotations
- **Perfect for**: Production builds with gyro stabilization and multi-camera
- **Why Best**: Ultra-compact, 12 circuits for expansion, excellent quality, UK supplier
- **Cost**: £15-20 from The Pi Hut (UK)

**Option 2: 6-Wire Miniature Slip Ring** - $15-25
- **Model**: MT0615 or similar (6 circuits, 15mm bore)
- **Specifications**:
  - Diameter: 15mm
  - Height: 20mm  
  - Circuits: 6 wires
  - Current: 2A per circuit (240V max)
  - Contact Resistance: < 0.01Ω
- **Perfect for**: Basic 2-axis gimbal without extras
- **Cost**: $15-20 on Amazon/AliExpress

**Option 3: 12-Wire Standard Slip Ring** - $25-35
- **Model**: MT1212 or similar (12 circuits, 22mm bore)
- **Specifications**:
  - Diameter: 22mm (larger)
  - Height: 25mm
  - Circuits: 12 wires
  - Current: 2A per circuit
- **Perfect for**: Builds where size isn't constrained
- **Cost**: $25-30 on Amazon/AliExpress

#### Wire Allocation (12-Circuit Slip Ring - Recommended)

**The Pi Hut 12-wire model provides maximum flexibility:**

**Core Servo Circuits** (6 wires):
1. **Circuit 1**: Servo power (+5V) - Red
2. **Circuit 2**: Ground (GND) - Black  
3. **Circuit 3**: Pan servo signal (PWM) - Orange
4. **Circuit 4**: Tilt servo signal (PWM) - Yellow
5. **Circuit 5**: Roll servo signal (PWM) - Optional, for 3-axis
6. **Circuit 6**: Common ground return - Black/Brown

**Gyroscope/Sensor Circuits** (4 wires):
7. **Circuit 7**: Gyro power (3.3V) - Red/White
8. **Circuit 8**: Gyro ground (GND) - Black/White
9. **Circuit 9**: I2C SDA (data) - Green
10. **Circuit 10**: I2C SCL (clock) - Blue

**Camera/Expansion Circuits** (2 wires):
11. **Circuit 11**: Camera power (5V) or LED ring - White
12. **Circuit 12**: Camera data or spare - Gray

**Benefits of 12-wire configuration**:
- All servos powered independently
- Dedicated gyro circuits for stabilization
- Camera power without voltage drop
- Future expansion (LED ring, encoders, additional sensors)

#### Wire Allocation (6-Circuit Slip Ring)

For budget builds using 6-wire slip rings:
1. **Circuit 1**: Servo power (+5V) - Red
2. **Circuit 2**: Ground (GND) - Black
3. **Circuit 3**: Pan servo signal (PWM) - Orange
4. **Circuit 4**: Tilt servo signal (PWM) - Yellow
5. **Circuit 5**: Camera power (optional) - Green
6. **Circuit 6**: Spare/Camera data - Blue

**Note**: 6-wire limits you to 2-axis without gyro. For gyro stabilization, use 12-wire model.

For multi-camera or lighting:
- Use 12-circuit slip ring with additional circuits for:
  - LED ring power and control
  - Secondary camera power/data
  - IMU sensor data lines
  - Spare circuits for future expansion

#### 3D Print Integration

**Mounting Design**:
The slip ring mounts between the gimbal base and the pan rotating platform. Updated STL files include:

1. **slip_ring_mount_base.stl** - Stationary side mounts to base
2. **slip_ring_mount_rotor.stl** - Rotating side mounts to pan bracket
3. **slip_ring_housing.stl** - Protective cover with cable channels

**Print Settings**:
```
Material: PETG (better for slip ring heat)
Layer Height: 0.2mm
Infill: 50% (needs strength for bearing load)
Supports: Yes (for cable channels)
Walls: 4 perimeters for rigidity
```

**Design Features**:
- Precision bore for 15mm slip ring (or 22mm for 12-wire)
- Integrated ball bearing seat (608ZZ bearing)
- Cable management channels
- M3 mounting holes (4×) for slip ring flange
- Central shaft passage for strength
- Snap-fit protective cover

#### Installation Steps

1. **Prepare Slip Ring**:
   - Note which side is stationary vs. rotating
   - Most slip rings have color-coded wire sets
   - Test continuity before installation

2. **Mount Stationary Side**:
   - Insert slip ring into `slip_ring_mount_base.stl`
   - Secure with M3 screws through mounting holes
   - Mount base to gimbal base platform
   - Connect stationary wires to Raspberry Pi GPIO

3. **Mount Rotating Side**:
   - Attach `slip_ring_mount_rotor.stl` to pan bracket
   - Ensure concentric alignment with stationary side
   - Connect rotating wires to servos and camera

4. **Wire Routing**:
   - **Stationary Side**: Route wires through base to Pi
   - **Rotating Side**: Route through cable channels in pan bracket
   - Leave slack for smooth rotation
   - Use cable clips to prevent snagging

5. **Test Rotation**:
   - Manually rotate pan bracket 360°
   - Check for binding or wire interference
   - Verify electrical continuity through full rotation
   - Test with multimeter: resistance should stay constant

6. **Install Housing**:
   - Snap protective cover over slip ring
   - Secures cables and prevents dust ingress

#### Wiring Diagram with Slip Ring

```
External 5V Power Supply
         |
         ├─→ Slip Ring (Stationary) Circuit 1 (5V)
         │      ↓
         │   Slip Ring (Rotating) Circuit 1
         │      ↓
         │   ├─→ Pan Servo (Red)
         │   └─→ Tilt Servo (Red)
         │
         └─→ Raspberry Pi GND ←─ Slip Ring Circuit 2 (GND)
                                       ↓
                                  Slip Ring (Rotating) Circuit 2
                                       ↓
                                  ├─→ Pan Servo (Black)
                                  └─→ Tilt Servo (Black)

Raspberry Pi GPIO:
   GP17 (Pin 11) → Slip Ring Circuit 3 → Pan Servo (Orange)
   GP18 (Pin 12) → Slip Ring Circuit 4 → Tilt Servo (Yellow)
```

#### Benefits of Slip Ring

- **Unlimited Pan Rotation**: No 180° limits or homing required
- **No Cable Twist**: Wires never wrap around base
- **Continuous Scanning**: Perfect for surveillance or 360° mapping
- **Professional Appearance**: Clean cable management
- **Reliability**: Millions of rotations rated
- **Easy Maintenance**: Replaceable if worn

#### Alternatives to Slip Ring

If slip ring is not available:
1. **Limited Rotation**: Restrict pan to ±90° or ±135°
2. **Homing Routine**: Return to 0° periodically to unwind cables
3. **Wireless Power**: Battery-powered servos on rotating platform
4. **Wireless Control**: Bluetooth/WiFi control module (adds complexity)

**Not Recommended**: Cable spiral wrap alone - causes tension and wear

#### Troubleshooting Slip Ring Issues

**High Resistance/Intermittent Connection**:
- Clean contacts with isopropyl alcohol
- Check wire crimps are secure
- Replace if resistance > 0.05Ω

**Noise on Signal Lines**:
- Add 0.1µF capacitor between signal and ground
- Use shielded cable for PWM signals
- Ensure proper ground connection

**Mechanical Binding**:
- Check alignment of stationary and rotating sides
- Verify ball bearing is seated correctly
- Lubricate slip ring bearing lightly

**Overheating**:
- Verify current draw is within spec (< 2A per circuit)
- Check for short circuits
- Improve ventilation around slip ring

---

## Gyroscope Stabilization (Optional Enhancement)

### Overview

Adding a gyroscope sensor enables automatic horizon leveling and vibration compensation, crucial for high-quality image capture on CNC machines with moving parts.

### Recommended Gyroscopes

**MPU6050 (Budget Option)** - £3-5
- 3-axis gyroscope + 3-axis accelerometer
- I2C interface (easy Pi integration)
- ±250 to ±2000°/s gyro range
- Built-in temperature sensor
- Perfect for: Basic horizon leveling

**MPU9250 (Advanced Option)** - £8-12
- 9-axis: gyro + accelerometer + magnetometer
- Better accuracy than MPU6050
- Compass for absolute heading
- Perfect for: Precise orientation tracking

**BNO055 (Professional Option)** - £15-20
- 9-axis with built-in sensor fusion
- Hardware-based orientation calculation
- Quaternion output (no gimbal lock)
- Perfect for: Production systems requiring high accuracy

### Features Enabled by Gyroscope

1. **Horizon Leveling**: Automatically compensate for CNC bed tilt
2. **Vibration Damping**: Filter out machine vibrations in real-time
3. **Drift Correction**: Maintain stable camera orientation during long operations
4. **Active Stabilization**: Servo-based compensation for movement
5. **Absolute Positioning**: Know exact camera orientation at all times

### Wiring (I2C Connection)

**With 12-wire Slip Ring** (Recommended):
```
MPU6050/MPU9250:
   VCC  → Slip Ring Circuit 7  → Pi 3.3V (Pin 1)
   GND  → Slip Ring Circuit 8  → Pi GND (Pin 6)
   SDA  → Slip Ring Circuit 9  → Pi GPIO 2 (Pin 3)
   SCL  → Slip Ring Circuit 10 → Pi GPIO 3 (Pin 5)
```

**Without Slip Ring** (Fixed Mount):
- Mount gyro on gimbal base (non-rotating)
- Direct connection to Pi I2C pins
- No slip ring circuits needed

### Software Integration

The gyro data can be read via I2C and used to adjust servo positions:

```python
from infrastructure.gimbal_controller import TwoAxisGimbal
from infrastructure.gyro_stabilizer import GyroStabilizer

# Initialize gimbal and gyro
gimbal = TwoAxisGimbal(pan_pin=17, tilt_pin=18)
stabilizer = GyroStabilizer(i2c_address=0x68)  # MPU6050 default

# Enable auto-leveling
stabilizer.enable_auto_level()

while True:
    # Read gyro orientation
    pitch, roll, yaw = stabilizer.get_orientation()
    
    # Compensate gimbal position
    gimbal.set_tilt(target_tilt + pitch)  # Correct for pitch
    gimbal.set_roll(target_roll + roll)    # Correct for roll (3-axis only)
    
    time.sleep(0.01)  # 100Hz update rate
```

### Mounting Location

**Rotating Platform** (requires slip ring):
- Measures actual camera orientation
- Best for active stabilization
- Requires 4 slip ring circuits

**Gimbal Base** (no slip ring needed):
- Measures machine/base vibration
- Good for drift correction
- Simpler wiring

### Calibration

1. **Place gimbal on level surface**
2. **Run calibration script**:
```bash
python src/gyro_calibrate.py
```
3. **Record zero position offsets**
4. **Test with known tilt angles**

### Benefits

✅ **Image Quality**: Sharper images from vibration compensation
✅ **Consistency**: Repeatable orientations across sessions
✅ **Flexibility**: Works on unlevel CNC beds
✅ **Professionalism**: Active stabilization like commercial gimbals
✅ **Future-Proof**: Foundation for advanced features (object tracking, etc.)

### Integration with CNCSorter

The gyroscope data can be logged alongside detection data:
- Track camera orientation for each capture
- Enable 3D reconstruction with known angles
- Verify gimbal positioning accuracy
- Detect mechanical issues (drift, binding)

---

## Troubleshooting

### Import Error When Running Code

**Error**: `ModuleNotFoundError: No module named 'src'`

**Problem**: Running `python3 main.py` from inside the `src/` directory.

**Solution**: Always run from the repository root:

```bash
# ❌ Wrong (from inside src/ directory):
cd CNCSorter/src
python3 main.py

# ✅ Correct (from repository root):
cd CNCSorter
python3 -m src.main

# ✅ Or use the launcher scripts:
./run.sh          # Mac/Linux
./run_rpi.sh      # Raspberry Pi
run.bat           # Windows
./run_gui.sh      # Touchscreen GUI
```

The code uses absolute imports (`from src.infrastructure...`) which require running as a module from the parent directory.

---

## Next Steps

1. **Print Components**: Start with 2-axis budget build
2. **Order Hardware**: See hardware list above
3. **Assemble**: Follow assembly instructions
4. **Test**: Run `gimbal_test.py` for basic testing
5. **Integrate**: Add gimbal to your CNCSorter workflow
6. **Optimize**: Fine-tune positioning for your specific CNC setup

For questions or issues, refer to the [GitHub Issues](https://github.com/keithjasper83/CNCSorter/issues) page.
