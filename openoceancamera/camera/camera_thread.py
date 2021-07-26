from Scheduler import Scheduler
from subsealight import PWM
import json 
from .capture import start_capture
from .upload import start_upload
from datetime import datetime, timedelta
import os
from logger import logger
from time import sleep

def camera_thread():
    # load the schedule from the schedule json
    camera_schedule = Scheduler()
    PWM.switch_off()

    try:
        with open("/home/pi/openoceancamera/schedule.json") as f:
                data = json.load(f)    
                camera_schedule.load_scheduler_data(data)
    except:
        return

    logger.debug("In Camera thread")
    while True:
        # check if a schedule slot needs to run
        slot_index = camera_schedule.should_start()
        # if it needs to run, call the correct function to start the slot (photo/video)
        if (slot_index >= 0):
            slot = camera_schedule.get_slot(slot_index)
            if(slot["upload"]):
                try:
                    start_upload(slot)
                except Exception as err:
                    logger.error(err)
            else:
                start_capture(slot)
        # else check when the next schedule is
        next_slot = camera_schedule.next_future_timeslot()
        slot_index = camera_schedule.should_start()
        if slot_index == -1 and next_slot is not None:
            # if the camera needs to shutdown, do wittypi stuff to shutdown the camera and set restart time and stop this loop
            mins_to_next_slot = int(camera_schedule.time_to_slot(next_slot) / 60)
            if mins_to_next_slot > 10:
                shutdown_time = datetime.now() + timedelta(minutes=2)
                shutdown_time = shutdown_time.strftime("%d %H:%M")
                reboot_time = next_slot["start"] - timedelta(minutes=2)
                reboot_time = reboot_time.strftime("%d %H:%M:%S")
                reboot_cmd = (
                    'sudo sh /home/pi/openoceancamera/wittypi/wittycam.sh 5 "' + reboot_time + '"'
                )

                os.system(reboot_cmd)
                logger.info(f"The reboot time has been set to {reboot_time}")
                shutdown_cmd = (
                    'sudo sh /home/pi/openoceancamera/wittypi/wittycam.sh 4 "' + shutdown_time + '"'
                )
                os.system(shutdown_cmd)
                logger.info(f"The camera will shut down at {shutdown_time}")
                break
        sleep(1)