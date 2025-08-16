import cv2
import numpy as np
import mediapipe as mp
import time
import threading
import queue

class HandDetector:
    def __init__(self, max_hands=1, min_detection_confidence=0.7, grab_threshold=0.05, skip_frames=2):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=max_hands,
                                         min_detection_confidence=min_detection_confidence)
        self.mp_draw = mp.solutions.drawing_utils
        self.cap = cv2.VideoCapture(0)
        self.prev_center = None
        self.lower_hsv = None
        self.upper_hsv = None
        self.grab_threshold = grab_threshold
        self.hand_center = None
        self.movement = None
        self.is_grab = False

        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.frame_queue = queue.Queue(maxsize=2)
        threading.Thread(target=self._capture_thread, daemon=True).start()

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.4,   # plus rapide, moins strict
            min_tracking_confidence=0.4
        )

        self.grab_threshold = grab_threshold
        self.prev_center = None
        self.hand_center = None
        self.movement = None
        self.is_grab = False

        self.skip_frames = skip_frames
        self.frame_count = 0

    def start_calibration(self, calibration_time=3):
        print(f"Show your hand for {calibration_time} seconds for calibration...")
        hsv_samples = []
        start_time = time.time()
        while time.time() - start_time < calibration_time:
            ret, frame = self.cap.read()
            if not ret:
                continue
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.hands.process(frame_rgb)
            mask = np.zeros(frame.shape[:2], dtype=np.uint8)
            if result.multi_hand_landmarks:
                for hand_landmarks in result.multi_hand_landmarks:
                    points = []
                    h, w, _ = frame.shape
                    for lm in hand_landmarks.landmark:
                        points.append([int(lm.x * w), int(lm.y * h)])
                    points = np.array(points, dtype=np.int32)
                    cv2.fillPoly(mask, [points], 255)
                    self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                hsv_pixels = hsv_frame[mask == 255]
                if len(hsv_pixels) > 0:
                    hsv_samples.append(hsv_pixels)
            cv2.imshow("Calibration", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break
        if hsv_samples:
            hsv_samples = np.vstack(hsv_samples)
            mean_hsv = np.mean(hsv_samples, axis=0)
            tol = np.array([15, 50, 50])
            self.lower_hsv = np.clip(mean_hsv - tol, 0, 255).astype(np.uint8)
            self.upper_hsv = np.clip(mean_hsv + tol, 0, 255).astype(np.uint8)
            print("Calibration done!")
            cv2.destroyWindow("Calibration")

    def _capture_thread(self):
        while True:
            ret, frame = self.cap.read()
            if ret:
                if self.frame_queue.full():
                    self.frame_queue.get()
                self.frame_queue.put(frame)

    def update(self):
        if self.frame_queue.empty():
            return None

        self.frame_count += 1
        if self.frame_count % self.skip_frames != 0:
            return None

        frame = self.frame_queue.get()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(frame_rgb)

        self.movement = None
        self.is_grab = False
        self.hand_center = None

        if result.multi_hand_landmarks:
            hand_landmarks = result.multi_hand_landmarks[0]
            h, w, _ = frame.shape
            points = np.array([[int(lm.x * w), int(lm.y * h)] for lm in hand_landmarks.landmark], dtype=np.int32)

            # centre de la main
            x, y, w_box, h_box = cv2.boundingRect(points)
            center = (x + w_box // 2, y + h_box // 2)
            self.hand_center = center

            # distance pouce - index
            idx_tip = hand_landmarks.landmark[8]
            thumb_tip = hand_landmarks.landmark[4]
            dist = np.sqrt((idx_tip.x - thumb_tip.x) ** 2 + (idx_tip.y - thumb_tip.y) ** 2)
            self.is_grab = dist < self.grab_threshold

            # mouvement
            if not self.is_grab and self.prev_center:
                dx = center[0] - self.prev_center[0]
                dy = center[1] - self.prev_center[1]
                direction = ""
                if abs(dx) > abs(dy):
                    if dx > 20:
                        direction = "Left"
                    elif dx < -20:
                        direction = "Right"
                else:
                    if dy > 20:
                        direction = "Down"
                    elif dy < -20:
                        direction = "Up"
                self.movement = direction if direction else None

            self.prev_center = center

        return self.hand_center, self.is_grab, self.movement
    
    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()
