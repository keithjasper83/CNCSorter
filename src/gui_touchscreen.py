"""Touchscreen GUI for Raspberry Pi - Simple, touch-friendly interface."""
import tkinter as tk
from tkinter import messagebox
from typing import Optional
from datetime import datetime

from infrastructure.vision import VisionSystem, ImageStitcher
from infrastructure.cnc_controller import FluidNCSerial, FluidNCHTTP, CNCController
from application.bed_mapping import BedMappingService
from domain.entities import BedMap


class TouchscreenGUI:
    """Touch-friendly GUI for Raspberry Pi with large buttons and clear status."""

    def __init__(self, root: tk.Tk):
        """
        Initialize the touchscreen GUI.

        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("CNCSorter - Touchscreen Interface")

        # Make fullscreen on Raspberry Pi
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='#2c3e50')

        # Components
        self.vision_system: Optional[VisionSystem] = None
        self.cnc_controller: Optional[CNCController] = None
        self.bed_mapping_service: Optional[BedMappingService] = None
        self.current_map: Optional[BedMap] = None

        # State
        self.is_running = False
        self.camera_active = False
        self.cnc_connected = False
        self.objects_detected = 0
        self.images_captured = 0

        # UI Elements
        self.status_var = tk.StringVar(value="Ready")
        self.cnc_pos_var = tk.StringVar(value="CNC: Disconnected")
        self.stats_var = tk.StringVar(value="Images: 0 | Objects: 0")

        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface with large touch-friendly buttons."""
        # Header
        header = tk.Frame(self.root, bg='#34495e', height=80)
        header.pack(fill=tk.X, side=tk.TOP)

        title = tk.Label(
            header,
            text="CNCSorter",
            font=('Arial', 28, 'bold'),
            bg='#34495e',
            fg='#ecf0f1'
        )
        title.pack(side=tk.LEFT, padx=20, pady=10)

        # Exit button in header
        exit_btn = tk.Button(
            header,
            text="✕ Exit",
            font=('Arial', 18, 'bold'),
            bg='#e74c3c',
            fg='white',
            command=self.exit_app,
            relief=tk.FLAT,
            width=8,
            height=2
        )
        exit_btn.pack(side=tk.RIGHT, padx=20, pady=10)

        # Status Panel
        status_frame = tk.Frame(self.root, bg='#34495e', height=100)
        status_frame.pack(fill=tk.X, pady=5)

        status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            font=('Arial', 20),
            bg='#34495e',
            fg='#ecf0f1'
        )
        status_label.pack(pady=10)

        info_frame = tk.Frame(status_frame, bg='#34495e')
        info_frame.pack(fill=tk.X, padx=20)

        cnc_label = tk.Label(
            info_frame,
            textvariable=self.cnc_pos_var,
            font=('Arial', 14),
            bg='#34495e',
            fg='#95a5a6'
        )
        cnc_label.pack(side=tk.LEFT, padx=10)

        stats_label = tk.Label(
            info_frame,
            textvariable=self.stats_var,
            font=('Arial', 14),
            bg='#34495e',
            fg='#95a5a6'
        )
        stats_label.pack(side=tk.RIGHT, padx=10)

        # Main Button Grid
        btn_frame = tk.Frame(self.root, bg='#2c3e50')
        btn_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        # Configure grid
        for i in range(3):
            btn_frame.grid_rowconfigure(i, weight=1)
        for i in range(3):
            btn_frame.grid_columnconfigure(i, weight=1)

        # Button configurations
        buttons = [
            ("🎥 Start\nCamera", self.start_camera, '#3498db', 0, 0),
            ("🔌 Connect\nCNC", self.connect_cnc, '#9b59b6', 0, 1),
            ("📋 New\nMap", self.start_new_map, '#1abc9c', 0, 2),
            ("📸 Capture\nImage", self.capture_image, '#f39c12', 1, 0),
            ("🔄 Stitch\nImages", self.stitch_map, '#e67e22', 1, 1),
            ("💾 Save\nMap", self.save_map, '#27ae60', 1, 2),
            ("🛑 Stop\nCamera", self.stop_camera, '#c0392b', 2, 0),
            ("🔧 Test\nMode", self.launch_test_mode, '#7f8c8d', 2, 1),
            ("ℹ️ Info", self.show_info, '#34495e', 2, 2),
        ]

        for text, command, color, row, col in buttons:
            btn = tk.Button(
                btn_frame,
                text=text,
                font=('Arial', 18, 'bold'),
                bg=color,
                fg='white',
                command=command,
                relief=tk.RAISED,
                bd=5
            )
            btn.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')

        # Footer
        footer = tk.Frame(self.root, bg='#34495e', height=40)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        footer_text = tk.Label(
            footer,
            text=f"© 2026 CNCSorter | {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            font=('Arial', 10),
            bg='#34495e',
            fg='#95a5a6'
        )
        footer_text.pack(pady=10)

    def start_camera(self):
        """Start the camera system."""
        if self.camera_active:
            messagebox.showinfo("Info", "Camera is already active")
            return

        try:
            self.vision_system = VisionSystem(camera_index=0)
            if self.vision_system.open_camera():
                self.camera_active = True
                self.status_var.set("Status: Camera Active")
                messagebox.showinfo("Success", "Camera started successfully!")

                # Initialize bed mapping service
                if self.bed_mapping_service is None:
                    image_stitcher = ImageStitcher()
                    self.bed_mapping_service = BedMappingService(
                        self.vision_system,
                        self.cnc_controller,
                        image_stitcher
                    )
            else:
                messagebox.showerror("Error", "Failed to open camera")
        except Exception as e:
            messagebox.showerror("Error", f"Camera error: {e}")

    def stop_camera(self):
        """Stop the camera system."""
        if not self.camera_active:
            messagebox.showinfo("Info", "Camera is not active")
            return

        try:
            if self.vision_system:
                self.vision_system.close_camera()
                self.camera_active = False
                self.status_var.set("Status: Camera Stopped")
                messagebox.showinfo("Success", "Camera stopped")
        except Exception as e:
            messagebox.showerror("Error", f"Error stopping camera: {e}")

    def connect_cnc(self):
        """Connect to CNC controller."""
        if self.cnc_connected:
            messagebox.showinfo("Info", "CNC is already connected")
            return

        # Create dialog for connection type
        dialog = tk.Toplevel(self.root)
        dialog.title("Connect CNC")
        dialog.geometry("400x300")
        dialog.configure(bg='#ecf0f1')

        tk.Label(
            dialog,
            text="Select Connection Type",
            font=('Arial', 16, 'bold'),
            bg='#ecf0f1'
        ).pack(pady=20)

        def connect_serial():
            try:
                self.cnc_controller = FluidNCSerial('/dev/ttyUSB0', 115200)
                if self.cnc_controller.connect():
                    self.cnc_connected = True
                    self.status_var.set("Status: CNC Connected (Serial)")
                    self.update_cnc_position()
                    dialog.destroy()
                    messagebox.showinfo("Success", "CNC connected via Serial")
                else:
                    messagebox.showerror("Error", "Failed to connect to CNC via Serial")
            except Exception as e:
                messagebox.showerror("Error", f"Serial connection error: {e}")

        def connect_http():
            try:
                self.cnc_controller = FluidNCHTTP('192.168.1.100', 80)
                if self.cnc_controller.connect():
                    self.cnc_connected = True
                    self.status_var.set("Status: CNC Connected (HTTP)")
                    self.update_cnc_position()
                    dialog.destroy()
                    messagebox.showinfo("Success", "CNC connected via HTTP")
                else:
                    messagebox.showerror("Error", "Failed to connect to CNC via HTTP")
            except Exception as e:
                messagebox.showerror("Error", f"HTTP connection error: {e}")

        tk.Button(
            dialog,
            text="Serial Connection\n(/dev/ttyUSB0)",
            font=('Arial', 14),
            bg='#3498db',
            fg='white',
            command=connect_serial,
            height=2,
            width=25
        ).pack(pady=10)

        tk.Button(
            dialog,
            text="HTTP Connection\n(192.168.1.100)",
            font=('Arial', 14),
            bg='#9b59b6',
            fg='white',
            command=connect_http,
            height=2,
            width=25
        ).pack(pady=10)

        tk.Button(
            dialog,
            text="Cancel",
            font=('Arial', 12),
            bg='#95a5a6',
            fg='white',
            command=dialog.destroy,
            height=1,
            width=15
        ).pack(pady=10)

    def start_new_map(self):
        """Start a new bed mapping session."""
        if not self.camera_active:
            messagebox.showwarning("Warning", "Please start the camera first")
            return

        if not self.bed_mapping_service:
            messagebox.showerror("Error", "Bed mapping service not initialized")
            return

        self.current_map = self.bed_mapping_service.start_new_map()
        self.images_captured = 0
        self.objects_detected = 0
        self.update_stats()
        self.status_var.set("Status: New Map Started")
        messagebox.showinfo("Success", f"New map started: {self.current_map.map_id}")

    def capture_image(self):
        """Capture an image and add to current map."""
        if not self.camera_active:
            messagebox.showwarning("Warning", "Please start the camera first")
            return

        if self.current_map is None:
            messagebox.showwarning("Warning", "Please start a new map first")
            return

        try:
            captured = self.bed_mapping_service.capture_and_add_image(
                threshold=127,
                min_area=150
            )

            if captured:
                self.images_captured = len(self.current_map.images)
                self.objects_detected = len(self.current_map.all_objects)
                self.update_stats()
                self.status_var.set(f"Status: Image Captured ({len(captured.detected_objects)} objects)")
                messagebox.showinfo("Success", f"Image captured with {len(captured.detected_objects)} objects!")
        except Exception as e:
            messagebox.showerror("Error", f"Capture error: {e}")

    def stitch_map(self):
        """Stitch all captured images."""
        if self.current_map is None:
            messagebox.showwarning("Warning", "No map to stitch")
            return

        if len(self.current_map.images) < 2:
            messagebox.showwarning("Warning", "Need at least 2 images to stitch")
            return

        self.status_var.set("Status: Stitching images...")
        self.root.update()

        try:
            success = self.bed_mapping_service.stitch_current_map()
            if success:
                self.status_var.set("Status: Stitching Complete!")
                messagebox.showinfo("Success", "Images stitched successfully!")
            else:
                self.status_var.set("Status: Stitching Failed")
                messagebox.showerror("Error", "Failed to stitch images")
        except Exception as e:
            messagebox.showerror("Error", f"Stitching error: {e}")

    def save_map(self):
        """Save the current map to disk."""
        if self.current_map is None:
            messagebox.showwarning("Warning", "No map to save")
            return

        try:
            if self.bed_mapping_service.save_map_images():
                self.status_var.set("Status: Map Saved")
                messagebox.showinfo("Success", f"Map saved: {self.current_map.map_id}")
            else:
                messagebox.showerror("Error", "Failed to save map")
        except Exception as e:
            messagebox.showerror("Error", f"Save error: {e}")

    def launch_test_mode(self):
        """Launch the interactive test menu in a terminal."""
        messagebox.showinfo(
            "Test Mode",
            "Test mode must be launched from terminal:\n\n"
            "python src/test_menu.py\n\n"
            "This allows testing individual components."
        )

    def show_info(self):
        """Show information about the system."""
        info_text = f"""CNCSorter - Touchscreen Interface

Version: 1.0
Platform: Raspberry Pi

Current Status:
• Camera: {'Active' if self.camera_active else 'Inactive'}
• CNC: {'Connected' if self.cnc_connected else 'Disconnected'}
• Images Captured: {self.images_captured}
• Objects Detected: {self.objects_detected}

Controls:
• Start Camera: Initialize vision system
• Connect CNC: Connect to CNC controller
• New Map: Begin new bed mapping session
• Capture Image: Take photo and detect objects
• Stitch Images: Combine all images
• Save Map: Save results to disk

For advanced features, use terminal interface:
python src/main.py
"""
        messagebox.showinfo("System Information", info_text)

    def update_cnc_position(self):
        """Update CNC position display."""
        if self.cnc_connected and self.cnc_controller:
            pos = self.cnc_controller.get_position()
            if pos:
                self.cnc_pos_var.set(f"CNC: X={pos.x:.2f} Y={pos.y:.2f} Z={pos.z:.2f}")
            else:
                self.cnc_pos_var.set("CNC: Position unavailable")

            # Schedule next update
            self.root.after(2000, self.update_cnc_position)
        else:
            self.cnc_pos_var.set("CNC: Disconnected")

    def update_stats(self):
        """Update statistics display."""
        self.stats_var.set(f"Images: {self.images_captured} | Objects: {self.objects_detected}")

    def exit_app(self):
        """Exit the application."""
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            # Cleanup
            if self.camera_active and self.vision_system:
                self.vision_system.close_camera()
            if self.cnc_connected and self.cnc_controller:
                self.cnc_controller.disconnect()

            self.root.quit()
            self.root.destroy()


def main():
    """Main entry point for touchscreen GUI."""
    root = tk.Tk()
    TouchscreenGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
