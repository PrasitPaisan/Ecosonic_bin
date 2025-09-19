# sensor/ultra_drop_pass.py
"""
HC-SR04 drop-pass detector (µs-accurate, non-blocking) for pigpio.
- Provides a class you can import and call like an IR sensor:
    detector.read() -> 0 (NEAR / detected) or 1 (FAR / not detected)
- Hysteresis + dead-zone release to avoid sticky states.
- No LED calls here; handle LEDs in your app to keep responsibilities clean.
"""

import time
import pigpio

US_PER_CM_ROUND_TRIP = 58.0

class DropPassDetector:
    def __init__(
        self,
        TRIG: int = 26,
        ECHO: int = 25,
        # NOTE: For idle ~16.2 cm, use NEAR below idle, FAR above idle.
        # FAR must be > NEAR (hysteresis gap ~1–2 cm typically).
        NEAR_CM: float = 15.6,       # into NEAR when d < NEAR_CM
        FAR_CM_RELEASE: float = 17.0,# back to FAR when d > FAR_CM_RELEASE
        CYCLE_MS: int = 12,
        DEADZONE_TIMEOUT_MS: int = 120,
        glitch_filter_us: int = 100,
        watchdog_ms: int = 25,
    ):
        if FAR_CM_RELEASE <= NEAR_CM:
            raise ValueError("FAR_CM_RELEASE must be > NEAR_CM for hysteresis")

        self.TRIG = TRIG
        self.ECHO = ECHO
        self.NEAR_CM = NEAR_CM
        self.FAR_CM_RELEASE = FAR_CM_RELEASE
        self.CYCLE_MS = CYCLE_MS
        self.DEADZONE_TIMEOUT_MS = DEADZONE_TIMEOUT_MS

        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("pigpio not running. Start with: sudo systemctl enable --now pigpiod")

        # GPIO setup
        self.pi.set_mode(self.TRIG, pigpio.OUTPUT)
        self.pi.write(self.TRIG, 0)
        self.pi.set_mode(self.ECHO, pigpio.INPUT)
        self.pi.set_pull_up_down(self.ECHO, pigpio.PUD_OFF)
        self.pi.set_glitch_filter(self.ECHO, glitch_filter_us)
        self.pi.set_watchdog(self.ECHO, watchdog_ms)

        # measurement state
        self._latest_cm = float("inf")
        self._rise_tick = None
        self._cb = self.pi.callback(self.ECHO, pigpio.EITHER_EDGE, self._echo_cb)

        # detection state
        self._current_state = 1   # 1=FAR, 0=NEAR
        self._armed = True        # re-arms in FAR
        self._last_near_ms = 0
        self._next_ping_ms = 0

    # ====== pigpio echo callback ======
    def _echo_cb(self, gpio, level, tick):
        if level == 1:  # rising
            self._rise_tick = tick
        elif level == 0 and self._rise_tick is not None:  # falling
            width_us = pigpio.tickDiff(self._rise_tick, tick)
            self._latest_cm = width_us / US_PER_CM_ROUND_TRIP
            self._rise_tick = None
        elif level == 2:  # watchdog (no echo)
            self._latest_cm = float("inf")
            self._rise_tick = None

    # ====== internal ======
    def _trigger(self):
        # 10 µs HIGH pulse
        self.pi.gpio_trigger(self.TRIG, 10, 1)

    def _now_ms(self):
        return int(time.time() * 1000)

    def _step(self):
        """Run one fast step: ping, update hysteresis, manage dead-zone."""
        now_ms = self._now_ms()

        # Fast pinging
        if now_ms >= self._next_ping_ms:
            self._trigger()
            self._next_ping_ms = now_ms + self.CYCLE_MS

        d = self._latest_cm
        near_now = (d < self.NEAR_CM)
        far_now  = (d > self.FAR_CM_RELEASE) or (d == float("inf"))

        if near_now:
            self._current_state = 0
            self._last_near_ms = now_ms
        elif far_now:
            self._current_state = 1

        # Dead-zone release if stuck between thresholds
        if (not near_now) and (not far_now) and self._current_state == 0:
            if now_ms - self._last_near_ms > self.DEADZONE_TIMEOUT_MS:
                self._current_state = 1

        # Re-arm in FAR
        if self._current_state == 1:
            self._armed = True

    # ====== public APIs ======
    def read(self) -> int:
        """
        Drop-in replacement style:
        - Returns 0 when NEAR (detected)
        - Returns 1 when FAR  (not detected)
        Call this frequently inside your main loop (e.g., every iteration).
        """
        self._step()
        return self._current_state  # 0 or 1

    def edge_detected(self) -> bool:
        """
        Returns True exactly once on FAR->NEAR transitions ("Detected !!").
        Read it in your loop if you want a one-shot trigger.
        """
        prev_armed = self._armed
        # _step already re-arms in FAR; we need to see if we just went NEAR while armed
        self._step()
        if self._armed and self._current_state == 0:
            # not triggered yet; after going NEAR, disarm and report True once
            self._armed = False
            return True
        return False if prev_armed or self._current_state == 1 else False

    def distance_cm(self) -> float:
        """Latest measured distance in cm (float('inf') if no echo yet)."""
        return self._latest_cm

    def close(self):
        try:
            if self._cb is not None:
                self._cb.cancel()
                self._cb = None
        finally:
            try:
                self.pi.write(self.TRIG, 0)
            except Exception:
                pass
            self.pi.stop()
