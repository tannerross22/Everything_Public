"""Control-rod worth (the S-curve) and a rate-limited rod bank.

A control rod's *differential* worth drho/dx is proportional to the square of
the local neutron flux (the neutron importance) at the rod tip. For the cosine
axial flux of Phase 3, integrating from the top gives the classic S-shaped
*integral* worth: shallow near the ends (low flux) and steep in the middle.

With fractional insertion p in [0, 1] (0 = fully withdrawn, 1 = fully inserted)
and total worth W_tot (the magnitude of negative reactivity at full insertion):

    W(p)   = W_tot * [ p - sin(2 pi p) / (2 pi) ]          (integral worth)
    dW/dp  = W_tot * [ 1 - cos(2 pi p) ] = 2 W_tot sin^2(pi p)

W(p) is monotonic, so it inverts uniquely. The differential worth peaks at
mid-stroke (p = 0.5), which is why regulating banks are parked mid-band -- there
the rods have the most authority per step.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from scipy.optimize import brentq

_2PI = 2.0 * math.pi


def integral_worth(p: float, total_worth: float) -> float:
    """Magnitude of inserted negative reactivity at fractional insertion p."""
    p = min(max(p, 0.0), 1.0)
    return total_worth * (p - math.sin(_2PI * p) / _2PI)


def differential_worth(p: float, total_worth: float) -> float:
    """dW/dp at fractional insertion p (reactivity per unit insertion)."""
    p = min(max(p, 0.0), 1.0)
    return total_worth * (1.0 - math.cos(_2PI * p))


def insertion_for_worth(W: float, total_worth: float) -> float:
    """Invert the integral-worth S-curve: fractional insertion giving worth W."""
    if W <= 0.0:
        return 0.0
    if W >= total_worth:
        return 1.0
    return brentq(lambda p: integral_worth(p, total_worth) - W, 0.0, 1.0,
                  xtol=1e-12, rtol=1e-12)


@dataclass
class ControlRodBank:
    """A bank of control rods with an S-curve worth and a finite drive speed.

    Reactivity contributed is negative: reactivity() = -W(position).
    """
    name: str
    total_worth: float            # magnitude of full-insertion worth (delta-k/k)
    position: float = 0.0         # fractional insertion [0, 1]
    max_speed: float = 0.01       # max |d position/dt| (1/s)

    def worth_magnitude(self) -> float:
        return integral_worth(self.position, self.total_worth)

    def reactivity(self) -> float:
        """Negative reactivity contributed at the current position."""
        return -self.worth_magnitude()

    def differential(self) -> float:
        return differential_worth(self.position, self.total_worth)

    def target_for_worth(self, W: float) -> float:
        return insertion_for_worth(W, self.total_worth)

    def move_toward(self, target_position: float, dt: float) -> None:
        """Move toward a target insertion, rate-limited by max_speed."""
        target_position = min(max(target_position, 0.0), 1.0)
        max_step = self.max_speed * dt
        dp = target_position - self.position
        dp = min(max(dp, -max_step), max_step)
        self.position = min(max(self.position + dp, 0.0), 1.0)


# --- grey / black regulating banks (the taxonomy) ------------------------- #
def black_bank(total_worth: float = 0.018, max_speed: float = 0.01) -> ControlRodBank:
    """Strong-absorber regulating bank (high worth) -- coarse power control."""
    return ControlRodBank("black", total_worth=total_worth, max_speed=max_speed)


def grey_bank(total_worth: float = 0.003, max_speed: float = 0.01) -> ControlRodBank:
    """Weak-absorber regulating bank (low worth) -- fine maneuvering with less
    flux distortion."""
    return ControlRodBank("grey", total_worth=total_worth, max_speed=max_speed)
