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
            data_string = "".join([chr(b) for b in data]) 
            if gps.has_fix:
                print("Fixed")
            else:
                if time.monotonic() - timestamp > 5:
                    print(data.decode())
                    print("satellites", gps.satellites)
        if time.monotonic() - timestamp > 5: 
            gps.send_command(b"PMTK605") 
            timestamp = time.monotonic() 

if __name__ == "__main__":
    get_gps_data() 
