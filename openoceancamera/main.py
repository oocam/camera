import os
import io
import sys
import subprocess
import smbus
import threading
import base64
import logging
import json
from uuid import uuid1
from time import sleep, time, gmtime, strftime
from os import path
from datetime import datetime, timedelta
from flask import Flask, request, send_file, jsonify, Response
from flask_cors import CORS
from flask_socketio import SocketIO, send, emit
from picamera import PiCamera

from StreamingOutput import StreamingOutput
from Scheduler import Scheduler
from camera_pi import Camera_Pi
from subsealight import PWM

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)


camera_name = "OpenOceanCamera"
camera = None
logging.basicConfig(filename="system_logs.txt", format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)

try:
    with open("/home/pi/openoceancamera/camera_name.txt", "r") as camera_name_file:
        camera_name = camera_name_file.read()
except Exception as err:
    with open("/home/pi/openoceancamera/camera_name.txt", "w") as camera_name_file:
        camera_name_file.write(camera_name)

logger.info(f"Loaded camera name: {camera_name}")

sys.path.append("/usr/lib/python3.5/")
sys.path.append("/usr/lib/python3/")
cmdoff = "sudo ifconfig wlan0 down"
cmdoff1 = "sudo service dnsmasq stop"

try:
    from Camera import Camera
except:
    logger.error("Could not initialise camera")

threads = []

app = Flask("OpenOceanCam")
app.config["CORS_HEADERS"] = "Content-Type"
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=5, ping_interval=5)

external_drive = "/media/pi/OPENOCEANCA"
camera_config = []
thread_active = False

last_file_name = ""
stream_duration = 0
lightSensor = -1.0
temperatureSensor = -1.0
pressureSensor = -1.0
mstemperatureSensor = -1.0
depthSensor = -1.0

def readSensorData():
    return {
        "luminosity": lightSensor,
        "temp": temperatureSensor,
        "pressure": pressureSensor,
        "mstemp": mstemperatureSensor,
        "depth": depthSensor,
    }

def writeSensorData(sensor_data):
    log_filename = f"{external_drive}/log.txt"
    file_mode = None
    if os.path.exists(log_filename):
        file_mode = "a"
    else:
        file_mode = "w"
    try:
        with open(log_filename, file_mode) as f:
            f.write(
                json.dumps(
                    {
                        "timestamp": datetime.now().strftime(
                            "%m/%d/%Y, %H:%M:%S"
                        ),
                        "luminosity": sensor_data["luminosity"],
                        "temp": sensor_data["temp"],
                        "pressure": sensor_data["pressure"],
                        "mstemp": sensor_data["mstemp"],
                       "depth": sensor_data["depth"],
                  }
               )
            )
            f.write("\n")
    except:
        logging.warn("Sensor data file did not exist. Making it now")
        with open(log_filename, "w"):
            pass

