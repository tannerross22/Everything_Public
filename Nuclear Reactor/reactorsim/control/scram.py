"""SCRAM -- the reactor safety supervisor.

This is deliberately *not* part of the PID loop. It is an independent state
machine that monitors power and temperatures against trip setpoints and, once
any limit is exceeded, latches a trip and drives the dedicated shutdown rods
fully in at high speed, inserting a large negative reactivity that overrides the
controller and shuts the reactor down. A latched trip stays tripped until
explicitly reset (as on a real plant).

The shutdown rods use the same S-curve worth as a normal bank but with a large
total worth and a fast drive speed (full insertion in a couple of seconds).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .rod_worth import ControlRodBank


@dataclass
class ScramSystem:
    power_trip: float = 1.5            # normalized power trip (150% power)
    T_fuel_trip: float = 1400.0        # avg fuel temperature trip (K)
    T_coolant_trip: float = 605.0      # coolant temperature trip (K)

    scram_worth: float = 0.10          # full shutdown-rod worth (delta-k/k)
    scram_speed: float = 0.5           # fast drive (full stroke ~2 s)

    tripped: bool = field(default=False, init=False)
    trip_reason: str = field(default="", init=False)
    _rods: ControlRodBank = field(init=False)

    def __post_init__(self) -> None:
        self._rods = ControlRodBank("shutdown", total_worth=self.scram_worth,
                                    position=0.0, max_speed=self.scram_speed)

    def reset(self) -> None:
        self.tripped = False
        self.trip_reason = ""
        self._rods.position = 0.0

    @property
    def position(self) -> float:
        return self._rods.position

    def _check(self, meas: dict) -> None:
        if self.tripped:
            return
        if meas["power"] > self.power_trip:
            self.tripped, self.trip_reason = True, f"power {meas['power']:.3f} > {self.power_trip}"
        elif meas["T_fuel_avg"] > self.T_fuel_trip:
            self.tripped, self.trip_reason = True, f"T_fuel {meas['T_fuel_avg']:.1f}K > {self.T_fuel_trip}K"
        elif meas["T_coolant"] > self.T_coolant_trip:
            self.tripped, self.trip_reason = True, f"T_cool {meas['T_coolant']:.1f}K > {self.T_coolant_trip}K"

    def update(self, dt: float, meas: dict) -> float:
        """Check trips and, if tripped, drive the shutdown rods in. Returns the
        (negative) reactivity contributed by the shutdown rods."""
        self._check(meas)
        if self.tripped:
            self._rods.move_toward(1.0, dt)
        return self._rods.reactivity()
