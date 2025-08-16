import cv2 as cv
import numpy as np
import time
import mediapipe as mp
# import pygame 

# ------ Function to get command from face gesture ----------
# -----------------------------------------------------------
def determine_command(latest_center, screen_center, dead_zone_x, dead_zone_y):
    if latest_center is None or screen_center is None:
        return "STAY"
    
    dx = latest_center[0] - screen_center[0]
    dy = latest_center[1] - screen_center[1]

    def no_move(theta, dead_zone):
        return 0 if (abs(theta) < dead_zone) else theta
    
    dx, dy = no_move(dx, dead_zone_x), no_move(dy, dead_zone_y)

    if (abs(dx) == 0 and abs(dy) == 0): return "STAY"
    else:
        if (dx > 0): return "RIGHT"
        if (dx < 0): return "LEFT"
        if (dy > 0): return "DOWN"
        if (dy < 0): return "UP"


def to_px(landmark, w, h):
    return int(landmark.x * w), int(landmark.y * h)        

def avg_points(points):
    pts = np.array(points, dtype=np.float32)
    c = pts.mean(axis=0)
    return int(c[0]), int(c[1])

def ema_update(prev_xy, new_xy, alpha):
    if prev_xy is None: 
        return new_xy
    return (
        # (1 - SMOOTH_ALPHA) * current_coordinates + SMOOTH_ALPHA * next_coordinates
        # The lower the SMOOTH_ALPHA, the less adjustment of current_coordinates
        int((1 - alpha) * prev_xy[0] + alpha * new_xy[0]),
        int((1 - alpha) * prev_xy[1] + alpha * new_xy[1]),
    )

# --------------------- Main -------------------------
# ----------------------------------------------------
def main():
    webcam = cv.VideoCapture(0) # Capture using default webcam 

    SMOOTH_ALPHA = 0.1 # lower -> smoother, higher -> snappier 
    ema_left  = None # EMA-smoothed left-iris coordinates (x, y)
    ema_right = None # EMA-smoothed right-iris coordinates (x, y)
    DEAD_ZONE_HORIZONTAL = 20 # Zone which is 40 pixels 
                            # from the right/left of center of the screen 
                            # where no movement capture occured
    DEAD_ZONE_VERTICAL = 10 # Zone which is 20 pixels 
                            # from above/below of center of the screen 
                            # where no movement capture occured
    COOLDOWN_S = 1 # Time taken between each consecutive commands
    last_cmd_time = 0.0 # Time point when last command was executed

    # -------------------MediaPipe setup -----------------------
    # ----------------------------------------------------------
    mediapipe_face = mp.solutions.face_mesh
    face_mesh = mediapipe_face.FaceMesh(
        static_image_mode = False,
        max_num_faces = 1,
        refine_landmarks = True,
        min_detection_confidence = 0.5,
        min_tracking_confidence = 0.5
    )

    # FaceMesh landmark indices for irises when refine_landmarks=True:
    # (These are standard for the MP 468+ iris topology.)
    LEFT_IRIS_IDX  = [469, 470, 471, 472]  # left eye (as seen by the person)
    RIGHT_IRIS_IDX = [474, 475, 476, 477]  # right eye

    while (webcam.isOpened()):
        canRead, frame = webcam.read() # Read the webcam 
                                   # and check if it was sucessfully read
        if (canRead == False):
            raise SystemExit("ERROR: Could not open webcam.")

        frameH, frameW = frame.shape[:2] # Get screen width and height

        # ---- Detect face & add its position into pts list ----
        # ------------------------------------------------------
        # Horizontal flip (make the laptop as a mirror)
        frame = cv.flip(frame, 1) 
        # MediaPipe expects RGB
        rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        result = face_mesh.process(rgb)

        if (result.multi_face_landmarks):
            landmarks = result.multi_face_landmarks[0].landmark
            # --- Compute left & right iris centers (mean of 4 iris points) ---
            left_iris_pts = [to_px(landmarks[i], frameW, frameH) for i in LEFT_IRIS_IDX]
            right_iris_pts = [to_px(landmarks[i], frameW, frameH) for i in RIGHT_IRIS_IDX]
            
            # Find the mean coordinates within the range of coordinates
            left_iris_center  = avg_points(left_iris_pts)
            right_iris_center = avg_points(right_iris_pts)

            # Smooth each eye separately, then average for a robust "pupil" center
            ema_left  = ema_update(ema_left,  left_iris_center, SMOOTH_ALPHA)
            ema_right = ema_update(ema_right, right_iris_center, SMOOTH_ALPHA)

            # Use the midpoint of the two smoothed irises as the single "gaze point"
            iris_center = avg_points([ema_left, ema_right])

            # -------- Debug drawing --------
            # Iris contours
            for p in left_iris_pts:
                cv.circle(frame, p, 2, (0, 255, 0), -1)
            for p in right_iris_pts:
                cv.circle(frame, p, 2, (0, 255, 0), -1)

            # Smoothed iris centers
            cv.circle(frame, ema_left,  4, (255, 0, 0), -1)
            cv.circle(frame, ema_right, 4, (255, 0, 0), -1)

            # Combined "gaze" point
            cv.circle(frame, iris_center, 6, (0, 0, 255), -1)

        # Draw a dead-zone box around a screen-centered point
        shift_x, shift_y = -50, 30
        screen_center = ((frameW // 2) + shift_x, (frameH // 2) + shift_y)
        cv.rectangle(frame, (screen_center[0] - DEAD_ZONE_HORIZONTAL, screen_center[1] - DEAD_ZONE_VERTICAL),
                    (screen_center[0] + DEAD_ZONE_HORIZONTAL, screen_center[1] + DEAD_ZONE_VERTICAL),
                    (0, 255, 255), 1)
        cv.circle(frame, screen_center, 6, (0, 255, 255), 1) # Coordinates (0, 0)
        
        # Get command
        command = determine_command(iris_center, screen_center, DEAD_ZONE_HORIZONTAL, DEAD_ZONE_VERTICAL) 
        
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

if __name__ == "__main__":
    main()

