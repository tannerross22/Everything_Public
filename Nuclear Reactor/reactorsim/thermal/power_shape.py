"""Axial power distribution along the fuel rod.

Fission power is not uniform along the rod -- it follows roughly a cosine, peaked
at the core mid-plane, because the neutron flux falls toward the ends. The
classic model is a "chopped cosine":

    q'(z) = q'_avg * F(z),   F(z) = A cos( pi (z - H/2) / H_e )

where H is the active height and H_e = H + 2*delta is an extrapolated height
(delta accounts for flux not vanishing exactly at the physical ends). A is fixed
by requiring the axial average of F over [0, H] to equal 1, so q'_avg is the true
average linear heat rate.

With no extrapolation (H_e = H) the peak-to-average factor is pi/2 ~= 1.57; a
finite extrapolation length flattens the profile toward realistic values
(~1.3-1.5).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class AxialPowerShape:
    height: float                     # active fuel height H (m)
    extrapolation_length: float = 0.0 # delta per end (m); H_e = H + 2*delta

    @property
    def H_e(self) -> float:
        return self.height + 2.0 * self.extrapolation_length

    @property
    def _A(self) -> float:
        """Normalization so the axial average of F over [0, H] is 1."""
        H, He = self.height, self.H_e
        return math.pi * H / (2.0 * He * math.sin(math.pi * H / (2.0 * He)))

    def factor(self, z):
        """Normalized axial peaking factor F(z) (average 1 over the rod)."""
        z = np.asarray(z, dtype=float)
        return self._A * np.cos(math.pi * (z - self.height / 2.0) / self.H_e)

    @property
    def peak_factor(self) -> float:
        """Peak-to-average ratio (value of F at the mid-plane)."""
        return self._A

    def q_linear(self, z, q_linear_avg: float):
        """Local linear heat rate q'(z) (W/m) given the rod average."""
        return q_linear_avg * self.factor(z)
