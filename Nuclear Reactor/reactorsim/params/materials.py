"""Material thermal properties.

Conductivity k(T) and specific heat c_p(T) are temperature-dependent and stored
as callables (T in kelvin); density is taken constant over the operating range.
The temperature dependence of UO2 conductivity in particular is physically
important -- k drops as T rises, which is why fuel centerline temperatures climb
so high and is the root of the strong negative Doppler feedback in Phase 5.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Material:
    name: str
    k_fn: Callable[[float], float]   # thermal conductivity (W/m/K), T in K
    rho: float                        # density (kg/m^3)
    cp_fn: Callable[[float], float]   # specific heat (J/kg/K), T in K

    def k(self, T: float) -> float:
        return self.k_fn(T)

    def cp(self, T: float) -> float:
        return self.cp_fn(T)


def constant_material(name: str, k: float, rho: float, cp: float) -> Material:
    """A material with temperature-independent properties (useful for analytic
    validation, where the closed-form solution assumes constant k)."""
    return Material(name=name, k_fn=lambda T: k, rho=rho, cp_fn=lambda T: cp)


# --- UO2 (95% theoretical density) ---------------------------------------- #
def _k_uo2(T: float) -> float:
    """Conductivity of 95%-dense UO2 (Fink-type correlation), W/m/K.

    Valid roughly 298-3120 K. The first term is the phonon contribution
    (falls with T), the second the small-polaron electronic term (rises near
    melting).
    """
    t = T / 1000.0
    return 100.0 / (7.5408 + 17.692 * t + 3.6142 * t * t) \
        + 6400.0 / (t ** 2.5) * math.exp(-16.35 / t)


def _cp_uo2(T: float) -> float:
    """Specific heat of UO2, J/kg/K (simple engineering fit; near-constant
    across the operating range, rising modestly with T)."""
    return 264.0 + 0.0470 * T


def uo2() -> Material:
    return Material(name="UO2", k_fn=_k_uo2, rho=10400.0, cp_fn=_cp_uo2)


# --- Zircaloy cladding ----------------------------------------------------- #
def _k_zry(T: float) -> float:
    """Conductivity of Zircaloy, W/m/K (cubic fit in T [K])."""
    return 7.51 + 2.09e-2 * T - 1.45e-5 * T * T + 7.67e-9 * T ** 3


def _cp_zry(T: float) -> float:
    """Specific heat of Zircaloy, J/kg/K."""
    return 252.5 + 0.110 * T


def zircaloy() -> Material:
    return Material(name="Zircaloy", k_fn=_k_zry, rho=6550.0, cp_fn=_cp_zry)
