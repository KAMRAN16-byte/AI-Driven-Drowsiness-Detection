# ================== DROWSINESS DETECTION SYSTEM ==================
# Combines: High-accuracy eye detection + Yawn detection (smooth & reliable)

# Import packages
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
import upload
import EAR


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
# Uses landmarks for inner mouth: (61, 67), (63, 65) for vertical, (60, 64) for horizontal
def mouth_aspect_ratio(mouth):
    # Vertical distances (inner mouth points)
    A = dist.euclidean(mouth[2], mouth[10])  # 51, 59 in 68-point index
    B = dist.euclidean(mouth[4], mouth[8])   # 53, 57 in 68-point index
    # Horizontal distance (outer mouth corners)
    C = dist.euclidean(mouth[0], mouth[6])   # 49, 55 in 68-point index
    mar = (A + B) / (2.0 * C)
    return mar

def play_audio(file_path):
    # The playsound function can sometimes block the main thread, 
    # hence the threading is a good choice for alarms.
    playsound(file_path)

# ================== Constants ==================
"""EAR_THRESHOLD: if EAR < 0.23 → eye is considered closed.
CONSECUTIVE_FRAMES: must stay closed for 20 frames = real drowsiness."""
#EAR_THRESHOLD = 0.23
#EAR_THRESHOLD =EAR.run()
CONSECUTIVE_FRAMES = 10
EAR_SMOOTHING_WINDOW = 5
ear_buffer = deque(maxlen=EAR_SMOOTHING_WINDOW)
# --- Yawn Detection Constants (FIXED/IMPROVED) ---
# A typical MAR threshold for a clear yawn, adjust based on testing if needed.
MAR_THRESHOLD = 0.60
# Number of consecutive frames MAR must be above threshold to trigger a yawn alert
YAWN_CONSECUTIVE_FRAMES = 10
MAR_SMOOTHING_WINDOW = 5
mar_buffer = deque(maxlen=MAR_SMOOTHING_WINDOW)

# Twilio setup (kept as-is)
account_sid = "" #Enter your Twilio Account SID
auth_token = "" #Enter your Twilio Auth Token
#client = Client(account_sid, auth_token) # Comment out if not using Twilio
no = [""] #Enter the phone numbers to receive alerts (in E.164 format, e.g., +1234567890)

# initialize counters
FRAME_COUNT = 0 
count_sleep = 0
count_yawn = 0
YAWN_FRAME_COUNT = 0 # New counter for yawn consecutive frames

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
# The shape predictor file (e.g., shape_predictor_68_face_landmarks.dat) must be provided 
# via the command line argument -p
predictor = dlib.shape_predictor(args["shape_predictor"])
# 

# correct facial indexes
(lstart, lend) = face_utils.FACIAL_LANDMARKS_68_IDXS["left_eye"] # Left eye points 37-42
(rstart, rend) = face_utils.FACIAL_LANDMARKS_68_IDXS["right_eye"] # Right eye points 43-48
(mstart, mend) = face_utils.FACIAL_LANDMARKS_68_IDXS["mouth"] # Mouth points 49-68
EAR_THRESHOLD =EAR.run()
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

    # Reset frame count if no faces detected
    if len(rects) == 0:
        FRAME_COUNT = 0
        YAWN_FRAME_COUNT = 0

    for rect in rects:
        shape = predictor(gray, rect)
        shape = face_utils.shape_to_np(shape)

        # extract eyes and mouth
        leftEye = shape[lstart:lend]
        rightEye = shape[rstart:rend]
        mouth = shape[mstart:mend]

        # Calculate EAR
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

        # ================== Drowsiness Detection (Unmodified Logic) ==================
        if smoothed_EAR < EAR_THRESHOLD:
            FRAME_COUNT += 1
            cv2.drawContours(frame, [leftEyeHull], -1, (0, 0, 255), 1)
            cv2.drawContours(frame, [rightEyeHull], -1, (0, 0, 255), 1)
            if FRAME_COUNT >= CONSECUTIVE_FRAMES:
                # Twilio SMS Alert (kept as-is, but commented out to prevent accidental spamming during testing)
                '''for number in no:
                    client.messages.create(
                        body="Alert! Driver is drowsing.",
                        from_="", #Enter your Twilio phone number (in E.164 format, e.g., +1234567890)
                        to=number
                    )
                '''
                count_sleep += 1
                filename = f"dataset/frame_sleep{count_sleep}.jpg"
                cv2.imwrite(filename, frame)
                audio_file = "sound files/alarm.mp3"
                thread2 = threading.Thread(target=upload.server, args=(filename,))
                thread2.start()

                # Start the audio playback in a separate thread
                thread = threading.Thread(target=play_audio, args=(audio_file,))
                thread.start()

                cv2.putText(frame, "DROWSINESS ALERT!", (270, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                FRAME_COUNT = -30 # Prevents immediate re-trigger
        else:
            FRAME_COUNT = 0

        # ================== Yawn Detection (FIXED Logic) ==================
        MAR = mouth_aspect_ratio(mouth)
        
        # Smooth MAR
        mar_buffer.append(MAR)
        smoothed_MAR = sum(mar_buffer) / float(len(mar_buffer))
        
        # Store smoothed MAR for plotting
        mar_list.append(smoothed_MAR) 

        # Yawn logic using fixed MAR threshold and consecutive frames
        if smoothed_MAR > MAR_THRESHOLD:
            YAWN_FRAME_COUNT += 1
            cv2.drawContours(frame, [mouth], -1, (0, 165, 255), 1) # Orange contour
            
            if YAWN_FRAME_COUNT >= YAWN_CONSECUTIVE_FRAMES:
                count_yawn += 1
                cv2.putText(frame, "YAWN ALERT!", (270, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                cv2.imwrite(f"dataset/frame_yawn{count_yawn}.jpg", frame)
                
                # Play audio in a separate thread to prevent blocking
                yawn_thread = threading.Thread(target=play_audio, args=('sound files/warning_yawn.mp3',))
                yawn_thread.start()
                
                # Reset yawn counter to prevent re-triggering immediately
                YAWN_FRAME_COUNT = 0 
        else:
            YAWN_FRAME_COUNT = 0


    # save data for plotting
    total_ear.extend(ear_list)
    total_mar.extend(mar_list)
    total_ts.extend(ts)
    ear_list, mar_list, ts = [], [], [] # Clear lists after appending to total lists

    cv2.imshow("Output", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

# ================== Save & Plot ==================
df = pd.DataFrame({"EAR": total_ear, "MAR": total_mar, "TIME": total_ts})
df.to_csv("op_webcam.csv", index=False)
df = pd.read_csv("op_webcam.csv")

df.plot(x='TIME', y=['EAR', 'MAR'])
plt.subplots_adjust(bottom=0.30)
plt.title('EAR & MAR over Time (Webcam)')
plt.ylabel('EAR & MAR')
# Hide x-axis labels if too cluttered
# plt.gca().axes.get_xaxis().set_visible(False) 
plt.show()

cv2.destroyAllWindows()
vs.stop()