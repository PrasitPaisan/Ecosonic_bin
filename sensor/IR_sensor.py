import RPi.GPIO as GPIO
import time

IR_PIN = 3

GPIO.setmode(GPIO.BCM)
GPIO.setup(IR_PIN, GPIO.IN)

def read_ir_sensor():
    if GPIO.input(IR_PIN) == GPIO.LOW:
        return 0
    else:
        return 1 
    
