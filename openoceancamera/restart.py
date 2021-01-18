import os 
from time import sleep 

def restart_code():
    sleep(5)
    os.system("sudo reboot")

def reboot_camera():
    sleep(300)
    os.system("sudo reboot")