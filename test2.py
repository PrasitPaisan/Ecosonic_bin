# Fast dual HC-SR04 drop-pass detector using pigpio (µs-accurate, non-blocking)
import time
import pigpio
from sensor.LED_status import LED_status_color

# ========= Pins (BCM) =========
TRIG1, ECHO1 = 26, 25
TRIG2, ECHO2 = 16, 7

# ========= Tunables =========
NEAR_CM        = 15.0      # detect if either sensor < this
FAR_CM_RELEASE = 14.0      # hysteresis release
PING_GAP_MS    = 18        # time between pings on S1 and S2 (avoid crosstalk)
CYCLE_MS       = 18        # re-ping each sensor roughly every ~18ms
COOLDOWN_MS    = 60        # block re-triggers immediately after a detection
PRINT_EVERY_MS = 100       # print status occasionally (keeps loop light)

# Derived
US_PER_CM_ROUND_TRIP = 58.0  # ~58 µs per cm round-trip
NEAR_SAMPLES_REQ = 1         # single sample is enough for fast-moving object

pi = pigpio.pi()
if not pi.connected:
    raise RuntimeError("pigpio not running. Start with: sudo systemctl start pigpiod")

# Setup
for t in (TRIG1, TRIG2):
    pi.set_mode(t, pigpio.OUTPUT)
    pi.write(t, 0)
for e in (ECHO1, ECHO2):
    pi.set_mode(e, pigpio.INPUT)
    pi.set_pull_up_down(e, pigpio.PUD_OFF)  # better if HW divider -> 3.3V

# State containers (filled by callbacks)
latest_cm = {ECHO1: float("inf"), ECHO2: float("inf")}
_rise_tick = {ECHO1: None, ECHO2: None}

def _echo_cb_factory(echo_pin):
    def _cb(gpio, level, tick):
        # level 1: rising edge -> store start tick
        if level == 1:
            _rise_tick[echo_pin] = tick
        # level 0: falling edge -> compute width
        elif level == 0 and _rise_tick[echo_pin] is not None:
            width_us = pigpio.tickDiff(_rise_tick[echo_pin], tick)
            # Convert µs to cm (round-trip): cm = width_us / 58 (approx)
            latest_cm[echo_pin] = width_us / US_PER_CM_ROUND_TRIP
            _rise_tick[echo_pin] = None
        # level 2: watchdog timeout, treat as no echo
    return _cb

# Register edge callbacks (both edges)
cb1 = pi.callback(ECHO1, pigpio.EITHER_EDGE, _echo_cb_factory(ECHO1))
cb2 = pi.callback(ECHO2, pigpio.EITHER_EDGE, _echo_cb_factory(ECHO2))

def _trigger(trig_pin):
    # Sends a ~10 µs pulse (handled in C; non-blocking)
    pi.gpio_trigger(trig_pin, 10, 1)

# Drop-pass detection state
last_led = None
last_detect_ms = -10_000
last_print_ms = 0
near_streak = 0
current_state = 1  # 1 = FAR (not detected), 0 = NEAR (detected)

# Ping scheduling
next_ping_ms = {TRIG1: 0, TRIG2: 0}
order = [ (TRIG1, ECHO1), (TRIG2, ECHO2) ]  # staggered

try:
    LED_status_color("Green")
    while True:
        now_ms = int(time.time() * 1000)

        # Staggered pinging to avoid crosstalk, keep each sensor ~every CYCLE_MS
        for idx, (tpin, epin) in enumerate(order):
            if now_ms >= next_ping_ms[tpin]:
                _trigger(tpin)
                # Schedule the *other* sensor after a short stagger gap to avoid overlapping echoes
                next_ping_ms[tpin] = now_ms + (CYCLE_MS if idx == 0 else CYCLE_MS)
                # Add stagger so two sensors don't talk at the same time
                next_ping_ms[order[(idx+1) % 2][0]] = now_ms + PING_GAP_MS

        d1 = latest_cm[ECHO1]
        d2 = latest_cm[ECHO2]

        # Fast decision: if either is clearly near right now, count it
        if (d1 < NEAR_CM) or (d2 < NEAR_CM):
            near_streak += 1
        elif (d1 > FAR_CM_RELEASE) and (d2 > FAR_CM_RELEASE):
            near_streak = 0

        # Trigger immediately on first near sample (fast objects)
        detected_now = (near_streak >= NEAR_SAMPLES_REQ)

        # Apply short cooldown so one falling object doesn't spam multiple triggers
        if detected_now and (now_ms - last_detect_ms) > COOLDOWN_MS:
            current_state = 0
            last_detect_ms = now_ms
            print("Detected !!")

        # Release back to FAR when both are clearly far again
        if (d1 > FAR_CM_RELEASE) and (d2 > FAR_CM_RELEASE):
            current_state = 1

        # LED update only on state change
        desired_led = "Red" if current_state == 0 else "Green"
        if desired_led != last_led:
            LED_status_color(desired_led)
            last_led = desired_led

        # Optional light status print (doesn't block)
        if now_ms - last_print_ms >= PRINT_EVERY_MS:
            def fmt(x): return "err" if x == float("inf") else f"{x:5.1f}"
            print(f"{'NEAR' if current_state==0 else 'FAR '} | d1={fmt(d1)} cm  d2={fmt(d2)} cm")
            last_print_ms = now_ms

        # 1ms tick; pigpio handles timing, so tiny sleep is fine
        time.sleep(0.001)

except KeyboardInterrupt:
    pass
finally:
    try:
        LED_status_color("Green")
    except Exception:
        pass
    cb1.cancel(); cb2.cancel()
    for t in (TRIG1, TRIG2): pi.write(t, 0)
    pi.stop()
