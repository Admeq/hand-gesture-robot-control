import cv2
import mediapipe as mp
import time
import socket

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

MODEL_PATH = "hand_landmarker.task"
ESP_IP = "192.168.4.1"
ESP_PORT = 5000

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17)
]

FINGER_TIPS = {
    "thumb": 4,
    "index": 8,
    "middle": 12,
    "ring": 16,
    "pinky": 20,
}

FINGER_PIPS = {
    "index": 6,
    "middle": 10,
    "ring": 14,
    "pinky": 18,
}

GESTURE_TO_CMD = {
    "FORWARD": "F",
    "LEFT": "L",
    "RIGHT": "R",
    "REVERSE": "B",
    "STOP": "S",
    "MORSE_HOLD": "M",
    "SOS_MODE": "O",
    "NO HAND": "S",
    "UNKNOWN": "S",
}

sock = None
sock_file = None
last_sent_cmd = None
last_send_time = 0
SEND_INTERVAL = 0.15


def connect_esp():
    global sock, sock_file
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ESP_IP, ESP_PORT))
    sock_file = sock.makefile('r')
    print("Connected to ESP8266")
    print("ESP says:", sock_file.readline().strip())


def send_command(cmd):
    global last_sent_cmd, last_send_time, sock, sock_file
    now = time.time()
    if sock is None:
        return
    if cmd != last_sent_cmd or (now - last_send_time) > SEND_INTERVAL:
        sock.sendall((cmd + '\n').encode())
        reply = sock_file.readline().strip()
        print(f"Sent: {cmd} | ESP replied: {reply}")
        last_sent_cmd = cmd
        last_send_time = now


def draw_hand(frame, hand_landmarks):
    h, w, _ = frame.shape
    points = []
    for lm in hand_landmarks:
        x = int(lm.x * w)
        y = int(lm.y * h)
        points.append((x, y))
    for start_idx, end_idx in HAND_CONNECTIONS:
        cv2.line(frame, points[start_idx], points[end_idx], (0, 255, 0), 2)
    for i, (x, y) in enumerate(points):
        if i in [4, 8, 12, 16, 20]:
            cv2.circle(frame, (x, y), 8, (0, 0, 255), -1)
        else:
            cv2.circle(frame, (x, y), 5, (255, 0, 0), -1)


def get_handedness(result, hand_index=0):
    if result.handedness and len(result.handedness) > hand_index:
        if len(result.handedness[hand_index]) > 0:
            label = result.handedness[hand_index][0].category_name
            if label == "Right":
                return "Left"
            elif label == "Left":
                return "Right"
            return label
    return "Unknown"


def finger_states(landmarks, handedness_name):
    fingers = {
        "thumb": False,
        "index": False,
        "middle": False,
        "ring": False,
        "pinky": False,
    }
    thumb_tip_x = landmarks[FINGER_TIPS["thumb"]].x
    thumb_ip_x = landmarks[3].x
    if handedness_name == "Right":
        fingers["thumb"] = thumb_tip_x < thumb_ip_x
    elif handedness_name == "Left":
        fingers["thumb"] = thumb_tip_x > thumb_ip_x
    for finger in ["index", "middle", "ring", "pinky"]:
        tip_id = FINGER_TIPS[finger]
        pip_id = FINGER_PIPS[finger]
        fingers[finger] = landmarks[tip_id].y < landmarks[pip_id].y
    return fingers


def classify_gesture(fingers):
    thumb = fingers["thumb"]
    index = fingers["index"]
    middle = fingers["middle"]
    ring = fingers["ring"]
    pinky = fingers["pinky"]

    if thumb and index and middle and ring and pinky:
        return "STOP"
    if (not thumb) and index and (not middle) and (not ring) and (not pinky):
        return "FORWARD"
    if (not thumb) and index and middle and (not ring) and (not pinky):
        return "REVERSE"
    if thumb and (not index) and (not middle) and (not ring) and (not pinky):
        return "LEFT"
    if (not thumb) and (not index) and (not middle) and (not ring) and (not pinky):
        return "RIGHT"
    if (not thumb) and index and middle and ring and pinky:
        return "MORSE_HOLD"
    if thumb and index and middle and (not ring) and (not pinky):
        return "SOS_MODE"
    return "UNKNOWN"


def main():
    global sock
    connect_esp()

    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=VisionRunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.7,
        min_hand_presence_confidence=0.7,
        min_tracking_confidence=0.7,
    )

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        if sock:
            sock.close()
        return

    start_time = time.time()
    last_gesture = "NO HAND"
    stable_gesture = "NO HAND"
    stable_count = 0
    required_stable_frames = 5

    with HandLandmarker.create_from_options(options) as landmarker:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame.")
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            timestamp_ms = int((time.time() - start_time) * 1000)
            result = landmarker.detect_for_video(mp_image, timestamp_ms)

            current_gesture = "NO HAND"

            if result.hand_landmarks and len(result.hand_landmarks) > 0:
                hand_landmarks = result.hand_landmarks[0]
                draw_hand(frame, hand_landmarks)
                handedness_name = get_handedness(result, 0)
                fingers = finger_states(hand_landmarks, handedness_name)
                current_gesture = classify_gesture(fingers)

                wrist_x = int(hand_landmarks[0].x * frame.shape[1])
                wrist_y = int(hand_landmarks[0].y * frame.shape[0])

                cv2.putText(frame, f"{handedness_name} Hand", (wrist_x, wrist_y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                cv2.putText(frame, f"T:{int(fingers['thumb'])} I:{int(fingers['index'])} M:{int(fingers['middle'])} R:{int(fingers['ring'])} P:{int(fingers['pinky'])}", (20, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            if current_gesture == last_gesture:
                stable_count += 1
            else:
                stable_count = 0
                last_gesture = current_gesture

            if stable_count >= required_stable_frames:
                stable_gesture = current_gesture

            cmd = GESTURE_TO_CMD.get(stable_gesture, "S")
            send_command(cmd)

            cv2.putText(frame, f"Command: {stable_gesture}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
            cv2.putText(frame, f"Sent: {cmd}", (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
            cv2.putText(frame, "STOP=open palm FORWARD=index REVERSE=index+middle", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 2)
            cv2.putText(frame, "LEFT=thumb RIGHT=fist MORSE=4 fingers(no thumb) SOS=thumb+index+middle", (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 2)
            cv2.putText(frame, "q=quit", (20, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 2)

            cv2.imshow("Hand Gesture Robot Control", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                send_command("S")
                break

    cap.release()
    cv2.destroyAllWindows()
    if sock:
        sock.close()


if __name__ == "__main__":
    main()
