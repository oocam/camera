import time 
import board 
import busio  
import adafruit_gps 

i2c = board.I2C() 

gps = adafruit_gps.GPS_GtopI2C(i2c) 

gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
gps.send_command(b"PMTK220,1000") 

def get_gps_data(): 
    timestamp = time.monotonic() 
    while True: 
        try:
            data = gps.read(32) 
        except:
            continue
        if data is not None: 
            if gps.has_fix:
                print(gps.latitude, gps.longitude, gps.fix_quality)
            else:
                pass
        if time.monotonic() - timestamp > 5: 
            gps.send_command(b"PMTK605") 
            timestamp = time.monotonic() 
        gps.update()

if __name__ == "__main__":
    get_gps_data() 
