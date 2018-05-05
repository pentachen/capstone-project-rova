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
import carAPI as car

# define the lower and upper boundaries of the "green"
# ball in the HSV color space, then initialize the
# list of tracked points
# greenLower = (29, 86, 6)
greenLower = (25, 159, 125)
# greenLower = (25, 130, 125)
greenUpper = (64, 255, 255)

cameraDist = 7.5
D = 6.0 + cameraDist # ball was kept 3 inches away from camera
P = 39.6 # width in pixels at 3 inches away
actualRadius = 2.6 # radius of ball in inches
focalLength = D*P/actualRadius

D_marker = 12.0 + cameraDist # kept 17 inches away from camera
P_marker = 392.0 # height in pixels
actualHeight = 17 # in inches
markerFocalLength = D_marker * P_marker/actualRadius


num_markers = 4
boxSize = 120
markers = {0: "CYAN", 1: "BLUE", 2: "PINK", 3: "ORANGE"}
marker_ranges = {	0: [(80, 101, 0), (91, 255, 255)],
				 	1: [(92,52,0), (119,255,167)],
				 	2: [(165, 113, 77), (179, 255, 255)],
				 	3: [(0, 157, 90), (8, 255, 255)]	}
marker_pos = {		0: (0,0), 
					1: (boxSize, 0),
					2: (0, boxSize),
					3: (boxSize, boxSize)	}

# Total angle view given by fisheye
angleView = 160 
defaultRotate = 90

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (960, 720)
camera.framerate = 10
rawCapture = PiRGBArray(camera, size=(960, 720))

# allow the camera to warmup
time.sleep(0.1)

def find_centers(image, rangeLower, rangeUpper):
	#blurred = cv2.GaussianBlur(image, (11, 11), 0)
	hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

	# construct a mask for the color "green", then perform
	# a series of dilations and erosions to remove any small
	# blobs left in the mask
	mask = cv2.inRange(hsv, rangeLower, rangeUpper)
	mask = cv2.erode(mask, None, iterations=5)
	mask = cv2.dilate(mask, None, iterations=5)

	# find contours in the mask and initialize the current
	# (x, y) center of the ball
	#~ cv2.imshow("img", mask)
	#~ key = cv2.waitKey(1) & 0xFF
	cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)[-2]
	return cnts

def calcDist(focalLength, realRadius, pixelRadius):
    return focalLength * float(realRadius)/pixelRadius - cameraDist

def calcAngle(image, x):
	height, width, _ = image.shape
	center = width/2 
	angle = (x - center)/float(center) * angleView/2
	return angle

def determine_position(image):
	distances = [-1 for i in range(num_markers)]
	angles = [-200 for i in range(num_markers)]
	for i in range(num_markers):
		cnts = find_centers(image, marker_ranges[i][0], marker_ranges[i][1])
		if len(cnts) > 0:
			c = max(cnts, key=cv2.contourArea)
			x, y, w, h = cv2.boundingRect(c)

			distances[i] = calcDist(markerFocalLength, actualHeight, h)
			angles[i] = np.radians(calcAngle(image, x))

	positions = [(-1,-1), (-1,-1), (-1,-1), (-1,-1)]
	for i in xrange(num_markers):
		if distances[i] == -1:
			continue
		curr_angle = abs(angles[i])
		x = 0
		y = 0
		if i == 0 and angles[i] >= 0:
			x = marker_pos[i][0] + distances[i]*np.cos(curr_angle)
			y = marker_pos[i][1] + distances[i]*np.sin(curr_angle)
		elif i == 0 and angles[i] < 0:
			x = marker_pos[i][0] + distances[i]*np.sin(curr_angle)
			y = marker_pos[i][1] + distances[i]*np.cos(curr_angle)
		elif i == 1 and angles[i] >= 0:
			x = marker_pos[i][0] - distances[i]*np.sin(curr_angle)
			y = marker_pos[i][1] + distances[i]*np.cos(curr_angle)
		elif i == 1 and angles[i] < 0:
			x = marker_pos[i][0] - distances[i]*np.cos(curr_angle)
			y = marker_pos[i][1] + distances[i]*np.sin(curr_angle)
		elif i == 2 and angles[i] >= 0:
			x = marker_pos[i][0] + distances[i]*np.sin(curr_angle)
			y = marker_pos[i][1] - distances[i]*np.cos(curr_angle)
		elif i == 2 and angles[i] < 0:
			x = marker_pos[i][0] + distances[i]*np.cos(curr_angle)
			y = marker_pos[i][1] - distances[i]*np.sin(curr_angle)
		elif i == 3 and angles[i] >= 0:
			x = marker_pos[i][0] - distances[i]*np.cos(curr_angle)
			y = marker_pos[i][1] - distances[i]*np.sin(curr_angle)
		elif i == 3 and angles[i] < 0:
			x = marker_pos[i][0] - distances[i]*np.sin(curr_angle)
			y = marker_pos[i][1] - distances[i]*np.cos(curr_angle)

		positions[i] = (x,y)
	return positions

