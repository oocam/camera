import RPi.GPIO as GPIO
import datetime
import sys
from logger import logger
# TODO : remove unaccessed imports

class SubSeaLight: 

    def __init__(self):
        GPIO.setwarnings(False)
        # originally 11
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(24, GPIO.OUT)
        try: 
            self.pwm = GPIO.PWM(24,500)     # PIN 12 = Board 32
        except Exception as err: 
            logger.error(f"PWM not found")
    
    def switch_off(self):
        self.pwm.ChangeDutyCycle(0)
        self.pwm.stop()


    def switch_on(self,dc):
        print(dc)
        self.pwm.start(dc)


