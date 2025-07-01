import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import time
import numpy as np
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import keyboard
import screen_brightness_control as sbc
import mediapipe as mp
import autopy

# ========== HandTrackingModule ==========
class handDetector():
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.maxHands,
            min_detection_confidence=self.detectionCon,
            min_tracking_confidence=self.trackCon
        )
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
        return img

    def findPosition(self, img, handNo=0, draw=True):
        xList = []
        yList = []
        bbox = []
        self.lmList = []
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHand.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                xList.append(cx)
                yList.append(cy)
                self.lmList.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
            xmin, xmax = min(xList), max(xList)
            ymin, ymax = min(yList), max(yList)
            bbox = xmin, ymin, xmax, ymax

            if draw:
                cv2.rectangle(img, (bbox[0] - 20, bbox[1] - 20),
                              (bbox[2] + 20, bbox[3] + 20), (0, 255, 0), 2)

        return self.lmList, bbox

    def fingersUp(self):
        fingers = []
        if len(self.lmList) != 0:
            if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)
            for id in range(1, 5):
                if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                    fingers.append(1)
                else:
                    fingers.append(0)
        return fingers

    def findDistance(self, p1, p2, img, draw=True):
        x1, y1 = self.lmList[p1][1], self.lmList[p1][2]
        x2, y2 = self.lmList[p2][1], self.lmList[p2][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        if draw:
            cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)

        length = math.hypot(x2 - x1, y2 - y1)
        return length, img, [x1, y1, x2, y2, cx, cy]