def look_for_balls(image):
	
	cnts = find_centers(image, greenLower, greenUpper)
	center = None

	print "Length of contours is: ", len(cnts)
	# only proceed if at least one contour was found
	if len(cnts) > 0:
		# assume that largest contour is the closest ball
		c = max(cnts, key=cv2.contourArea)
		((x, y), radius) = cv2.minEnclosingCircle(c)
		M = cv2.moments(c)
		center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

		# only proceed if the radius meets a minimum size

		distance = calcDist(focalLength, actualRadius, radius)
		angle = calcAngle(image, x)
		# Add code to convert center to distance and angle somehow
		
		return angle, True, center, distance

	return -1, False, (-1,-1), -1

def determine_closest_center(image, error):
	cnts = find_centers(image, greenLower, greenUpper)
	print image.shape
	height, width, _ = image.shape
	center = (-1,-1)
	radius = -1
	angle = -999

	if len(cnts) > 0:
		# assume that largest contour is the closest ball
		c = max(cnts, key=cv2.contourArea)
		((x, y), radius) = cv2.minEnclosingCircle(c)
		M = cv2.moments(c)
		center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
		if (abs(y - center[1]) < 20):
			print "Probably the right ball"
		angle = np.radians(calcAngle(image, x))

	return center, radius, angle

def pickup():
	print "PICKING UP BALL"
	car.accelT(28, 0.8)

def look_for_marker(image, marker_num):
	# Returns angle, position, distance
	cnts = find_centers(image, marker_ranges[marker_num][0], marker_ranges[marker_num][1])
	if len(cnts) > 0:
		c = max(cnts, key=cv2.contourArea)
		x, y, w, h = cv2.boundingRect(c)

		distance = calcDist(markerFocalLength, actualHeight, h)
		angle = np.radians(calcAngle(image, x))

		return angle, found, distance

	return 0, False, -1

states = ["LOOK FOR BALL", "ROTATE TO LOOK", "MOVE", "PICKUP", "DONE", "LOOK FOR MARKER"]
v = [False for i in xrange(num_markers)]
data = {"angle": 0, "found": False, "is_ball": False, "num_rot": 0, "count": 0, "distance": -1, "positions": [], "visited": v, "curr_marker": -1}

state_changed = False
curr_state = states[0]

car.initialize()

