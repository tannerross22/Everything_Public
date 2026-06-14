"""1D axial spatial neutron kinetics (Phase 6.5).

Upgrades point kinetics to a one-group, time-dependent neutron diffusion model
discretized along the core axis, with six delayed-neutron precursor groups per
node:

    (1/v) dphi/dt = D d2phi/dz2 - Sigma_a(z,t) phi + (1-beta) nuSigma_f phi
                                 + sum_i lambda_i C_i
        dC_i/dt   = beta_i nuSigma_f phi - lambda_i C_i

Finite volume on N axial nodes; zero-flux (extrapolated) boundaries at the core
ends. The fundamental mode (the steady flux shape) is found by a criticality
search: solve the eigenproblem for k_eff and scale nuSigma_f so the reference
state is exactly critical (k=1).

What this buys us over point kinetics:
  * the cosine axial flux shape emerges instead of being assumed;
  * control-rod worth follows the S-curve automatically (phi^2 weighting of the
    local absorption), rather than being hand-coded;
  * each node carries its own temperature feedback, so the flux *shape* responds
    to where rods sit and where the core is hot -- which makes the axial offset
    AO = (P_top - P_bottom)/(P_top + P_bottom) a controllable dynamic quantity.

Feedback is mapped onto the absorption cross-section so that the lumped behavior
matches the Phase-5 reactivity coefficients:  dSigma_a = -nuSigma_f*(alpha_f*dT_f
+ alpha_m*dT_m).  (Xenon, the classic driver of axial instability, is a deferred
future addition.)
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.linalg import eigh, expm

from ..params.kinetics import KineticsParams, u235


@dataclass
class AxialKineticsModel:
    kin: KineticsParams = field(default_factory=u235)
    height: float = 3.66            # active core height (m)
    n_axial: int = 20
    D: float = 0.13                 # diffusion coefficient (m); L_migration ~ 8 cm
    Sigma_a: float = 20.0           # reference absorption cross-section (1/m)
    v: float = 2500.0               # one-group neutron speed (m/s)
    extrapolation: float = 0.10     # extrapolation length at each end (m)

    # set in __post_init__
    nuSigma_f: float = field(init=False, default=0.0)
    Lap: np.ndarray = field(init=False, default=None)
    z: np.ndarray = field(init=False, default=None)
    dz: float = field(init=False, default=0.0)
    phi_ref: np.ndarray = field(init=False, default=None)
    k_ref: float = field(init=False, default=1.0)

    def __post_init__(self) -> None:
        N = self.n_axial
        self.dz = self.height / N
        self.z = (np.arange(N) + 0.5) * self.dz
        self.Lap = self._laplacian()

        # criticality search on the bare core (sets nuSigma_f, phi_ref, k_ref)
        self.set_reference_absorption(self.Sigma_a * np.ones(N))
        # cross-section used to calibrate rod-worth strengths; kept fixed even if
        # the reference is later recomputed with parked rods, so the rod
        # absorption added in the dynamics stays consistent with the search
        self._nuSf_cal = self.nuSigma_f

    def set_reference_absorption(self, sigma_ref: np.ndarray) -> None:
        """Criticality search for a given reference absorption field: solve for
        the fundamental mode and scale nuSigma_f so that state is critical (k=1).

        Used to make the reference critical *with the regulating banks parked* --
        i.e. the core carries excess reactivity that the parked rods hold down,
        as a real core does.
        """
        M = np.diag(sigma_ref) - self.D * self.Lap
        evals, evecs = eigh(M)
        mu = evals[0]                       # smallest eigenvalue = fundamental
        phi = evecs[:, 0]
        if phi.mean() < 0:
            phi = -phi
        self.nuSigma_f = mu                 # so k_eff = nuSigma_f / mu = 1
        self.phi_ref = phi / phi.mean()     # normalize to unit mean
        self.k_ref = self.nuSigma_f / mu

    # ------------------------------------------------------------------ #
    def _laplacian(self) -> np.ndarray:
        """Discrete d2/dz2 (1/m^2) with extrapolated zero-flux ends."""
        N = self.n_axial
        dz = self.dz
        c = 1.0 / dz ** 2
        cb = 1.0 / ((dz / 2 + self.extrapolation) * dz)   # boundary face
        L = np.zeros((N, N))
        for k in range(N):
            if k > 0:
                L[k, k - 1] += c
                L[k, k] -= c
            else:
                L[k, k] -= cb
            if k < N - 1:
                L[k, k + 1] += c
                L[k, k] -= c
            else:
                L[k, k] -= cb
        return L

    # ------------------------------------------------------------------ #
    # static / diagnostic helpers
    # ------------------------------------------------------------------ #
    def equilibrium_precursors(self, phi: np.ndarray) -> np.ndarray:
        """C_i,k = beta_i nuSigma_f phi_k / lambda_i  (shape (G, N))."""
        return (self.kin.beta_i[:, None] * self.nuSigma_f * phi[None, :]
                / self.kin.lambda_i[:, None])

    def initial_state(self) -> np.ndarray:
        """Flat state [phi (N), C (G*N)] at the critical reference."""
        C = self.equilibrium_precursors(self.phi_ref)
        return np.concatenate([self.phi_ref, C.ravel()])

    def split(self, y: np.ndarray):
        """Return (phi, C) with C shape (G, N)."""
        N, G = self.n_axial, self.kin.n_groups
        return y[:N], y[N:].reshape(G, N)

    def total_power(self, phi: np.ndarray) -> float:
        """Normalized total power (1 at the reference state)."""
        return float(phi.sum() / self.phi_ref.sum())

    def axial_offset(self, phi: np.ndarray) -> float:
        """AO = (P_top - P_bottom)/(P_top + P_bottom) using node power = phi*dz."""
        mid = self.height / 2
        lower = phi[self.z < mid].sum()
        upper = phi[self.z >= mid].sum()
        return float((upper - lower) / (upper + lower))

    def linear_power(self, phi: np.ndarray, q_linear_avg: float) -> np.ndarray:
        """Local linear heat rate q'(z) (W/m); reference axial mean = q_linear_avg."""
        return q_linear_avg * phi

    # ------------------------------------------------------------------ #
    # dynamics
    # ------------------------------------------------------------------ #
    def system_matrix(self, sigma_a: np.ndarray) -> np.ndarray:
        """Assemble the (G+1)*N evolution matrix A for given absorption field."""
        N, G = self.n_axial, self.kin.n_groups
        p = self.kin
        beta = p.beta
        A = np.zeros(((G + 1) * N, (G + 1) * N))

        # flux block: dphi/dt = v[ D Lap - diag(sigma_a) + (1-beta) nuSf I ] phi
        flux = self.v * (self.D * self.Lap
                         - np.diag(sigma_a)
                         + (1.0 - beta) * self.nuSigma_f * np.eye(N))
        A[:N, :N] = flux

        for i in range(G):
            r = N + i * N
            # dphi/dt += v lambda_i C_i
            A[:N, r:r + N] += self.v * p.lambda_i[i] * np.eye(N)
            # dC_i/dt = beta_i nuSf phi - lambda_i C_i
            A[r:r + N, :N] = p.beta_i[i] * self.nuSigma_f * np.eye(N)
            A[r:r + N, r:r + N] = -p.lambda_i[i] * np.eye(N)
        return A

    def advance(self, y: np.ndarray, sigma_a: np.ndarray, dt: float) -> np.ndarray:
        """Advance the state over dt with fixed cross-sections (exact: expm)."""
        return expm(self.system_matrix(sigma_a) * dt) @ y

    # ------------------------------------------------------------------ #
    # absorption perturbations: rods and feedback
    # ------------------------------------------------------------------ #
    def rod_sigma(self, position: float, total_worth: float,
                  from_top: bool) -> np.ndarray:
        """Absorption added by a bank inserted to fractional depth `position`
        from the top (or bottom). `total_worth` is the full-insertion worth
        magnitude (delta-k/k); the partial-insertion S-curve emerges from the
        flux weighting in the dynamics. Returns dSigma_a per node (1/m)."""
        N = self.n_axial
        sigma_full = total_worth * self._nuSf_cal      # calibrated strength
        ds = np.zeros(N)
        depth = position * self.height
        for k in range(N):
            z_lo = k * self.dz
            z_hi = (k + 1) * self.dz
            if from_top:
                covered = max(0.0, z_hi - (self.height - depth))
            else:
                covered = max(0.0, depth - z_lo)
            frac = min(covered, self.dz) / self.dz
            ds[k] = sigma_full * max(0.0, min(frac, 1.0))
        return ds

    def feedback_sigma(self, dT_fuel: np.ndarray, dT_mod: np.ndarray,
                       alpha_fuel: float, alpha_mod: float) -> np.ndarray:
        """Absorption perturbation from temperature feedback, calibrated so the
        lumped reactivity effect matches alpha_fuel/alpha_mod."""
        return -self.nuSigma_f * (alpha_fuel * dT_fuel + alpha_mod * dT_mod)

    # ------------------------------------------------------------------ #
    def k_eff(self, sigma_a: np.ndarray) -> float:
        """Static k_eff for a given absorption field (for worth diagnostics)."""
        M = np.diag(sigma_a) - self.D * self.Lap
        evals = eigh(M, eigvals_only=True)
        return self.nuSigma_f / evals[0]

    def reactivity(self, sigma_a: np.ndarray) -> float:
        k = self.k_eff(sigma_a)
        return (k - 1.0) / k
