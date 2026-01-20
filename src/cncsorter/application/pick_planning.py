"""Service for planning efficient pick and place operations."""
import math
import logging
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4

from cncsorter.domain.entities import (
    DetectedObject,
    CNCCoordinate,
    PickPlan,
    PickOperation,
    BinLocation
)
from cncsorter.config import SORTING, CNC

logger = logging.getLogger(__name__)

class PickPlanningService:
    """
    Generates optimized pick and place plans based on detected objects
    and sorting configuration.
    """

    def __init__(self, sorting_config: Dict[str, Any] = SORTING):
        """
        Initialize planner.

        Args:
            sorting_config: Configuration dictionary (SORTING from config.py)
        """
        self.config = sorting_config
        self.tools = self.config.get("tools", {})
        self.bins = self._parse_bins(self.config.get("bins", []))
        self.default_tool = self.config.get("default_tool", "magnet_tool")
        self.default_bin_id = self.config.get("default_bin", "bin_rejects")

    def _parse_bins(self, bins_config: List[Dict]) -> List[BinLocation]:
        """Convert bin dicts to BinLocation entities."""
        bins = []
        for b in bins_config:
            loc = b["location"]
            bins.append(BinLocation(
                bin_id=b["id"],
                location=CNCCoordinate(x=loc["x"], y=loc["y"], z=loc["z"]),
                accepted_types=b.get("accepts", []),
                size_ranges=b.get("size_range", ["all"])
            ))
        return bins

    def create_plan(self, objects: List[DetectedObject], start_position: Optional[CNCCoordinate] = None) -> PickPlan:
        """
        Create an optimized pick plan for the given objects.

        Algorithm:
        1. Assign Tool and Bin to each object.
        2. Group objects by Tool.
        3. For each tool group:
           a. Add Tool Change operation if needed.
           b. Solve TSP (Nearest Neighbor) for (Pick -> Place) pairs.
        4. Concatenate operations.

        Args:
            objects: List of objects to pick.
            start_position: Current machine position (defaults to 0,0,0).

        Returns:
            PickPlan entity containing ordered operations.
        """
        if start_position is None:
            start_position = CNCCoordinate(0, 0, 0)

        plan_id = f"plan_{uuid4().hex[:8]}"
        operations: List[PickOperation] = []

        # 1. Classification & Assignment
        # List of (object, tool_id, bin) tuples
        tasks = []

        for obj in objects:
            # Determine size category if not already present
            # We assume obj.area is available
            size_cat, _ = self._classify_size(obj.area)

            tool_id = self._select_tool(obj, size_cat)
            bin_loc = self._select_bin(obj, size_cat)

            tasks.append({
                "object": obj,
                "tool": tool_id,
                "bin": bin_loc,
                "size": size_cat
            })

        # 2. Group by Tool
        # We want to minimize tool changes, so process all items for one tool, then the next.
        # Order of tools could be optimized, but simple iteration is usually fine.
        tasks_by_tool = {}
        for task in tasks:
            t_id = task["tool"]
            if t_id not in tasks_by_tool:
                tasks_by_tool[t_id] = []
            tasks_by_tool[t_id].append(task)

        current_pos = start_position
        current_tool = None # Assume no tool or unknown tool initially

        tool_changes = 0

        # Process each tool group
        for tool_id, group_tasks in tasks_by_tool.items():
            # If we need to change tool
            if current_tool != tool_id:
                # Add tool change operation
                tool_config = self.tools.get(tool_id, {})
                change_loc = tool_config.get("tool_change_location")

                if change_loc:
                    change_coord = CNCCoordinate(change_loc["x"], change_loc["y"], change_loc["z"])

                    # Move to change location
                    operations.append(PickOperation(
                        op_type="MOVE",
                        target_coordinate=change_coord,
                        details=f"Move to tool change for {tool_id}"
                    ))

                    # Perform change (abstracted as one op)
                    operations.append(PickOperation(
                        op_type="TOOL_CHANGE",
                        target_coordinate=change_coord,
                        details=f"Equip {tool_id}",
                        tool_id=tool_id
                    ))

                    current_pos = change_coord
                    tool_changes += 1

                current_tool = tool_id

            # 3. Route Optimization (Nearest Neighbor)
            # We have a set of tasks. Each task consists of a Pick Loc and a Place Loc.
            # We are at current_pos.
            # While tasks remain:
            #   Find task with nearest Pick Loc to current_pos
            #   Add Move -> Pick -> Move -> Place
            #   Update current_pos to Place Loc

            pending_tasks = group_tasks.copy()

            while pending_tasks:
                # Find nearest task
                nearest_task = None
                min_dist = float('inf')
                nearest_idx = -1

                for i, task in enumerate(pending_tasks):
                    obj_loc = self._get_object_cnc_coords(task["object"])
                    dist = self._distance(current_pos, obj_loc)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_idx = i

                # Execute nearest task
                task = pending_tasks.pop(nearest_idx)
                obj = task["object"]
                bin_loc = task["bin"]

                obj_cnc_loc = self._get_object_cnc_coords(obj)

                # Move to Object (Safety Height)
                safe_z = CNC["safe_z_height_mm"]
                hover_loc = CNCCoordinate(obj_cnc_loc.x, obj_cnc_loc.y, safe_z)

                operations.append(PickOperation(
                    op_type="MOVE",
                    target_coordinate=hover_loc,
                    details="Move above object",
                    object_id=obj.object_id
                ))

                # Pick (Descent) - Simplification, real G-code would be more complex
                pick_loc = CNCCoordinate(obj_cnc_loc.x, obj_cnc_loc.y, obj_cnc_loc.z) # Z=0 usually
                operations.append(PickOperation(
                    op_type="PICK",
                    target_coordinate=pick_loc,
                    details=f"Pick object {obj.object_id} ({obj.classification})",
                    object_id=obj.object_id,
                    tool_id=current_tool
                ))

                # Move to Bin (Safety Height first)
                operations.append(PickOperation(
                    op_type="MOVE",
                    target_coordinate=hover_loc,
                    details="Retract"
                ))

                bin_hover = CNCCoordinate(bin_loc.location.x, bin_loc.location.y, safe_z)
                operations.append(PickOperation(
                    op_type="MOVE",
                    target_coordinate=bin_hover,
                    details=f"Move to {bin_loc.bin_id}"
                ))

                # Place
                place_loc = bin_loc.location # Drop height
                operations.append(PickOperation(
                    op_type="PLACE",
                    target_coordinate=place_loc,
                    details=f"Place in {bin_loc.bin_id}",
                    object_id=obj.object_id
                ))

                # Update position (we end up at bin location, or maybe safety height above it)
                current_pos = bin_hover

        # Estimate duration (very rough: distance / speed + constant per op)
        total_dist = 0.0
        last_pos = start_position
        for op in operations:
            dist = self._distance(last_pos, op.target_coordinate)
            total_dist += dist
            last_pos = op.target_coordinate

        avg_speed = CNC["feed_rate_mm_min"] / 60.0 # mm/sec
        move_time = total_dist / avg_speed
        op_overhead = len(operations) * 2.0 # 2 seconds per operation overhead

        return PickPlan(
            plan_id=plan_id,
            operations=operations,
            estimated_duration_seconds=move_time + op_overhead,
            total_items=len(objects),
            tool_changes=tool_changes
        )

    def _select_tool(self, obj: DetectedObject, size_cat: str) -> str:
        """Find the best tool for an object."""
        # Try to match by exact classification first
        item_type = obj.classification

        for tool_id, config in self.tools.items():
            handling = config.get("handling_types", [])
            # Check exact match or generic match
            if item_type in handling:
                return tool_id

            # Check if tool handles this size range? (Not in current config schema but useful)

        return self.default_tool

    def _select_bin(self, obj: DetectedObject, size_cat: str) -> BinLocation:
        """Find the correct bin for an object."""
        item_type = obj.classification

        # Priority 1: Match type AND size
        for b in self.bins:
            type_match = item_type in b.accepted_types or "all" in b.accepted_types
            size_match = size_cat in b.size_ranges or "all" in b.size_ranges

            if type_match and size_match:
                return b

        # Priority 2: Match type only (any size)
        for b in self.bins:
            if item_type in b.accepted_types:
                return b

        # Default bin
        for b in self.bins:
            if b.bin_id == self.default_bin_id:
                return b

        # Fallback if default bin not found (shouldn't happen with valid config)
        return self.bins[-1]

    def _get_object_cnc_coords(self, obj: DetectedObject) -> CNCCoordinate:
        """Get or estimate CNC coordinates for an object."""
        if obj.cnc_coordinate:
            return obj.cnc_coordinate

        # If no CNC coordinate (e.g. simulation), use pixel mapping or dummy
        # In real app, bed mapping provides this.
        # Fallback: Assume center_x/y are roughly mm if 1px=1mm (unlikely but safe fallback)
        return CNCCoordinate(obj.center.x, obj.center.y, 0)

    def _distance(self, p1: CNCCoordinate, p2: CNCCoordinate) -> float:
        """Euclidean distance."""
        return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)

    def _classify_size(self, area: float) -> Tuple[str, str]:
        """Helper to classify size using global config."""
        from cncsorter.config import classify_object_by_size
        return classify_object_by_size(area)