def start_capture(video, slot):
    global external_drive, last_file_name
    global camera
    filename = ""
    print("start capture")
    logger.info("Starting to capture")
    try:
        camera = Camera()
        logger.info("Camera object initialised")
        camera.set_iso(slot.get("iso", 0))
        camera.set_camera_resolution((int(slot["resolution"]["x"]), int(slot["resolution"]["y"])))
        camera.set_camera_exposure_mode(slot.get("exposure_mode", "auto"))
        camera.set_camera_exposure_compensation(int(slot.get("exposure_compensation", 0)))
        camera.set_shutter_speed(slot.get("shutter_speed", 0))
        logger.info(f"Finised setting up the camera for the slot {slot}")
        try:
            if not video:
                camera.set_capture_frequency(slot["frequency"])
                filename = external_drive + "/" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S")  + ".jpg"
                last_file_name = filename
                print("Capturing:")
                #Don't do capture inside camera class
                
                PWM.switch_on(slot["light"])
                try:
                    logger.info("Going to capture continuous capture mode")
                    sensor_data = readSensorData()
                    writeSensorData(sensor_data)
                    sensor_data["camera_name"] = camera_name
                    camera.camera.exif_tags["IFD0.ImageDescription"] = json.dumps(sensor_data)
                    for f in camera.camera.capture_continuous(f"/media/pi/OPENOCEANCA/{camera_name}_" + 'img{timestamp:%Y-%m-%d-%H-%M-%S}.jpg', use_video_port=True): 
                        if thread_active:
                            PWM.switch_off()
                            sleep(camera.frequency-1)
                            PWM.switch_on(slot["light"])
                            currenttime=datetime.now()
                            if currenttime<datetime.strptime(slot["stop"],"%Y-%m-%d-%H:%M:%S"):
                                sensor_data = readSensorData()
                                writeSensorData(sensor_data)
                                sensor_data["camera_name"] = camera_name
                                camera.camera.exif_tags["IFD0.ImageDescription"] = json.dumps(sensor_data)
                            else:
                                PWM.switch_off()
                                logger.info("Current timeslot ended")
                                break
                        else:
                            PWM.switch_off()
                            logger.info("The main thread was closed")
                            break
                except Exception as err:
                    PWM.switch_off()
                    print(err)
                    logger.error(err)
                    reboot_camera()

                #camera.do_capture(filename=filename, continuous=True, slot=slot)
                #move camera continuous call here so that can be controlled by while loop? camera continuous seems to be like video capture- once on stays on?
                logger.info("Finished capturing for the slot")
                camera.do_close()
                logger.info("Closed the camera object")
            else:
                camera.set_camera_frame_rate(slot["framerate"])
                filename = external_drive + "/" + camera_name + "_" + slot["start"].replace(":","-") + "_" + slot["stop"].replace(":","-") + str(slot["framerate"]) + ".h264"
                camera.do_record(filename=filename)
                print("Started Recording")
                logger.debug("Going to capture in video mode")
                currenttime=datetime.now()
                PWM.switch_on(slot["light"])
                while currenttime<datetime.strptime(slot["stop"],"%Y-%m-%d-%H:%M:%S"):
                    if thread_active:
                        camera.camera.annotate_text = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} @ {slot['framerate']} fps"
                        sensor_data = readSensorData()
                        writeSensorData(sensor_data)
                        sleep(1)
                        currenttime=datetime.now()
                    else:
                        PWM.switch_off()
                        break
                PWM.switch_off()
                camera.do_close()
            logger.debug("Returing back to the main function")
            return filename
        except Exception as err:
            PWM.switch_off()
            camera.do_close()
            logger.error(err)
            reboot_camera()
    except Exception as e:
        print("Camera objection creation error ")
        print(e)
        PWM.switch_off()
        logger.error(e)
        if camera is not None:
            camera.do_close()
        reboot_camera()
    
def main():
    global camera
    if camera is not None:
        camera.do_close()
    print("Main started")
    global thread_active
    PWM.switch_off()
    while True:
        sleep(2)
        try:
            if thread_active:
                data = camera_config
                switch_flag = 0
                my_schedule = Scheduler(data)
                print("Loaded Scheduler. Main thread active")

                # Stall the camera to let it initialise
                while thread_active:
                    my_schedule.update_current_time()
                    slot = my_schedule.should_start()
                    if slot == -1:
                        sleep(2)

                    if slot >= 0:  # if slot open
                        sensor_data = readSensorData()
                        writeSensorData(sensor_data)
                        light_mode = data[slot]["light"]
                        if not data[slot]["video"]:  # slot for photo
                            start_capture(False, data[slot])
                        else:
                            start_capture(True, data[slot])
                        switch_flag = 0

                    else:
                        if switch_flag == 0:
                            logging.info("Stop: " + str(datetime.now()))
                            switch_flag = 1

                    next_slot = my_schedule.next_future_timeslot()
                    slot = my_schedule.should_start()
                    if next_slot is not None:
                        mins_to_next_slot = int(my_schedule.time_to_nearest_schedule() / 60)
                        print(f"We have {mins_to_next_slot} mins to next slot")
                        if (mins_to_next_slot > 10) and slot == -1:
                            logger.info("Camera is going to prepare to go to sleep")
                            five_mins = timedelta(minutes=2)
                            one_mins = timedelta(minutes=2)
                            sleeptime = datetime.now() + one_mins
                            sleeptime = sleeptime.strftime("%d %H:%M")
                            next_reboot = next_slot["start"] - five_mins
                            print(f"I will wake up at {next_reboot}")
                            logger.info(f"The reboot time has been set to {next_reboot}")
                            next_reboot = next_reboot.strftime("%d %H:%M:%S")
                            print(next_reboot)
                            startup_cmd = (
                                'sudo sh /home/pi/openoceancamera/wittypi/wittycam.sh 5 "' + next_reboot + '"'
                            )
                            os.system(startup_cmd)
                            logger.info(startup_cmd)
                            print(
                                "raspberry pi is going to sleep now in 5 min, do not disturb"
                            )
                            shutdown_cmd = (
                                'sudo sh /home/pi/openoceancamera/wittypi/wittycam.sh 4 "' + sleeptime + '"'
                            )
                            os.system(shutdown_cmd)
                            logger.info(shutdown_cmd)
                            thread_active = False
                            break
        except Exception as e:
            if camera is not None:
                camera.do_close()
            print(e)
            PWM.switch_off()
            logger.error(e)
            #threading.Thread(target=restart_code).start()

