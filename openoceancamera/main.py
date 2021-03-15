import os
import io
import sys
import threading
import base64
import json
from time import sleep, time, gmtime, strftime
from datetime import datetime, timedelta
from picamera import PiCamera
from logger import logger
from camera import camera_thread
from sensors import Sensor
from Scheduler import Scheduler

from appserver import start_api_server

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

if __name__ == "__main__":
    api_thread = threading.Thread(target=start_api_server)
    main_thread = threading.Thread(target=camera_thread)
    api_thread.start()
    main_thread.start()
    logger.info("Started all threads")
    main_thread.join()
    api_thread.join()
    logger.info("Program is shutting down")
