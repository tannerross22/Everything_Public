"""The regulating-bank controller assembly: PID + rod bank + SCRAM.

Wraps the pieces into one object with a `step(dt, meas) -> rho_rods` interface
that the simulator can drive each timestep. The reactivity it returns is
*relative to the initial critical operating point* (matching the simulator's
convention that rho_rods = 0 is critical at the start):

    rho_rods = -(W(p) - W(p0))  +  rho_scram

where p0 is the bank's parked mid-band position. The PID acts on the chosen
controlled variable (e.g. power), outputs a reactivity demand, which is mapped
through the inverse S-curve to a target insertion; the bank then slews toward it
at its rate limit. SCRAM, if tripped, adds its large negative contribution and
freezes the regulating bank.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .pid import PID
from .rod_worth import ControlRodBank, black_bank, integral_worth
from .scram import ScramSystem


@dataclass
class RodController:
    pid: PID
    bank: ControlRodBank = field(default_factory=black_bank)
    scram: ScramSystem = field(default_factory=ScramSystem)
    controlled: str = "power"      # measurement key the PID regulates
    p0: float = 0.5                # parked mid-band insertion (max differential worth)

    _W0: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        self._configure()

    def _configure(self) -> None:
        self._W0 = integral_worth(self.p0, self.bank.total_worth)
        # PID output is a reactivity demand bounded by the bank's authority
        # about the parked position: withdraw fully -> +W0, insert fully -> -(W_tot - W0).
        self.pid.out_max = self._W0
        self.pid.out_min = -(self.bank.total_worth - self._W0)

    def reset(self) -> None:
        self.bank.position = self.p0
        self.scram.reset()
        self.pid.reset()
        self._configure()

    def regulating_reactivity(self) -> float:
        return -(self.bank.worth_magnitude() - self._W0)

    def step(self, dt: float, meas: dict) -> float:
        rho_scram = self.scram.update(dt, meas)
        if not self.scram.tripped:
            demand = self.pid.update(meas[self.controlled], dt)  # desired rho_reg
            W_target = self._W0 - demand
            W_target = min(max(W_target, 0.0), self.bank.total_worth)
            self.bank.move_toward(self.bank.target_for_worth(W_target), dt)
        return self.regulating_reactivity() + rho_scram


def power_controller(setpoint: float = 1.0, Kp: float = 0.05, Ki: float = 0.01,
                     Kd: float = 0.0, bank: ControlRodBank | None = None,
                     scram: ScramSystem | None = None) -> RodController:
    """A PI(D) power controller driving a black regulating bank."""
    pid = PID(Kp=Kp, Ki=Ki, Kd=Kd, setpoint=setpoint)
    return RodController(
        pid=pid,
        bank=bank if bank is not None else black_bank(),
        scram=scram if scram is not None else ScramSystem(),
        controlled="power",
    )
