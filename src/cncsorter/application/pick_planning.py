"""Service for planning efficient pick and place operations."""
import math
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Callable
from uuid import uuid4

from cncsorter.domain.entities import (
    DetectedObject,
    CNCCoordinate,
    PickPlan,
    PickOperation,
    BinLocation,
    PickTask
)
from cncsorter.domain.interfaces import DetectionRepository, WorkStatus
from cncsorter.infrastructure.cnc_controller import CNCController
from cncsorter.config import SORTING, OBJECTS, CNC

logger = logging.getLogger(__name__)

class PickPlanningService:
    """Service for planning and executing pick and place operations."""

    def __init__(self, repository: DetectionRepository, cnc_controller: CNCController):
        self.repository = repository
        self.cnc_controller = cnc_controller
        self.safe_z = CNC.get("safe_z_height_mm", 50.0)
        self.pick_z_offset = 5.0  # Height above bed to pick
        # Default drop location (should be configurable)
        self.drop_location = CNCCoordinate(x=10, y=10, z=self.safe_z)
        self.is_running = False

    def plan_picks(self) -> List[PickTask]:
        """Generate pick tasks for all pending objects."""
        objects = self.repository.list_pending()
        tasks = []
        for obj in objects:
            # Only pick objects that have coordinates
            if obj.cnc_coordinate:
                task = PickTask(
                    task_id=f"pick-{obj.object_id}",
                    object_id=obj.uuid,
                    target_position=obj.cnc_coordinate
                )
                tasks.append(task)
            else:
                logger.warning(f"Object {obj.object_id} has no CNC coordinate, skipping.")
        return tasks

    async def execute_pick_and_place(self, progress_callback: Optional[Callable[[float, str], None]] = None):
        """Execute the pick and place sequence for pending objects."""
        if self.is_running:
            logger.warning("Pick and place already running")
            if progress_callback:
                progress_callback(0.0, "Already running")
            return

        self.is_running = True
        try:
            tasks = self.plan_picks()
            total = len(tasks)
            if total == 0:
                logger.info("No pending objects to pick.")
                if progress_callback:
                    progress_callback(1.0, "No objects to pick")
                return

            logger.info(f"Starting pick and place for {total} objects")

            # Connect if not connected
            if not self.cnc_controller.is_connected():
                logger.info("Connecting to CNC controller...")
                if not self.cnc_controller.connect():
                    raise RuntimeError("Failed to connect to CNC controller")

            # Home or ensure safe Z first?
            # Assuming machine is homed. We move to safe Z.
            current_pos = self.cnc_controller.get_position()
            start_x = current_pos.x if current_pos else 0
            start_y = current_pos.y if current_pos else 0

            await self._move_and_wait(CNCCoordinate(x=start_x, y=start_y, z=self.safe_z))

            for i, task in enumerate(tasks):
                if not self.is_running:
                    logger.info("Pick and place stopped by user.")
                    break

                if progress_callback:
                    progress_callback(i / total, f"Picking object {task.task_id}...")

                # Execute single pick
                success = await self._execute_single_pick(task)

                if success:
                    # Update status in repository
                    self.repository.update_status(task.object_id, WorkStatus.COMPLETED)
                else:
                    self.repository.update_status(task.object_id, WorkStatus.FAILED)
                    logger.error(f"Failed to pick object {task.task_id}")

            if progress_callback:
                progress_callback(1.0, "Pick and place cycle completed")

        except Exception as e:
            logger.error(f"Pick and place failed: {e}", exc_info=True)
            if progress_callback:
                progress_callback(0.0, f"Error: {str(e)}")
        finally:
            self.is_running = False

    async def _execute_single_pick(self, task: PickTask) -> bool:
        """Execute a single pick and place operation."""
        try:
            target = task.target_position

            # 1. Move to Safe Z above target
            safe_target = CNCCoordinate(x=target.x, y=target.y, z=self.safe_z)
            await self._move_and_wait(safe_target)

            # 2. Move down to Pick Z
            # Using object's Z if available, else pick_z_offset
            pick_z = target.z if target.z > 0 else self.pick_z_offset
            pick_target = CNCCoordinate(x=target.x, y=target.y, z=pick_z)
            await self._move_and_wait(pick_target)

            # 3. Simulate Pick (activate magnet/suction)
            # TODO: Implement actual tool activation
            await asyncio.sleep(0.5)

            # 4. Move back to Safe Z
            await self._move_and_wait(safe_target)

            # 5. Move to Drop location
            # For now, just a fixed location.
            # Ideally this should be dynamic based on classification.
            drop_pos = self.drop_location
            # Move to safe Z above drop
            drop_safe = CNCCoordinate(x=drop_pos.x, y=drop_pos.y, z=self.safe_z)
            await self._move_and_wait(drop_safe)

            # Move down to drop
            # await self._move_and_wait(drop_pos) # Optional: move down to drop

            # 6. Drop
            # TODO: Deactivate tool
            await asyncio.sleep(0.5)

            return True
        except Exception as e:
            logger.error(f"Error executing pick task {task.task_id}: {e}")
            return False

    async def _move_and_wait(self, target: CNCCoordinate):
        """Send move command and wait for completion."""
        # This is a simplification.
        # In a real system we need better feedback loop.
        if not self.cnc_controller.move_to(target):
             raise RuntimeError(f"Failed to move to {target}")

        # Poll for position/idle
        # If the controller doesn't support get_position, we just wait based on estimated time?
        # MockCNCController updates is_moving flag but it's not in the interface.
        # We'll use a simple polling on get_position if available.

        timeout = 30.0
        start_time = asyncio.get_event_loop().time()

        while True:
            if asyncio.get_event_loop().time() - start_time > timeout:
                logger.warning("Timeout waiting for move to complete")
                break

            # For Mock Controller we can cheat if we know it is a Mock
            # But let's try to be generic.
            # If get_position returns None, we assume open loop and just wait a bit?
            # Or we can check if position is close to target.

            current_pos = self.cnc_controller.get_position()
            if current_pos:
                dist = ((current_pos.x - target.x)**2 +
                        (current_pos.y - target.y)**2 +
                        (current_pos.z - target.z)**2) ** 0.5
                if dist < 1.0: # 1mm tolerance
                    break

            # Check if controller has 'is_moving' property (Mock has it, but it's not abstract)
            if hasattr(self.cnc_controller, 'is_moving') and not self.cnc_controller.is_moving:
                 # If it supports is_moving and says False, we are done
                 # But we need to be careful about race condition (checking before it starts moving)
                 # So checking distance is safer if get_position works.
                 pass

            await asyncio.sleep(0.1)

    def stop(self):
        """Stop the pick and place operation."""
        self.is_running = False
