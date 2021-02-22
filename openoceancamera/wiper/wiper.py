import os
import time
import sys

SERVO_LOWER_LIMIT=50
SERVO_UPPER_LIMIT=250

class Wiper:
    def __init__(self, pin):
        self.PIN = pin
        os.system("gpio pwm-ms")
        os.system("gpio pwmc 192")
        os.system("gpio pwmr 2000")

    def set_angle(self, angle):
        pwm_output = (SERVO_UPPER_LIMIT * angle + SERVO_LOWER_LIMIT * (360-angle))/360
        os.system(f"gpio -g pwm {self.PIN} {angle}")
