"""Vision system for object detection and image processing."""
import cv2
import numpy as np
from typing import List, Tuple, Optional
from ..domain.entities import DetectedObject, Point2D, CapturedImage, CNCCoordinate


class VisionSystem:
    """Handles camera operations and object detection."""
    
    def __init__(self, camera_index: int = 0):
        """
        Initialize the vision system.
        
        Args:
            camera_index: Camera device index (default 0)
        """
        self.camera_index = camera_index
        self.capture: Optional[cv2.VideoCapture] = None
        self._is_open = False
    
    def open_camera(self) -> bool:
        """Open the camera connection."""
        self.capture = cv2.VideoCapture(self.camera_index)
        self._is_open = self.capture.isOpened()
        
        if self._is_open:
            # Set camera properties for better quality
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            print(f"Camera {self.camera_index} opened successfully")
        else:
            print(f"Failed to open camera {self.camera_index}")
        
        return self._is_open
    
    def close_camera(self):
        """Close the camera connection."""
        if self.capture:
            self.capture.release()
            self._is_open = False
            print("Camera closed")
    
    def is_camera_open(self) -> bool:
        """Check if camera is open."""
        return self._is_open and self.capture is not None
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame from the camera.
        
        Returns:
            Frame as numpy array or None if capture fails
        """
        if not self.is_camera_open():
            return None
        
        ret, frame = self.capture.read()
        return frame if ret else None
    
    def detect_objects(
        self,
        frame: np.ndarray,
        threshold: int = 127,
        min_area: int = 150
    ) -> List[DetectedObject]:
        """
        Detect objects in the given frame.
        
        Args:
            frame: Input image frame
            threshold: Binary threshold value
            min_area: Minimum contour area to consider as an object
            
        Returns:
            List of detected objects
        """
        # Pre-processing
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Thresholding
        _, thresh = cv2.threshold(blur, threshold, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Process contours and create DetectedObject instances
        detected_objects = []
        obj_id = 1
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > min_area:
                # Get bounding box
                x, y, w, h = cv2.boundingRect(cnt)
                
                # Calculate center
                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cx = M["m10"] / M["m00"]
                    cy = M["m01"] / M["m00"]
                else:
                    cx, cy = x + w / 2.0, y + h / 2.0
                
                # Convert contour to list of tuples
                contour_points = [(int(pt[0][0]), int(pt[0][1])) for pt in cnt]
                
                detected_obj = DetectedObject(
                    object_id=obj_id,
                    contour_points=contour_points,
                    bounding_box=(x, y, w, h),
                    area=area,
                    center=Point2D(cx, cy)
                )
                
                detected_objects.append(detected_obj)
                obj_id += 1
        
        return detected_objects
    
    def draw_objects_on_frame(
        self,
        frame: np.ndarray,
        objects: List[DetectedObject],
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2
    ) -> np.ndarray:
        """
        Draw detected objects on the frame.
        
        Args:
            frame: Input frame to draw on
            objects: List of detected objects
            color: Drawing color (BGR)
            thickness: Line thickness
            
        Returns:
            Frame with drawn objects
        """
        frame_copy = frame.copy()
        
        for obj in objects:
            x, y, w, h = obj.bounding_box
            
            # Draw contour
            contour_array = np.array([obj.contour_points], dtype=np.int32)
            cv2.drawContours(frame_copy, contour_array, -1, color, thickness)
            
            # Draw label
            label = f"Obj {obj.object_id}"
            cv2.putText(
                frame_copy,
                label,
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                thickness
            )
            
            # Draw center point
            center = (int(obj.center.x), int(obj.center.y))
            cv2.circle(frame_copy, center, 5, (0, 0, 255), -1)
        
        return frame_copy
    
    def create_captured_image(
        self,
        frame: np.ndarray,
        image_id: str,
        cnc_position: Optional[CNCCoordinate] = None,
        threshold: int = 127,
        min_area: int = 150
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
        detected_objects = self.detect_objects(frame, threshold, min_area)
        
        return CapturedImage(
            image_id=image_id,
            image_data=frame.copy(),
            cnc_position=cnc_position,
            detected_objects=detected_objects
        )


class ImageStitcher:
    """Handles stitching multiple images together to create a bed map."""
    
    def __init__(self):
        """Initialize the image stitcher."""
        self.stitcher = cv2.Stitcher_create(cv2.Stitcher_PANORAMA)
    
    def stitch_images(self, images: List[np.ndarray]) -> Optional[np.ndarray]:
        """
        Stitch multiple images together.
        
        Args:
            images: List of image frames to stitch
            
        Returns:
            Stitched image or None if stitching fails
        """
        if len(images) < 2:
            return images[0] if images else None
        
        try:
            status, stitched = self.stitcher.stitch(images)
            
            if status == cv2.Stitcher_OK:
                print("Image stitching successful")
                return stitched
            else:
                print(f"Image stitching failed with status: {status}")
                return None
        except Exception as e:
            print(f"Error during image stitching: {e}")
            return None
