# USAGE
# python ball_tracking.py --video ball_tracking_example.mp4
# python ball_tracking.py

# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
from collections import deque
import numpy as np
import argparse
import imutils
import time
import cv2

BUFFER_SIZE = 64

# define the lower and upper boundaries of the "green"
# ball in the HSV color space, then initialize the
# list of tracked points
# greenLower = (29, 86, 6)
# greenUpper = (64, 255, 255)

greenLower = (25, 122, 125)
greenUpper = (64, 255, 255)

pts = deque(maxlen=BUFFER_SIZE)

# width = 960
# height = 720
# fps = 3

width = 480
height = 360
fps = 8

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (width, height)
camera.framerate = fps
rawCapture = PiRGBArray(camera, size=(width, height))

# allow the camera to warmup
time.sleep(0.1)

# keep looping
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
	# grab the raw NumPy array representing the image, then initialize the timestamp
	# and occupied/unoccupied text
	image = frame.array

	# blur the image and convert it to HSV
	# blurred = cv2.GaussianBlur(image, (11, 11), 0)
	hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
	# imageG = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

	# construct a mask for the color "green", then perform
	# a series of dilations and erosions to remove any small
	# blobs left in the mask
	mask = cv2.erode(hsv, None, iterations=2)
	mask = cv2.dilate(mask, None, iterations=2)

	mask = cv2.inRange(mask, greenLower, greenUpper)

	# find contours in the mask and initialize the current
	# (x, y) center of the ball
	im2, cnts, hierarchy = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
	
	image3 = cv2.drawContours(image, cnts, -1, (0,99,255), 3)

	# show the image to our screen
	cv2.imshow("image", image3)
	key = cv2.waitKey(1) & 0xFF
	cv2.imshow("mask", mask)
	key = cv2.waitKey(1) & 0xFF

	# clear the stream in preparation for the next frame
	rawCapture.truncate(0)

	# if the 'q' key is pressed, stop the loop
	if key == ord("q"):
		break

# cleanup the camera and close any open windows
camera.release()
cv2.destroyAllWindows()