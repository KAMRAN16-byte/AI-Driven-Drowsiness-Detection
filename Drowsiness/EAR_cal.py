import cv2
import mediapipe as mp
import numpy as np
import time

def calculate_ear(eye):
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    C = np.linalg.norm(eye[0] - eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def get_adaptive_threshold(ear_list):
    if len(ear_list) < 15:
        return None
    avg_ear = np.mean(ear_list)
    threshold = avg_ear * 0.78
    return threshold
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

ear_open_samples = []

cap = cv2.VideoCapture(0)
def fun():
    print("\n>> Keep your eyes open for 7 seconds to calibrate EAR threshold...\n")
    start_time = time.time()
    threshold_printed = False  # To ensure we print only once

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        if results.multi_face_landmarks:
            mesh = results.multi_face_landmarks[0]

            left_eye = np.array([[mesh.landmark[i].x * w, mesh.landmark[i].y * h] for i in LEFT_EYE])
            right_eye = np.array([[mesh.landmark[i].x * w, mesh.landmark[i].y * h] for i in RIGHT_EYE])

            left_ear = calculate_ear(left_eye)
            right_ear = calculate_ear(right_eye)
            ear = (left_ear + right_ear) / 2.0

            if time.time() - start_time <= 7:
                ear_open_samples.append(ear)
                cv2.putText(frame, "CALIBRATING... Keep eyes open for 7 Sec", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

            else:
                threshold = get_adaptive_threshold(ear_open_samples)

                if threshold:
                    cv2.putText(frame, f"EAR: {ear:.2f}  Threshold: {threshold:.2f}", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

                    # PRINT ONLY ONCE
                    if not threshold_printed:
                        print("\n==========================")
                        print("   EAR THRESHOLD =", round(threshold, 3))
                        print("==========================\n")
                        threshold_printed = True
                else:
                    cv2.putText(frame, "Calibrating threshold...", (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

        cv2.imshow("EAR Threshold Detection", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            return 
        elif key == ord('r'):
            fun()

fun()
cap.release()
cv2.destroyAllWindows()
