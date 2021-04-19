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
from sensors import Sensor, start_sensor_readings
from Scheduler import Scheduler
import uuid
from appserver import start_api_server

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

if __name__ == "__main__":
    # Generates a product ID first time
    if not (os.path.exists(".oocamkey") and os.path.isfile(".oocamkey")):
        with open(".oocamkey", "w") as idfile:
            generated_id = str(uuid.uuid4())
            idfile.write(generated_id)
    
    # Load environment variables
    with open(".oocamkey", "r") as idfile:
        os.environ['CAMERA_UID'] = str(idfile.read()).strip()

    sensors = Sensor()
    # Start code
    api_thread = threading.Thread(target=start_api_server)
    main_thread = threading.Thread(target=camera_thread, args=(sensors,))
    sensor_thread = threading.Thread(target=start_sensor_readings, args=(sensors,))
    api_thread.start()
    main_thread.start()
    sensor_thread.start()
    logger.info("Started all threads")
    sensor_thread.join()
    main_thread.join()
    api_thread.join()
    logger.info("Program is shutting down")