def update_config():
    pass

def restart_code():
    sleep(5)
    os.system("sudo reboot")

def reboot_camera():
    sleep(300)
    os.system("sudo reboot")

@app.route("/setCameraName", methods=["POST"])
def set_camera_name():
    global camera_name
    if request.method == 'POST':
        camera_name = request.get_json()["name"]
        with open("/home/pi/openoceancamera/camera_name.txt", "w") as camera_name_file:
            camera_name_file.write(camera_name)
    return camera_name

@app.route("/syncTime", methods=["GET", "POST"])
def sync_time():
    global thread_active
    if request.method == "POST":
        try:
            data = request.get_json()
            date_input = data["date"]
            timezone = data["timezone"]
            clear_cmd = ('sudo sh /home/pi/openoceancamera/wittypi/wittycam.sh 10 6')
            os.system(clear_cmd)
            os.system(f"sudo timedatectl set-timezone {timezone}")
            os.system(f"sudo date -s '{date_input}'")
            # Save the system time to RTC -
            os.system("sudo sh /home/pi/openoceancamera/wittypi/wittycam.sh 1")
            os.system("sudo sh /home/pi/openoceancamera/wittypi/wittycam.sh 2")
            threading.Thread(target=restart_code).start()
            return "OK", 200
        except Exception as err:
            return str(err), 400

@app.route("/clearSchedule", methods=["GET"])
def clearSchedule():
    try:
        with open("/home/pi/openoceancamera/schedule.json", "w") as outfile:
            json.dump(json.loads("[]"), outfile)
        clear_cmd = ('sudo sh /home/pi/openoceancamera/wittypi/wittycam.sh 10 6')
        os.system(clear_cmd)
        threading.Thread(target=restart_code).start()
        return "OK", 200
    except Exception as err:
        return str(err), 400

@app.route("/setSchedule", methods=["POST", "GET"])
def app_connect():
    global external_drive
    global camera_config
    global thread_active
    if request.method == "POST":
        thread_active = False
        print(request.get_json())
        camera_config = request.get_json()
        try: 
            with open("/home/pi/openoceancamera/schedule.json", "w") as outfile:
                json.dump(camera_config, outfile)
            date_input = camera_config[0]["date"]
            timezone = camera_config[0]["timezone"]
            try: 
                clear_cmd = ('sudo sh /home/pi/openoceancamera/wittypi/wittycam.sh 10 6')
                os.system(clear_cmd)
                os.system(f"sudo timedatectl set-timezone {timezone}")
                print(timezone)
                print(date_input)
                # Sets the system time to the user's phone time
                os.system(f"sudo date -s '{date_input}'")
                # Save the system time to RTC -
                os.system("sudo sh /home/pi/openoceancamera/wittypi/wittycam.sh 1")
                os.system("sudo sh /home/pi/openoceancamera/wittypi/wittycam.sh 2")
                pathv = path.exists(external_drive)
                threading.Thread(target=restart_code).start()
                if pathv:
                    thread_active = True
                    return "OK", 200
                else:
                    logger.error("Error: USB storage device not mounted")
                    return "Error: USB storage device not mounted", 400
            except Exception as err: 
                logger.error(err)
                return str(err), 400
        except Exception as err: 
            logger.error(err)
            return "Schedule could not be set", 400

