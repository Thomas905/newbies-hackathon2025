import cv2 as cv
import numpy as np
import os
import time
from collections import deque 

webcam = cv.VideoCapture(0) # Capture using default webcam 

lowerSkin = np.array([7, 40, 60], dtype=np.uint8) # Lower bound of skin color 
upperSkin = np.array([25, 255, 255], dtype=np.uint8) # Upper bound of skin color

# ----------- Tracking & decision params -----------
pts = deque(maxlen=12) # Double-ended queue which store 12 recent frames
AREA_MIN   = 2000 # Smallest contour area that counts as a valid hand\
                  # If a contour is smaller than 2000 -> counted as noise
DEADZONE   = 35 # Min movement distance between the oldest and newest hand position
                # Ignore movement smaller than this
COOLDOWN_S = 0.5 # Time taken between each consecutive commands
last_cmd_time = 0.0 # Time point when last command was executed

# ----------- Function to get command from hand gesture -----------
def determine_command(pts_list, deadzone):
    if (len(pts_list) < 6): return ""
    # Get coordinates of hand from oldest frame and newest 
    (x0, y0), (x1, y1) = pts_list[0], pts_list[-1]
    # Change in x and y coordinates
    dx, dy = x1 - x0, y1 - y0

    if (abs(dx) > abs(dy)):
        # If more change in x axis than y axis
        return "RIGHT" if (dx > deadzone) else "LEFT"
    else:
        # If more change in y axis than x axis
        return "DOWN" if (dy > deadzone) else "UP"
    return ""

# ----------- Face detector (to exclude face from mask) -----------
# Uses OpenCV's built-in Haar cascade
cascade_path = cv.data.haarcascades + "haarcascade_frontalface_default.xml"
if (os.path.exists(cascade_path) == False):
    raise FileNotFoundError("Haar cascade not found: " + cascade_path)
face_cascade = cv.CascadeClassifier(cascade_path)

while (webcam.isOpened()):
    canRead, frame = webcam.read() # Read the webcam 
                                   # and check if it was sucessfully read
    if (canRead == False):
        print("Failed to grab frame")
        break
    # Horizontal flip (make the laptop as a mirror)
    frame = cv.flip(frame, 1) 
    # Convert from BGR to HSV and load images in HSV
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV) 
    # Create a binary mask which keep in pixels within HSV color range                                           
    mask = cv.inRange(hsv, lowerSkin, upperSkin)
    # Create a 5x5 kernel 
    kernel = np.ones((5, 5), np.uint8)
    # Morphological open to remove small, isolated noise in the skin mask
    mask = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel, iterations=1)
    # Morphological close to close small gaps inside the hand region
    mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel, iterations=1)

    # ---- Detect face & remove it from the mask ----
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(80, 80))
    for (fx, fy, fw, fh) in faces:
        # Optional: draw face box for debugging
        cv.rectangle(frame, (fx, fy), (fx+fw, fy+fh), (0, 0, 255), 2)
        # Zero out the face region in the skin mask
        mask[fy:fy+fh, fx:fx+fw] = 0

    # Remove remaining small holes and speckles caused by lighting/shadows
    # (5, 5) kernel and omega = 0 => work in most lightning 
    mask = cv.GaussianBlur(mask, (5, 5), 0) 

    # ---- Find largest remaining contour (hand) ----
    contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    if contours:
        c = max(contours, key=cv.contourArea)
        if cv.contourArea(c) > AREA_MIN: # Filter smaller object than a hand
            # Create a green retangle that cover the contour
            x, y, w, h = cv.boundingRect(c)
            cv.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # Give a single point to represent the hand's location
            M = cv.moments(c)
            if M["m00"] > 0: # Prevent divide by 0
                # (Sum of x/y coordinates in pixels) / (No of pixels) 
                # = Middle pixels within a line of x/y coordinates
                cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
                pts.append((cx, cy)) # Add coordinates of hand into list
                cv.circle(frame, (cx, cy), 6, (255, 0, 0), -1)

    command = determine_command(list(pts), DEADZONE) # Get command
    now = time.time() # Get current time
    if ((now - last_cmd_time) > COOLDOWN_S):
        # Print command every certain time
        print(command)
        last_cmd_time = now # Update time line

    # Draw the command
    if (command != ""):
        cv.putText(frame, command, (20, 40), cv.FONT_HERSHEY_SIMPLEX, 1.1, (0, 200, 255), 3)

    # Open/update Mask and Frame window image
    cv.imshow("Mask", mask)
    cv.imshow("Frame", frame)

    if (cv.waitKey(1) & 0xFF == 27): # If ESC is pressed, escape
        break

# Free the web cam and terminate all windows
webcam.release()
cv.destroyAllWindows()

