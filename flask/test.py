#!/usr/bin/python3

import cv2

from picamera2 import Picamera2

# Grab images as numpy arrays and leave everything else to OpenCV.

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (1920, 1080)}))
picam2.start()

while True:
    im = picam2.capture_array()

    cv2.imshow("Camera", im)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break