import RPi.GPIO as GPIO

IR_PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(IR_PIN, GPIO.IN)

def read_ir_sensor():
    if GPIO.input(IR_PIN) == GPIO.LOW:
        return 0
    else:
        return 1