@app.route("/viewConfig", methods=["GET"])
def returnConfig():
    if request.method == "GET":
        try:
            response = {
                "local_time": datetime.now().strftime("%d-%B-%Y %H:%M:%S"),
                "local_timezone": str(datetime.utcnow().astimezone().tzinfo) ,
                "config": json.dumps(camera_config),
                "camera_name": camera_name
            }
            return response, 200
        except Exception as err:
            logger.error(err)
            return str(err), 400

@app.route("/getLogs", methods=["GET"])
def getLogs():
    if request.method == "GET":
        try:
            lines = int(request.args.get("lines")) + 1 
            with open("/home/pi/system_logs.txt", 'r') as f:
                data = f.read()
                logs = data.split('\n')
                result = "\n"
                return result.join(logs[-lines:])
        except Exception as err:
            logger.error(err)
            return str(err), 400

@app.route("/clearLogs", methods=["GET"])
def clearLogs():
    if request.method == "GET":
        try:
            open("/home/pi/system_logs.txt", 'w').close()
            return "OK", 200
        except Exception as err:
            return str(err), 400

@app.route("/testPhoto", methods=["POST", "GET"])
def sendTestPic():
    camera = Camera()
    if request.method == "POST":
        try:
            data = request.get_json(force=True)
            print(data)
            PWM.switch_on(data[0]["light"])
            camera.set_iso(data[0]["iso"])
            camera.set_shutter_speed(data[0]["shutter_speed"])
            camera.set_camera_exposure_mode(data[0].get("exposure_mode", 'auto'))
            camera.set_camera_exposure_compensation(int(data[0].get("exposure_compensation", 0)))
            if data[0].get("resolution", None):
                camera.set_camera_resolution((int(data[0]["resolution"].get("x", 1920)), int(data[0]["resolution"].get("y", 1080))))

            camera.do_capture("/home/pi/openoceancamera/test.jpg")
            with open("/home/pi/openoceancamera/test.jpg", "rb") as image:
                img_base64 = base64.b64encode(image.read())
            camera.do_close()
            sensor_data = readSensorData()
            response = {
                "image": img_base64.decode("utf-8"),
                "sensors": json.dumps(sensor_data),
            }
            PWM.switch_off()
            return jsonify(response), 200
        except Exception as err:
            logger.error(err)
            camera.do_close()
            PWM.switch_off()
            return str(err), 400

@app.route("/testPhotoMem", methods=["POST", "GET"])
def sendTestPicMem():
    if request.method == "POST":
        data = request.get_json(force=True)
        PWM.switch_on(data[0]["light"])
        flag = "SUCCESS"
        pathv = path.exists(external_drive)
        if pathv:
            try:
                camera = Camera()
                camera.set_iso(data[0]["iso"])
                camera.set_shutter_speed(data[0]["shutter_speed"])
                filename1 = external_drive + "/" + str(uuid1()) + ".jpg"
                camera.do_capture(filename=filename1)
                print("Written")
                camera.do_close()

                camera = Camera()
                camera.set_camera_resolution((1920, 1080))                
                camera.set_camera_frame_rate(30)
                filename2 = external_drive + "/" + str(uuid1()) + ".h264"
                camera.do_record(filename=filename2)
                print("Started recording")
                sleep(3)
                camera.do_close()
            except Exception as err:
                return str(err), 400
        else:
            return "USB storage device with name OOCAM required", 400
        PWM.switch_off()
        sensor_data = readSensorData()
        response = {
            "sensors": json.dumps(sensor_data),
        }
        return jsonify(response), 200


