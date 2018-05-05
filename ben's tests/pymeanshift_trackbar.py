from picamera.array import PiRGBArray
from picamera import PiCamera

import cv2
import numpy as np

#optional argument
def nothing(x):
    pass
cap = cv2.VideoCapture(0)
cv2.namedWindow('meanshift')

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (480, 368)
camera.framerate = 2
rawCapture = PiRGBArray(camera, size=(480, 368))

# add ON/OFF switch to "meanshift"
cv2.createTrackbar("meanshift", 'meanshift', 0, 1, nothing)
# cv2.createTrackbar("pre-erode", 'meanshift', 0, 1, nothing)
# cv2.createTrackbar("pre-dilate", 'meanshift', 0, 1, nothing)
# cv2.createTrackbar("post-erode", 'meanshift', 0, 1, nothing)
# cv2.createTrackbar("post-dilate", 'meanshift', 0, 1, nothing)

# add lower and upper threshold slidebars to "meanshift"
cv2.createTrackbar('sp', 'meanshift', 0, 255, nothing)
cv2.createTrackbar('sr', 'meanshift', 0, 255, nothing)
cv2.createTrackbar('maxLevel', 'meanshift', 0, 40, nothing)
cv2.createTrackbar('erode', 'meanshift', 0, 6, nothing)
cv2.createTrackbar('dilate', 'meanshift', 0, 6, nothing)

for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):

    image = frame.array

    erodeIter = cv2.getTrackbarPos('erode', 'meanshift')
    dilateIter = cv2.getTrackbarPos('dilate', 'meanshift')
    sp = cv2.getTrackbarPos('sp', 'meanshift')
    sr = cv2.getTrackbarPos('sr', 'meanshift')
    maxLevel = cv2.getTrackbarPos('maxLevel', 'meanshift')

    ms = cv2.getTrackbarPos('meanshift', 'meanshift')
    # preE = cv2.getTrackbarPos('pre-erode', 'meanshift')
    # preD = cv2.getTrackbarPos('pre-dilate', 'meanshift')
    # postE = cv2.getTrackbarPos('post-erode', 'meanshift')
    # postD = cv2.getTrackbarPos('post-dilate', 'meanshift')

    img = cv2.erode(image, None, iterations=erodeIter)
    img = cv2.dilate(img, None, iterations=dilateIter)

    if ms == 0:
        edges = img
    else:
        edges = cv2.pyrMeanShiftFiltering(img, sp, sr, maxLevel)

    # display images
    cv2.imshow('original', img)
    cv2.imshow('meanshift', edges)
  
    key = cv2.waitKey(1) & 0xFF

    # clear the stream in preparation for the next frame
    rawCapture.truncate(0)

    # if the 'q' key is pressed, stop the loop
    if key == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
