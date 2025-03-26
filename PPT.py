import win32com.client
from cvzone.HandTrackingModule import HandDetector
import cv2
import tkinter as tk
from tkinter import filedialog
import time

# Camera Setup
cap = cv2.VideoCapture(0)
cap.set(3, 900)
cap.set(4, 720)

# Check Camera Mirroring Before Proceeding
flip_camera = False
print("Checking if the camera feed is mirrored...")

while True:
    success, frame = cap.read()
    if not success:
        print("Camera error, skipping mirroring check.")
        break

    cv2.putText(frame, "Is this image mirrored? (Y/N)", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.imshow("Mirror Test", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('y'):
        flip_camera = True
        print("Camera is mirrored. Applying flip correction.")
        break
    elif key == ord('n'):
        flip_camera = False
        print("Camera is normal. No flip correction needed.")
        break

cv2.destroyWindow("Mirror Test")

# Function to open a PowerPoint file
def open_ppt():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select a PowerPoint File",
        filetypes=[("PowerPoint Files", "*.pptx *.ppt")]
    )
    return file_path

# Open a PowerPoint file
ppt_path = open_ppt()
if not ppt_path:
    print("No file selected. Exiting...")
    cap.release()
    exit()

ppt_path = ppt_path.replace("/", "\\")
print(f"Selected File: {ppt_path}")

# Initialize PowerPoint Application
Application = win32com.client.Dispatch("PowerPoint.Application")
Application.Visible = True
Presentation = Application.Presentations.Open(ppt_path)
print(f"Loaded Presentation: {Presentation.Name}")

SlideShow = Presentation.SlideShowSettings.Run()
time.sleep(2)

if Application.SlideShowWindows.Count > 0:
    SlideShowWindow = Application.SlideShowWindows(1)
    SlideShowView = SlideShowWindow.View
    SlideShowView.PointerType = 2  # Set pen mode
else:
    print("Error: Slideshow did not start properly.")
    Presentation.Close()
    Application.Quit()
    exit()

# Hand Detector
detectorHand = HandDetector(detectionCon=0.8, maxHands=1)

# Variables
annotationStart = False
last_x, last_y = None, None

while True:
    success, img = cap.read()
    if not success:
        print("Failed to capture image from camera.")
        break

    if flip_camera:
        img = cv2.flip(img, 1)

    imgCurrent = img.copy()

    hands, img = detectorHand.findHands(img)

    if hands:
        hand = hands[0]
        lmList = hand["lmList"]
        fingers = detectorHand.fingersUp(hand)

        # NEXT SLIDE: All fingers up
        if fingers == [1, 1, 1, 1, 1]:
            print("Next Slide")
            SlideShowView.Next()
            time.sleep(0.3)

        # PREVIOUS SLIDE: Only thumb up
        elif fingers == [1, 0, 0, 0, 0]:
            print("Previous Slide")
            SlideShowView.Previous()
            time.sleep(0.3)

        # ANNOTATE SLIDE: Only index finger up
        elif fingers == [0, 1, 0, 0, 0]:
            x, y = lmList[8][0], lmList[8][1]
            if not annotationStart:
                annotationStart = True
                last_x, last_y = x, y
            else:
                if last_x is not None and last_y is not None:
                    try:
                        SlideShowView.DrawLine(last_x, last_y, x, y)
                        last_x, last_y = x, y
                    except Exception as e:
                        print(f"Error drawing annotation: {e}")
        else:
            annotationStart = False
            last_x, last_y = None, None

        # ERASE SPECIFIC INK: Two fingers up (Index and Middle)
        if fingers == [0, 1, 1, 0, 0]:
            print("Erasing all annotations")
            SlideShowView.EraseDrawing()
            time.sleep(0.3)

    cv2.imshow("Image", imgCurrent)

    key = cv2.waitKey(1)
    if key == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
Presentation.Close()
Application.Quit()
print("PowerPoint application closed.")