import re
from handTracker import *
import cv2
import mediapipe as mp
import numpy as np
import random
import time
import os
from google.cloud import vision_v1
from google.cloud.vision_v1 import types
from gtts import gTTS
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Set the path to the Google Cloud credentials file
credentials_path = 'SkyScribe.json'
client = vision_v1.ImageAnnotatorClient.from_service_account_file(credentials_path)

# Set the API key for Gemini
os.getenv('API_KEY')
genai.configure(api_key=os.environ["API_KEY"])

class ColorRect():
    def __init__(self, x, y, w, h, color, text='', alpha=0.5):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.text = text
        self.alpha = alpha

    def drawRect(self, img, text_color=(255, 255, 255), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.8, thickness=2):
        # Draw the box
        alpha = self.alpha
        bg_rec = img[self.y: self.y + self.h, self.x: self.x + self.w]
        white_rect = np.ones(bg_rec.shape, dtype=np.uint8)
        white_rect[:] = self.color
        res = cv2.addWeighted(bg_rec, alpha, white_rect, 1 - alpha, 1.0)

        # Putting the image back to its position
        img[self.y: self.y + self.h, self.x: self.x + self.w] = res

        # Put the letter
        tetx_size = cv2.getTextSize(self.text, fontFace, fontScale, thickness)
        text_pos = int(self.x + self.w / 2 - tetx_size[0][0] / 2), int(self.y + self.h / 2 + tetx_size[0][1] / 2)
        cv2.putText(img, self.text, text_pos, fontFace, fontScale, text_color, thickness)

    def isOver(self, x, y):
        if (self.x + self.w > x > self.x) and (self.y + self.h > y > self.y):
            return True
        return False


# Initialize the hand detector
detector = HandTracker(detectionCon=0.8)

# Initialize the camera
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

# Create canvas to draw on it
canvas = np.zeros((720, 1280, 3), np.uint8)

# Create white canvas
whiteCanvas = np.ones((720, 1280, 3), dtype=np.uint8) * 255  # White background canvas
whiteCanvasVisible = False  # Flag to check if the white canvas is visible

# Define a previous point to be used with drawing a line
px, py = 0, 0

# Initial brush color
color = (255, 0, 0)

# Brush and eraser sizes
brushSize = 5
eraserSize = 20

# Create colors
colorsBtn = ColorRect(200, 0, 100, 100, (120, 255, 0), 'Colors')

colors = []
# Random color
b = int(random.random() * 255) - 1
g = int(random.random() * 255)
r = int(random.random() * 255)
print(b, g, r)
colors.append(ColorRect(300, 0, 100, 100, (b, g, r)))
# Red
colors.append(ColorRect(400, 0, 100, 100, (0, 0, 255)))
# Blue
colors.append(ColorRect(500, 0, 100, 100, (255, 0, 0)))
# Green
colors.append(ColorRect(600, 0, 100, 100, (0, 255, 0)))
# Yellow
colors.append(ColorRect(700, 0, 100, 100, (0, 255, 255)))
# Erase (black)
colors.append(ColorRect(800, 0, 100, 100, (0, 0, 0), "Eraser"))

# Clear button
clear = ColorRect(900, 0, 100, 100, (100, 100, 100), "Clear")

# Pen sizes
pens = []
for i, penSize in enumerate(range(5, 25, 5)):
    pens.append(ColorRect(1100, 50 + 100 * i, 100, 100, (50, 50, 50), str(penSize)))

penBtn = ColorRect(1100, 0, 100, 50, color, 'Pen')

# Capture button
captureBtn = ColorRect(1000, 0, 100, 50, (200, 200, 50), 'Capture')

# White board button
boardBtn = ColorRect(50, 0, 100, 100, (255, 255, 0), 'Board')

# Define a white board to draw on
whiteBoard = ColorRect(50, 120, 1020, 580, (255, 255, 255), alpha=0.6)

coolingCounter = 20
hideBoard = True
hideColors = True
hidePenSizes = True

# Create the "Captures" folder if it doesn't exist
if not os.path.exists("Captures"):
    os.makedirs("Captures")

def detect_text(image_path):
    """Detects text in an image using Google Vision API."""
    with open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if texts:
        return texts[0].description  # Return the detected text
    return None

