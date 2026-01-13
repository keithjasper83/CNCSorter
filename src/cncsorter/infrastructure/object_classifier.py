"""
Object Classification System

Shape-based classifier for identifying fasteners (M2-M12) and guessing
unknown objects. Uses geometric features like circularity, aspect ratio,
and area to classify objects for pick and place operations.
"""

import cv2
import numpy as np
from typing import Tuple, Dict, List, Optional
from dataclasses import dataclass

# Import domain entities
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.domain.entities import DetectedObject


@dataclass
class ObjectClassification:
    """Classification result for a detected object."""
    shape_type: str  # circular, hexagonal, rectangular, irregular
    size_category: str  # tiny, small, medium, large
    estimated_size: str  # M2, M3, ..., M12, or "unknown"
    likely_types: List[str]  # Possible object types (nut, bolt, washer, etc.)
    confidence: float  # 0.0-1.0
    needs_review: bool
    shape_features: Dict  # Detailed geometric features


class ObjectClassifier:
    """
    Classifies detected objects based on shape and size features.
    Handles both standard fasteners (M2-M12) and unknown objects.
    """

    def __init__(self):
        """Initialize the classifier with shape templates."""
        self.shape_templates = self._load_shape_templates()
        self.size_calibration = self._load_size_calibration()

    def _load_shape_templates(self) -> Dict:
        """Load shape classification templates."""
        return {
            "circular": {
                "aspect_ratio_range": (0.85, 1.15),
                "circularity_min": 0.7,
                "corner_count_range": (0, 8),  # Allow some corners for imperfect circles
                "likely_types": ["washer", "nut", "spring_washer", "o-ring", "bearing"],
            },
            "hexagonal": {
                "aspect_ratio_range": (0.9, 1.1),
                "circularity_range": (0.6, 0.85),
                "corner_count_range": (5, 7),  # 6 corners ± tolerance
                "likely_types": ["hex_nut", "hex_bolt_head"],
            },
            "rectangular": {
                "aspect_ratio_range": (1.5, 5.0),
                "circularity_max": 0.5,
                "corner_count_range": (3, 5),  # 4 corners ± tolerance
                "likely_types": ["bolt", "screw", "pin", "nail", "standoff"],
            },
            "elongated_circular": {
                "aspect_ratio_range": (1.2, 1.8),
                "circularity_range": (0.5, 0.7),
                "likely_types": ["spring_washer", "lock_washer", "clip"],
            },
            "irregular": {
                # Catch-all for objects that don't fit other categories
                "circularity_max": 0.6,
                "likely_types": ["wire", "clip", "spring", "debris", "unknown"],
            },
        }

    def _load_size_calibration(self) -> Dict:
        """Load size calibration for M2-M12 fasteners."""
        return {
            "M2": {"min_px": 50, "max_px": 100, "typical_diameter_mm": 2.0},
            "M3": {"min_px": 80, "max_px": 180, "typical_diameter_mm": 3.0},
            "M4": {"min_px": 120, "max_px": 280, "typical_diameter_mm": 4.0},
            "M5": {"min_px": 150, "max_px": 400, "typical_diameter_mm": 5.0},
            "M6": {"min_px": 200, "max_px": 600, "typical_diameter_mm": 6.0},
            "M8": {"min_px": 350, "max_px": 1000, "typical_diameter_mm": 8.0},
            "M10": {"min_px": 550, "max_px": 1500, "typical_diameter_mm": 10.0},
            "M12": {"min_px": 800, "max_px": 2000, "typical_diameter_mm": 12.0},
        }

    def calculate_shape_features(self, contour: np.ndarray) -> Dict:
        """
        Calculate geometric features from contour.

        Args:
            contour: OpenCV contour (Nx2 numpy array)

        Returns:
            Dictionary of shape features
        """
        # Basic properties
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)

        # Bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / h if h > 0 else 0

        # Circularity (4*pi*area / perimeter^2)
        # Perfect circle = 1.0, lower values = less circular
        circularity = (4 * np.pi * area) / (perimeter * perimeter) if perimeter > 0 else 0

        # Approximate polygon to count corners
        epsilon = 0.02 * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, True)
        corner_count = len(approx)

        # Convexity
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = float(area) / hull_area if hull_area > 0 else 0

        # Extent (object area / bounding box area)
        rect_area = w * h
        extent = float(area) / rect_area if rect_area > 0 else 0

        # Moments for centroid
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = x + w // 2, y + h // 2

        return {
            "area": area,
            "perimeter": perimeter,
            "aspect_ratio": aspect_ratio,
            "circularity": circularity,
            "corner_count": corner_count,
            "solidity": solidity,
            "extent": extent,
            "centroid": (cx, cy),
            "bounding_box": (x, y, w, h),
        }

    def classify_shape(self, features: Dict) -> Tuple[str, List[str], float]:
        """
        Classify object shape based on geometric features.

        Args:
            features: Dictionary from calculate_shape_features()

        Returns:
            Tuple of (shape_type, likely_types, confidence)
        """
        aspect_ratio = features["aspect_ratio"]
        circularity = features["circularity"]
        corner_count = features["corner_count"]

        best_match = None
        best_confidence = 0.0

        for shape_type, template in self.shape_templates.items():
            confidence = 0.0
            match_count = 0

            # Check aspect ratio
            if "aspect_ratio_range" in template:
                ar_min, ar_max = template["aspect_ratio_range"]
                if ar_min <= aspect_ratio <= ar_max:
                    confidence += 0.3
                    match_count += 1
                else:
                    continue  # Hard constraint

            # Check circularity
            if "circularity_min" in template:
                if circularity >= template["circularity_min"]:
                    confidence += 0.25
                    match_count += 1

            if "circularity_max" in template:
                if circularity <= template["circularity_max"]:
                    confidence += 0.25
                    match_count += 1

            if "circularity_range" in template:
                c_min, c_max = template["circularity_range"]
                if c_min <= circularity <= c_max:
                    confidence += 0.3
                    match_count += 1

            # Check corner count
            if "corner_count_range" in template:
                c_min, c_max = template["corner_count_range"]
                if c_min <= corner_count <= c_max:
                    confidence += 0.2
                    match_count += 1

            # Normalize confidence
            if match_count > 0:
                confidence = confidence / match_count

                # Boost confidence for high circularity on circular shapes
                if shape_type == "circular" and circularity > 0.85:
                    confidence += 0.15

                # Boost confidence for hexagonal with 6 corners
                if shape_type == "hexagonal" and corner_count == 6:
                    confidence += 0.15

                confidence = min(confidence, 1.0)

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = (shape_type, template["likely_types"])

        if best_match:
            return (best_match[0], best_match[1], best_confidence)

        # Default to irregular with low confidence
        return ("irregular", ["unknown", "debris"], 0.3)

    def classify_size(self, area: float) -> Tuple[str, str]:
        """
        Classify object size based on pixel area.

        Args:
            area: Object area in pixels

        Returns:
            Tuple of (size_category, estimated_size)
        """
        # Try to match to M2-M12 sizes
        for size_name, calibration in self.size_calibration.items():
            if calibration["min_px"] <= area <= calibration["max_px"]:
                # Determine category
                if size_name in ["M2", "M3"]:
                    category = "tiny"
                elif size_name in ["M4", "M5", "M6"]:
                    category = "small"
                elif size_name in ["M8", "M10"]:
                    category = "medium"
                else:
                    category = "large"

                return (category, size_name)

        # Outside known range
        if area < 50:
            return ("tiny", "sub-M2")
        elif area > 2000:
            return ("large", "super-M12")
        else:
            return ("unknown", "unclassified")

    def classify(self, detected_object: DetectedObject) -> ObjectClassification:
        """
        Perform full classification on a detected object.

        Args:
            detected_object: DetectedObject from vision system

        Returns:
            ObjectClassification with complete analysis
        """
        # Calculate shape features from contour
        if detected_object.contour is not None and len(detected_object.contour) > 0:
            # Convert contour to proper format if needed
            if isinstance(detected_object.contour, list):
                contour = np.array(detected_object.contour, dtype=np.int32)
            else:
                contour = detected_object.contour

            features = self.calculate_shape_features(contour)
        else:
            # Fallback: use basic properties
            features = {
                "area": detected_object.area,
                "aspect_ratio": 1.0,  # Unknown
                "circularity": 0.5,  # Unknown
                "corner_count": 0,
                "solidity": 1.0,
                "extent": 1.0,
                "centroid": (detected_object.x, detected_object.y),
                "bounding_box": (detected_object.x, detected_object.y, 10, 10),
            }

        # Classify shape
        shape_type, likely_types, shape_confidence = self.classify_shape(features)

        # Classify size
        size_category, estimated_size = self.classify_size(detected_object.area)

        # Overall confidence combines shape and size confidence
        overall_confidence = shape_confidence

        # Reduce confidence for unknown sizes
        if estimated_size in ["unclassified", "sub-M2", "super-M12"]:
            overall_confidence *= 0.7

        # Determine if manual review is needed
        needs_review = overall_confidence < 0.50 or estimated_size == "unclassified"

        return ObjectClassification(
            shape_type=shape_type,
            size_category=size_category,
            estimated_size=estimated_size,
            likely_types=likely_types,
            confidence=overall_confidence,
            needs_review=needs_review,
            shape_features=features,
        )

    def batch_classify(self, detected_objects: List[DetectedObject]) -> List[ObjectClassification]:
        """
        Classify multiple objects.

        Args:
            detected_objects: List of DetectedObjects

        Returns:
            List of ObjectClassifications
        """
        return [self.classify(obj) for obj in detected_objects]


