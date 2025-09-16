import RPi.GPIO as GPIO
import time

LED_PIN = 27

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

def LED_status_color(color):
    if color == "Green":
        GPIO.output(LED_PIN, GPIO.HIGH)
    elif color == "Red":
        GPIO.output(LED_PIN, GPIO.LOW )
    else:
        print("The color have just Red and Green !!")

if __name__ == "__main__":
    while True:
        color_input = str(input("Input color of LED !"))
        LED_status_color(color=color_input)