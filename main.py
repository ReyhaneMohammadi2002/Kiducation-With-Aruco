import cv2
import cv2.aruco as aruco
import pandas as pd
import json
import requests
from datetime import datetime
from eitaa import Eitaa
from jalaliDate import datetime2jalali

# ========== Device and Server Info ========== #
DEVICE_INFO = {
    "device_name": "Tablet-A",
    "device_ip": "192.168.1.10",
    "device_mac": "00:1A:2B:3C:4D:5E",
    "device_location": "Classroom 1"
}
SERVER_URL = "https://thingspod.com/api/v1/c17H7PQk0TEoTHe2K7IJ/telemetry"

# Eitaa messaging setup
token = "bot385610:020f950b-7ab0-4647-8783-7fd942de2e24"
e = Eitaa(token)
CHANNEL_ID = "ArUcoGame"

# ========== Load Data ========== #
# Read mapping of card IDs to words and users
word_data = pd.read_csv('id_words.csv', encoding='utf-8-sig')
user_data = pd.read_csv('user_ids.csv', encoding='utf-8-sig')

# Create dictionaries for ID to word and ID to user name
id_to_word = dict(zip(word_data['id'], word_data['word']))
id_to_name = dict(zip(user_data['id'], user_data['lastname']))

# Marker IDs defining the trainer and student zones
corner_ids = [34, 35, 36, 37]

# ========== Utility Functions ========== #
def detect_markers(image):
    """Detect ArUco markers in the given image."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_100)
    parameters = aruco.DetectorParameters()
    detector = aruco.ArucoDetector(aruco_dict, parameters)
    corners, ids, _ = detector.detectMarkers(gray)
    return ids, corners

def get_center(corner):
    """Calculate the center of the marker."""
    return int(corner[0][:, 0].mean()), int(corner[0][:, 1].mean())

def is_inside_zone(point, zone):
    """Check if a point is inside the given rectangular zone."""
    x, y = point
    x_min, y_min = zone[0]
    x_max, y_max = zone[1]
    return x_min <= x <= x_max and y_min <= y <= y_max

def send_json(data):
    """Send JSON data to the server."""
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(SERVER_URL, headers=headers, data=json.dumps(data))
        print(f"Sent ({response.status_code}): {data}")
    except Exception as e:
        print(f"Error sending data: {e}")

def end_class(trainer_id, student_id, lesson_card_count, learned_words):
    """Handle class end logic: send data and notify via Eitaa."""
    now = datetime.now()
    jalali_date = datetime2jalali(now)
    jalali_time_str = f"{jalali_date}T{now.strftime('%H:%M:%S')}"
    
    # Prepare end-of-class JSON
    end_json = {
        "time": jalali_time_str,
        "device_name": DEVICE_INFO["device_name"],
        "trainer_id": int(trainer_id),
        "student_id": int(student_id),
        "lesson_card_count": lesson_card_count,
        "class_started": False
    }
    send_json(end_json)
    print("Class ended.")

    # Build notification message
    trainer_name = id_to_name.get(trainer_id, "ناشناس")
    student_name = id_to_name.get(student_id, "ناشناس")
    words_text = "\n".join(f"- {id_to_word[w]}" for w in learned_words) if learned_words else "هیچ کلمه‌ای یادگرفته نشده است."

    message = (
        f"📚 کلاس تمام شد!\n"
        f"🕒 زمان پایان: {jalali_date} {now.strftime('%H:%M:%S')}\n"
        f"👩‍🏫 مربی: {trainer_name}\n"
        f"👨‍🎓 دانش‌آموز: {student_name}\n"
        f"✅ تعداد کلمات یادگرفته شده: {lesson_card_count}\n"
        f"📖 کلمات:\n{words_text}"
    )

    try:
        e.send_message(CHANNEL_ID, message, pin=True)
        print("Message sent to channel.")
    except Exception as ex:
        print(f"Error sending message to channel: {ex}")

# ========== Main Program ========== #
# Start video capture from IP webcam
cap = cv2.VideoCapture("http://192.168.1.102:8080/video")
print("Program started. Waiting for trainer and student...")

# Initialize state variables
trainer_id = None
student_id = None
class_started = False
lesson_card_count = 0
sent_cards = set()
PADDING = 50  # Extra margin for student zone

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame.")
        break

    ids, corners = detect_markers(frame)
    ids = ids if ids is not None else []
    visible_ids = [id[0] for id in ids]

    # Get positions of the zone-defining markers
    zone_corners = {id[0]: c for id, c in zip(ids, corners) if id[0] in corner_ids}
    if all(k in zone_corners for k in corner_ids):
        # Get centers of corner markers
        cx34, cy34 = get_center(zone_corners[34])
        cx35, cy35 = get_center(zone_corners[35])
        cx36, cy36 = get_center(zone_corners[36])
        cx37, cy37 = get_center(zone_corners[37])

        # Define rectangular zones for trainer and student
        trainer_zone = (
            (min(cx34, cx35), min(cy34, cy35)),
            (max(cx34, cx35), max(cy34, cy35))
        )
        student_zone = (
            (min(cx36, cx37) - PADDING, min(cy36, cy37) - PADDING),
            (max(cx36, cx37) + PADDING, max(cy36, cy37) + PADDING)
        )

        # If class hasn't started, detect trainer and student IDs
        if not class_started:
            candidates = [id for id in visible_ids if id in id_to_name]
            if len(candidates) >= 2:
                trainer_id = candidates[0]
                student_id = candidates[1]

                # Send class start data
                now = datetime.now()
                jalali_date = datetime2jalali(now)
                jalali_time_str = f"{jalali_date}T{now.strftime('%H:%M:%S')}"
                session_json = {
                    "time": jalali_time_str,
                    "device_name": DEVICE_INFO["device_name"],
                    "IP": DEVICE_INFO["device_ip"],
                    "MAC": DEVICE_INFO["device_mac"],
                    "location": DEVICE_INFO["device_location"],
                    "trainer_id": int(trainer_id),
                    "student_id": int(student_id),
                    "class_started": True
                }
                send_json(session_json)
                class_started = True
                sent_cards.clear()
                lesson_card_count = 0
                print("Class started.")
        else:
            # If either the trainer or student is no longer visible, end class
            if trainer_id not in visible_ids or student_id not in visible_ids:
                end_class(trainer_id, student_id, lesson_card_count, sent_cards)
                class_started = False
                trainer_id = None
                student_id = None
                sent_cards.clear()

        # During class, check for new word cards shown in student zone
        if class_started:
            for marker_id, corner in zip(ids, corners):
                id_val = marker_id[0]
                if id_val in id_to_word and id_val not in sent_cards:
                    center = get_center(corner)
                    if is_inside_zone(center, student_zone):
                        now = datetime.now()
                        jalali_date = datetime2jalali(now)
                        jalali_time_str = f"{jalali_date}T{now.strftime('%H:%M:%S')}"
                        training_json = {
                            "time": jalali_time_str,
                            "device_id": DEVICE_INFO["device_name"],
                            "trainer_id": int(trainer_id),
                            "student_id": int(student_id),
                            "lesson_card_id": int(id_val),
                            "lesson_card_word": id_to_word[id_val],
                            "zone": "student",
                            "class_started": class_started,
                            "lesson_card_count": lesson_card_count + 1
                        }
                        send_json(training_json)
                        lesson_card_count += 1
                        sent_cards.add(id_val)

    # Draw detected markers on the video frame
    if corners:
        aruco.drawDetectedMarkers(frame, corners)

    # Display the result
    cv2.imshow("Aruco Learning", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        print("Program stopped.")
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