# ============================================================================
# PICK AND PLACE DATA EXPORT
# ============================================================================

def export_to_pick_and_place_csv(
    detected_objects: List[DetectedObject],
    classifications: List[ObjectClassification],
    cnc_positions: List[Tuple[float, float, float]],
    output_path: str,
    pixels_per_mm: float = 5.0
) -> str:
    """
    Export detection and classification data to CSV for pick and place.

    Args:
        detected_objects: List of DetectedObject entities
        classifications: Corresponding ObjectClassification results
        cnc_positions: List of (x_mm, y_mm, z_mm) CNC coordinates
        output_path: Path to output CSV file
        pixels_per_mm: Calibration factor for pixel to mm conversion

    Returns:
        Path to created CSV file
    """
    import csv
    from datetime import datetime

    # Ensure lists are same length
    assert len(detected_objects) == len(classifications) == len(cnc_positions)

    # CSV column headers
    headers = [
        "object_id",
        "x_mm",
        "y_mm",
        "z_mm",
        "area_px",
        "size_category",
        "estimated_size",
        "shape_type",
        "likely_type_1",
        "likely_type_2",
        "likely_type_3",
        "confidence",
        "needs_review",
        "circularity",
        "aspect_ratio",
        "corner_count",
        "timestamp",
    ]

    timestamp = datetime.now().isoformat()

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()

        for obj, cls, cnc_pos in zip(detected_objects, classifications, cnc_positions):
            # Convert pixel coordinates to mm
            x_mm = cnc_pos[0] + (obj.x / pixels_per_mm)
            y_mm = cnc_pos[1] + (obj.y / pixels_per_mm)
            z_mm = cnc_pos[2]

            # Get up to 3 likely types
            likely_types = cls.likely_types + ["", "", ""]  # Pad with empty strings

            row = {
                "object_id": obj.object_id,
                "x_mm": f"{x_mm:.2f}",
                "y_mm": f"{y_mm:.2f}",
                "z_mm": f"{z_mm:.2f}",
                "area_px": obj.area,
                "size_category": cls.size_category,
                "estimated_size": cls.estimated_size,
                "shape_type": cls.shape_type,
                "likely_type_1": likely_types[0],
                "likely_type_2": likely_types[1],
                "likely_type_3": likely_types[2],
                "confidence": f"{cls.confidence:.3f}",
                "needs_review": str(cls.needs_review),
                "circularity": f"{cls.shape_features.get('circularity', 0):.3f}",
                "aspect_ratio": f"{cls.shape_features.get('aspect_ratio', 0):.3f}",
                "corner_count": cls.shape_features.get('corner_count', 0),
                "timestamp": timestamp,
            }

            writer.writerow(row)

    return output_path


