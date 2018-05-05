from picamera.array import PiRGBArray
from picamera import PiCamera

import cv2
import numpy as np

#optional argument
def nothing(x):
    pass
cap = cv2.VideoCapture(0)
cv2.namedWindow('canny')
cv2.namedWindow('bars')

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (480, 368)
camera.framerate = 5
rawCapture = PiRGBArray(camera, size=(480, 368))

# add ON/OFF switch to "canny"
switch = 'CANNY'
cv2.createTrackbar(switch, 'bars', 0, 1, nothing)
switch2 = 'GAUSSIAN'
cv2.createTrackbar(switch2, 'bars', 0, 1, nothing)
switch3 = 'BOX'
cv2.createTrackbar(switch3, 'bars', 0, 1, nothing)
switch4 = 'MEDIAN'
cv2.createTrackbar(switch4, 'bars', 0, 1, nothing)
switch5 = 'BILATERAL'
cv2.createTrackbar(switch5, 'bars', 0, 1, nothing)

# add lower and upper threshold slidebars to "canny"
cv2.createTrackbar('lower', 'bars', 0, 255, nothing)
cv2.createTrackbar('upper', 'bars', 0, 255, nothing)
cv2.createTrackbar('erode', 'bars', 0, 20, nothing)
cv2.createTrackbar('dilate', 'bars', 0, 20, nothing)
cv2.createTrackbar('kernel', 'bars', 1, 20, nothing)

for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):

    image = frame.array

    erodeIter = cv2.getTrackbarPos('erode', 'bars')
    dilateIter = cv2.getTrackbarPos('dilate', 'bars')
    lower = cv2.getTrackbarPos('lower', 'bars')
    upper = cv2.getTrackbarPos('upper', 'bars')
    kernel = cv2.getTrackbarPos('kernel', 'bars')

    s = cv2.getTrackbarPos(switch, 'bars')
    gaussian = cv2.getTrackbarPos(switch2, 'bars')
    box = cv2.getTrackbarPos(switch3, 'bars')
    median = cv2.getTrackbarPos(switch4, 'bars')
    bilateral = cv2.getTrackbarPos(switch5, 'bars')

    img = image.copy()

    if gaussian == 1:
        img = cv2.GaussianBlur(img, (kernel, kernel), 0)       
    if box == 1:
        img = cv2.blur(img, (kernel, kernel))
    if median == 1:
        img = cv2.medianBlur(img, kernel)
    if bilateral == 1:
        img = cv2.bilateralFilter(img, kernel, 75, 75)

    img = cv2.erode(img, None, iterations=erodeIter)
    img = cv2.dilate(img, None, iterations=dilateIter)

    if s == 0:
        edges = img
    else:
        edges = cv2.Canny(img, lower, upper)


    # display images
    cv2.imshow('original', image)
    cv2.imshow('canny', edges)
  
    key = cv2.waitKey(1) & 0xFF

    # clear the stream in preparation for the next frame
    rawCapture.truncate(0)

    # if the 'q' key is pressed, stop the loop
    if key == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
