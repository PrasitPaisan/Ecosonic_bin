# Fast single HC-SR04 drop-pass detector (µs-accurate, non-blocking)
# - d1 only, with proper hysteresis for your ~16.2 cm idle
# - Dead-zone timeout to force release if stuck between thresholds

import time
import pigpio
from sensor.LED_status import LED_status_color

# ========= Pins (BCM) =========
TRIG1, ECHO1 = 26, 25

# ========= Tunables =========
NEAR_CM         = 16.6    # detect NEAR when below this
FAR_CM_RELEASE  = 17.5    # release back to FAR when above this (must be > NEAR_CM)
CYCLE_MS        = 12      # 10–15 ms is typical; lower = faster
PRINT_EVERY_MS  = 150
DEADZONE_TIMEOUT_MS = 120 # if stuck between NEAR and FAR for this long, force FAR

US_PER_CM_ROUND_TRIP = 58.0

pi = pigpio.pi()
if not pi.connected:
    raise RuntimeError("pigpio not running. Start with: sudo systemctl enable --now pigpiod")

# TRIG/ECHO
pi.set_mode(TRIG1, pigpio.OUTPUT); pi.write(TRIG1, 0)
pi.set_mode(ECHO1, pigpio.INPUT)
pi.set_pull_up_down(ECHO1, pigpio.PUD_OFF)
pi.set_glitch_filter(ECHO1, 100)   # ignore <100 µs spikes
pi.set_watchdog(ECHO1, 25)         # quick clear when no echo

latest_cm  = float("inf")
_rise_tick = None

def _echo_cb(gpio, level, tick):
    global _rise_tick, latest_cm
    if level == 1:                          # rising
        _rise_tick = tick
    elif level == 0 and _rise_tick is not None:  # falling
        width_us = pigpio.tickDiff(_rise_tick, tick)
        latest_cm = width_us / US_PER_CM_ROUND_TRIP
        _rise_tick = None
    elif level == 2:                         # watchdog -> no echo
        latest_cm = float("inf")
        _rise_tick = None

cb = pi.callback(ECHO1, pigpio.EITHER_EDGE, _echo_cb)

def _trigger():
    pi.gpio_trigger(TRIG1, 10, 1)

# Detection state
armed = True            # only print "Detected !!" on FAR->NEAR
current_state = 1       # 1=FAR, 0=NEAR
last_led = None
last_print_ms = 0
next_ping_ms = 0
last_near_ms = 0        # for dead-zone release

try:
    LED_status_color("Green")

    while True:
        now_ms = int(time.time() * 1000)

        # Fast pinging
        if now_ms >= next_ping_ms:
            _trigger()
            next_ping_ms = now_ms + CYCLE_MS

        d1 = latest_cm

        # Hysteresis decisions
        near_now = (d1 < NEAR_CM)
        far_now  = (d1 > FAR_CM_RELEASE) or (d1 == float("inf"))

        if near_now:
            current_state = 0
            last_near_ms = now_ms
        elif far_now:
            current_state = 1

        # Dead-zone: force release if stuck between thresholds for too long
        if (not near_now) and (not far_now) and current_state == 0:
            if now_ms - last_near_ms > DEADZONE_TIMEOUT_MS:
                current_state = 1

        # Re-arm when FAR
        if current_state == 1:
            armed = True

        # FAR -> NEAR edge: announce once
        if armed and current_state == 0:
            print("Detected !!")
            armed = False

        # LED
        desired_led = "Red" if current_state == 0 else "Green"
        if desired_led != last_led:
            LED_status_color(desired_led)
            last_led = desired_led

        # Status print
        if now_ms - last_print_ms >= PRINT_EVERY_MS:
            d1s = "err" if d1 == float("inf") else f"{d1:5.1f}"
            print(f"{'NEAR' if current_state==0 else 'FAR '} | d1={d1s} cm")
            last_print_ms = now_ms

        time.sleep(0.001)

except KeyboardInterrupt:
    pass
finally:
    try:
        LED_status_color("Green")
    except Exception:
        pass
    cb.cancel()
    pi.write(TRIG1, 0)
    pi.stop()