# ============================================================================
# TESTING AND VALIDATION
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Object Classifier Test")
    print("=" * 70)

    # Create test classifier
    classifier = ObjectClassifier()

    # Test with synthetic contours
    print("\n1. Testing Circular Object (Washer)")
    circle_contour = np.array([
        [100 + int(20 * np.cos(theta)), 100 + int(20 * np.sin(theta))]
        for theta in np.linspace(0, 2*np.pi, 50)
    ], dtype=np.int32)

    features = classifier.calculate_shape_features(circle_contour)
    print(f"   Area: {features['area']:.1f} px")
    print(f"   Circularity: {features['circularity']:.3f}")
    print(f"   Aspect Ratio: {features['aspect_ratio']:.3f}")
    print(f"   Corners: {features['corner_count']}")

    shape_type, likely_types, confidence = classifier.classify_shape(features)
    print(f"   Classification: {shape_type}")
    print(f"   Likely Types: {', '.join(likely_types[:3])}")
    print(f"   Confidence: {confidence:.2f}")

    print("\n2. Testing Hexagonal Object (Nut)")
    hex_contour = np.array([
        [100 + int(20 * np.cos(theta)), 100 + int(20 * np.sin(theta))]
        for theta in np.linspace(0, 2*np.pi, 7)  # 6 vertices + close
    ], dtype=np.int32)

    features = classifier.calculate_shape_features(hex_contour)
    print(f"   Area: {features['area']:.1f} px")
    print(f"   Circularity: {features['circularity']:.3f}")
    print(f"   Corners: {features['corner_count']}")

    shape_type, likely_types, confidence = classifier.classify_shape(features)
    print(f"   Classification: {shape_type}")
    print(f"   Likely Types: {', '.join(likely_types[:3])}")
    print(f"   Confidence: {confidence:.2f}")

    print("\n3. Size Classification Test")
    test_sizes = [75, 150, 300, 700, 1200, 2500]
    for area in test_sizes:
        category, size = classifier.classify_size(area)
        print(f"   Area {area}px → {category} ({size})")

    print("\n" + "=" * 70)
    print("Object Classifier Ready for Production")
    print("=" * 70)
