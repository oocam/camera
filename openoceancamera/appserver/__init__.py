import os 
from os import path 
from flask import Flask, request, send_file, jsonify, Response
from flask_cors import CORS
from flask_socketio import SocketIO, send, emit
from picamera import PiCamera
import threading
from time import sleep 
import json
import base64
from datetime import datetime
from uuid import uuid1

from .StreamingOutput import StreamingOutput
from constants import EXTERNAL_DRIVE
from sensors import Sensor
from subsealight import PWM
from logger import logger
from restart import restart_code
from camera.utils import get_camera_name
from uploader import DropboxUploader

app = Flask("OpenOceanCam")
app.config["CORS_HEADERS"] = "Content-Type"

socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=5, ping_interval=5)

@app.route("/setCameraName", methods=["POST"])
def set_camera_name():
    if request.method == 'POST':
        camera_name = request.get_json()["name"]
        with open("/home/pi/openoceancamera/camera_name.txt", "w") as camera_name_file:
            camera_name_file.write(camera_name)
    return camera_name

@app.route("/syncTime", methods=["GET", "POST"])
def sync_time():
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
def set_schedule():
    if request.method == "POST":
        print(request.get_json())
        camera_config = request.get_json()
        with open("/home/pi/openoceancamera/schedule.json", "w") as outfile:
            json.dump(camera_config, outfile)
        date_input = camera_config[0]["date"]
        timezone = camera_config[0]["timezone"]
        clear_cmd = ('sudo sh /home/pi/openoceancamera/wittypi/wittycam.sh 10 6') # convert to python function calls for wittyPi 
        os.system(clear_cmd)
        os.system(f"sudo timedatectl set-timezone {timezone}")
        print(timezone)
        print(date_input)
        # Sets the system time to the user's phone time
        os.system(f"sudo date -s '{date_input}'")
        # Save the system time to RTC -
        os.system("sudo sh /home/pi/openoceancamera/wittypi/wittycam.sh 1")
        os.system("sudo sh /home/pi/openoceancamera/wittypi/wittycam.sh 2")
        pathv = path.exists(EXTERNAL_DRIVE)
        threading.Thread(target=restart_code).start()
        if pathv:
            return "OK", 200
        else:
            logger.error("Error: USB storage device not mounted")
            return "Error: USB storage device not mounted", 400

@app.route("/viewConfig", methods=["GET"])
def returnConfig():
    if request.method == "GET":
        try:
            with open("/home/pi/openoceancamera/schedule.json", "r") as camera_config_file:
                camera_config = json.loads(camera_config_file.read())
                response = {
                    "local_time": datetime.now().strftime("%d-%B-%Y %H:%M:%S"),
                    "local_timezone": str(datetime.utcnow().astimezone().tzinfo) ,
                    "config": json.dumps(camera_config),
                    "camera_name": get_camera_name(),
                    "camera_id": os.environ.get('CAMERA_UID')
                }
                return response, 200
        except Exception as err:
            return str(err), 400

@app.route("/getLogs", methods=["GET"])
def getLogs():
    if request.method == "GET":
        try:
            with open("/home/pi/system_logs.txt", 'r') as f:
                data = f.read()
                return data
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
    if request.method == "POST":
        try:
            data = request.get_json(force=True)
            sensor = Sensor()
            print(data)
            PWM.switch_on(data[0]["light"])
            iso = data[0].get("iso", "auto")
            shutter_speed = data[0].get("shutter_speed", "auto")
            exposure_mode = data[0].get("exposure_mode", "auto")
            exposure_compensation = data[0].get("exposure_compensation", 0)
            slot_resolution = data[0].get("resolution", {"x": "1920", "y": "1080"})
            resolution = (int(slot_resolution["x"]), int(slot_resolution["y"]))
            with PiCamera(resolution=resolution) as camera: 
                camera.iso = iso 
                camera.shutter_speed = shutter_speed 
                camera.exposure_mode = exposure_mode 
                camera.exposure_compensation = exposure_compensation 
                camera.capture("/home/pi/openoceancamera/test.jpg")
                with open("/home/pi/openoceancamera/test.jpg", "rb") as image:
                    img_base64 = base64.b64encode(image.read())
                sensor.read_sensor_data() 
                sensor_data = sensor.get_sensor_data() 
                response = {
                    "image": img_base64.decode("utf-8"),
                    "sensors": json.dumps(sensor_data),
                }
                PWM.switch_off()
                return jsonify(response), 200
        except Exception as err:
            logger.error(err)
            PWM.switch_off()
            return str(err), 400

@app.route("/testPhotoMem", methods=["POST", "GET"])
def sendTestPicMem():
    if request.method == "POST":
        data = request.get_json(force=True)
        PWM.switch_on(data[0]["light"])
        flag = "SUCCESS"
        pathv = path.exists(EXTERNAL_DRIVE)
        sensor = Sensor() 
        if pathv:
            try:
                iso = data[0].get("iso", "auto") 
                shutter_speed = data[0].get("shutter_speed", "auto")
                resolution = (1920,1080) 
                framerate = 30 
                try: 
                    with PiCamera() as camera: 
                        camera.iso = iso 
                        camera.shutter_speed = shutter_speed 
                        filename1 = EXTERNAL_DRIVE + "/" + str(uuid1()) + ".jpg"
                        camera.capture(filename1)
                        print("Written")
                except Exception as err: 
                    return str(err) , 400

                try:     
                    with PiCamera(resolution=resolution, framerate=framerate) as camera: 
                        filename2 = EXTERNAL_DRIVE + "/" + str(uuid1()) + ".h264"
                        camera.start_recording(filename2)
                        print("Started recording")
                        sleep(3)
                        camera.stop_recording() 
                except Exception as err: 
                    return str(err), 400
            except Exception as err:
                return str(err), 400
        else:
            return "USB storage device with name OOCAM required", 400
        PWM.switch_off()
        sensor.read_sensor_data() 
        sensor_data = sensor.get_sensor_data() 
        response = {
            "sensors": json.dumps(sensor_data),
        }
        return jsonify(response), 200

@app.route("/update", methods=["GET","POST"])
def update_code(): 
    if request.method == "POST": 
        try: 
            data = request.get_json() 
            ssid = data["ssid"]
            psk = data["psk"]
            os.system(f"sudo sh /home/pi/connect_to_wifi.sh {ssid} {psk}")
            os.system("sudo sh /home/pi/update.sh")
            return "OK" , 200
        except Exception as err: 
            logger.error(f"Error: {err}")
            return str(err) , 400 


@app.route("/version", methods=["GET"])
def get_version():
    try:
        with open("/home/pi/version.txt") as vfile:
            version_string = vfile.read()
        return version_string , 200
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

@socketio.on("dropbox_auth_start")
def start_dropbox_auth():
    dbx = DropboxUploader()
    url = dbx.start_auth_flow()
    logger.info(url)
    emit("dropbox_auth_url", url)

@socketio.on("dropbox_auth_finish")
def finish_dropbox_auth(data):
    dbx = DropboxUploader()
    dbx.complete_auth_flow(data)
    try:
        user_details = dbx.get_user_details()
        emit("dropbox_auth_complete", user_details.email)
    except:
        pass

@socketio.on("dropbox_auth_get_user")
def get_auth_user():
    try:
        dbx = DropboxUploader()
        user_details = dbx.get_user_details()
        if user_details:
            emit("dropbox_auth_complete", user_details.email)
        else:
            emit("dropbox_auth_complete", None)
    except:
        emit("dropbox_auth_complete", None)

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