# TODO:
# PORT _withFeed changes over

# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
from collections import deque
import numpy as np
import argparse
import imutils
import time
import cv2
import carAPI as car

# define the lower and upper boundaries of the "green"
# ball in the HSV color space, then initialize the
# list of tracked points
# greenLower = (29, 86, 6)
greenLower = (25, 159, 125)
# greenLower = (25, 130, 125)
greenUpper = (64, 255, 255)

marker_ranges = {"RED": [(), ()], "BLUE": [(), ()], "BLACK": [(), ()], "WHITE": [(), ()]}
markers = {0: "RED", 1: "BLUE", 2: "BLACK", 3: "WHITE"}

# Total angle view given by fisheye
angleView = 160 
defaultRotate = 90

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (480, 360)
camera.framerate = 10
rawCapture = PiRGBArray(camera, size=(480, 360))

# allow the camera to warmup
time.sleep(0.1)

def find_centers(image):
	# blurred = cv2.GaussianBlur(image, (11, 11), 0)
	hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

	# construct a mask for the color "green", then perform
	# a series of dilations and erosions to remove any small
	# blobs left in the mask
	mask = cv2.inRange(hsv, greenLower, greenUpper)
	mask = cv2.erode(mask, None, iterations=2)
	mask = cv2.dilate(mask, None, iterations=2)

	# find contours in the mask and initialize the current
	# (x, y) center of the ball
	cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)[-2]
	return cnts

def look_for_balls(image):
	
	cnts = find_centers(image)
	center = None

	# only proceed if at least one contour was found
	if len(cnts) > 0:
		# assume that largest contour is the closest ball
		c = max(cnts, key=cv2.contourArea)
		((x, y), radius) = cv2.minEnclosingCircle(c)
		M = cv2.moments(c)
		center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

		# only proceed if the radius meets a minimum size

		# Add code to convert center to distance and angle somehow
		height, width, _ = image.shape
		center = width/2 
		angle = (x - center)/float(center) * angleView/2
		return angle, True, center

	return -1, False, (-1,-1)

def determine_closest_center(image, error):
	cnts = find_centers(image)
	print image.shape
	height, width, _ = image.shape
	center = (-1,-1)
	radius = -1
	angle = -1

	if len(cnts) > 0:
		# assume that largest contour is the closest ball
		c = max(cnts, key=cv2.contourArea)
		((x, y), radius) = cv2.minEnclosingCircle(c)
		M = cv2.moments(c)
		center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
		if (abs(y - center[1]) < 20):
			print "Probably the right ball"

		height, width, _ = image.shape
		c = width/2 
		angle = (x - c)/float(c) * angleView/2

	return center, radius, angle

def look_for_marker(color):
	# Returns angle and position

	return 0, False

def pickup():
	print "PICKING UP BALL"
	car.accelT(28, 0.8)

def look_for_marker(image, marker_num):
	pass


markers = ["BLACK", "WHITE", "RED", "BLUE"]
states = ["LOOK FOR BALL", "ROTATE TO LOOK", "MOVE", "PICKUP", "DONE", "LOOK FOR MARKER"]
data = {"angle": 0, "found": False, "is_ball": False, "num_rot": 0, "ball_center": (-1,-1), "ball_radius": -1, "curr_marker": -1, "count": 0}

(major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')
tracker = None
if int(minor_ver) < 3:
    tracker = cv2.Tracker_create('KCF')
else:
    tracker = cv2.TrackerKCF_create()
state_changed = False
curr_state = states[0]

car.initialize()

# keep looping
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
	# grab the raw NumPy array representing the image, then initialize the timestamp
	# and occupied/unoccupied text
	image = frame.array
	print curr_state

	# LOOK FOR BALL
	if curr_state == states[0]:

		data["angle"], found, data["ball_center"] = look_for_balls(image)
		data["found"] = data["found"] or found

		print data["found"]

		data["count"] += 1

		if data["count"] == 10 or data["found"] == True:
			state_changed = True
			data["count"] = 0
			if not data["found"]:
				data["angle"] = defaultRotate
			data["is_ball"] = True
			curr_state = states[1]
		else:
			state_changed = False

	# LOOK FOR MARKER
	elif curr_state == states[5]:

		data["angle"], found, _ = look_for_balls(image)
		data["found"] = data["found"] or found

		data["count"] += 1

		if data["count"] == 10 or data["found"] == True:
			state_changed = True
			data["count"] = 0
			if not data["found"]:
				data["angle"] = defaultRotate
			data["is_ball"] = False
			curr_state = states[1]
		else:
			state_changed = False

			
	# ROTATE TO ANGLE
	elif curr_state == states[1]:

		print "Angle: ", data["angle"]
		if data["angle"] > 22 and data["angle"] < 67:
			car.turnLeft45()
		elif data["angle"] > 67:
			car.turnLeft90()
		elif data["angle"] < -22 and data["angle"] > -67:
			car.turnRight45()
		elif data["angle"] < -67:
			car.turnRight90()

		state_changed = True

		# If looking for ball and it's not found, rotate in place 
		# till we hit 360, and then look for marker
		if data["is_ball"] and not data["found"]:
			data["num_rot"] += 1
			if data["num_rot"] < 4:
				curr_state = states[0]
			elif data["num_rot"] == 4:
				data["curr_marker"] += 1
				curr_state = states[5]

		# If looking for ball and found, go towards it
		elif data["is_ball"] and data["found"]:
			data["num_rot"] = 0
			data["curr_marker"] = -1
			curr_state = states[2]

		# If looking for marker and not found, turn in place till we back to
		# same position. If none of the markers are found, give up
		elif not data["is_ball"] and not data["found"]:
			data["num_rot"] += 1
			if data["num_rot"] < 4:
				curr_state = states[5]
			elif data["num_rot"] == 4 and data["curr_marker"] == 3:
				curr_state = states[4]
			elif data["num_rot"] == 4 and data["curr_marker"] < 3:
				data["num_rot"] = 0
				data["curr_marker"] += 1
				curr_state = states[5]

		# If marker found, go to it
		elif not data["is_ball"] and data["found"]:
			data["num_rot"] = 0
			curr_state = states[2]


	# MOVE TO BALL OR MARKER
	elif curr_state == states[2]:

		if data["is_ball"]:
			data["ball_center"], data["ball_radius"], data["angle"] = determine_closest_center(image, 15)
		
			# DEBUG
			print "Radius: ", data["ball_radius"]
			print "Center: ", data["ball_center"]
			print "Angle: ", data["angle"]

			if data["ball_radius"] > 25:
				state_changed = True
				curr_state = states[3]
			else:
				state_changed = False
				print "driving forward"
				car.turnAngle(int(data["angle"] * 3)) # maybe x2 or another multiplier
				car.accel(30)

		else:


			# TODO: Think of logic to move to marker, shouldn't be too hard
			look_for_marker(image, data["curr_marker"]) 

	# Pick up ball from here
	elif curr_state == states[3]:
		pickup()
		state_changed = True
		curr_state = states[4]


	elif curr_state == states[4]:
		print "Done doing things"
		break
	

	# show the image to our screen
	# cv2.imshow("image", image)
	# key = cv2.waitKey(1) & 0xFF

	# clear the stream in preparation for the next frame
	rawCapture.truncate(0)

# cleanup the camera and close any open windows
camera.release()
# cv2.destroyAllWindows()