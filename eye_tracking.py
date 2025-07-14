import cv2
import time

# === Constants ===
FRAME_WIDTH = 320
FRAME_HEIGHT = 240
SLEEP_INTERVAL = 0.2

# === Load Haar cascades ===
face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_detector  = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

# === Initialize webcam ===
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

# === Initialize state ===
dot_x = FRAME_WIDTH // 2  # Start dot horizontally in the middle
prev_dot_x_normalized = None

# === Main loop ===
while True:
    ret, frame = camera.read()
    if not ret:
        break

    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    detected_faces = face_detector.detectMultiScale(gray_frame, 1.3, 5)

    eye_centers_x = []

    for (x, y, w, h) in detected_faces:
        face_region = gray_frame[y:y + h // 2, x:x + w]
        detected_eyes = eye_detector.detectMultiScale(face_region)
        detected_eyes = sorted(detected_eyes, key=lambda eye: eye[0])[:2]

        for (ex, ey, ew, eh) in detected_eyes:
            center_x = x + ex + ew // 2
            eye_centers_x.append(center_x)

    # === Update dot x position only if eyes detected ===
    if len(eye_centers_x) == 2:
        avg_x = (eye_centers_x[0] + eye_centers_x[1]) // 2
        dot_x = avg_x
    elif len(eye_centers_x) == 1:
        dot_x = eye_centers_x[0]
    # else: keep dot_x as is

    # === Draw dot every frame at vertical center ===
    cv2.circle(frame, (dot_x, FRAME_HEIGHT // 2), 5, (0, 0, 255), -1)

    dot_x_normalized = round(dot_x / FRAME_WIDTH, 2)

    if prev_dot_x_normalized != dot_x_normalized:
        print(f"x={dot_x_normalized:.2f}")
        prev_dot_x_normalized = dot_x_normalized

    # === Show frame ===
    cv2.imshow('Eye Tracker', frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC key to exit
        break

    time.sleep(SLEEP_INTERVAL)

# === Cleanup ===
camera.release()
cv2.destroyAllWindows()
