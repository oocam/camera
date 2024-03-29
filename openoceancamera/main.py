import os
import threading
from logger import logger
from camera import camera_thread
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

    # Start code
    api_thread = threading.Thread(target=start_api_server)
    main_thread = threading.Thread(target=camera_thread)
    api_thread.start()
    main_thread.start()
    logger.info("Started all threads")
    main_thread.join()
    api_thread.join()
    logger.info("Program is shutting down")
