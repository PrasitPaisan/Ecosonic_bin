import RPi.GPIO as GPIO
import time

# กำหนด GPIO ของ Ultrasonic ตัวที่ 1
TRIG1 = 23
ECHO1 = 24

# กำหนด GPIO ของ Ultrasonic ตัวที่ 2
TRIG2 = 17
ECHO2 = 27

GPIO.setmode(GPIO.BCM)

for trig, echo in [(TRIG1, ECHO1), (TRIG2, ECHO2)]:
    GPIO.setup(trig, GPIO.OUT)
    GPIO.setup(echo, GPIO.IN)
    GPIO.output(trig, False)


def read_ultrasonic(trig, echo):
    #sent pulse 10µs
    GPIO.output(trig, True)
    time.sleep(0.00001)
    GPIO.output(trig, False)

    # wait echo = HIGH
    while GPIO.input(echo) == 0:
        pulse_start = time.time()

    # wait echo = LOW
    while GPIO.input(echo) == 1:
        pulse_end = time.time()

    # calulate distance
    pulse_duration = pulse_end - pulse_start
    distance = (pulse_duration * 34300) / 2  # cm
    return distance

def detection_with_ultrasonic(threshold=10):
    dist1 = read_ultrasonic(TRIG1, ECHO1)
    dist2 = read_ultrasonic(TRIG2, ECHO2)
    if dist1 < threshold or dist2 < threshold:
        return 0  # Detected
    else:
        return 1  # Non-detected
