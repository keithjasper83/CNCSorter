"""Live status display for Raspberry Pi with full process monitoring."""
import cv2
import numpy as np
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..domain.entities import DetectedObject, CNCCoordinate, BedMap


class LiveStatusDisplay:
    """Comprehensive live status display for Raspberry Pi screen."""
    
    def __init__(self, width: int = 1280, height: int = 720):
        """
        Initialize the live status display.
        
        Args:
            width: Display width
            height: Display height
        """
        self.width = width
        self.height = height
        self.window_name = "CNCSorter - Live Status"
        
        # Status tracking
        self.status_message = "Initializing..."
        self.current_stage = "STARTUP"
        self.progress_percent = 0
        self.objects_detected = 0
        self.images_captured = 0
        self.cnc_position: Optional[CNCCoordinate] = None
        self.fps = 0
        self.last_update = datetime.now()
        
        # Colors (BGR format)
        self.COLOR_BG = (40, 40, 40)
        self.COLOR_PANEL = (60, 60, 60)
        self.COLOR_TEXT = (255, 255, 255)
        self.COLOR_SUCCESS = (0, 255, 0)
        self.COLOR_WARNING = (0, 165, 255)
        self.COLOR_ERROR = (0, 0, 255)
        self.COLOR_ACCENT = (255, 200, 0)
        
        # Layout
        self.panel_margin = 10
        self.header_height = 80
        self.status_panel_height = 200
        self.footer_height = 40
        
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, width, height)
    
    def create_base_canvas(self) -> np.ndarray:
        """Create the base canvas for the display."""
        canvas = np.full((self.height, self.width, 3), self.COLOR_BG, dtype=np.uint8)
        return canvas
    
    def draw_header(self, canvas: np.ndarray):
        """Draw the header section."""
        # Header background
        cv2.rectangle(
            canvas,
            (0, 0),
            (self.width, self.header_height),
            self.COLOR_PANEL,
            -1
        )
        
        # Title
        cv2.putText(
            canvas,
            "CNCSorter - CNC Object Detection & Mapping",
            (20, 40),
            cv2.FONT_HERSHEY_BOLD,
            1.0,
            self.COLOR_ACCENT,
            2
        )
        
        # Current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(
            canvas,
            current_time,
            (self.width - 300, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            self.COLOR_TEXT,
            1
        )
        
        # FPS indicator
        fps_text = f"FPS: {self.fps:.1f}"
        cv2.putText(
            canvas,
            fps_text,
            (self.width - 150, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            self.COLOR_SUCCESS if self.fps > 20 else self.COLOR_WARNING,
            1
        )
    
    def draw_status_panel(self, canvas: np.ndarray):
        """Draw the status information panel."""
        y_start = self.header_height + self.panel_margin
        panel_height = self.status_panel_height
        
        # Status panel background
        cv2.rectangle(
            canvas,
            (self.panel_margin, y_start),
            (self.width - self.panel_margin, y_start + panel_height),
            self.COLOR_PANEL,
            -1
        )
        
        # Current stage
        stage_color = self._get_stage_color()
        cv2.putText(
            canvas,
            f"Stage: {self.current_stage}",
            (20, y_start + 35),
            cv2.FONT_HERSHEY_BOLD,
            0.8,
            stage_color,
            2
        )
        
        # Status message
        cv2.putText(
            canvas,
            self.status_message,
            (20, y_start + 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            self.COLOR_TEXT,
            1
        )
        
        # Progress bar
        self._draw_progress_bar(canvas, 20, y_start + 90, self.width - 40, 30)
        
        # Statistics
        stats_y = y_start + 140
        col1_x = 20
        col2_x = self.width // 2
        
        cv2.putText(
            canvas,
            f"Images Captured: {self.images_captured}",
            (col1_x, stats_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            self.COLOR_TEXT,
            1
        )
        
        cv2.putText(
            canvas,
            f"Objects Detected: {self.objects_detected}",
            (col2_x, stats_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            self.COLOR_TEXT,
            1
        )
        
        # CNC Position
        if self.cnc_position:
            pos_text = f"CNC: X={self.cnc_position.x:.2f} Y={self.cnc_position.y:.2f} Z={self.cnc_position.z:.2f}"
            cv2.putText(
                canvas,
                pos_text,
                (col1_x, stats_y + 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                self.COLOR_ACCENT,
                1
            )
    
    def _draw_progress_bar(self, canvas: np.ndarray, x: int, y: int, width: int, height: int):
        """Draw a progress bar."""
        # Background
        cv2.rectangle(canvas, (x, y), (x + width, y + height), (80, 80, 80), -1)
        
        # Progress fill
        fill_width = int(width * (self.progress_percent / 100.0))
        if fill_width > 0:
            color = self.COLOR_SUCCESS if self.progress_percent == 100 else self.COLOR_ACCENT
            cv2.rectangle(canvas, (x, y), (x + fill_width, y + height), color, -1)
        
        # Border
        cv2.rectangle(canvas, (x, y), (x + width, y + height), self.COLOR_TEXT, 2)
        
        # Percentage text
        text = f"{self.progress_percent:.0f}%"
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)[0]
        text_x = x + (width - text_size[0]) // 2
        text_y = y + (height + text_size[1]) // 2
        cv2.putText(canvas, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.COLOR_TEXT, 1)
    
    def draw_camera_view(
        self,
        canvas: np.ndarray,
        frame: Optional[np.ndarray],
        detected_objects: Optional[List[DetectedObject]] = None
    ):
        """Draw the camera view with detected objects."""
        y_start = self.header_height + self.status_panel_height + 2 * self.panel_margin
        view_height = self.height - y_start - self.footer_height - self.panel_margin
        view_width = self.width - 2 * self.panel_margin
        
        if frame is not None:
            # Resize frame to fit the view area
            resized_frame = cv2.resize(frame, (view_width, view_height))
            
            # Draw detected objects if provided
            if detected_objects:
                for obj in detected_objects:
                    x, y, w, h = obj.bounding_box
                    # Scale coordinates to resized frame
                    scale_x = view_width / frame.shape[1]
                    scale_y = view_height / frame.shape[0]
                    
                    scaled_x = int(x * scale_x)
                    scaled_y = int(y * scale_y)
                    scaled_w = int(w * scale_x)
                    scaled_h = int(h * scale_y)
                    
                    # Draw bounding box
                    cv2.rectangle(
                        resized_frame,
                        (scaled_x, scaled_y),
                        (scaled_x + scaled_w, scaled_y + scaled_h),
                        self.COLOR_SUCCESS,
                        2
                    )
                    
                    # Draw label
                    label = f"Obj {obj.object_id}"
                    cv2.putText(
                        resized_frame,
                        label,
                        (scaled_x, scaled_y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        self.COLOR_SUCCESS,
                        2
                    )
            
            # Place frame on canvas
            canvas[y_start:y_start + view_height, self.panel_margin:self.panel_margin + view_width] = resized_frame
        else:
            # No camera feed - show placeholder
            cv2.rectangle(
                canvas,
                (self.panel_margin, y_start),
                (self.panel_margin + view_width, y_start + view_height),
                self.COLOR_PANEL,
                -1
            )
            
            text = "No Camera Feed"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
            text_x = self.panel_margin + (view_width - text_size[0]) // 2
            text_y = y_start + (view_height + text_size[1]) // 2
            cv2.putText(
                canvas,
                text,
                (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                self.COLOR_WARNING,
                2
            )
    
    def draw_footer(self, canvas: np.ndarray):
        """Draw the footer with controls."""
        y_start = self.height - self.footer_height
        
        # Footer background
        cv2.rectangle(
            canvas,
            (0, y_start),
            (self.width, self.height),
            self.COLOR_PANEL,
            -1
        )
        
        # Control hints
        controls = "Controls: [SPACE] Capture Image | [S] Start Map | [M] Stitch Map | [Q] Quit"
        cv2.putText(
            canvas,
            controls,
            (20, y_start + 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            self.COLOR_TEXT,
            1
        )
    
    def _get_stage_color(self) -> tuple:
        """Get color for current stage."""
        stage_colors = {
            "STARTUP": self.COLOR_WARNING,
            "READY": self.COLOR_SUCCESS,
            "CAPTURING": self.COLOR_ACCENT,
            "PROCESSING": self.COLOR_ACCENT,
            "STITCHING": self.COLOR_ACCENT,
            "COMPLETE": self.COLOR_SUCCESS,
            "ERROR": self.COLOR_ERROR
        }
        return stage_colors.get(self.current_stage, self.COLOR_TEXT)
    
    def update(
        self,
        frame: Optional[np.ndarray] = None,
        detected_objects: Optional[List[DetectedObject]] = None,
        status: Optional[str] = None,
        stage: Optional[str] = None,
        progress: Optional[float] = None,
        cnc_pos: Optional[CNCCoordinate] = None,
        images_count: Optional[int] = None,
        objects_count: Optional[int] = None,
        fps: Optional[float] = None
    ):
        """
        Update the display with new information.
        
        Args:
            frame: Camera frame to display
            detected_objects: List of detected objects
            status: Status message
            stage: Current stage
            progress: Progress percentage (0-100)
            cnc_pos: Current CNC position
            images_count: Number of images captured
            objects_count: Number of objects detected
            fps: Current FPS
        """
        # Update internal state
        if status is not None:
            self.status_message = status
        if stage is not None:
            self.current_stage = stage
        if progress is not None:
            self.progress_percent = max(0, min(100, progress))
        if cnc_pos is not None:
            self.cnc_position = cnc_pos
        if images_count is not None:
            self.images_captured = images_count
        if objects_count is not None:
            self.objects_detected = objects_count
        if fps is not None:
            self.fps = fps
        
        # Create canvas
        canvas = self.create_base_canvas()
        
        # Draw all components
        self.draw_header(canvas)
        self.draw_status_panel(canvas)
        self.draw_camera_view(canvas, frame, detected_objects)
        self.draw_footer(canvas)
        
        # Show the display
        cv2.imshow(self.window_name, canvas)
    
    def wait_key(self, delay: int = 1) -> int:
        """
        Wait for key press.
        
        Args:
            delay: Delay in milliseconds
            
        Returns:
            Key code
        """
        return cv2.waitKey(delay) & 0xFF
    
    def close(self):
        """Close the display window."""
        cv2.destroyWindow(self.window_name)
