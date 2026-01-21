import cv2
import numpy as np

def nothing(x):
    pass

# Initialize Camera
cap = cv2.VideoCapture(0)

stacked = None

# Create a window for the controls
cv2.namedWindow("Settings")
cv2.createTrackbar("Threshold", "Settings", 127, 255, nothing)
cv2.createTrackbar("Min Area", "Settings", 150, 5000, nothing)

print("Press 's' to save a snapshot, 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
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
    h, w = frame.shape[:2]
    if stacked is None or stacked.shape[0] != h or stacked.shape[1] != w * 2:
        stacked = np.zeros((h, w * 2, 3), dtype=np.uint8)

    stacked[:, :w] = frame
    cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR, dst=stacked[:, w:])
    
    cv2.imshow("Live Feed (Left) | Computer Vision (Right)", stacked)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        # Save the current view for your commute notes
        cv2.imwrite(f"snapshot_{obj_count}_objs.jpg", frame)
        print("Snapshot saved!")

cap.release()
cv2.destroyAllWindows()
