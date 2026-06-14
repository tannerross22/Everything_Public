"""Fuel-pin geometry. Defaults are representative of a standard 17x17 PWR
assembly (UO2 pellet ~8.19 mm dia, Zircaloy clad 9.5 mm OD, 3.66 m active
height). All lengths in metres.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PinGeometry:
    r_fuel: float = 4.095e-3        # pellet outer radius (m)
    gap_thickness: float = 8.25e-5  # pellet-clad radial gap (m)
    clad_thickness: float = 5.70e-4 # cladding thickness (m)
    active_height: float = 3.66     # active fuel height (m)
    pitch: float = 1.26e-2          # rod-to-rod pitch (m)

    @property
    def r_clad_inner(self) -> float:
        return self.r_fuel + self.gap_thickness

    @property
    def r_clad_outer(self) -> float:
        return self.r_clad_inner + self.clad_thickness

    @property
    def fuel_area(self) -> float:
        """Cross-sectional area of the fuel pellet (m^2)."""
        import math
        return math.pi * self.r_fuel ** 2

    def q_volumetric_from_linear(self, q_linear: float) -> float:
        """Convert a linear heat rate q' (W/m) to a uniform volumetric heat
        generation rate q''' (W/m^3) in the pellet."""
        return q_linear / self.fuel_area

    # --- coolant subchannel geometry (square lattice) ---------------------
    @property
    def flow_area(self) -> float:
        """Coolant flow area of one unit subchannel (m^2): the square pitch
        cell minus the rod cross-section."""
        import math
        return self.pitch ** 2 - math.pi * self.r_clad_outer ** 2

    @property
    def wetted_perimeter(self) -> float:
        """Wetted (= heated) perimeter of the subchannel: the rod
        circumference (m)."""
        import math
        return 2.0 * math.pi * self.r_clad_outer

    @property
    def hydraulic_diameter(self) -> float:
        """Hydraulic diameter D_h = 4 A_flow / P_wetted (m)."""
        return 4.0 * self.flow_area / self.wetted_perimeter


def pwr_17x17() -> PinGeometry:
    """Standard 17x17 PWR fuel pin."""
    return PinGeometry()
