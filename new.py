import cv2 as cv
import numpy as np
import os
import time
from collections import deque 

webcam = cv.VideoCapture(0) # Capture using default webcam 

SMOOTH_ALPHA = 0.1 # lower -> smoother, higher -> snappier 
ema = None # Smooth face coordinates
DEAD_ZONE = 40 # Zone 40 pixels from the center of the screen 
               # where no movement capture occured
COOLDOWN_S = 2 # Time taken between each consecutive commands
last_cmd_time = 0.0 # Time point when last command was executed

# ------ Function to get command from face gesture ----------
# -----------------------------------------------------------
def determine_command(latest_face_center, screen_center, dead_zone):
    if latest_face_center is None or screen_center is None:
        return "STAY"
    
    dx = latest_face_center[0] - screen_center[0]
    dy = latest_face_center[1] - screen_center[1]

    def no_move(theta):
        return 0 if (abs(theta) < dead_zone) else theta
    
    dx, dy = no_move(dx), no_move(dy)

    if (abs(dx) == 0 and abs(dy) == 0): return "STAY"
    else:
        if (dx > 0): return "RIGHT"
        if (dx < 0): return "LEFT"
        if (dy > 0): return "DOWN"
        if (dy < 0): return "UP"

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

    frameW, frameH = frame.shape[:2] # Get screen width and height

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
        # (Sum of x/y coordinates in pixels from top left conner coordinates) 
        # / (No of pixels = 2) 
        # = Middle pixels within a line of x/y coordinates
        faceCenterX, faceCenterY = fx + fw // 2, fy + fh // 2

        # EMA smoothing
        if ema is None:
            ema = (faceCenterX, faceCenterY)
        else:
            # (1 - SMOOTH_ALPHA) * current_coordinates + SMOOTH_ALPHA * next_coordinates
            # The lower the SMOOTH_ALPHA, the less adjustment of current_coordinates
            ema = (int((1 - SMOOTH_ALPHA) * ema[0] + SMOOTH_ALPHA * faceCenterX), 
                   int((1 - SMOOTH_ALPHA) * ema[1] + SMOOTH_ALPHA * faceCenterY))

        # Draw face box for debugging
        cv.rectangle(frame, (fx, fy), (fx + fw, fy + fh), (0, 0, 255), 2)
        # Draw face center for debugging
        cv.circle(frame, ema, 6, (255, 0, 0), -1)

    # Draw a screen box and its center (let center in the vicinity of the screen)
    screen_center = ((frameW // 2) + 80, (frameH // 2) - 80)
    cv.rectangle(frame, (screen_center[0] - DEAD_ZONE, screen_center[1] - DEAD_ZONE),
                 (screen_center[0] + DEAD_ZONE, screen_center[1] + DEAD_ZONE),
                 (0, 255, 255), 1)
    cv.circle(frame, screen_center, 6, (0, 255, 255), 1) # Coordinates (0, 0)
    
    # Get command
    command = determine_command(ema, screen_center, DEAD_ZONE) 
    
    now = time.time() # Get current time
    if ((now - last_cmd_time) > COOLDOWN_S):
        # Print command every certain time
        print("Command = ",  command)
        print("\n")
        last_cmd_time = now # Update time line
        # Draw the command
        cv.putText(frame, command, (20, 40), cv.FONT_HERSHEY_SIMPLEX, 1.1, (0, 200, 255), 3)

    # Open/update Frame window image
    cv.imshow("Frame", frame)

    if (cv.waitKey(1) & 0xFF == 27): # If ESC is pressed, escape
        break

# Free the web cam and terminate all windows
webcam.release()
cv.destroyAllWindows()

