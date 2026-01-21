"""
Enhanced vision module for CNCSorter with multi-source support.
Supports: Webcam, Raspberry Pi Camera, iPhone IP Camera, and other IP streams.
Optimized for high-resolution streams on Raspberry Pi hardware.
"""
import cv2
import numpy as np
import time
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum

from domain.entities import DetectedObject, Point2D, CapturedImage, CNCCoordinate


# ============================================================================
# CONFIGURATION
# ============================================================================
CONFIG = {
    # Video source options:
    # - 0, 1, 2, etc.: USB/built-in webcam index
    # - "http://192.168.1.100:8080/video": iPhone IP camera (e.g., using IP Webcam app)
    # - "http://192.168.1.101:8081/video": Another IP camera
    # - "/dev/video0": Raspberry Pi Camera (if using V4L2 driver)
    # - "picamera": Use picamera2 library (Pi Camera Module)
    "SOURCE": 0,  # Default: first webcam

    # iPhone cameras provide high resolution (1080p/4K)
    # Scale factor for preview window (0.5 = 50% size)
    # Processing is done on FULL resolution for accuracy
    "PREVIEW_SCALE": 0.5,

    # Frame skip for performance on Raspberry Pi
    # Process every Nth frame (1 = no skip, 2 = every 2nd frame, etc.)
    "FRAME_SKIP": 1,

    # Camera resolution (width, height) - None for auto
    # Set lower for Raspberry Pi, higher for desktop
    "RESOLUTION": None,  # None = use camera default, or (1280, 720), (1920, 1080), etc.

    # Reconnection settings for IP cameras
    "RECONNECT_ATTEMPTS": 3,
    "RECONNECT_DELAY": 2.0,  # seconds

    # Detection parameters
    "DEFAULT_THRESHOLD": 127,
    "DEFAULT_MIN_AREA": 150,
}


class SourceType(Enum):
    """Enum for different camera source types."""
    WEBCAM = "webcam"
    PI_CAMERA = "picamera"
    IP_CAMERA = "ip_camera"
    V4L2 = "v4l2"


