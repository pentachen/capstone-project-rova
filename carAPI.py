# This is a "driver" for our RC car, the Exceed Rally Monster Truck.
# Hobby-level RC car control involves transmitting a PWM signal at 50Hz.
# Pulse lengths tend to be within 1ms and 2ms, with a period of 20ms.
# In other words, duty cycles are within 5% and 10%.
#
# The steering servo on our car seems to be miscalibrated.  We introduce
# an offset to compensate its urge to turn right.

from __future__ import division
import time
import Adafruit_PCA9685

# Initialize the PCA9685 using the default address (0x40).
pwm = Adafruit_PCA9685.PCA9685()

# Configure PCA9685 channels
throttle = 0
steering = 15

# Configure min and max pulse lengths, out of 4096
base = 4096 / 20
throttleMin = base
throttleMed = base * 1.5
throttleMax = base * 2

offset = 29
amplitude = 70
steeringMed = base * 1.5 + offset
steeringMin = steeringMed - amplitude
steeringMax = steeringMed + amplitude

# Arm the ESC and set frequency to 50Hz
def initializeAndPause():
    pwm.set_pwm(throttle, 0, throttleMed)
    pwm.set_pwm(steering, 0, steeringMed)
    time.sleep(1.5)
    pwm.set_pwm_freq(50)

def accel(percent):
    if (percent < 0):
        percent = 0
    elif (percent > 100):
        percent = 100
        
    pulse = throttleMed + percent * 1.024
    pwm.set_pwm(throttle, 0, pulse)

def reverse(percent):
    if (percent < 0):
        percent = 0
    elif (percent > 100):
        percent = 100

    pulse = throttleMed - percent * 1.024
    pwm.set_pwm(throttle, 0, pulse)

def turn(angle):
