"""Axial offset + power control via two rod banks (Phase 6.5).

Two control inputs (a top bank and a bottom bank) are driven so that:
  * their *mean* insertion controls total power, and
  * their *differential* insertion controls the axial offset.

This modal decoupling is the clean way to do MIMO power/AO control with two
banks: pushing both banks in together lowers power with little shape change,
while pushing one in and pulling the other out tilts the flux with little power
change. Two PIDs (one per mode) then handle the residual cross-coupling.

    p_top    = p0 - u_power - u_ao
    p_bottom = p0 - u_power + u_ao

where u_power = power_pid(power) and u_ao = ao_pid(axial_offset). Rod motion is
rate-limited (real banks have a finite drive speed).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .pid import PID


@dataclass
class AxialController:
    power_pid: PID
    ao_pid: PID
    p0: float = 0.25
    max_speed: float = 0.03          # bank drive speed (fraction/s)

    p_top: float = field(init=False, default=0.5)
    p_bottom: float = field(init=False, default=0.5)

    def reset(self) -> None:
        self.power_pid.reset()
        self.ao_pid.reset()
        self.p_top = self.p0
        self.p_bottom = self.p0

    @staticmethod
    def _rate_limit(current, target, max_step):
        dp = target - current
        dp = min(max(dp, -max_step), max_step)
        return min(max(current + dp, 0.0), 1.0)

    def step(self, dt: float, meas: dict) -> tuple[float, float]:
        u_power = self.power_pid.update(meas["power"], dt)
        u_ao = self.ao_pid.update(meas["axial_offset"], dt)

        target_top = self.p0 - u_power - u_ao
        target_bottom = self.p0 - u_power + u_ao
        target_top = min(max(target_top, 0.0), 1.0)
        target_bottom = min(max(target_bottom, 0.0), 1.0)

        max_step = self.max_speed * dt
        self.p_top = self._rate_limit(self.p_top, target_top, max_step)
        self.p_bottom = self._rate_limit(self.p_bottom, target_bottom, max_step)
        return self.p_top, self.p_bottom


def power_ao_controller(power_setpoint: float = 1.0, ao_setpoint: float = 0.0,
                        Kp_power: float = 0.6, Ki_power: float = 0.05,
                        Kp_ao: float = 1.5, Ki_ao: float = 0.1,
                        p0: float = 0.25) -> AxialController:
    """A power + axial-offset controller with sensible default gains.

    Output limits keep each bank's modal contribution within +/-(p0) so the
    combined insertion stays in [0, 1] for centred operation.
    """
    power_pid = PID(Kp=Kp_power, Ki=Ki_power, setpoint=power_setpoint,
                    out_min=-p0, out_max=p0)
    ao_pid = PID(Kp=Kp_ao, Ki=Ki_ao, setpoint=ao_setpoint,
                 out_min=-p0, out_max=p0)
    return AxialController(power_pid=power_pid, ao_pid=ao_pid, p0=p0)