# ========== Main App ==========
class HandControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🖐️ Hand Gesture Controller")
        self.root.geometry("1000x800")
        self.root.configure(bg="#232946")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Cairo", 14), padding=8, background="#eebbc3", foreground="#232946")
        style.configure("TLabel", font=("Cairo", 12), background="#232946", foreground="#eebbc3")
        style.configure("TCombobox", font=("Cairo", 12))

        title = tk.Label(root, text="Hand Gesture Controller", font=("Cairo", 24, "bold"), bg="#232946", fg="#eebbc3")
        title.pack(pady=10)

        frame = tk.Frame(root, bg="#232946")
        frame.pack(pady=10)

        tk.Label(frame, text="Select Camera Index:", font=("Cairo", 14), bg="#232946", fg="#eebbc3").grid(row=0, column=0, padx=5)
        self.camera_index = tk.IntVar(value=0)
        self.camera_selector = ttk.Combobox(frame, values=list(range(5)), textvariable=self.camera_index, width=5)
        self.camera_selector.grid(row=0, column=1, padx=5)

        self.mode = tk.StringVar(value="media")
        tk.Radiobutton(frame, text="Media/Volume/Brightness", variable=self.mode, value="media", font=("Cairo", 12), bg="#232946", fg="#eebbc3", selectcolor="#eebbc3").grid(row=0, column=2, padx=10)
        tk.Radiobutton(frame, text="Mouse Control", variable=self.mode, value="mouse", font=("Cairo", 12), bg="#232946", fg="#eebbc3", selectcolor="#eebbc3").grid(row=0, column=3, padx=10)

        self.start_btn = ttk.Button(frame, text="Start", command=self.start)
        self.start_btn.grid(row=0, column=4, padx=10)

        self.stop_btn = ttk.Button(frame, text="Exit", command=self.close_app)
        self.stop_btn.grid(row=0, column=5, padx=10)

        self.info_frame = tk.Frame(root, bg="#232946")
        self.info_frame.pack(pady=10)

        self.vol_label = tk.Label(self.info_frame, text="Volume: -- %", font=("Cairo", 16), bg="#232946", fg="#eebbc3")
        self.vol_label.grid(row=0, column=0, padx=20)
        self.bright_label = tk.Label(self.info_frame, text="Brightness: -- %", font=("Cairo", 16), bg="#232946", fg="#eebbc3")
        self.bright_label.grid(row=0, column=1, padx=20)
        self.fps_label = tk.Label(self.info_frame, text="FPS: --", font=("Cairo", 16), bg="#232946", fg="#eebbc3")
        self.fps_label.grid(row=0, column=2, padx=20)

        self.canvas_frame = tk.Frame(root, bg="#eebbc3", bd=4, relief="ridge")
        self.canvas_frame.pack(pady=10)
        self.canvas = tk.Label(self.canvas_frame, bg="#232946")
        self.canvas.pack()

        self.running = False

    def start(self):
        self.running = True
        if self.mode.get() == "media":
            self.start_media_mode()
        else:
            self.start_mouse_mode()

    # ========== Media Mode ==========
    def start_media_mode(self):
        self.cap = cv2.VideoCapture(self.camera_index.get())
        self.cap.set(3, 640)
        self.cap.set(4, 480)
        self.pTime = 0

        self.detector = handDetector(detectionCon=0.7, maxHands=1)
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))
        self.volRange = self.volume.GetVolumeRange()
        self.minVol, self.maxVol = self.volRange[0], self.volRange[1]
        self.volBar = 400
        self.volPer = 0
        self.brightnessBar = 400
        self.brightnessPer = 0

        self.update_frame_media()

    def update_frame_media(self):
        if not self.running:
            if hasattr(self, 'cap'):
                self.cap.release()
            return

        success, img = self.cap.read()
        if not success:
            self.root.after(10, self.update_frame_media)
            return

        img = self.detector.findHands(img)
        lmList, bbox = self.detector.findPosition(img, draw=True)

        if len(lmList) != 0:
            area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) // 100
            if 250 < area < 1000:
                length, img, lineInfo = self.detector.findDistance(4, 8, img)

                thumb_pinky_dist, _, _ = self.detector.findDistance(4, 20, img, draw=False)
                if thumb_pinky_dist < 40:
                    keyboard.send('play/pause media')
                    time.sleep(0.5)

                thumb_middle_dist, _, _ = self.detector.findDistance(4, 12, img, draw=False)
                if thumb_middle_dist < 40:
                    keyboard.send('shift+n')
                    keyboard.send('next track')
                    time.sleep(0.5)

                thumb_ring_dist, _, _ = self.detector.findDistance(4, 16, img, draw=False)
                if thumb_ring_dist < 40:
                    keyboard.send('shift+p')
                    keyboard.send('previous track')
                    time.sleep(0.5)

                self.volBar = np.interp(length, [50, 200], [400, 150])
                self.volPer = np.interp(length, [50, 200], [0, 100])
                self.volPer = 10 * round(self.volPer / 10)

                fingers = self.detector.fingersUp()

                if not fingers[4]:
                    self.volume.SetMasterVolumeLevelScalar(self.volPer / 100, None)
                    cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)

                brightness_length, img, brightness_lineInfo = self.detector.findDistance(8, 12, img)
                self.brightnessBar = np.interp(brightness_length, [30, 150], [400, 150])
                self.brightnessPer = np.interp(brightness_length, [30, 150], [0, 100])
                self.brightnessPer = 10 * round(self.brightnessPer / 10)

                if fingers[3] == 0 and fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 1 and fingers[4] == 1:
                    sbc.set_brightness(int(self.brightnessPer))
                    cv2.circle(img, (brightness_lineInfo[4], brightness_lineInfo[5]), 15, (0, 255, 255), cv2.FILLED)

        # رسم أشرطة الصوت والإضاءة بشكل أجمل
        cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)
        cv2.rectangle(img, (50, int(self.volBar)), (85, 400), (255, 0, 0), cv2.FILLED)
        cv2.putText(img, f'{int(self.volPer)} %', (40, 430), cv2.FONT_HERSHEY_COMPLEX, 0.9, (255, 0, 0), 2)
        cVol = int(self.volume.GetMasterVolumeLevelScalar() * 100)
        cv2.putText(img, f'Vol: {int(cVol)}', (120, 180), cv2.FONT_HERSHEY_COMPLEX, 0.9, (0, 255, 0), 2)

        cv2.rectangle(img, (100, 150), (135, 400), (255, 255, 0), 3)
        cv2.rectangle(img, (100, int(self.brightnessBar)), (135, 400), (255, 255, 0), cv2.FILLED)
        cv2.putText(img, f'{int(self.brightnessPer)} %', (90, 430), cv2.FONT_HERSHEY_COMPLEX, 0.9, (255, 255, 0), 2)

        cTime = time.time()
        fps = 1 / (cTime - getattr(self, 'pTime', time.time()))
        self.pTime = cTime
        cv2.putText(img, f'FPS: {int(fps)}', (500, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 2)

        # تحديث المعلومات أعلى النافذة
        self.vol_label.config(text=f"Volume: {int(self.volPer)} %")
        self.bright_label.config(text=f"Brightness: {int(self.brightnessPer)} %")
        self.fps_label.config(text=f"FPS: {int(fps)}")

        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        imgTK = ImageTk.PhotoImage(image=Image.fromarray(imgRGB))
        self.canvas.imgtk = imgTK
        self.canvas.configure(image=imgTK)

        self.root.after(10, self.update_frame_media)

    # ========== Mouse Mode ==========
    def start_mouse_mode(self):
        self.cap = cv2.VideoCapture(self.camera_index.get())
        wCam, hCam = 640, 480
        self.cap.set(3, wCam)
        self.cap.set(4, hCam)
        self.detector = handDetector(maxHands=1)
        self.wScr, self.hScr = autopy.screen.size()
        self.frameR = 100
        self.smoothening = 7
        self.pTime = 0
        self.plocX, self.plocY = 0, 0
        self.clocX, self.clocY = 0, 0
        self.update_frame_mouse()

    def update_frame_mouse(self):
        if not self.running:
            if hasattr(self, 'cap'):
                self.cap.release()
            return

        success, img = self.cap.read()
        if not success:
            self.root.after(10, self.update_frame_mouse)
            return

        lmList, bbox = self.detector.findPosition(self.detector.findHands(img), draw=True)
        if len(lmList) >= 13:
            x1, y1 = lmList[8][1:]
            x2, y2 = lmList[12][1:]
            fingers = self.detector.fingersUp()
            cv2.rectangle(img, (self.frameR, self.frameR), (640 - self.frameR, 480 - self.frameR), (255, 0, 255), 2)
            # Move Mode
            if fingers[1] == 1 and fingers[2] == 0:
                x3 = np.interp(x1, (self.frameR, 640 - self.frameR), (0, self.wScr))
                y3 = np.interp(y1, (self.frameR, 480 - self.frameR), (0, self.hScr))
                self.clocX = self.plocX + (x3 - self.plocX) / self.smoothening
                self.clocY = self.plocY + (y3 - self.plocY) / self.smoothening
                autopy.mouse.move(self.wScr - self.clocX, self.clocY)
                cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
                self.plocX, self.plocY = self.clocX, self.clocY
            # Click Mode
            if fingers[1] == 1 and fingers[2] == 1:
                length, img, lineInfo = self.detector.findDistance(8, 12, img)
                if length < 40:
                    cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)
                    autopy.mouse.click()
        cTime = time.time()
        fps = 1 / (cTime - getattr(self, 'pTime', time.time()))
        self.pTime = cTime
        cv2.putText(img, str(int(fps)), (20, 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        imgTK = ImageTk.PhotoImage(image=Image.fromarray(imgRGB))
        self.canvas.imgtk = imgTK
        self.canvas.configure(image=imgTK)
        self.root.after(10, self.update_frame_mouse)

    def close_app(self):
        self.running = False
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = HandControlApp(root)
    root.mainloop()