class EnhancedVisionSystem:
    """
    Enhanced vision system with multi-source support and performance optimization.

    Features:
    - Multiple camera sources (webcam, Pi camera, IP camera)
    - High-resolution stream handling
    - Automatic reconnection for IP cameras
    - Frame skipping for performance
    - Modular object detection
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the enhanced vision system.

        Args:
            config: Configuration dictionary (uses CONFIG if None)
        """
        self.config = config or CONFIG.copy()
        self.capture: Optional[cv2.VideoCapture] = None
        self.picamera = None  # For picamera2 library
        self._is_open = False
        self.source_type = self._determine_source_type()
        self.frame_count = 0
        self.last_frame = None

        # Performance tracking
        self.fps = 0
        self.last_fps_time = time.time()
        self.fps_frame_count = 0

    def _determine_source_type(self) -> SourceType:
        """Determine the type of video source."""
        source = self.config["SOURCE"]

        if source == "picamera":
            return SourceType.PI_CAMERA
        elif isinstance(source, str):
            if source.startswith("http://") or source.startswith("https://"):
                return SourceType.IP_CAMERA
            elif source.startswith("/dev/"):
                return SourceType.V4L2

        return SourceType.WEBCAM

    def open_camera(self) -> bool:
        """
        Open the camera connection based on source type.

        Returns:
            True if camera opened successfully
        """
        try:
            if self.source_type == SourceType.PI_CAMERA:
                # Use picamera2 for Raspberry Pi Camera Module
                return self._open_picamera()
            else:
                # Use OpenCV VideoCapture for all other sources
                return self._open_opencv_camera()
        except Exception as e:
            print(f"Error opening camera: {e}")
            return False

    def _open_picamera(self) -> bool:
        """Open Raspberry Pi camera using picamera2."""
        try:
            from picamera2 import Picamera2

            self.picamera = Picamera2()

            # Configure camera
            config = self.picamera.create_preview_configuration()
            if self.config["RESOLUTION"]:
                config["main"]["size"] = self.config["RESOLUTION"]

            self.picamera.configure(config)
            self.picamera.start()
            self._is_open = True
            print("Raspberry Pi Camera opened successfully")
            return True
        except ImportError:
            print("picamera2 library not found. Install with: pip install picamera2")
            return False
        except Exception as e:
            print(f"Error opening Pi Camera: {e}")
            return False

    def _open_opencv_camera(self) -> bool:
        """Open camera using OpenCV VideoCapture."""
        source = self.config["SOURCE"]

        # Create VideoCapture
        if isinstance(source, int):
            self.capture = cv2.VideoCapture(source)
        else:
            self.capture = cv2.VideoCapture(source, cv2.CAP_FFMPEG)

        if not self.capture.isOpened():
            print(f"Failed to open camera: {source}")
            return False

        # Set resolution if specified
        if self.config["RESOLUTION"]:
            width, height = self.config["RESOLUTION"]
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        self._is_open = True
        print(f"Camera opened successfully: {source}")

        # Print actual resolution
        actual_width = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"Resolution: {int(actual_width)}x{int(actual_height)}")

        return True

    def close_camera(self):
        """Close the camera connection."""
        if self.source_type == SourceType.PI_CAMERA and self.picamera:
            self.picamera.stop()
            self.picamera = None
        elif self.capture:
            self.capture.release()
            self.capture = None

        self._is_open = False
        print("Camera closed")

    def is_camera_open(self) -> bool:
        """Check if camera is open."""
        return self._is_open

    def capture_frame_with_retry(self, max_attempts: int = None) -> Optional[np.ndarray]:
        """
        Capture a frame with automatic retry for IP cameras.

        Args:
            max_attempts: Maximum reconnection attempts (uses config if None)

        Returns:
            Frame as numpy array or None if capture fails
        """
        if max_attempts is None:
            max_attempts = self.config["RECONNECT_ATTEMPTS"]

        for attempt in range(max_attempts):
            frame = self._capture_single_frame()

            if frame is not None:
                self.last_frame = frame
                return frame

            # Frame capture failed
            if self.source_type == SourceType.IP_CAMERA:
                print(f"IP camera stream lost. Reconnecting... (Attempt {attempt + 1}/{max_attempts})")
                time.sleep(self.config["RECONNECT_DELAY"])

                # Try to reconnect
                self.close_camera()
                if self.open_camera():
                    continue

            # Non-IP camera failure or reconnection failed
            break

        print("Failed to capture frame after retries")
        return self.last_frame  # Return last good frame if available

    def _capture_single_frame(self) -> Optional[np.ndarray]:
        """Capture a single frame from the camera source."""
        try:
            if self.source_type == SourceType.PI_CAMERA and self.picamera:
                # Capture from Pi Camera
                frame = self.picamera.capture_array()
                # Convert RGB to BGR for OpenCV compatibility
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                return frame
            elif self.capture:
                # Capture from OpenCV source
                ret, frame = self.capture.read()
                return frame if ret else None
        except Exception as e:
            print(f"Error capturing frame: {e}")

        return None

    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture a frame with frame skipping for performance.

        Returns:
            Frame as numpy array or None if capture fails
        """
        if not self.is_camera_open():
            return None

        self.frame_count += 1

        # Frame skipping logic
        if self.frame_count % self.config["FRAME_SKIP"] != 0:
            # Skip this frame, return last captured frame
            return self.last_frame

        # Capture new frame with retry
        frame = self.capture_frame_with_retry()

        # Update FPS
        self._update_fps()

        return frame

    def _update_fps(self):
        """Update FPS calculation."""
        self.fps_frame_count += 1
        current_time = time.time()
        elapsed = current_time - self.last_fps_time

        if elapsed >= 1.0:  # Update every second
            self.fps = self.fps_frame_count / elapsed
            self.fps_frame_count = 0
            self.last_fps_time = current_time

    def get_fps(self) -> float:
        """Get current FPS."""
        return self.fps

    def detect_objects(
        self,
        frame: np.ndarray,
        min_area: int = None,
        thresh_val: int = None
    ) -> Tuple[List[Dict[str, Any]], np.ndarray, np.ndarray]:
        """
        Modular object detection function.
        Processes full-resolution image for accuracy.

        Args:
            frame: Input image frame (full resolution)
            min_area: Minimum contour area (uses config default if None)
            thresh_val: Threshold value (uses config default if None)

        Returns:
            Tuple of:
            - List of detected object coordinates and info
            - Annotated frame with green outlines
            - Black-and-white threshold mask
        """
        if min_area is None:
            min_area = self.config["DEFAULT_MIN_AREA"]
        if thresh_val is None:
            thresh_val = self.config["DEFAULT_THRESHOLD"]

        # 1. Pre-processing
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # 2. Thresholding (Invert so objects are white, background is black)
        _, thresh = cv2.threshold(blur, thresh_val, 255, cv2.THRESH_BINARY_INV)

        # 3. Find Contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 4. Process contours and create annotated frame
        annotated_frame = frame.copy()
        detected_objects = []
        obj_count = 0

        valid_contours = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > min_area:
                obj_count += 1
                valid_contours.append(cnt)

                # Get bounding box
                x, y, w, h = cv2.boundingRect(cnt)

                # Calculate center
                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cx = M["m10"] / M["m00"]
                    cy = M["m01"] / M["m00"]
                else:
                    cx, cy = x + w / 2.0, y + h / 2.0

                # Store object info
                detected_objects.append({
                    'id': obj_count,
                    'center': (cx, cy),
                    'bounding_box': (x, y, w, h),
                    'area': area,
                    'contour': cnt
                })

        # Batch draw contours
        if valid_contours:
            cv2.drawContours(annotated_frame, valid_contours, -1, (0, 255, 0), 2)

        # Draw labels and center points (after contours to ensure visibility)
        for obj in detected_objects:
            x, y, w, h = obj['bounding_box']
            cx, cy = obj['center']

            cv2.putText(
                annotated_frame,
                f"Obj {obj['id']}",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )
            cv2.circle(annotated_frame, (int(cx), int(cy)), 5, (0, 0, 255), -1)

        return detected_objects, annotated_frame, thresh

    def create_preview_frame(
        self,
        annotated_frame: np.ndarray,
        thresh: np.ndarray,
        show_side_by_side: bool = True
    ) -> np.ndarray:
        """
        Create a preview frame scaled for Raspberry Pi screen.

        Args:
            annotated_frame: Frame with detected objects drawn
            thresh: Threshold mask
            show_side_by_side: If True, show original and threshold side-by-side

        Returns:
            Preview frame scaled according to PREVIEW_SCALE
        """
        if show_side_by_side:
            # Convert threshold to BGR for stacking
            thresh_bgr = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

            # Stack side by side
            preview = np.hstack((annotated_frame, thresh_bgr))
        else:
            preview = annotated_frame

        # Scale for display
        scale = self.config["PREVIEW_SCALE"]
        if scale != 1.0:
            height, width = preview.shape[:2]
            new_width = int(width * scale)
            new_height = int(height * scale)
            preview = cv2.resize(preview, (new_width, new_height), interpolation=cv2.INTER_AREA)

        return preview

    def detect_objects_legacy(
        self,
        frame: np.ndarray,
        threshold: int = None,
        min_area: int = None
    ) -> List[DetectedObject]:
        """
        Legacy detection method for backward compatibility.
        Returns DetectedObject entities.

        Args:
            frame: Input image frame
            threshold: Binary threshold value
            min_area: Minimum contour area

        Returns:
            List of DetectedObject entities
        """
        if threshold is None:
            threshold = self.config["DEFAULT_THRESHOLD"]
        if min_area is None:
            min_area = self.config["DEFAULT_MIN_AREA"]

        # Use new detection method
        detected_coords, _, _ = self.detect_objects(frame, min_area, threshold)

        # Convert to DetectedObject entities
        detected_objects = []
        for obj_data in detected_coords:
            # Convert contour to list of tuples
            contour_points = [(int(pt[0][0]), int(pt[0][1])) for pt in obj_data['contour']]

            detected_obj = DetectedObject(
                object_id=obj_data['id'],
                contour_points=contour_points,
                bounding_box=obj_data['bounding_box'],
                area=obj_data['area'],
                center=Point2D(obj_data['center'][0], obj_data['center'][1])
            )

            detected_objects.append(detected_obj)

        return detected_objects

    def create_captured_image(
        self,
        frame: np.ndarray,
        image_id: str,
        cnc_position: Optional[CNCCoordinate] = None,
        threshold: int = None,
        min_area: int = None
    ) -> CapturedImage:
        """
        Create a CapturedImage entity with detected objects.

        Args:
            frame: Image frame
            image_id: Unique identifier for the image
            cnc_position: CNC position when image was captured
            threshold: Detection threshold
            min_area: Minimum object area

        Returns:
            CapturedImage entity
        """
        detected_objects = self.detect_objects_legacy(frame, threshold, min_area)

        return CapturedImage(
            image_id=image_id,
            image_data=frame.copy(),
            cnc_position=cnc_position,
            detected_objects=detected_objects
        )


# Backward compatibility: VisionSystem class
VisionSystem = EnhancedVisionSystem


# ============================================================================
# EXAMPLE USAGE
# ============================================================================
if __name__ == "__main__":
    """
    Example usage showing different camera configurations.
    """

    print("=" * 70)
    print("Enhanced Vision System - Multi-Source Camera Demo")
    print("=" * 70)
    print()
    print("Configuration Examples:")
    print("  1. Webcam:         CONFIG['SOURCE'] = 0")
    print("  2. Pi Camera:      CONFIG['SOURCE'] = 'picamera'")
    print("  3. iPhone Camera:  CONFIG['SOURCE'] = 'http://192.168.1.100:8080/video'")
    print("  4. V4L2 Device:    CONFIG['SOURCE'] = '/dev/video0'")
    print()

    # Example: Use webcam with frame skip
    config = CONFIG.copy()
    config["FRAME_SKIP"] = 2  # Process every 2nd frame for better performance
    config["PREVIEW_SCALE"] = 0.5  # 50% preview size

    vision = EnhancedVisionSystem(config)

    if not vision.open_camera():
        print("Failed to open camera")
        exit(1)

    print()
    print("Controls:")
    print("  'q' - Quit")
    print("  's' - Save snapshot")
    print("  '+' - Increase threshold")
    print("  '-' - Decrease threshold")
    print("  '>' - Increase min area")
    print("  '<' - Decrease min area")
    print()

    # Detection parameters
    threshold = CONFIG["DEFAULT_THRESHOLD"]
    min_area = CONFIG["DEFAULT_MIN_AREA"]

    try:
        while True:
            # Capture frame (with automatic retry for IP cameras)
            frame = vision.capture_frame()

            if frame is None:
                print("No frame available")
                break

            # Detect objects on FULL resolution frame
            detected_coords, annotated_frame, thresh = vision.detect_objects(
                frame, min_area, threshold
            )

            # Create scaled preview
            preview = vision.create_preview_frame(annotated_frame, thresh)

            # Add status overlay
            status_text = f"FPS: {vision.get_fps():.1f} | Objects: {len(detected_coords)} | Thresh: {threshold} | MinArea: {min_area}"
            cv2.putText(
                preview,
                status_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2
            )

            # Show preview
            cv2.imshow("CNCSorter - Enhanced Vision", preview)

            # Handle key presses
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            elif key == ord('s'):
                filename = f"snapshot_{int(time.time())}.jpg"
                cv2.imwrite(filename, annotated_frame)
                print(f"Saved: {filename}")
            elif key == ord('+') or key == ord('='):
                threshold = min(255, threshold + 5)
                print(f"Threshold: {threshold}")
            elif key == ord('-') or key == ord('_'):
                threshold = max(0, threshold - 5)
                print(f"Threshold: {threshold}")
            elif key == ord('>') or key == ord('.'):
                min_area += 50
                print(f"Min Area: {min_area}")
            elif key == ord('<') or key == ord(','):
                min_area = max(0, min_area - 50)
                print(f"Min Area: {min_area}")

    except KeyboardInterrupt:
        print("\nInterrupted by user")

    finally:
        vision.close_camera()
        cv2.destroyAllWindows()
        print("Vision system closed")
