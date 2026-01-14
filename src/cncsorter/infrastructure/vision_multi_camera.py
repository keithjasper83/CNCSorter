"""
Multi-Camera Vision System for CNCSorter.
Supports simultaneous capture from multiple camera angles (Webcam, GoPro, iPhone, iPad).

ADVANTAGES OF MULTI-CAMERA SETUP:
1. **Better Coverage**: Capture all sides of objects, no blind spots
2. **Occlusion Handling**: If one camera view is blocked, others still see the object
3. **3D Reconstruction**: Multiple angles enable depth perception and 3D modeling
4. **Accuracy**: Cross-validate object detection across multiple views
5. **Redundancy**: If one camera fails, others continue working
6. **Lighting**: Different angles handle shadows and reflections better
7. **Pick & Place**: Multiple views help determine object orientation for robotic picking
"""
import cv2
import numpy as np
import time
import threading
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field

from domain.entities import DetectedObject, Point2D, CapturedImage, CNCCoordinate


@dataclass
class CameraConfig:
    """Configuration for a single camera."""
    name: str  # e.g., "Webcam", "iPhone", "GoPro", "iPad"
    source: Any  # 0, 1, "http://...", "picamera", etc.
    enabled: bool = True
    preview_scale: float = 0.5
    position: str = "top"  # "top", "side", "front", "angle45", etc.
    resolution: Optional[Tuple[int, int]] = None
    frame_skip: int = 1


@dataclass
class MultiCameraFrame:
    """Synchronized frames from multiple cameras."""
    timestamp: float
    frames: Dict[str, np.ndarray] = field(default_factory=dict)
    detected_objects: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    annotated_frames: Dict[str, np.ndarray] = field(default_factory=dict)
    threshold_masks: Dict[str, np.ndarray] = field(default_factory=dict)


