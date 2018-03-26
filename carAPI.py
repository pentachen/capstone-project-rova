# This is a "driver" for our RC car, the Exceed Rally Monster Truck.
# Hobby-level RC car control involves transmitting a PWM signal at 50Hz.
# Pulse lengths tend to be within 1ms and 2ms, with a period of 20ms.
# In other words, duty cycles are within 5% and 10%.
#
# The steering servo on our car seems to be miscalibrated.  We introduce
# an offset to compensate its urge to turn right.

import time
import Adafruit_PCA9685

# Initialize the PCA9685 using the default address (0x40).
pwm = Adafruit_PCA9685.PCA9685()

# Configure PCA9685 channels
throttle = 0
steering = 15

# Configure min and max pulse lengths, out of 4096
base = 4096 / 20
throttleAmp = base/2 
throttleMed = 307   # (4096 / 20) * 1.5

offset = 29
steeringAmp = 70
steeringMed = 307 + offset
#steeringMin = steeringMed - steeringAmp (right)
#steeringMax = steeringMed + steeringAmp (left)

# Arm the ESC and set frequency to 50Hz
def initialize():
    print throttleMed
    print throttle
    print steeringMed
    print steering

    pwm.set_pwm_freq(50) 
    pwm.set_pwm(throttle, 0, throttleMed)
    pwm.set_pwm(steering, 0, steeringMed)
    time.sleep(1.5)

def accel(percent):
    if (percent < 0):
        percent = 0
    elif (percent > 100):
        percent = 100

    pulse = throttleMed + (throttleAmp * percent / 100)
    pwm.set_pwm(throttle, 0, pulse)

def reverse(percent):
    if (percent < 0):
        percent = 0
    elif (percent > 100):
        percent = 100

    pulse = throttleMed - (throttleAmp * percent / 100)
    pwm.set_pwm(throttle, 0, pulse)

def stop():
    pwm.set_pwm(throttle, 0, throttleMed)

# FSM uses angle, 0 to 80 degrees?
def turnRight(percent):
    if (percent < 0):
        percent = 0
    elif (percent > 100):
        percent = 100

    pulse = steeringMed - (steeringAmp * percent / 100)
    pwm.set_pwm(steering, 0, pulse)

def turnLeft(percent):
    if (percent < 0):
        percent = 0
    elif (percent > 100):
        percent = 100

    pulse = steeringMed + (steeringAmp * percent / 100)
    pwm.set_pwm(steering, 0, pulse)

def straighten():
    pwm.set_pwm(steering, 0, steeringMed)

#TODO: MULTITHREAD
def turnInPlace(degree):
    #left
    accel(100)
    time.sleep(0.4)
    stop()
    time.sleep(0.1)

    turnRight(100)
    reverse(100)
    time.sleep(0.8)
    stop()
    time.sleep(0.1)

    turnLeft(100)
    accel(100)
    time.sleep(0.4)
    stop()
    time.sleep(0.1)

    pass