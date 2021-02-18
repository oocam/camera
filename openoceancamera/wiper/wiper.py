import RPi.GPIO as GPIO

class Wiper:
    def __init__(self, pin):
        GPIO.setup(pin, GPIO.OUT)
        self.pwm = GPIO.PWM(pin, 490)

    def set_angle(self, angle):
        GPIO.start(angle)

if __name__ == '__main__':
    wiper = Wiper()
    wiper.set_angle(11)