while True:
    if coolingCounter:
        coolingCounter -= 1

    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.resize(frame, (1280, 720))
    frame = cv2.flip(frame, 1)

    detector.findHands(frame)
    positions = detector.getPosition(frame, draw=False)
    upFingers = detector.getUpFingers(frame)

    if upFingers:
        x, y = positions[8][0], positions[8][1]
        if upFingers[1] and not whiteBoard.isOver(x, y):
            px, py = 0, 0

            ##### Pen sizes ######
            if not hidePenSizes:
                for pen in pens:
                    if pen.isOver(x, y):
                        brushSize = int(pen.text)
                        pen.alpha = 0
                    else:
                        pen.alpha = 0.5

            ###### Choose a color for drawing #######
            if not hideColors:
                for cb in colors:
                    if cb.isOver(x, y):
                        color = cb.color
                        cb.alpha = 0
                    else:
                        cb.alpha = 0.5

                # Clear button
                if clear.isOver(x, y):
                    clear.alpha = 0
                    canvas = np.zeros((720, 1280, 3), np.uint8)
                    whiteCanvas = np.ones((720, 1280, 3), dtype=np.uint8) * 255  # Clear white canvas
                else:
                    clear.alpha = 0.5

            # Color button
            if colorsBtn.isOver(x, y) and not coolingCounter:
                coolingCounter = 10
                colorsBtn.alpha = 0
                hideColors = False if hideColors else True
                colorsBtn.text = 'Colors' if hideColors else 'Hide'
            else:
                colorsBtn.alpha = 0.5

            # Pen size button
            if penBtn.isOver(x, y) and not coolingCounter:
                coolingCounter = 10
                penBtn.alpha = 0
                hidePenSizes = False if hidePenSizes else True
                penBtn.text = 'Pen' if hidePenSizes else 'Hide'
            else:
                penBtn.alpha = 0.5

            # Capture button
            if captureBtn.isOver(x, y) and not coolingCounter:
                coolingCounter = 10
                captureBtn.alpha = 0
                if not hideBoard:  # Save only if board is visible
                    # Capture the white canvas content
                    whiteCanvasRegion = whiteCanvas[
                        whiteBoard.y: whiteBoard.y + whiteBoard.h,
                        whiteBoard.x: whiteBoard.x + whiteBoard.w
                    ]
                    filename = f"Captures/capture_{int(time.time())}.png"
                    cv2.imwrite(filename, whiteCanvasRegion)
                    print(f"Saved {filename}")

                    # Use Google Vision API to detect text
                    detected_text = detect_text(filename)
                    if detected_text:
                        print("Detected Text:", detected_text)

                        # Send detected_text to Gemini and print the response
                        model = genai.GenerativeModel("gemini-1.5-pro")  # Load the Gemini model
                        response = model.generate_content(detected_text)  # Generate response
                        gemini_response = response.text  # Extract text
                        print("Gemini Response:", gemini_response)
                        # Convert text to speech
                        tts = gTTS(text=gemini_response, lang='en')
                        tts.save("response.mp3")
                        os.system("start response.mp3")  # Play the audio
                    else:
                        print("No text detected.")
            else:
                captureBtn.alpha = 0.5
            if boardBtn.isOver(x, y) and not coolingCounter:
                coolingCounter = 10
                boardBtn.alpha = 0
                hideBoard = False if hideBoard else True
                boardBtn.text = 'Board' if hideBoard else 'Hide'
                whiteCanvasVisible = not hideBoard
            else:
                boardBtn.alpha = 0.5

        elif upFingers[1] and not upFingers[2]:
            if whiteBoard.isOver(x, y) and not hideBoard:
                cv2.circle(frame, positions[8], brushSize, color, -1)
                if px == 0 and py == 0:
                    px, py = positions[8]
                if color == (0, 0, 0):
                    cv2.line(canvas, (px, py), positions[8], color, eraserSize)
                    cv2.line(whiteCanvas, (px, py), positions[8], (255, 255, 255), eraserSize)
                else:
                    cv2.line(canvas, (px, py), positions[8], color, brushSize)
                    cv2.line(whiteCanvas, (px, py), positions[8], color, brushSize)
                px, py = positions[8]
        else:
            px, py = 0, 0
    colorsBtn.drawRect(frame)
    cv2.rectangle(frame, (colorsBtn.x, colorsBtn.y), (colorsBtn.x + colorsBtn.w, colorsBtn.y + colorsBtn.h), (255, 255, 255), 2)
    boardBtn.drawRect(frame)
    cv2.rectangle(frame, (boardBtn.x, boardBtn.y), (boardBtn.x + boardBtn.w, boardBtn.y + boardBtn.h), (255, 255, 255), 2)
    captureBtn.drawRect(frame)
    cv2.rectangle(frame, (captureBtn.x, captureBtn.y), (captureBtn.x + captureBtn.w, captureBtn.y + captureBtn.h), (255, 255, 255), 2)
    if not hideBoard:
        whiteBoard.drawRect(frame)
        canvasGray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
        _, imgInv = cv2.threshold(canvasGray, 20, 255, cv2.THRESH_BINARY_INV)
        imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)
        frame = cv2.bitwise_and(frame, imgInv)
        frame = cv2.bitwise_or(frame, canvas)
    if whiteCanvasVisible:
        cv2.imshow('White Canvas', whiteCanvas)
    if not hideColors:
        for c in colors:
            c.drawRect(frame)
            cv2.rectangle(frame, (c.x, c.y), (c.x + c.w, c.y + c.h), (255, 255, 255), 2)

        clear.drawRect(frame)
        cv2.rectangle(frame, (clear.x, clear.y), (clear.x + clear.w, clear.y + clear.h), (255, 255, 255), 2)
    penBtn.color = color
    penBtn.drawRect(frame)
    cv2.rectangle(frame, (penBtn.x, penBtn.y), (penBtn.x + penBtn.w, penBtn.y + penBtn.h), (255, 255, 255), 2)
    if not hidePenSizes:
        for pen in pens:
            pen.drawRect(frame)
            cv2.rectangle(frame, (pen.x, pen.y), (pen.x + pen.w, pen.y + pen.h), (255, 255, 255), 2)

    cv2.imshow('video', frame)
    k = cv2.waitKey(1)
    if k == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()