import RPi.GPIO as GPIO
import time
import subprocess

FAN_PIN = 32
GPIO.setmode(GPIO.BOARD)
GPIO.setup(FAN_PIN, GPIO.OUT)

pwm = GPIO.PWM(FAN_PIN, 50)
pwm.start(0)

def get_temp():
    output = subprocess.getoutput("vcgencmd measure_temp")
    try:
        return float(output.replace("temp=", "").replace("'C", ""))
    except ValueError:
        return 0.0  # fallback if parsing fails

try:
    while True:
        temp = get_temp()

        if temp < 45.0:
            pwm.ChangeDutyCycle(0)
        else:
            pwm.ChangeDutyCycle(100)

        time.sleep(5)  # reduce CPU usage

except KeyboardInterrupt:
    pass

pwm.stop()
GPIO.cleanup()
