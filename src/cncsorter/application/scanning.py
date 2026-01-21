"""Service for orchestrating the scanning process."""
import asyncio
import logging
from typing import Optional, List, Callable
from uuid import uuid4

from cncsorter.domain.entities import CNCCoordinate, DetectedObject, CapturedImage
from cncsorter.domain.interfaces import DetectionRepository, WorkStatus
from cncsorter.domain.system_config import SystemConfig, CameraConfig
from cncsorter.infrastructure.cnc_controller import CNCController
from cncsorter.infrastructure.vision import VisionSystem
from cncsorter.application.events import EventBus, ObjectsDetected, BedMapCompleted

logger = logging.getLogger(__name__)


class ScanningService:
    """Service to manage the scanning cycle."""

    def __init__(
        self,
        repository: DetectionRepository,
        cnc_controller: CNCController,
        vision_system: VisionSystem,
        event_bus: EventBus,
        config: SystemConfig
    ):
        self.repository = repository
        self.cnc_controller = cnc_controller
        self.vision_system = vision_system
        self.event_bus = event_bus
        self.config = config
        self.is_running = False

    async def run_scan(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> None:
        """Execute the full scanning cycle."""
        if self.is_running:
            logger.warning("Scan cycle already running")
            if progress_callback:
                progress_callback(0.0, "Already running")
            return

        self.is_running = True
        try:
            logger.info("Starting scan cycle...")

            # Ensure CNC is connected
            if not self.cnc_controller.is_connected():
                logger.info("Connecting to CNC controller...")
                if not self.cnc_controller.connect():
                    raise RuntimeError("Failed to connect to CNC controller")

            # Calculate scan points
            scan_points = self._calculate_scan_points()
            total_points = len(scan_points)
            if total_points == 0:
                logger.warning("No scan points generated. Check configuration.")
                if progress_callback:
                    progress_callback(1.0, "No scan points")
                return

            logger.info(f"Generated {total_points} scan points.")

            # Move to safe Z first
            current_pos = self.cnc_controller.get_position()
            start_x = current_pos.x if current_pos else 0
            start_y = current_pos.y if current_pos else 0
            safe_z = self.config.safe_z

            await self._move_and_wait(CNCCoordinate(x=start_x, y=start_y, z=safe_z))

            total_detected = 0
            image_count = 0

            for i, point in enumerate(scan_points):
                if not self.is_running:
                    logger.info("Scan stopped by user.")
                    break

                progress = i / total_points
                msg = f"Scanning point {i+1}/{total_points}..."
                if progress_callback:
                    progress_callback(progress, msg)

                # Move to point
                scan_target = CNCCoordinate(x=point.x, y=point.y, z=safe_z)
                await self._move_and_wait(scan_target)

                # Wait a bit for vibration to settle
                await asyncio.sleep(0.5)

                # Capture and Detect
                # We need to handle multiple cameras if configured
                for cam_config in self.config.cameras:
                    if not cam_config.enabled:
                        continue

                    # Check if this config matches our active vision system
                    if hasattr(self.vision_system, 'camera_index') and self.vision_system.camera_index != cam_config.camera_id:
                        continue

                    frame = self.vision_system.capture_frame()
                    if frame is None:
                        logger.error(f"Failed to capture frame at {point}")
                        continue

                    image_count += 1
                    detected_objects = self.vision_system.detect_objects(frame)
                    image_id = str(uuid4())

                    # Transform coordinates and save
                    processed_objects = []
                    for obj in detected_objects:
                        # Calculate world coordinates
                        world_obj = self._transform_to_world_coordinates(obj, scan_target, cam_config, frame.shape)
                        world_obj.image_id = image_id

                        # Save to repository
                        self.repository.save(world_obj)
                        processed_objects.append(world_obj)

                    if processed_objects:
                        total_detected += len(processed_objects)
                        self.event_bus.publish(ObjectsDetected(
                            detected_objects=processed_objects,
                            image_id=image_id,
                            camera_index=cam_config.camera_id
                        ))

            if self.is_running:
                logger.info(f"Scan cycle completed. Total objects: {total_detected}")
                if progress_callback:
                    progress_callback(1.0, f"Scan complete. Found {total_detected} objects.")
                self.event_bus.publish(BedMapCompleted(
                    bed_map_id=str(uuid4()),
                    total_objects=total_detected,
                    image_count=image_count
                ))

        except Exception as e:
            logger.error(f"Scan cycle failed: {e}", exc_info=True)
            if progress_callback:
                progress_callback(0.0, f"Error: {str(e)}")
        finally:
            self.is_running = False

    def _calculate_scan_points(self) -> List[CNCCoordinate]:
        """Calculate the grid of points to visit."""
        points = []

        # Determine the area to cover
        x_start = self.config.x_min
        x_end = self.config.x_max
        y_start = self.config.y_min
        y_end = self.config.y_max

        # Grid size
        nx = self.config.grid_x
        ny = self.config.grid_y

        if nx < 1 or ny < 1:
            return []

        step_x = (x_end - x_start) / nx
        step_y = (y_end - y_start) / ny

        # Generate points (centers of grid cells)
        for i in range(nx):
            x = x_start + step_x * (i + 0.5)
            for j in range(ny):
                y = y_start + step_y * (j + 0.5)
                # Zig-zag pattern to minimize travel?
                # For now, simple raster scan.
                points.append(CNCCoordinate(x=x, y=y, z=0)) # Z will be overridden by safe_z

        return points

    def _transform_to_world_coordinates(
        self,
        obj: DetectedObject,
        cnc_pos: CNCCoordinate,
        cam_config: CameraConfig,
        frame_shape: tuple
    ) -> DetectedObject:
        """
        Transform object coordinates from image space to world (CNC) space.

        cnc_pos: Position of the spindle/toolhead.
        cam_config: Configuration of the camera (offsets from spindle).
        """
        height, width = frame_shape[:2]

        # Image center
        cx = width / 2.0
        cy = height / 2.0

        # Pixels per mm
        px_per_mm_x = width / cam_config.visible_width
        px_per_mm_y = height / cam_config.visible_height

        # Object center in image relative to image center
        # Y axis in image is down, X is right.
        # Check camera mounting orientation.
        # Assuming standard mounting: Camera X aligns with CNC X, Camera Y aligns with CNC Y.
        # But usually image Y is down, while CNC Y is up (away from front).
        # We need to check coordinate systems.
        # Let's assume standard computer vision (Y down) and CNC (Y up).
        # And camera is mounted looking down.

        img_dx_px = obj.center.x - cx
        img_dy_px = obj.center.y - cy

        # Convert to mm offset from camera center
        # If camera Y is inverted relative to CNC Y:
        cam_dx_mm = img_dx_px / px_per_mm_x
        cam_dy_mm = -(img_dy_px / px_per_mm_y) # Invert Y

        # Apply camera rotation if needed (pan_angle?)
        # For now, assume aligned.

        # Camera world position = CNC position + Camera Offset
        cam_world_x = cnc_pos.x + cam_config.mount_x
        cam_world_y = cnc_pos.y + cam_config.mount_y

        # Object world position
        obj_world_x = cam_world_x + cam_dx_mm
        obj_world_y = cam_world_y + cam_dy_mm

        # Update object with CNC coordinate
        obj.cnc_coordinate = CNCCoordinate(x=obj_world_x, y=obj_world_y, z=0) # Objects are on bed (Z=0)
        obj.source_camera = cam_config.camera_id

        return obj

    async def _move_and_wait(self, target: CNCCoordinate):
        """Send move command and wait for completion."""
        # Reuse logic from PickPlanningService or abstract it.
        # Ideally CNCController should have an async `move_to_async` method.
        # For now, duplicate simple polling logic.

        if not self.cnc_controller.move_to(target):
             raise RuntimeError(f"Failed to move to {target}")

        timeout = 30.0
        start_time = asyncio.get_event_loop().time()

        while True:
            if asyncio.get_event_loop().time() - start_time > timeout:
                logger.warning("Timeout waiting for move to complete")
                break

            current_pos = self.cnc_controller.get_position()
            if current_pos:
                dist = ((current_pos.x - target.x)**2 +
                        (current_pos.y - target.y)**2 +
                        (current_pos.z - target.z)**2) ** 0.5
                if dist < 1.0: # 1mm tolerance
                    break

            await asyncio.sleep(0.1)

    def stop(self):
        """Stop the scanning operation."""
        self.is_running = False
