"""Single-phase water properties and forced-convection correlations.

The coolant in a PWR runs subcooled (single-phase liquid) at ~15.5 MPa, ~300 C.
Properties vary with temperature, but for a first-pass subchannel model we use
constant representative values evaluated near the average bulk temperature; this
is the standard engineering simplification and keeps the convective coefficient
analytic. Swapping in an IAPWS-97 property package (so rho, c_p, mu, k follow the
local bulk temperature) is a clean later upgrade -- the correlation functions
below already take properties as arguments.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WaterProperties:
    """Constant single-phase water properties (SI)."""
    rho: float      # density (kg/m^3)
    cp: float       # specific heat (J/kg/K)
    mu: float       # dynamic viscosity (Pa*s)
    k: float        # thermal conductivity (W/m/K)

    @property
    def Pr(self) -> float:
        """Prandtl number Pr = c_p mu / k."""
        return self.cp * self.mu / self.k


def pwr_water() -> WaterProperties:
    """Representative pressurized water near 15.5 MPa, ~310 C bulk."""
    return WaterProperties(rho=700.0, cp=5500.0, mu=8.5e-5, k=0.53)


def reynolds(mass_flux: float, D_h: float, mu: float) -> float:
    """Re = G D_h / mu, with G the mass flux (kg/m^2/s)."""
    return mass_flux * D_h / mu


def prandtl(props: WaterProperties) -> float:
    return props.Pr


def dittus_boelter(Re: float, Pr: float, heating: bool = True) -> float:
    """Dittus-Boelter Nusselt number for fully-developed turbulent flow:

        Nu = 0.023 Re^0.8 Pr^n,   n = 0.4 (heating) or 0.3 (cooling).

    Valid for Re > ~10^4 and 0.7 < Pr < ~160, which the PWR subchannel
    (Re ~ 5e5, Pr ~ 0.9) comfortably satisfies.
    """
    n = 0.4 if heating else 0.3
    return 0.023 * Re ** 0.8 * Pr ** n


def htc(mass_flux: float, D_h: float, props: WaterProperties,
        heating: bool = True) -> float:
    """Convective heat-transfer coefficient h = Nu k / D_h (W/m^2/K)."""
    Re = reynolds(mass_flux, D_h, props.mu)
    Nu = dittus_boelter(Re, props.Pr, heating=heating)
    return Nu * props.k / D_h
