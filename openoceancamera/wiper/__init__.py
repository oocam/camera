from . import wiper
import time

def run_wiper(sweeps):
    wiper_front = wiper.Wiper(10)
    wiper_front.set_angle(0)
    for i in range(sweeps):
        wiper_front.set_angle(50)
        time.sleep(5)
        wiper_front.set_angle(0)


if __name__ == "__main__":
    run_wiper(1)