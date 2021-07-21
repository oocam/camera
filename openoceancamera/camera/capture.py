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
from wiper import run_wiper

# TODO: Add docstring for these functions. 20/07/2021
# It'd probably be quite handy the next time an intern or new dev
# worked on the code.
# ALSO add docstring for this script, and the package 'camera'.

# TODO: Change all these string concatenations to f strings. 20/07/2021
def annotate_text_string(sensor_data):
    """Generates a string of all data to be written to logs and photo

    Args:
        sensor_data (str): Raw sensor data from the Sensors.get_sensor_data().

    Returns:
        str: A string of data which will be annotated to the photo.
    """
    result = ""
    if not sensor_data["camera_name"] == "":
        result += f"Camera: {sensor_data['camera_name']} "
    if not sensor_data["pressure"] == -1:
        result += "Pressure: " + str(sensor_data["pressure"]) + " "
    if not sensor_data["temperature"] == -1:
        result += "Temperature: " + str(sensor_data["temperature"]) + " "
    if not sensor_data["depth"] == -1:
        result += "Depth: " + str(sensor_data["depth"]) + " "
    if not sensor_data["luminosity"] == -1:
        result += "Luminosity: " + str(sensor_data["luminosity"]) + " "
    if not sensor_data["gps"]["lat"] == -1 and not sensor_data["gps"]["lng"] == -1:
        result += "Lat: " + str(sensor_data["gps"]["lat"]) + "Lng: " + str(sensor_data["gps"]["lng"]) + " "
    if not sensor_data["conductivity"] == -1:
        result += "Conductivity: " + str(sensor_data["conductivity"]) + "micro S/cm "
    if not sensor_data["total_dissolved_solids"] == -1:
        result += "TDS: " + str(sensor_data["total_dissolved_solids"]) + " "
    if not sensor_data["salinity"] == -1:
        result += "Salinity: " + str(sensor_data["salinity"]) + " "
    if not sensor_data["specific_gravity"] == -1:
        result += "SG: " + str(sensor_data["specific_gravity"]) + " "
    if not sensor_data["dissolved_oxygen"] == -1:
        result += "DO: " + str(sensor_data["dissolved_oxygen"]) + "mg/L "
    if not sensor_data["percentage_oxygen"] == -1:
        result += "PO: " + str(sensor_data["percentage_oxygen"]) + "% "
    if not sensor_data["pH"] == -1:
        result += "pH: " + str(sensor_data["pH"]) + " "
    return result


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
    wiper_status = slot["wiper"]
    if wiper_status:
        run_wiper(3)
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
            # TODO: Look at sensor_data var
            sensors = Sensor()
            sensors.write_sensor_data() 
            sensor_data = sensors.get_sensor_data(short=True)
            while current_time < slot["stop"]: 
                camera.annotate_text = f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} @ {slot['framerate']} fps"
                sensors.write_sensor_data() 
                sensor_data = sensors.get_sensor_data(short=True)
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
        camera_name = get_camera_name()
        wiper_status = slot.get("wiper", False)
        if wiper_status:
            run_wiper(3)
        logger.debug(f"Assigning camera config to {camera_name}")
        try: 
            with PiCamera(resolution=resolution) as camera:
                camera.iso = iso 
                camera.exposure_mode = exposure_mode 
                camera.exposure_compensation = exposure_compensation 
                camera.shutter_speed = shutter_speed
                camera.annotate_text_size = 10
                PWM.switch_on(light)
                logger.debug("Entering continuous capture")

                sensors = Sensor()
                sensor_data = sensors.get_sensor_data()
                sensor_data["camera_name"] = camera_name
                camera.annotate_text =  annotate_text_string(sensor_data)
                for f in camera.capture_continuous(f'{EXTERNAL_DRIVE}/{camera_name}_'+'img{timestamp:%Y-%m-%d-%H-%M-%S}.jpg', use_video_port=True):
                    PWM.switch_off()
                    currenttime = datetime.now()
                    if currenttime < slot["stop"]:
                        sleep(frequency-1)
                        sensors.write_sensor_data()
                        sensor_data = sensors.get_sensor_data()
                        sensor_data["camera_name"] = camera_name
                        camera.annotate_text = annotate_text_string(sensor_data)
                        PWM.switch_on(light)
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