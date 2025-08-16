import cv2
import numpy as np
import mediapipe as mp
import time

# --- Setup ---
cap = cv2.VideoCapture(0)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# --- Calibration ---
print("Show your hand for 3 seconds for calibration...")
time.sleep(1)

hsv_samples = []
start_time = time.time()
while time.time() - start_time < 3:
    ret, frame = cap.read()
    if not ret:
        break

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(frame_rgb)

    mask = np.zeros(frame.shape[:2], dtype=np.uint8)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            points = []
            h, w, _ = frame.shape
            for lm in hand_landmarks.landmark:
                points.append([int(lm.x * w), int(lm.y * h)])
            points = np.array(points, dtype=np.int32)
            cv2.fillPoly(mask, [points], 255)
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hsv_pixels = hsv_frame[mask == 255]
        if len(hsv_pixels) > 0:
            hsv_samples.append(hsv_pixels)

    cv2.imshow("Calibration", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

# Calculate mean HSV and range
hsv_samples = np.vstack(hsv_samples)
mean_hsv = np.mean(hsv_samples, axis=0)
tol = np.array([15, 50, 50])
lower_hsv = np.clip(mean_hsv - tol, 0, 255).astype(np.uint8)
upper_hsv = np.clip(mean_hsv + tol, 0, 255).astype(np.uint8)

print("Calibration done!")

# --- Tracking variables ---
prev_center = None

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(frame_rgb)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            # Get points and draw hand
            points = []
            h, w, _ = frame.shape
            for lm in hand_landmarks.landmark:
                points.append([int(lm.x * w), int(lm.y * h)])
            points = np.array(points, dtype=np.int32)
            cv2.polylines(frame, [points], True, (0, 255, 0), 2)

            # Calculate bounding rect center
            x, y, w_box, h_box = cv2.boundingRect(points)
            center = (x + w_box // 2, y + h_box // 2)
            cv2.circle(frame, center, 5, (255, 0, 0), -1)

            # Movement detection
            if prev_center is not None:
                dx = center[0] - prev_center[0]
                dy = center[1] - prev_center[1]
                direction = ""
                if abs(dx) > abs(dy):  # horizontal movement dominates
                    if dx > 20:
                        direction = "Right"
                    elif dx < -20:
                        direction = "Left"
                else:  # vertical movement dominates
                    if dy > 20:
                        direction = "Down"
                    elif dy < -20:
                        direction = "Up"

                if direction:
                    print(direction)
                    cv2.putText(frame, direction, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            prev_center = center

            # Grab detection
            # Compare distance between tip of index finger and tip of thumb
            idx_tip = hand_landmarks.landmark[8]
            thumb_tip = hand_landmarks.landmark[4]
            dist = np.sqrt((idx_tip.x - thumb_tip.x)**2 + (idx_tip.y - thumb_tip.y)**2)
            if dist < 0.05:
                print("GRABBBBBBBB")
                cv2.putText(frame, "GRAB!", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    cv2.imshow("Hand Tracking", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
