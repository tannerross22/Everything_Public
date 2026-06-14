"""Steam generator (secondary side) and the plant heat balance (Phase 7).

The steam generator (SG) is an evaporator: hot single-phase primary coolant
gives up heat to secondary water that boils at constant saturation temperature
T_sat (set by the chosen secondary pressure). Because the boiling side absorbs
heat at constant temperature, its effective heat-capacity rate is infinite, so
C_r = C_min/C_max = 0 and the effectiveness-NTU relation reduces to

    NTU = UA / C_min,   C_min = mdot_primary * cp_primary,
    eff = 1 - exp(-NTU),
    Q   = eff * C_min * (T_hot_in - T_sat).

The equivalent LMTD form (cross-checked in the tests) is

    Q = UA * (dT1 - dT2) / ln(dT1/dT2),  dT1 = T_hot_in - T_sat, dT2 = T_hot_out - T_sat.

Closing the loop: at steady state the SG removes exactly the core power, which
fixes the primary hot- and cold-leg temperatures (the cold leg is the core inlet)
and the secondary steam production rate. A simple Rankine estimate then gives the
plant thermal efficiency and the turbine exit moisture -- the quantities that
make the secondary-pressure choice a real design trade.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import steam_tables as st


@dataclass
class SteamGenerator:
    mdot_primary: float        # kg/s
    cp_primary: float          # J/kg/K
    secondary_pressure: float  # Pa
    UA: float                  # W/K
    T_hot_in: float            # primary inlet (hot leg) temperature, K
    feedwater_T: float = 500.0 # subcooled feedwater temperature, K (~227 C)

    @property
    def C_min(self) -> float:
        return self.mdot_primary * self.cp_primary

    @property
    def T_sat(self) -> float:
        return st.T_sat(self.secondary_pressure)

    @property
    def NTU(self) -> float:
        return self.UA / self.C_min

    @property
    def effectiveness(self) -> float:
        return 1.0 - math.exp(-self.NTU)

    def duty(self) -> float:
        """Heat transferred from primary to secondary (W)."""
        return self.effectiveness * self.C_min * (self.T_hot_in - self.T_sat)

    def T_hot_out(self) -> float:
        """Primary outlet (cold-leg) temperature (K)."""
        return self.T_hot_in - self.duty() / self.C_min

    def lmtd(self) -> float:
        dT1 = self.T_hot_in - self.T_sat
        dT2 = self.T_hot_out() - self.T_sat
        return (dT1 - dT2) / math.log(dT1 / dT2)

    def duty_lmtd(self) -> float:
        """Duty via the LMTD method (should equal duty())."""
        return self.UA * self.lmtd()

    def steam_rate(self) -> float:
        """Saturated steam produced (kg/s) = Q / (h_g - h_feedwater)."""
        sp = st.sat_props(self.secondary_pressure)
        h_fw = st.hf_at_T(self.feedwater_T)
        return self.duty() / (sp.h_g - h_fw)


# --------------------------------------------------------------------------- #
# sizing and design helpers
# --------------------------------------------------------------------------- #
def required_UA(duty: float, C_min: float, T_hot_in: float, T_sat: float) -> float:
    """UA needed to transfer `duty` at the given temperatures (evaporator)."""
    eff = duty / (C_min * (T_hot_in - T_sat))
    if not 0.0 < eff < 1.0:
        raise ValueError(f"infeasible: required effectiveness {eff:.3f} not in (0,1)")
    return -math.log(1.0 - eff) * C_min


def secondary_pressure_for_approach(T_primary_avg: float, approach: float) -> float:
    """Pick the secondary pressure from a target SG approach temperature:
    T_sat = T_primary_avg - approach, then P = P_sat(T_sat). Returns Pa."""
    return st.P_sat(T_primary_avg - approach)


@dataclass
class PrimaryLoop:
    """Steady primary loop closed by the SG: given core power and the SG, find
    the hot/cold-leg temperatures (cold leg = core inlet)."""
    core_power: float          # W
    mdot_primary: float        # kg/s
    cp_primary: float          # J/kg/K
    UA: float                  # W/K
    secondary_pressure: float  # Pa

    @property
    def C_min(self) -> float:
        return self.mdot_primary * self.cp_primary

    def solve(self) -> dict:
        T_sat = st.T_sat(self.secondary_pressure)
        eff = 1.0 - math.exp(-self.UA / self.C_min)
        # SG duty must equal core power at steady state
        T_hot = T_sat + self.core_power / (eff * self.C_min)
        T_cold = T_hot - self.core_power / self.C_min
        return {
            "T_hot": T_hot, "T_cold": T_cold, "T_avg": 0.5 * (T_hot + T_cold),
            "T_sat": T_sat, "effectiveness": eff,
            "approach": T_hot - T_sat,
        }


# --------------------------------------------------------------------------- #
# Rankine cycle estimate (the secondary-pressure trade)
# --------------------------------------------------------------------------- #
@dataclass
class RankineResult:
    efficiency: float
    turbine_exit_quality: float
    turbine_work: float        # J/kg
    heat_added: float          # J/kg


def rankine_cycle(P_boiler: float, P_cond: float,
                  turbine_eff: float = 0.85, pump_eff: float = 0.80) -> RankineResult:
    """Saturated Rankine cycle: dry saturated steam at the boiler pressure
    expands to the condenser pressure. Returns thermal efficiency and the
    turbine exit steam quality (a moisture / blade-erosion indicator)."""
    boiler = st.sat_props(P_boiler)
    cond = st.sat_props(P_cond)

    # 1: saturated steam at the boiler
    h1, s1 = boiler.h_g, boiler.s_g
    # 2: isentropic expansion to condenser pressure (wet)
    x2s = (s1 - cond.s_f) / cond.s_fg
    h2s = cond.h_f + x2s * cond.h_fg
    w_turb_ideal = h1 - h2s
    w_turb = turbine_eff * w_turb_ideal
    h2 = h1 - w_turb
    x2 = (h2 - cond.h_f) / cond.h_fg     # actual exit quality

    # pump (incompressible): v_f ~ 1.0e-3 m^3/kg
    v_f = 1.0e-3
    w_pump = v_f * (P_boiler - P_cond) / pump_eff
    h3 = cond.h_f + w_pump               # feedwater after pump

    q_in = h1 - h3
    eta = (w_turb - w_pump) / q_in
    return RankineResult(efficiency=eta, turbine_exit_quality=x2,
                         turbine_work=w_turb, heat_added=q_in)


# --------------------------------------------------------------------------- #
# factories (whole-plant scale defaults; the model itself is scale-agnostic)
# --------------------------------------------------------------------------- #
def pwr_steam_generator(secondary_pressure: float = 6.9e6,
                        T_hot_in: float = 597.15) -> SteamGenerator:
    """A representative whole-plant PWR steam generator (~3.4 GW class)."""
    return SteamGenerator(
        mdot_primary=18000.0, cp_primary=5500.0,
        secondary_pressure=secondary_pressure, UA=2.1e8, T_hot_in=T_hot_in,
    )