def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route("/stream", methods=["GET", "POST"])
def get_video():
    global stream_duration
    if request.method == "GET":
        return Response(gen(Camera_Pi(stream_duration)),mimetype='multipart/x-mixed-replace; boundary=frame' )
    if request.method == "POST":
        time_duration = request.get_json()["time_duration"]
        stream_duration = int(time_duration)
        return "OK"

def pull_updated_code(): 
    os.system("bash /home/pi/update.sh >> /home/pi/system_logs.txt 2>&1")

@app.route("/update", methods=["GET","POST"])
def update_code(): 
    if request.method == "POST": 
        try: 
            data = request.get_json() 
            ssid = data["ssid"]
            psk = data["psk"]
            os.system(f"sudo bash /home/pi/connect_to_wifi.sh {ssid} {psk}")
            threading.Thread(target=pull_updated_code).start()
            return "OK" , 200
        except Exception as err: 
            logger.error(f"Error: {err}")
            return str(err) , 400 

livestream_running = False
run_livestream = False

@socketio.on("connect")
def on_connect():
    logger.debug("new device connected")

@socketio.on("disconnect")
def on_disconnect():
    global run_livestream
    logger.debug("device disconnected")
    run_livestream = False

@socketio.on("livestream")
def livestream():
    global livestream_running
    global run_livestream
    run_livestream = True
    if livestream_running:
        return
    try:
        with PiCamera(resolution=(640, 480)) as camera:
            output = StreamingOutput()
            logger.debug("Starting livestream")
            camera.start_recording(output, format='mjpeg')
            run_livestream = True
            while run_livestream:
                socketio.sleep(0)
                if output.frame:
                    emit("livestream_data", output.frame)
    except Exception as err:
        emit("livestream_data", json.dumps({"error": err}))
        logger.error(err)
    livestream_running = False
    logger.debug("Closed livestream")

@socketio.on("close_livestream")
def close_livestream():
    global run_livestream
    run_livestream = False
    logger.debug("Closed livestream")

def start_api_server():
    socketio.run(app, host="0.0.0.0", port=8000)

def start_sensor_reading():
    global lightSensor, temperatureSensor, pressureSensor, mstemperatureSensor, depthSensor
    while True:
        try:
            lightSensor = float(
                str(
                    subprocess.check_output(
                        "python /home/pi/openoceancamera/TSL2561/Python/TSL2561.py", shell=True, text=True
                    )
                )
            )
        except Exception as e:
            lightSensor = -1.0

        try:
            temperatureSensor = float(
                str(
                    subprocess.check_output(
                        "python /home/pi/openoceancamera/tsys01-python/example.py", shell=True, text=True
                    )
                )
            )
        except Exception as e:
            temperatureSensor = -1.0

        try:
            pressureSensorReadings = subprocess.check_output(
                "python /home/pi/openoceancamera/ms5837-python/example.py", shell=True, text=True
            )

            pressureSensorReadings = pressureSensorReadings.split()

            pressureSensor, mstemperatureSensor, depthSensor = (
                float(pressureSensorReadings[0]),
                float(pressureSensorReadings[1]),
                float(pressureSensorReadings[2]),
            )
        except Exception as e:
            pressureSensor = -1.0
            mstemperatureSensor = -1.0
            depthSensor = -1.0


if __name__ == "__main__":
    # if len(sys.argv) < 2:
    #    print("Usage: python main.py <external drive name>")
    #    exit(0)
    try:
        with open("/home/pi/openoceancamera/schedule.json") as f:
            camera_config = json.load(f)
            thread_active = True
            logger.info("schedule opened, should start new thread")
    except IOError as err:
        logger.info(err)
    finally:
        api_thread = threading.Thread(target=start_api_server)
        sensor_thread  = threading.Thread(target=start_sensor_reading)
        main_thread = threading.Thread(target=main)
        api_thread.start()
        main_thread.start()
        sensor_thread.start()
        logger.info("Started all threads")
        sensor_thread.join()
        main_thread.join()
        api_thread.join()
        logger.info("Program is shutting down")
