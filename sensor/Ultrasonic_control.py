import RPi.GPIO as GPIO
import time
from sensor.LED_status import LED_status_color

# Define the pins for the HC-SR04 sensors
TRIG1, ECHO1 = 26, 7
TRIG2, ECHO2 = 16, 25

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG1, GPIO.OUT)
GPIO.setup(ECHO1, GPIO.IN)
GPIO.output(TRIG1, False)
GPIO.setup(TRIG2, GPIO.OUT)
GPIO.setup(ECHO2, GPIO.IN)
GPIO.output(TRIG2, False)
time.sleep(2)

def read_distance(TRIG_PIN, ECHO_PIN):
    # Send a 10us pulse to trigger
    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, False)

    pulse_start = time.time()
    timeout = pulse_start + 0.02
    while GPIO.input(ECHO_PIN) == 0:
        pulse_start = time.time()
        if pulse_start > timeout:
            return -1
    pulse_end = time.time()
    timeout = pulse_end + 0.02
    while GPIO.input(ECHO_PIN) == 1:
        pulse_end = time.time()
        if pulse_end > timeout:
            return -1
    pulse_duration = pulse_end - pulse_start
    distance = (pulse_duration * 34300) / 2
    return distance

def detection_fast(threshold_cm=14.0):
    dist1 = read_distance(TRIG1, ECHO1)
    dist2 = read_distance(TRIG2, ECHO2)
    detected = (dist1 < threshold_cm and dist1 != -1) or (dist2 < threshold_cm and dist2 != -1)
    return (0 if detected else 1), dist1, dist2

# try:
#     while True:
#         status, dist1, dist2 = detection_fast()
#         if dist1 == -1:
#             print("Sensor1 error or out of range")
#         else:
#             print(f"Distance1: {dist1:.2f} cm")
#         if dist2 == -1:
#             print("Sensor2 error or out of range")
#         else:
#             print(f"Distance2: {dist2:.2f} cm")
#         if status == 0:
#             print("Detected !!")
#             LED_status_color("Red")
#         else:
#             LED_status_color("Green")
#         time.sleep(0.1)
# except KeyboardInterrupt:
#     print("Measurement stopped by User")
# finally:
#     GPIO.cleanup()