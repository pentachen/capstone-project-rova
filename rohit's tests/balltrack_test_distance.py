from picamera.array import PiRGBArray
from picamera import PiCamera
from collections import deque
import numpy as np
import argparse
import imutils
import time
import cv2

BUFFER_SIZE = 64

# 1ms, 1.5ms, and 2ms pulses 
servoMin = 205
servoMed = 307
servoMax = 409

# define the lower and upper boundaries of the "green"
# ball in the HSV color space, then initialize the
# list of tracked points
greenLower = (29, 86, 6)
greenUpper = (64, 255, 255)

# distance calc stuff
D = 3 # ball was kept 3 inches away from camera
P = 101 # width in pixels at 3 inches away
actualRadius = 2.6 # radius of ball in inches
focalLength = D*P/actualRadius
pts = deque(maxlen=BUFFER_SIZE)

def calcDist(focalLength, realRadius, pixelRadius):
	return focalLength * realRadius/pixelRadius

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (480, 360)
camera.framerate = 10
rawCapture = PiRGBArray(camera, size=(480, 360))

# allow the camera to warmup and arm the ESC
time.sleep(2)

# keep looping
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
	# grab the raw NumPy array representing the image, then initialize the timestamp
	# and occupied/unoccupied text
	image = frame.array

	# blur the image and convert it to HSV
	blurred = cv2.GaussianBlur(image, (11, 11), 0)
	hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

	# construct a mask for the color "green", then perform
	# a series of dilations and erosions to remove any small
	# blobs left in the mask
	mask = cv2.inRange(hsv, greenLower, greenUpper)
	mask = cv2.erode(mask, None, iterations=2)
	mask = cv2.dilate(mask, None, iterations=2)

	# find contours in the mask and initialize the current
	# (x, y) center of the ball
	cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
	center = None

	# only proceed if at least one contour was found
	if len(cnts) > 0:
		# find the largest contour in the mask, then use
		# it to compute the minimum enclosing circle and
		# centroid
		c = max(cnts, key=cv2.contourArea)
		((x, y), radius) = cv2.minEnclosingCircle(c)
		M = cv2.moments(c)
		center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

		# only proceed if the radius meets a minimum size
		if radius > 10:
			# draw the circle and centroid on the image,
			cv2.circle(image, (int(x), int(y)), int(radius), (0, 255, 255), 2)
			cv2.circle(image, center, 5, (0, 0, 255), -1)
		
		distance = calcDist(focalLength, actualRadius, radius)

		print "Radius is: ", str(radius), " and distance is: ", str(distance)

	# show the image to our screen
	cv2.imshow("image", image)
	key = cv2.waitKey(1) & 0xFF

	# clear the stream in preparation for the next frame
	rawCapture.truncate(0)

	# if the 'q' key is pressed, stop the loop
	if key == ord("q"):
		break

# cleanup the camera and close any open windows
camera.release()
cv2.destroyAllWindows()
