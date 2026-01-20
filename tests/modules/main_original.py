import cv2
import numpy as np
import sys


def nothing(x):
    """Placeholder callback function for trackbar events."""
    pass


def main():
    """Main function to run the CNCSorter object detection application."""
    # Initialize Camera
    cap = cv2.VideoCapture(0)

    # Check if camera opened successfully
    if not cap.isOpened():
        print("Error: Could not open camera.")
        print("Please check:")
        print("  - Camera is connected")
        print("  - Camera permissions are granted")
        print("  - No other application is using the camera")
        sys.exit(1)

    print("Camera initialized successfully.")

    # Create a window for the controls
    cv2.namedWindow("Settings")
    cv2.createTrackbar("Threshold", "Settings", 127, 255, nothing)
    cv2.createTrackbar("Min Area", "Settings", 150, 5000, nothing)

    print("Press 's' to save a snapshot, 'q' to quit.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture frame from camera.")
                break

            # 1. Pre-processing
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)

            # 2. Get values from sliders
            thresh_val = cv2.getTrackbarPos("Threshold", "Settings")
            min_area = cv2.getTrackbarPos("Min Area", "Settings")

            # 3. Thresholding (Invert so objects are white, background is black)
            _, thresh = cv2.threshold(blur, thresh_val, 255, cv2.THRESH_BINARY_INV)

            # 4. Find Contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 5. Draw and ID
            obj_count = 0
            for cnt in contours:
                if cv2.contourArea(cnt) > min_area:
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
                break
            elif key == ord('s'):
                # Save the current frame for documentation and analysis
                filename = f"snapshot_{obj_count}_objs.jpg"
                cv2.imwrite(filename, frame)
                print(f"Snapshot saved as '{filename}'!")

    finally:
        # Clean up resources
        cap.release()
        cv2.destroyAllWindows()
        print("Application closed.")


if __name__ == "__main__":
    main()
