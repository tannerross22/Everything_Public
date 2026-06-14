"""Point-kinetics parameters.

Six-group delayed-neutron data for thermal fission of U-235. The values below
are the widely-tabulated Keepin set (absolute delayed fractions beta_i, in
units of delta-k/k, and precursor decay constants lambda_i in 1/s).

The total delayed fraction beta = sum(beta_i) ~= 0.0065, the canonical figure
for U-235. The mean neutron generation time Lambda is reactor-specific; ~2e-5 s
is representative of a large thermal PWR. Both are exposed as parameters so a
later phase can swap in MOX / fast-spectrum data without touching the solver.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# --- Keepin six-group data for thermal fission of U-235 -------------------
# group:        1         2         3         4         5         6
_BETA_U235 = np.array([0.000215, 0.001424, 0.001274, 0.002568, 0.000748, 0.000273])
_LAMBDA_U235 = np.array([0.0124,   0.0305,   0.111,    0.301,    1.14,     3.01])


@dataclass(frozen=True)
class KineticsParams:
    """Container for point-kinetics constants.

    Attributes
    ----------
    beta_i : ndarray, shape (G,)
        Absolute delayed-neutron fraction of each precursor group (delta-k/k).
    lambda_i : ndarray, shape (G,)
        Decay constant of each precursor group (1/s).
    Lambda : float
        Mean neutron generation time (s).
    """

    beta_i: np.ndarray
    lambda_i: np.ndarray
    Lambda: float = 2.0e-5

    @property
    def beta(self) -> float:
        """Total delayed-neutron fraction, sum over groups."""
        return float(np.sum(self.beta_i))

    @property
    def n_groups(self) -> int:
        return int(self.beta_i.size)

    def __post_init__(self) -> None:
        if self.beta_i.shape != self.lambda_i.shape:
            raise ValueError("beta_i and lambda_i must have the same shape")
        if np.any(self.lambda_i <= 0):
            raise ValueError("all lambda_i must be positive")
        if self.Lambda <= 0:
            raise ValueError("Lambda must be positive")


def u235() -> KineticsParams:
    """Standard U-235 thermal six-group parameters (Keepin)."""
    return KineticsParams(
        beta_i=_BETA_U235.copy(),
        lambda_i=_LAMBDA_U235.copy(),
        Lambda=2.0e-5,
    )
