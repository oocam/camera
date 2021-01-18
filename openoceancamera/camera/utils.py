from logger import logger 

def get_camera_name(): 
    try: 
        with open("/home/pi/openoceancamera/camera_name.txt") as f: 
            name = f.read() 
            return name 
    except Exception as err: 
        logger.error(f"Error: {str(err)}")
        return "OOCAM"