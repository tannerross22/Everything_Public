"""Plant / coolant operating conditions.

In Phase 2 the coolant is represented only as a convective boundary condition
on the pin surface (a fixed film coefficient h and bulk temperature T_inf).
Phase 3 replaces the fixed h/T_inf with values computed from a flow correlation
and an axial coolant energy balance.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CoolantBC:
    """Convective boundary condition on the clad outer surface."""
    h: float = 34000.0    # film heat-transfer coefficient (W/m^2/K)
    T_inf: float = 580.0  # bulk coolant temperature (K), ~307 C

    # Representative gap conductance (W/m^2/K). A beginning-of-life helium gap
    # is typically a few thousand; this rises substantially as the gap closes
    # with burnup. Lives here for now as a plant-level thermal parameter.
    h_gap: float = 5500.0


def pwr_nominal() -> CoolantBC:
    return CoolantBC()
