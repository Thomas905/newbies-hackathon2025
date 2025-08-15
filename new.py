import cv2 as cv
import numpy as np
import os
import time
from collections import deque 

webcam = cv.VideoCapture(0) # Capture using default webcam 

SMOOTH_ALPHA = 0.1 # lower -> smoother, higher -> snappier 
ema = None # Smooth face coordinates
pts = deque(maxlen=20) # Queue that store 20 smoothed centers
DEADZONE   = 50 # Min movement distance between the oldest and newest hand position
                # Ignore movement smaller than this
COOLDOWN_S = 0.5 # Time taken between each consecutive commands
last_cmd_time = 0.0 # Time point when last command was executed

# ------ Function to get command from hand gesture ----------
# -----------------------------------------------------------
def determine_command(pts_list, deadzone):
    if (len(pts_list) < 8): return "STAY"
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

# -------------------- Face detector -----------------------
# ----------------------------------------------------------
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

    # ---- Detect face & add its position into pts list ----
    # ------------------------------------------------------
    # Horizontal flip (make the laptop as a mirror)
    frame = cv.flip(frame, 1) 
    # Convert from BGR to grayscale and load images in grayscale
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    # Remove remaining small holes and speckles caused by lighting/shadows
    # (5, 5) kernel and omega = 0 => work in most lightning 
    gray = cv.GaussianBlur(gray, (5, 5), 0) 
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(80, 80))
    if (len(faces) > 0):
        # Capture the closest face to the camera
        # Get top left conner coordinates (fx, fy) 
        # and width, height (fw, fh) of the face
        fx, fy, fw, fh = max(faces, key=lambda r: r[2]*r[3])
        # Draw face box for debugging
        cv.rectangle(frame, (fx, fy), (fx+fw, fy+fh), (0, 0, 255), 2)
        # (Sum of x/y coordinates in pixels from top left conner coordinates) 
        # / (No of pixels = 2) 
        # = Middle pixels within a line of x/y coordinates
        centerX, centerY = fx + fw // 2, fy + fh // 2

        # EMA smoothing
        if ema is None:
            ema = (centerX, centerY)
        else:
            # (1 - SMOOTH_ALPHA) * current_coordinates + SMOOTH_ALPHA * next_coordinates
            # The lower the SMOOTH_ALPHA, the less adjustment of current_coordinates
            ema = (int((1 - SMOOTH_ALPHA) * ema[0] + SMOOTH_ALPHA * centerX), 
                   int((1 - SMOOTH_ALPHA) * ema[1] + SMOOTH_ALPHA * centerY))

        # Append coordinates to list
        pts.append(ema)
        cv.circle(frame, ema, 6, (255, 0, 0), -1)

    command = determine_command(list(pts), DEADZONE) # Get command
    now = time.time() # Get current time
    if ((now - last_cmd_time) > COOLDOWN_S):
        # Print command every certain time
        print(command)
        last_cmd_time = now # Update time line

    # Draw the command
    if (command != ""):
        cv.putText(frame, command, (20, 40), cv.FONT_HERSHEY_SIMPLEX, 1.1, (0, 200, 255), 3)

    # Open/update Frame window image
    cv.imshow("Frame", frame)

    if (cv.waitKey(1) & 0xFF == 27): # If ESC is pressed, escape
        break

# Free the web cam and terminate all windows
webcam.release()
cv.destroyAllWindows()

