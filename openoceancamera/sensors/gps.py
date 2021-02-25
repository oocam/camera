import time 
import threading
import board 
import busio  
import adafruit_gps
from adafruit_gps import GPS_GtopI2C

class GPS(GPS_GtopI2C):
    def __init__(self):
        super().__init__(board.I2C())
        self.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
        self.send_command(b"PMTK220,1000")
        threading.Timer(1, self.update).start()
        threading.Timer(5, self.request_firmware).start()

    def request_firmware(self):
        self.send_command(b"PMTK605")
        threading.Timer(5, self.request_firmware).start()

    def update(self):
        super().update()
        threading.Timer(1, self.update).start()


if __name__ == "__main__":
    gps = GPS()
    while not gps.has_fix:
        continue
    print("GPS fixed")
    while gps.has_fix:
        print(f"{gps.latitude}, {gps.longitude}")