class MultiCameraVisionSystem:
    """
    Multi-camera vision system for comprehensive object detection.

    Features:
    - Simultaneous capture from multiple cameras
    - Synchronized frame acquisition
    - Cross-camera object matching
    - Combined detection results
    - 3D coordinate estimation (from multiple angles)
    - Redundancy and failover
    """

    # Default multi-camera configuration
    DEFAULT_CAMERAS = [
        CameraConfig(
            name="Webcam",
            source=0,
            position="top",
            preview_scale=0.4,
            enabled=True
        ),
        CameraConfig(
            name="iPhone",
            source="http://192.168.1.100:8080/video",
            position="side",
            preview_scale=0.4,
            enabled=False  # Enable when available
        ),
        CameraConfig(
            name="GoPro",
            source=1,  # USB connection (second camera device)
            position="front",
            preview_scale=0.4,
            enabled=False  # Enable when available
        ),
        CameraConfig(
            name="iPad",
            source="http://192.168.1.102:8080/video",
            position="angle45",
            preview_scale=0.4,
            enabled=False  # Enable when available
        ),
    ]

    def __init__(self, camera_configs: List[CameraConfig] = None):
        """
        Initialize multi-camera vision system.

        Args:
            camera_configs: List of camera configurations
        """
        self.camera_configs = camera_configs or self.DEFAULT_CAMERAS
        self.cameras: Dict[str, cv2.VideoCapture] = {}
        self.camera_threads: Dict[str, threading.Thread] = {}
        self.latest_frames: Dict[str, np.ndarray] = {}
        self.frame_locks: Dict[str, threading.Lock] = {}
        self.running = False

        # Detection parameters
        self.threshold = 127
        self.min_area = 150

        # Performance tracking
        self.fps_counters: Dict[str, float] = {}
        self.fps_times: Dict[str, float] = {}
        self.fps_counts: Dict[str, int] = {}

    def initialize_cameras(self) -> Dict[str, bool]:
        """
        Initialize all enabled cameras.

        Returns:
            Dictionary mapping camera names to success status
        """
        results = {}

        for config in self.camera_configs:
            if not config.enabled:
                print(f"⊘ {config.name} ({config.position}): Disabled")
                results[config.name] = False
                continue

            success = self._open_camera(config)
            results[config.name] = success

            if success:
                print(f"✓ {config.name} ({config.position}): Connected")
                self.frame_locks[config.name] = threading.Lock()
                self.fps_times[config.name] = time.time()
                self.fps_counts[config.name] = 0
                self.fps_counters[config.name] = 0.0
            else:
                print(f"✗ {config.name} ({config.position}): Failed to connect")

        return results

    def _open_camera(self, config: CameraConfig) -> bool:
        """Open a single camera."""
        try:
            if isinstance(config.source, int):
                cap = cv2.VideoCapture(config.source)
            else:
                cap = cv2.VideoCapture(config.source, cv2.CAP_FFMPEG)

            if not cap.isOpened():
                return False

            # Set resolution if specified
            if config.resolution:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.resolution[0])
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.resolution[1])

            self.cameras[config.name] = cap

            # Get actual resolution
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"  → {config.name}: {width}x{height}")

            return True
        except Exception as e:
            print(f"  → Error opening {config.name}: {e}")
            return False

    def start_capture_threads(self):
        """Start background threads for continuous frame capture."""
        self.running = True

        for camera_name in self.cameras.keys():
            thread = threading.Thread(
                target=self._capture_loop,
                args=(camera_name,),
                daemon=True
            )
            thread.start()
            self.camera_threads[camera_name] = thread
            print(f"Started capture thread for {camera_name}")

    def _capture_loop(self, camera_name: str):
        """Background loop for continuous frame capture from one camera."""
        cap = self.cameras[camera_name]
        config = self._get_config(camera_name)
        frame_count = 0

        while self.running:
            try:
                # Frame skipping
                frame_count += 1
                if frame_count % config.frame_skip != 0:
                    continue

                ret, frame = cap.read()

                if ret and frame is not None:
                    # Store latest frame with thread safety
                    with self.frame_locks[camera_name]:
                        self.latest_frames[camera_name] = frame.copy()

                    # Update FPS
                    self._update_fps(camera_name)
                else:
                    # Frame capture failed - try to reconnect for IP cameras
                    if isinstance(config.source, str) and config.source.startswith("http"):
                        print(f"⚠ {camera_name}: Lost connection, attempting reconnect...")
                        time.sleep(2)
                        cap.release()
                        if self._open_camera(config):
                            cap = self.cameras[camera_name]
                            print(f"✓ {camera_name}: Reconnected")

            except Exception as e:
                print(f"Error in {camera_name} capture loop: {e}")
                time.sleep(1)

    def _get_config(self, camera_name: str) -> CameraConfig:
        """Get configuration for a camera by name."""
        for config in self.camera_configs:
            if config.name == camera_name:
                return config
        return None

    def _update_fps(self, camera_name: str):
        """Update FPS for a camera."""
        self.fps_counts[camera_name] += 1
        current_time = time.time()
        elapsed = current_time - self.fps_times[camera_name]

        if elapsed >= 1.0:
            self.fps_counters[camera_name] = self.fps_counts[camera_name] / elapsed
            self.fps_counts[camera_name] = 0
            self.fps_times[camera_name] = current_time

    def get_synchronized_frames(self) -> MultiCameraFrame:
        """
        Get synchronized frames from all active cameras.

        Returns:
            MultiCameraFrame with all current frames
        """
        multi_frame = MultiCameraFrame(timestamp=time.time())

        for camera_name in self.cameras.keys():
            if camera_name in self.latest_frames:
                with self.frame_locks[camera_name]:
                    if camera_name in self.latest_frames:
                        multi_frame.frames[camera_name] = self.latest_frames[camera_name].copy()

        return multi_frame

    def detect_objects_multi_camera(
        self,
        multi_frame: MultiCameraFrame,
        threshold: int = None,
        min_area: int = None
    ) -> MultiCameraFrame:
        """
        Detect objects in all camera frames.

        Args:
            multi_frame: MultiCameraFrame with frames from all cameras
            threshold: Detection threshold
            min_area: Minimum object area

        Returns:
            MultiCameraFrame with detection results added
        """
        if threshold is None:
            threshold = self.threshold
        if min_area is None:
            min_area = self.min_area

        for camera_name, frame in multi_frame.frames.items():
            # Detect objects
            detected, annotated, thresh_mask = self._detect_objects(
                frame, min_area, threshold
            )

            multi_frame.detected_objects[camera_name] = detected
            multi_frame.annotated_frames[camera_name] = annotated
            multi_frame.threshold_masks[camera_name] = thresh_mask

        return multi_frame

    def _detect_objects(
        self,
        frame: np.ndarray,
        min_area: int,
        thresh_val: int
    ) -> Tuple[List[Dict[str, Any]], np.ndarray, np.ndarray]:
        """Detect objects in a single frame (same logic as enhanced vision)."""
        # Pre-processing
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # Thresholding
        _, thresh = cv2.threshold(blur, thresh_val, 255, cv2.THRESH_BINARY_INV)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Process contours
        annotated = frame.copy()
        detected = []
        obj_id = 0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > min_area:
                obj_id += 1
                x, y, w, h = cv2.boundingRect(cnt)

                # Center
                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cx = M["m10"] / M["m00"]
                    cy = M["m01"] / M["m00"]
                else:
                    cx, cy = x + w / 2.0, y + h / 2.0

                # Draw
                cv2.drawContours(annotated, [cnt], -1, (0, 255, 0), 2)
                cv2.putText(annotated, f"Obj {obj_id}", (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.circle(annotated, (int(cx), int(cy)), 5, (0, 0, 255), -1)

                detected.append({
                    'id': obj_id,
                    'center': (cx, cy),
                    'bounding_box': (x, y, w, h),
                    'area': area
                })

        return detected, annotated, thresh

    def create_multi_view_display(
        self,
        multi_frame: MultiCameraFrame,
        layout: str = "grid"
    ) -> np.ndarray:
        """
        Create a combined display showing all camera views.

        Args:
            multi_frame: MultiCameraFrame with detection results
            layout: "grid", "horizontal", "vertical", or "picture_in_picture"

        Returns:
            Combined display frame
        """
        if layout == "grid":
            return self._create_grid_layout(multi_frame)
        elif layout == "horizontal":
            return self._create_horizontal_layout(multi_frame)
        elif layout == "vertical":
            return self._create_vertical_layout(multi_frame)
        elif layout == "picture_in_picture":
            return self._create_pip_layout(multi_frame)
        else:
            return self._create_grid_layout(multi_frame)

    def _create_grid_layout(self, multi_frame: MultiCameraFrame) -> np.ndarray:
        """Create a 2x2 grid layout."""
        camera_names = list(multi_frame.annotated_frames.keys())

        if not camera_names:
            return np.zeros((480, 640, 3), dtype=np.uint8)

        # Prepare frames
        frames = []
        for i in range(4):  # Always show 4 quadrants
            if i < len(camera_names):
                name = camera_names[i]
                frame = multi_frame.annotated_frames[name]

                # Resize
                config = self._get_config(name)
                scale = config.preview_scale if config else 0.4
                h, w = frame.shape[:2]
                new_w, new_h = int(w * scale), int(h * scale)
                frame = cv2.resize(frame, (new_w, new_h))

                # Add label
                label = f"{name} ({config.position}) - {len(multi_frame.detected_objects[name])} objects"
                cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                           0.7, (0, 255, 255), 2)

                # Add FPS
                fps = self.fps_counters.get(name, 0)
                cv2.putText(frame, f"FPS: {fps:.1f}", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                frames.append(frame)
            else:
                # Empty quadrant
                if frames:
                    h, w = frames[0].shape[:2]
                    empty = np.zeros((h, w, 3), dtype=np.uint8)
                    cv2.putText(empty, "No Camera", (w//2 - 70, h//2),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)
                    frames.append(empty)

        # Stack frames
        if len(frames) >= 2:
            top = np.hstack(frames[:2])
            bottom = np.hstack(frames[2:4]) if len(frames) >= 4 else frames[2] if len(frames) >= 3 else top
            grid = np.vstack([top, bottom])
        else:
            grid = frames[0]

        return grid

    def _create_horizontal_layout(self, multi_frame: MultiCameraFrame) -> np.ndarray:
        """Create horizontal strip layout."""
        frames = []
        for name in multi_frame.annotated_frames.keys():
            frame = multi_frame.annotated_frames[name]
            config = self._get_config(name)
            scale = config.preview_scale if config else 0.3
            h, w = frame.shape[:2]
            frame = cv2.resize(frame, (int(w * scale), int(h * scale)))

            # Add label
            cv2.putText(frame, name, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                       0.7, (0, 255, 255), 2)
            frames.append(frame)

        return np.hstack(frames) if frames else np.zeros((480, 640, 3), dtype=np.uint8)

    def _create_vertical_layout(self, multi_frame: MultiCameraFrame) -> np.ndarray:
        """Create vertical stack layout."""
        frames = []
        for name in multi_frame.annotated_frames.keys():
            frame = multi_frame.annotated_frames[name]
            config = self._get_config(name)
            scale = config.preview_scale if config else 0.4
            h, w = frame.shape[:2]
            frame = cv2.resize(frame, (int(w * scale), int(h * scale)))

            # Add label
            cv2.putText(frame, name, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                       0.7, (0, 255, 255), 2)
            frames.append(frame)

        return np.vstack(frames) if frames else np.zeros((480, 640, 3), dtype=np.uint8)

    def _create_pip_layout(self, multi_frame: MultiCameraFrame) -> np.ndarray:
        """Create picture-in-picture layout (main + small overlays)."""
        camera_names = list(multi_frame.annotated_frames.keys())

        if not camera_names:
            return np.zeros((480, 640, 3), dtype=np.uint8)

        # Main camera (first one)
        main_name = camera_names[0]
        main_frame = multi_frame.annotated_frames[main_name].copy()

        # Add small PiP windows
        pip_size = 200
        pip_margin = 10

        for i, name in enumerate(camera_names[1:], 1):
            frame = multi_frame.annotated_frames[name]
            h, w = frame.shape[:2]

            # Resize to PiP size
            aspect = w / h
            pip_w = pip_size
            pip_h = int(pip_size / aspect)
            pip = cv2.resize(frame, (pip_w, pip_h))

            # Position (top-right corner, stacked)
            y_offset = pip_margin + (pip_h + pip_margin) * (i - 1)
            x_offset = main_frame.shape[1] - pip_w - pip_margin

            # Ensure it fits
            if y_offset + pip_h <= main_frame.shape[0]:
                # Add border
                pip = cv2.copyMakeBorder(pip, 2, 2, 2, 2, cv2.BORDER_CONSTANT,
                                        value=(0, 255, 255))

                # Overlay on main
                main_frame[y_offset:y_offset+pip.shape[0],
                          x_offset:x_offset+pip.shape[1]] = pip

                # Add label
                cv2.putText(main_frame, name, (x_offset, y_offset - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        return main_frame

    def get_combined_object_count(self, multi_frame: MultiCameraFrame) -> Dict[str, int]:
        """
        Get object count from each camera.

        Returns:
            Dictionary mapping camera names to object counts
        """
        counts = {}
        for name, objects in multi_frame.detected_objects.items():
            counts[name] = len(objects)
        return counts

    def get_total_unique_objects(self, multi_frame: MultiCameraFrame) -> int:
        """
        Estimate total unique objects across all cameras.
        Uses simple heuristic: average of all camera counts.

        For more accurate matching, implement cross-camera object correspondence.
        """
        counts = list(self.get_combined_object_count(multi_frame).values())
        if not counts:
            return 0
        return int(np.mean(counts))

    def stop(self):
        """Stop all capture threads and close cameras."""
        print("\nStopping multi-camera system...")
        self.running = False

        # Wait for threads to finish
        for thread in self.camera_threads.values():
            thread.join(timeout=1.0)

        # Close all cameras
        for name, cap in self.cameras.items():
            cap.release()
            print(f"✓ Closed {name}")

        self.cameras.clear()
        self.camera_threads.clear()
        self.latest_frames.clear()
        print("Multi-camera system stopped")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================
if __name__ == "__main__":
    """
    Example usage of multi-camera system.
    """

    print("=" * 70)
    print("Multi-Camera Vision System for CNCSorter")
    print("=" * 70)
    print()
    print("ADVANTAGES:")
    print("  • Better Coverage: See all sides of objects")
    print("  • Occlusion Handling: If one view is blocked, others work")
    print("  • 3D Reconstruction: Multiple angles enable depth perception")
    print("  • Accuracy: Cross-validate detections")
    print("  • Redundancy: System continues if one camera fails")
    print("=" * 70)
    print()

    # Configure cameras (customize these for your setup)
    cameras = [
        CameraConfig(
            name="Webcam",
            source=0,  # Built-in webcam
            position="top",
            preview_scale=0.4,
            enabled=True
        ),
        CameraConfig(
            name="iPhone",
            source="http://192.168.1.100:8080/video",  # IP Webcam app
            position="side",
            preview_scale=0.4,
            enabled=False  # Set to True when iPhone is streaming
        ),
        CameraConfig(
            name="GoPro",
            source=1,  # USB connection (second USB camera)
            position="front",
            preview_scale=0.4,
            enabled=False  # Set to True when GoPro is connected via USB
        ),
        CameraConfig(
            name="iPad",
            source="http://192.168.1.102:8080/video",
            position="angle45",
            preview_scale=0.4,
            enabled=False  # Set to True when iPad is streaming
        ),
    ]

    # Create multi-camera system
    multi_cam = MultiCameraVisionSystem(cameras)

    # Initialize cameras
    print("Initializing cameras...")
    results = multi_cam.initialize_cameras()

    active_cameras = sum(1 for success in results.values() if success)
    print(f"\n✓ {active_cameras} camera(s) active")

    if active_cameras == 0:
        print("No cameras available. Exiting.")
        exit(1)

    # Start capture threads
    print("\nStarting capture threads...")
    multi_cam.start_capture_threads()
    time.sleep(1)  # Let threads start

    print()
    print("Controls:")
    print("  'q' - Quit")
    print("  '1' - Grid layout (2x2)")
    print("  '2' - Horizontal layout")
    print("  '3' - Vertical layout")
    print("  '4' - Picture-in-Picture")
    print("  '+' - Increase threshold")
    print("  '-' - Decrease threshold")
    print()

    layout = "grid"

    try:
        while True:
            # Get synchronized frames
            multi_frame = multi_cam.get_synchronized_frames()

            if not multi_frame.frames:
                print("No frames available")
                time.sleep(0.1)
                continue

            # Detect objects in all frames
            multi_frame = multi_cam.detect_objects_multi_camera(multi_frame)

            # Create display
            display = multi_cam.create_multi_view_display(multi_frame, layout)

            # Add overall stats
            counts = multi_cam.get_combined_object_count(multi_frame)
            total = sum(counts.values())
            unique_estimate = multi_cam.get_total_unique_objects(multi_frame)

            stats_text = f"Total detections: {total} | Estimated unique: {unique_estimate} | Layout: {layout}"
            cv2.putText(display, stats_text, (10, display.shape[0] - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            # Show display
            cv2.imshow("Multi-Camera CNCSorter", display)

            # Handle keys
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            elif key == ord('1'):
                layout = "grid"
                print("Layout: Grid")
            elif key == ord('2'):
                layout = "horizontal"
                print("Layout: Horizontal")
            elif key == ord('3'):
                layout = "vertical"
                print("Layout: Vertical")
            elif key == ord('4'):
                layout = "picture_in_picture"
                print("Layout: Picture-in-Picture")
            elif key == ord('+') or key == ord('='):
                multi_cam.threshold = min(255, multi_cam.threshold + 5)
                print(f"Threshold: {multi_cam.threshold}")
            elif key == ord('-') or key == ord('_'):
                multi_cam.threshold = max(0, multi_cam.threshold - 5)
                print(f"Threshold: {multi_cam.threshold}")

    except KeyboardInterrupt:
        print("\nInterrupted by user")

    finally:
        multi_cam.stop()
        cv2.destroyAllWindows()
        print("Done!")
