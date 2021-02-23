import subprocess
import time
import sys

SERVO_LOWER_LIMIT=50
SERVO_UPPER_LIMIT=250

class Wiper:
    def __init__(self):
        subprocess.run("gpio -g mode 18 pwm", shell=True)
        subprocess.run("gpio pwm-ms",shell=True)
        subprocess.run("gpio pwmc 192",shell=True)
        subprocess.run("gpio pwmr 2000",shell=True)

    def set_angle(self, angle):
        pwm_output = (SERVO_UPPER_LIMIT * angle + SERVO_LOWER_LIMIT * (360-angle))/360
        subprocess.run(f"gpio -g pwm 18 {pwm_output}", shell=True)

def run_wiper(sweeps):
    wiper_front = Wiper()
    wiper_front.set_angle(0)
    for i in range(sweeps):
        wiper_front.set_angle(70)
        time.sleep(1)
        wiper_front.set_angle(0)
        time.sleep(2)

if __name__ == "__main__":
    run_wiper(10)

