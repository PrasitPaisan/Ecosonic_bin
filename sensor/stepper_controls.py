import RPi.GPIO as GPIO
import time

DIR_PIN1 = 6
STEP_PIN1 = 24
DIR_PIN2 = 5
STEP_PIN2 = 23

CURRENT_MO1 = 0
CURRENT_MO2 = 3

# DIR pin level to move in the +position direction (0->1->2->3)
DIR_POS_LEVEL_M1 = 1   # set to 0 or 1 to match your wiring for motor 1
DIR_POS_LEVEL_M2 = 1   # set to 0 or 1 to match your wiring for motor 2


def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(DIR_PIN1, GPIO.OUT)
    GPIO.setup(STEP_PIN1, GPIO.OUT)
    GPIO.setup(DIR_PIN2, GPIO.OUT)
    GPIO.setup(STEP_PIN2, GPIO.OUT)

def motor_rotate(step_pin, dir_pin, direction, step, step_delay):
    GPIO.output(dir_pin, direction)
    for i in range(4):
        for _ in range(int(step)):
            GPIO.output(step_pin, GPIO.HIGH)
            time.sleep(step_delay)
            GPIO.output(step_pin, GPIO.LOW)
            time.sleep(step_delay)

def rotate_to_position(target_position, current_position, step_pin, dir_pin, step_delay=0.00001):
    MOD = 4
    target_position %= MOD
    current_position %= MOD

    raw = (target_position - current_position) % MOD   # 0..3
    delta = raw - MOD if raw > MOD / 2 else raw        # -2..+2 (shortest path)

    step_count_per_90 = 3200 / 4
    step = abs(delta) * step_count_per_90

    # choose mapping for this motor from its DIR pin
    dir_pos_level = DIR_POS_LEVEL_M1 if dir_pin == DIR_PIN1 else DIR_POS_LEVEL_M2
    # If delta > 0 (e.g., 0->1), use dir_pos_level; if delta < 0 (e.g., 0->3), use the opposite
    direction = dir_pos_level if delta > 0 else 1 - dir_pos_level

    print(f"Delta : {delta}  (raw={raw})")
    print(f"Step : {step/step_count_per_90}")
    print(f"Direction : {direction}")

    if delta == 0:
        print("Don't rotate, already at target position")
        return current_position

    motor_rotate(step_pin, dir_pin, direction, step, step_delay)
    return target_position



def motor_control(target_pos):
    global CURRENT_MO1, CURRENT_MO2
    if 0 <= target_pos <= 3:
        if CURRENT_MO2 != 3:
            CURRENT_MO2 = rotate_to_position(3, CURRENT_MO2, STEP_PIN2, DIR_PIN2)
            print("Upper motor to position hole")
        CURRENT_MO1 = rotate_to_position(target_pos, CURRENT_MO1, STEP_PIN1, DIR_PIN1)
    elif 4 <= target_pos <= 6 :
        CURRENT_MO2 = rotate_to_position(target_pos - 4, CURRENT_MO2, STEP_PIN2, DIR_PIN2)
    else:
        print("The number should between 0 and 6")

def reset_motors_position():
    rotate_to_position(0, CURRENT_MO1, STEP_PIN1, DIR_PIN1)
    rotate_to_position(3, CURRENT_MO2, STEP_PIN2, DIR_PIN2)
    print("Motors reset to position 0 (defult position)")

if __name__ == "__main__":
    setup_gpio()
    try:
        while True:
            target_position = int(input("Enter target position (0-6): "))
            motor_control(target_position)

    except KeyboardInterrupt:
        reset_motors_position()
        GPIO.cleanup()
        print("Program is Terminated <3")
