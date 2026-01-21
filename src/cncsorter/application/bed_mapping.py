"""Use cases for bed mapping and object detection."""
from typing import List, Optional, Callable
from datetime import datetime
import os
import re
import time
import cv2

from ..domain.entities import BedMap, CapturedImage, DetectedObject, CNCCoordinate
from ..infrastructure.vision import VisionSystem, ImageStitcher
from ..infrastructure.cnc_controller import CNCController


class BedMappingService:
    """Service for creating a complete map of the CNC bed."""

    def __init__(
        self,
        vision_system: VisionSystem,
        cnc_controller: Optional[CNCController] = None,
        image_stitcher: Optional[ImageStitcher] = None
    ):
        """
        Initialize the bed mapping service.

        Args:
            vision_system: Vision system for image capture
            cnc_controller: Optional CNC controller for position tracking
            image_stitcher: Optional image stitcher for creating panoramas
        """
        self.vision_system = vision_system
        self.cnc_controller = cnc_controller
        self.image_stitcher = image_stitcher or ImageStitcher()
        self.current_map: Optional[BedMap] = None

    def start_new_map(self) -> BedMap:
        """
        Start a new bed mapping session.

        Returns:
            New BedMap instance
        """
        map_id = f"map_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_map = BedMap(map_id=map_id, images=[])
        print(f"Started new bed map: {map_id}")
        return self.current_map

    def capture_and_add_image(
        self,
        threshold: int = 127,
        min_area: int = 150,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[CapturedImage]:
        """
        Capture an image and add it to the current bed map.

        Args:
            threshold: Detection threshold
            min_area: Minimum object area
            progress_callback: Optional callback for progress updates

        Returns:
            CapturedImage if successful, None otherwise
        """
        if self.current_map is None:
            print("Error: No active bed map. Call start_new_map() first.")
            return None

        if progress_callback:
            progress_callback("Capturing frame...")

        # Capture frame
        frame = self.vision_system.capture_frame()
        if frame is None:
            print("Error: Failed to capture frame")
            return None

        if progress_callback:
            progress_callback("Getting CNC position...")

        # Get CNC position if controller is available
        cnc_position = None
        if self.cnc_controller and self.cnc_controller.is_connected():
            cnc_position = self.cnc_controller.get_position()

        if progress_callback:
            progress_callback("Detecting objects...")

        # Create captured image with detection
        image_id = f"img_{len(self.current_map.images) + 1:03d}"
        captured_image = self.vision_system.create_captured_image(
            frame=frame,
            image_id=image_id,
            cnc_position=cnc_position,
            threshold=threshold,
            min_area=min_area
        )

        # Add to map
        self.current_map.add_image(captured_image)

        if progress_callback:
            obj_count = len(captured_image.detected_objects)
            progress_callback(f"Captured image {image_id} with {obj_count} objects")

        print(f"Added image {image_id} to map (objects: {len(captured_image.detected_objects)})")
        return captured_image

    def stitch_current_map(
        self,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Stitch all images in the current map together.

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            True if stitching successful, False otherwise
        """
        if self.current_map is None or len(self.current_map.images) < 2:
            print("Error: Need at least 2 images to stitch")
            return False

        if progress_callback:
            progress_callback(f"Stitching {len(self.current_map.images)} images...")

        # Extract image data
        image_frames = [img.image_data for img in self.current_map.images]

        # Stitch images
        stitched = self.image_stitcher.stitch_images(image_frames)

        if stitched is not None:
            self.current_map.stitched_image = stitched
            if progress_callback:
                progress_callback("Stitching completed successfully")
            return True
        else:
            if progress_callback:
                progress_callback("Stitching failed")
            return False

    def get_current_map(self) -> Optional[BedMap]:
        """Get the current bed map."""
        return self.current_map

    def get_all_detected_objects(self) -> List[DetectedObject]:
        """Get all detected objects from the current map."""
        if self.current_map is None:
            return []
        return self.current_map.all_objects

    def _sanitize_path_component(self, component: str) -> str:
        """
        Sanitize a string so it is safe to use as a single filesystem path component.
        Prevents path traversal and ensures valid filenames.
        """
        # Ensure we are working with a string
        component_str = str(component)
        # Drop any directory parts to mitigate path traversal
        component_str = os.path.basename(component_str)
        # Remove explicit parent directory references
        component_str = component_str.replace("..", "")
        # Allow only a safe subset of characters; replace others with underscore
        sanitized = re.sub(r"[^A-Za-z0-9._-]", "_", component_str)
        # Ensure we never return an empty name
        if not sanitized:
            sanitized = f"item_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return sanitized

    def save_map_images(self, output_dir: str = "maps") -> bool:
        """
        Save all images and stitched result to disk.

        Args:
            output_dir: Directory to save images

        Returns:
            True if successful
        """
        if self.current_map is None:
            return False

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        safe_map_id = self._sanitize_path_component(self.current_map.map_id)
        map_dir = os.path.join(output_dir, safe_map_id)
        os.makedirs(map_dir, exist_ok=True)

        # Save individual images
        for img in self.current_map.images:
            safe_image_id = self._sanitize_path_component(img.image_id)
            filename = os.path.join(map_dir, f"{safe_image_id}.jpg")
            cv2.imwrite(filename, img.image_data)
            print(f"Saved {filename}")

        # Save stitched image if available
        if self.current_map.stitched_image is not None:
            stitched_filename = os.path.join(map_dir, "stitched.jpg")
            cv2.imwrite(stitched_filename, self.current_map.stitched_image)
            print(f"Saved {stitched_filename}")

        # Save metadata
        metadata_file = os.path.join(map_dir, "metadata.txt")
        with open(metadata_file, 'w') as f:
            f.write(f"Map ID: {self.current_map.map_id}\n")
            f.write(f"Timestamp: {self.current_map.timestamp}\n")
            f.write(f"Number of images: {len(self.current_map.images)}\n")
            f.write(f"Total objects detected: {len(self.current_map.all_objects)}\n\n")

            for img in self.current_map.images:
                f.write(f"\n{img.image_id}:\n")
                f.write(f"  Objects: {len(img.detected_objects)}\n")
                if img.cnc_position:
                    f.write(f"  CNC Position: {img.cnc_position.to_dict()}\n")

        print(f"Map saved to {map_dir}")
        return True

    def _wait_for_move(self, target: CNCCoordinate, timeout: float = 30.0) -> bool:
        """Wait for CNC to reach target position."""
        if not self.cnc_controller:
            return True

        start_time = time.time()
        while time.time() - start_time < timeout:
            current = self.cnc_controller.get_position()
            if current:
                dist = ((current.x - target.x)**2 + (current.y - target.y)**2 + (current.z - target.z)**2)**0.5
                if dist < 0.5: # 0.5mm tolerance
                    return True
            time.sleep(0.1)
        return False

    def execute_scan(
        self,
        x_min: float, x_max: float,
        y_min: float, y_max: float,
        grid_x: int, grid_y: int,
        safe_z: float,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> int:
        """
        Execute a full scan cycle.

        Args:
            x_min: Minimum X coordinate
            x_max: Maximum X coordinate
            y_min: Minimum Y coordinate
            y_max: Maximum Y coordinate
            grid_x: Number of grid points in X
            grid_y: Number of grid points in Y
            safe_z: Safe Z height for movement
            progress_callback: Optional callback(progress_0_to_1, status_message)

        Returns:
            Total objects detected
        """
        # Calculate grid points
        points = []
        if grid_x > 1:
            x_step = (x_max - x_min) / (grid_x - 1)
        else:
            x_step = 0

        if grid_y > 1:
            y_step = (y_max - y_min) / (grid_y - 1)
        else:
            y_step = 0

        for y_idx in range(grid_y):
            for x_idx in range(grid_x):
                # Zig-zag pattern optimization
                if y_idx % 2 == 1:
                    xi = grid_x - 1 - x_idx
                else:
                    xi = x_idx

                x = x_min + xi * x_step
                y = y_min + y_idx * y_step
                points.append((x, y))

        print(f"Starting scan with {len(points)} points")
        if progress_callback:
            progress_callback(0.0, f"Starting scan with {len(points)} points")

        self.start_new_map()
        total_detected = 0

        for i, point in enumerate(points):
             # Move CNC
             target = CNCCoordinate(x=point[0], y=point[1], z=safe_z)
             if progress_callback:
                 progress_callback(i / len(points), f"Moving to {target.x:.1f}, {target.y:.1f}")

             if self.cnc_controller:
                 if not self.cnc_controller.move_to(target):
                     print("Failed to send move command")

                 # Wait for move to complete
                 if not self._wait_for_move(target):
                     print("Timeout waiting for move")
             else:
                 # Simulate move delay if no controller
                 time.sleep(1)

             # Capture
             if progress_callback:
                 progress_callback(i / len(points), "Capturing image...")

             result = self.capture_and_add_image()

             if result:
                 total_detected += len(result.detected_objects)

        # Stitch
        if progress_callback:
            progress_callback(1.0, "Stitching map...")
        self.stitch_current_map()

        # Save
        if progress_callback:
            progress_callback(1.0, "Saving map...")
        self.save_map_images()

        if progress_callback:
            progress_callback(1.0, "Scan complete")

        return total_detected
