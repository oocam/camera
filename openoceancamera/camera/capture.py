from picamera import PiCamera 
from datetime import datetime
from time import sleep 
import json
from constants import EXTERNAL_DRIVE
# from .sensors import readSensorData, writeSensorData
from sensors import Sensor
from logger import logger
from subsealight import PWM
from restart import reboot_camera
from .utils import get_camera_name

def capture_video(slot):
    resolution = slot["resolution"]
    framerate = slot["framerate"]
    iso = slot["iso"]
    exposure_mode = slot["exposure_mode"]
    exposure_compensation = slot["exposure_compensation"]
    light = slot["light"]
    shutter_speed = slot["shutter_speed"]
    try: 
        sensor = Sensor()
    except Exception as err: 
        logger.error(err)
    camera_name = get_camera_name()
    try: 
        with PiCamera(resolution=resolution, framerate=framerate) as camera:
            camera.iso = iso 
            camera.exposure_mode = exposure_mode 
            camera.exposure_compensation = exposure_compensation
            camera.shutter_speed = shutter_speed
            slot_name = f"{slot['start'].strftime('%Y-%m-%d_%H-%M-%S')}_{slot['stop'].strftime('%Y-%m-%d_%H-%M-%S')}.h264"
            filename = f"{EXTERNAL_DRIVE}/{camera_name}_{slot_name}"
            PWM.switch_on(light)
            camera.start_recording(filename, format="h264")
            current_time = datetime.now() 
            sensor.write_sensor_data() 
            sensor_data = sensor.get_sensor_data()
            while current_time < slot["stop"]: 
                camera.annotate_text = f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} @ {slot['framerate']} fps"
                sensor.write_sensor_data() 
                sensor_data = sensor.get_sensor_data()
                sleep(1)
                current_time = datetime.now() 
            camera.stop_recording() 
            PWM.switch_off()
    except Exception as err: 
        PWM.switch_off() 
        logger.error(err)
        reboot_camera()

def capture_images(slot):
    try:
        logger.debug("Going to set camera config")
        resolution = slot["resolution"]
        iso = slot["iso"]
        exposure_mode = slot["exposure_mode"]
        exposure_compensation = slot["exposure_compensation"]
        light = slot["light"]
        frequency = slot["frequency"]
        shutter_speed = slot["shutter_speed"]
        try: 
            sensor = Sensor()
        except Exception as err: 
            logger.error(err)
        camera_name = get_camera_name()
        logger.debug(f"Assigning camera config to {camera_name}")
        try: 
            with PiCamera(resolution=resolution) as camera:
                camera.iso = iso 
                camera.exposure_mode = exposure_mode 
                camera.exposure_compensation = exposure_compensation 
                camera.shutter_speed = shutter_speed
                PWM.switch_on(light)
                sensor.write_sensor_data() 
                sensor_data = sensor.get_sensor_data()
                sensor_data["camera_name"] = camera_name
                camera.exif_tags["IFDO.ImageDescription"] = json.dumps(sensor_data)
                logger.debug("Entering continuous capture")
                for f in camera.capture_continuous(f'{EXTERNAL_DRIVE}/{camera_name}_'+'img{timestamp:%Y-%m-%d-%H-%M-%S}.jpg', use_video_port=True):
                    PWM.switch_off()
                    currenttime = datetime.now()
                    if currenttime < slot["stop"]:
                        sleep(frequency-1)
                        sensor.write_sensor_data() 
                        sensor_data = sensor.get_sensor_data()
                        sensor_data["camera_name"] = camera_name
                        camera.exif_tags["IFDO.ImageDescription"] = json.dumps(sensor_data)
                    else: 
                        PWM.switch_off() 
                        break
        except Exception as err: 
            PWM.switch_off() 
            logger.error(err)
            reboot_camera()
    except Exception as err: 
        PWM.switch_off()
        logger.error(err)

def start_capture(slot):
    logger.debug("Going to capture")
    if slot["video"]:
        capture_video(slot)
    else:
        capture_images(slot)