# keep looping
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
	# grab the raw NumPy array representing the image, then initialize the timestamp
	# and occupied/unoccupied text
	image = frame.array
	data["positions"] = determine_position(image)
	
	print "Curr state is: ", curr_state

	# LOOK FOR BALL
	if curr_state == states[0]:

		data["angle"], found, ball_center, data["distance"] = look_for_balls(image)
		data["found"] = data["found"] or found
		if found:
			print "Ball found at ", data["distance"], " with center ", ball_center

		data["count"] += 1

		# UNCOMMENT THIS TO SWITCH STATES
		# if data["count"] == 10 or data["found"] == True:
		# 	state_changed = True
		# 	data["count"] = 0
		# 	if not data["found"]:
		# 		data["angle"] = defaultRotate
		# 	data["is_ball"] = True
		# 	curr_state = states[1]
		# else:
		# 	state_changed = False

	# LOOK FOR MARKER
	elif curr_state == states[5]:

		founds = [False for i in xrange(num_markers)]
		dists = [-1 for i in xrange(num_markers)]
		angles = [0 for i in xrange(num_markers)]
		for i in xrange(num_markers):
			angles[i], founds[i], dists[i] = look_for_marker(image, i)
			data["found"] = data["found"] or founds[i]

		data["count"] += 1


		if data["count"] == 10 or data["found"] == True:
			state_changed = True
			data["count"] = 0
			data["is_ball"] = False
			if not data["found"]:
				data["angle"] = defaultRotate
				curr_state = states[1]
			else:
				curr_marker = -1
				vis = True
				for i in xrange(num_markers):
					if founds[i] and not data["visited"][i]:
						curr_marker = i
						data["angle"] = angles[i]
						vis = vis and data["visited"][i]
				data["curr_marker"] = curr_marker

				if vis:
					curr_state = states[4]
				else:
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
				#data["curr_marker"] += 1
				data["num_rot"] = 0
				curr_state = states[5]

		# If looking for ball and found, go towards it
		elif data["is_ball"] and data["found"]:
			data["num_rot"] = 0
			#data["curr_marker"] = -1
			curr_state = states[2]

		# If looking for marker and not found, turn in place till we back to
		# same position. If none of the markers are found, give up
		elif not data["is_ball"] and not data["found"]:
			data["num_rot"] += 1
			if data["num_rot"] < 4:
				curr_state = states[5]
			elif data["num_rot"] == 4:
				curr_state = states[4]

		# If marker found, go to it
		elif not data["is_ball"] and data["found"]:
			data["num_rot"] = 0
			curr_state = states[2]


	# MOVE TO BALL OR MARKER
	elif curr_state == states[2]:

		if data["is_ball"]:
			ball_center, radius, data["angle"] = determine_closest_center(image, 15)
		

			# DEBUG
			print "Radius: ", radius
			print "Center: ", ball_center

			if radius > 25:
				state_changed = True
				curr_state = states[3]
				data["found"] = False
				data["visited"] = [False for i in xrange(num_markers)]
			else:
				state_changed = False
				print "Driving forward to ball"
				car.turnAngle(int(data["angle"] * 3)) # maybe x2 or another multiplier
				car.accelT(35, 0.75)

		else:

			# TODO: Think of logic to move to marker, shouldn't be too hard
			data["angle"], _, distance = look_for_marker(image, data["curr_marker"]) 
			print "Distance of marker is: ", distance
			if distance < 2:
				state_changed = True
				curr_state = states[0]
				data["found"] = False
				data["visited"][data["curr_marker"]] = True
				data["curr_marker"] = -1
			else:
				state_changed = False
				print "Driving forward to marker"
				car.turnAngle(int(data["angle"] * 3)) # maybe x2 or another multiplier
				car.accelT(35, 0.75)

	# Pick up ball from here
	elif curr_state == states[3]:
		pickup()
		state_changed = True
		curr_state = states[0]

	elif curr_state == states[4]:
		print "Done doing things"
		break
		
	print "Positions array: ", data["positions"]
	print "Found: ", data["found"]
	print "Visited: ", data["visited"]
	print "Curr_marker: ", data["curr_marker"]
	print "Number of rotations: ", data["num_rot"]
	

	# show the image to our screen
	cv2.imshow("image", image)
	key = cv2.waitKey(1) & 0xFF

	# clear the stream in preparation for the next frame
	rawCapture.truncate(0)

# cleanup the camera and close any open windows
camera.release()
cv2.destroyAllWindows()
