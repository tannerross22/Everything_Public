"""Saturated-water properties (a compact steam table).

Tabulated saturation data for water, interpolated as needed. Two pressure ranges
matter for a PWR secondary side: the condenser (~0.004-0.01 MPa) and the steam
generator / boiler (~4-9 MPa). Linear interpolation in pressure is adequate
within these ranges. All values returned in SI (Pa, K, J/kg, J/kg/K).

Source: standard saturated-water steam tables.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# columns: P(MPa), Tsat(C), hf(kJ/kg), hg(kJ/kg), sf(kJ/kgK), sg(kJ/kgK)
_TABLE = np.array([
    [0.004, 28.96, 121.4, 2553.7, 0.4226, 8.4746],
    [0.005, 32.88, 137.8, 2560.7, 0.4762, 8.3938],
    [0.006, 36.16, 151.5, 2566.6, 0.5209, 8.3304],
    [0.008, 41.51, 173.9, 2576.0, 0.5926, 8.2287],
    [0.010, 45.81, 191.8, 2584.6, 0.6493, 8.1502],
    [3.000, 233.90, 1008.4, 2804.1, 2.6457, 6.1869],
    [4.000, 250.40, 1087.3, 2800.8, 2.7965, 6.0696],
    [5.000, 263.99, 1154.5, 2794.5, 2.9207, 5.9737],
    [6.000, 275.64, 1213.4, 2784.3, 3.0273, 5.8901],
    [7.000, 285.88, 1267.0, 2772.1, 3.1219, 5.8143],
    [8.000, 295.06, 1316.6, 2758.0, 3.2076, 5.7448],
    [9.000, 303.40, 1363.3, 2742.1, 3.2867, 5.6782],
])

_P = _TABLE[:, 0]                       # MPa
_TSAT = _TABLE[:, 1] + 273.15           # K
_HF = _TABLE[:, 2] * 1e3                # J/kg
_HG = _TABLE[:, 3] * 1e3
_SF = _TABLE[:, 4] * 1e3                # J/kg/K
_SG = _TABLE[:, 5] * 1e3


@dataclass(frozen=True)
class SatProps:
    P: float        # Pa
    T_sat: float    # K
    h_f: float      # J/kg (sat liquid)
    h_g: float      # J/kg (sat vapor)
    s_f: float      # J/kg/K
    s_g: float      # J/kg/K

    @property
    def h_fg(self) -> float:
        return self.h_g - self.h_f

    @property
    def s_fg(self) -> float:
        return self.s_g - self.s_f


def sat_props(P_pa: float) -> SatProps:
    """Saturated-water properties at pressure P (Pa)."""
    P_mpa = P_pa / 1e6
    return SatProps(
        P=P_pa,
        T_sat=float(np.interp(P_mpa, _P, _TSAT)),
        h_f=float(np.interp(P_mpa, _P, _HF)),
        h_g=float(np.interp(P_mpa, _P, _HG)),
        s_f=float(np.interp(P_mpa, _P, _SF)),
        s_g=float(np.interp(P_mpa, _P, _SG)),
    )


def T_sat(P_pa: float) -> float:
    """Saturation temperature (K) at pressure P (Pa)."""
    return float(np.interp(P_pa / 1e6, _P, _TSAT))


def P_sat(T_k: float) -> float:
    """Saturation pressure (Pa) at temperature T (K)."""
    return float(np.interp(T_k, _TSAT, _P)) * 1e6


def hf_at_T(T_k: float) -> float:
    """Saturated-liquid enthalpy (J/kg) at temperature T (K) -- used as an
    approximation for subcooled feedwater enthalpy."""
    return float(np.interp(T_k, _TSAT, _HF))
