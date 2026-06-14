"""A general-purpose PID controller.

Features that matter for a stable rod controller:
  * derivative on the measurement (not the error) -- avoids a derivative "kick"
    when the setpoint changes stepwise;
  * output clamping to the actuator's range;
  * anti-windup by conditional integration -- the integral term stops
    accumulating while the output is saturated and the error would push it
    further into saturation, so it does not wind up and overshoot on recovery.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PID:
    Kp: float
    Ki: float = 0.0
    Kd: float = 0.0
    setpoint: float = 0.0
    out_min: float = -float("inf")
    out_max: float = float("inf")
    deriv_on_measurement: bool = True

    # internal state
    _integral: float = field(default=0.0, init=False)
    _prev_meas: float | None = field(default=None, init=False)
    _prev_err: float | None = field(default=None, init=False)

    def reset(self) -> None:
        self._integral = 0.0
        self._prev_meas = None
        self._prev_err = None

    def update(self, measurement: float, dt: float) -> float:
        err = self.setpoint - measurement

        # proportional
        P = self.Kp * err

        # tentative integral
        integral_new = self._integral + err * dt
        I = self.Ki * integral_new

        # derivative
        D = 0.0
        if self.Kd != 0.0:
            if self.deriv_on_measurement:
                if self._prev_meas is not None:
                    D = -self.Kd * (measurement - self._prev_meas) / dt
            else:
                if self._prev_err is not None:
                    D = self.Kd * (err - self._prev_err) / dt

        out = P + I + D
        out_clamped = min(max(out, self.out_min), self.out_max)

        # anti-windup: only commit the integral if not saturating further
        saturated = out != out_clamped
        pushing_out = (out > out_clamped and err > 0) or (out < out_clamped and err < 0)
        if not (saturated and pushing_out):
            self._integral = integral_new

        self._prev_meas = measurement
        self._prev_err = err
        return out_clamped

    @property
    def integral(self) -> float:
        return self._integral
