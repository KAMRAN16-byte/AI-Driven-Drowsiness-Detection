# ================== DROWSINESS DETECTION SYSTEM (Improved Version) ==================
# Combines: High-accuracy eye detection + Yawn detection (smooth & reliable)

# Import necessary packages
import datetime as dt
import matplotlib.pyplot as plt
import imutils
import dlib
import time
import argparse
import cv2
from playsound import playsound
from imutils import face_utils
from imutils.video import VideoStream
from scipy.spatial import distance as dist
import os
import pandas as pd
from datetime import datetime
from collections import deque
import threading
from twilio.rest import Client
import time
import upload
# ================== Setup ==================
def assure_path_exists(path):
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        os.makedirs(dir)

"""EAR = ratio of vertical eye distance to horizontal distance.

When eyes close → vertical distance (A, B) shrinks → EAR gets smaller.

So, small EAR = drowsiness."""
# EAR (Eye Aspect Ratio)
def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

# MAR (Mouth Aspect Ratio)
def mouth_aspect_ratio(mouth):
    A = dist.euclidean(mouth[2], mouth[10])  # 51, 59
    B = dist.euclidean(mouth[4], mouth[8])   # 53, 57
    C = dist.euclidean(mouth[0], mouth[6])   # 49, 55
    mar = (A + B) / (2.0 * C)
    return mar

def play_audio(file_path):
    playsound(file_path)

# ================== Constants ==================
"""EAR_THRESHOLD: if EAR < 0.25 → eye is considered closed.

CONSECUTIVE_FRAMES: must stay closed for 20 frames = real drowsiness.

ear_buffer: stores last 5 EAR readings to smooth sudden changes."""
EAR_THRESHOLD = 0.25
CONSECUTIVE_FRAMES = 20
EAR_SMOOTHING_WINDOW = 5
ear_buffer = deque(maxlen=EAR_SMOOTHING_WINDOW)

account_sid = "" #enter your Twilio account SID
auth_token = "" #enter your Twilio auth token
client = Client(account_sid, auth_token)    #Twilio client for SMS alerts
no = [""] #enter number to receive SMS alert (with country code, e.g. +1234567890)

# initialize counters
FRAME_COUNT = 0
count_sleep = 0
count_yawn = 0

# ================== Argument Parsing ==================
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--shape_predictor", required=True,
                help="path to dlib's facial landmark predictor")
ap.add_argument("-r", "--picamera", type=int, default=-1,
                help="use PiCamera or not")
args = vars(ap.parse_args())

# ================== Model Loading ==================
print("[INFO] Loading predictor...")
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(args["shape_predictor"])

# correct facial indexes
(lstart, lend) = face_utils.FACIAL_LANDMARKS_68_IDXS["left_eye"]
(rstart, rend) = face_utils.FACIAL_LANDMARKS_68_IDXS["right_eye"]
(mstart, mend) = face_utils.FACIAL_LANDMARKS_68_IDXS["mouth"]

# ================== Start Camera ==================
print("[INFO] Starting camera...")
vs = VideoStream(usePiCamera=args["picamera"] > 0).start()
time.sleep(2.0)
assure_path_exists("dataset/")

# ================== Data Lists ==================
ear_list, mar_list, ts = [], [], []
total_ear, total_mar, total_ts = [], [], []

# ================== Main Loop ==================
while True:
    frame = vs.read()
    cv2.putText(frame, "PRESS 'q' TO EXIT", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    (h, w) = frame.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    color = (0, 0, 255)
    thickness = 2
    (text_w, text_h), _ = cv2.getTextSize(timestamp, font, font_scale, thickness)
    x = w - text_w - 10
    y = h - 10
    cv2.putText(frame, timestamp, (x, y), font, font_scale, color, thickness)
    
    
    # resize and preprocess
    frame = imutils.resize(frame, width=500)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # detect faces
    rects = detector(gray, 1)

    for rect in rects:
        shape = predictor(gray, rect)
        shape = face_utils.shape_to_np(shape)

        # ==== show all 68 landmarks ====
        for (i, (x_point, y_point)) in enumerate(shape):
            cv2.circle(frame, (x_point, y_point), 1, (255, 0, 0), -1)
            cv2.putText(frame, str(i + 1), (x_point - 4, y_point - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 255), 1)

        # extract eyes and mouth
        leftEye = shape[lstart:lend]
        rightEye = shape[rstart:rend]
        mouth = shape[mstart:mend]

        leftEAR = eye_aspect_ratio(leftEye)
        rightEAR = eye_aspect_ratio(rightEye)
        EAR = (leftEAR + rightEAR) / 2.0

        # smooth EAR
        ear_buffer.append(EAR)
        smoothed_EAR = sum(ear_buffer) / float(len(ear_buffer))

        # draw eyes
        leftEyeHull = cv2.convexHull(leftEye)
        rightEyeHull = cv2.convexHull(rightEye)
        cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
        cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

        # store EAR and timestamp
        ear_list.append(smoothed_EAR)
        ts.append(dt.datetime.now().strftime('%H:%M:%S.%f'))

        # ================== Drowsiness Detection ==================
        if smoothed_EAR < EAR_THRESHOLD:
            FRAME_COUNT += 1
            cv2.drawContours(frame, [leftEyeHull], -1, (0, 0, 255), 1)
            cv2.drawContours(frame, [rightEyeHull], -1, (0, 0, 255), 1)
            if FRAME_COUNT >= CONSECUTIVE_FRAMES:
                '''for number in no:
                    client.messages.create(
                        body="Alert! Driver is drowsing.",
                        from_="enter_number",
                        to=number
                    )'''
                count_sleep += 1
                filename = f"dataset/frame_sleep{count_sleep}.jpg"
                cv2.imwrite(filename, frame)
                thread2 = threading.Thread(target=upload.server, args=(filename,))
                thread2.start()
                audio_file = "sound files/alarm.mp3"

                # Start the audio playback in a separate thread
                thread = threading.Thread(target=play_audio, args=(audio_file,))
                thread.start()

                cv2.putText(frame, "DROWSINESS ALERT!", (270, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                FRAME_COUNT = -20
        else:
            FRAME_COUNT = 0

        # ================== Yawn Detection ==================
        MAR = mouth_aspect_ratio(mouth)
        mar_list.append(MAR / 10)

        face_height = float(h) if h > 0 else 1.0
        norm_MAR = MAR / face_height
        YAWN_THRESHOLD_NORM = 0.6

        if norm_MAR > YAWN_THRESHOLD_NORM:
            count_yawn += 1
            cv2.drawContours(frame, [mouth], -1, (0, 0, 255), 1)
            cv2.putText(frame, "YAWN ALERT!", (270, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            cv2.imwrite(f"dataset/frame_yawn{count_yawn}.jpg", frame)
            playsound('sound files/warning_yawn.mp3')


    # save data for plotting
    total_ear.extend(ear_list)
    total_mar.extend(mar_list)
    total_ts.extend(ts)

    cv2.imshow("Output", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

# ================== Save & Plot ==================
df = pd.DataFrame({"EAR": total_ear, "MAR": total_mar, "TIME": total_ts})
df.to_csv("op_webcam.csv", index=False)
df = pd.read_csv("op_webcam.csv")


try:
    df.plot(x='TIME', y=['EAR', 'MAR'])
    plt.subplots_adjust(bottom=0.30)
    plt.title('EAR & MAR over Time (Webcam)')
    plt.ylabel('EAR & MAR')
    plt.gca().axes.get_xaxis().set_visible(False)
    plt.show()
except Exception as e:
    print(e)


cv2.destroyAllWindows()
vs.stop()
