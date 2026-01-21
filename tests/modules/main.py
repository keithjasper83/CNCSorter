import cv2
import numpy as np

class ObjectDetectorApp:
    def __init__(self):
        self.thresh_val = 127
        self.min_area = 150
        self.cap = None
        self.running = False

    def on_threshold_change(self, val):
        self.thresh_val = val

    def on_min_area_change(self, val):
        self.min_area = val

    def run(self):
        # Initialize Camera
        self.cap = cv2.VideoCapture(0)

        # Create a window for the controls
        cv2.namedWindow("Settings")
        cv2.createTrackbar("Threshold", "Settings", self.thresh_val, 255, self.on_threshold_change)
        cv2.createTrackbar("Min Area", "Settings", self.min_area, 5000, self.on_min_area_change)

        print("Press 's' to save a snapshot, 'q' to quit.")

        self.running = True
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break

            # 1. Pre-processing
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)

            # 2. Get values from instance variables (cached from callbacks)
            # Optimized: No longer polling getTrackbarPos every frame

            # 3. Thresholding (Invert so objects are white, background is black)
            _, thresh = cv2.threshold(blur, self.thresh_val, 255, cv2.THRESH_BINARY_INV)

            # 4. Find Contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 5. Draw and ID
            obj_count = 0
            for cnt in contours:
                if cv2.contourArea(cnt) > self.min_area:
                    obj_count += 1
                    # Get bounding box for the label
                    x, y, w, h = cv2.boundingRect(cnt)
                    # Draw green outline
                    cv2.drawContours(frame, [cnt], -1, (0, 255, 0), 2)
                    # Label it
                    cv2.putText(frame, f"Obj {obj_count}", (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # 6. Show the visual output
            # Concatenate the threshold view so you can see the "binary" logic too
            thresh_bgr = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
            stacked = np.hstack((frame, thresh_bgr))

            cv2.imshow("Live Feed (Left) | Computer Vision (Right)", stacked)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.running = False
            elif key == ord('s'):
                # Save the current view for your commute notes
                cv2.imwrite(f"snapshot_{obj_count}_objs.jpg", frame)
                print("Snapshot saved!")

        self.cleanup()

    def cleanup(self):
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = ObjectDetectorApp()
    app.run()
