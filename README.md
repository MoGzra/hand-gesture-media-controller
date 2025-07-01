# 🖐️ Hand Gesture Media Controller

Control your PC’s **volume**, **screen brightness**, **media playback**, and even the **mouse cursor** — all using just your hand gestures and a webcam.

Built with **Python**, **OpenCV**, **MediaPipe**, and a modern **Tkinter GUI**, this tool delivers a hands-free, real-time control experience.

---

## 📌 Description

This project allows you to interact with your computer using hand gestures only — no extra hardware or physical contact required.  
It features two powerful modes:

- 🎚️ **Media Mode** – Control system volume, brightness, play/pause, next/previous track  
- 🖱️ **Mouse Mode** – Move the mouse vertically and click using hand gestures

It uses a webcam feed, detects hand landmarks in real time using **MediaPipe**, and performs actions via Python libraries like **pycaw**, **screen_brightness_control**, and **autopy**.

---

## 🎯 Features

- ✅ Real-time hand detection and tracking
- ✅ Volume control via thumb-index distance
- ✅ Brightness control via index-middle distance
- ✅ Media control (play/pause, next, previous)
- ✅ Mouse movement & click using finger gestures
- ✅ Fully responsive GUI using Tkinter
- ✅ Smooth, lag-free experience with FPS tracking

---

## 🧑‍🏫 How It Works

### ✋ Gesture Mapping

| Gesture / Fingers Used                                | Action                                  |
|--------------------------------------------------------|-----------------------------------------|
| 👉 Thumb + Index pinch <br>+ **pinky down**            | Control **volume level**                |
| ✌️ Index + Middle distance <br>+ **pinky down**        | Control **brightness level**            |
| 🤏 Thumb + Pinky close together                        | Toggle **play/pause** media             |
| 🤏 Thumb + Middle close together                       | Skip to **next track**                  |
| 🤏 Thumb + Ring close together                         | Go to **previous track**                |
| ☝️ Index finger only (in mouse mode)                   | **Move mouse** vertically               |
| ✌️ Index + Middle close together (in mouse mode)       | **Mouse click**                         |
| 🖐️ Open palm (all fingers up)                          | Neutral / Standby (no action)           |

> All actions are triggered only when gestures are stable and valid (to prevent accidental controls).

---

## 📷 Screenshots


![Screenshot 2025-06-30 025859](https://github.com/user-attachments/assets/a5d1d8ea-7751-4a17-ac8f-99394e749194)



---
### 🔧 Requirements

Install the required libraries:

```bash
pip install -r requirements.txt
```

### 🧪 How to Run
```bash
python main.py
```

