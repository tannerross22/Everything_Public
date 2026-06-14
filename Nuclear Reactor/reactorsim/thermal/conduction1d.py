"""1D radial heat conduction in a cylindrical fuel pin (Phase 2).

Solves the transient cylindrical heat equation

    rho c_p dT/dt = (1/r) d/dr ( k r dT/dr ) + q'''(r)

over the pin cross-section: a UO2 pellet, a helium gap (modelled as a contact
conductance, not a meshed material), and a Zircaloy clad, with a convective
(Robin) boundary to the coolant.

Discretization: cell-centred Finite Volume. Integrating the equation over an
annular control volume turns the conduction term into a balance of face fluxes,

    2*pi*r_face * k_face * (T_neighbour - T_cell) / dr,

which conserves energy exactly and handles the material interfaces cleanly. The
result is a tridiagonal system, solved directly. Temperature-dependent
conductivity is handled by Picard iteration (re-evaluate k(T), re-solve, repeat).

The gap is a series thermal resistance between the outer pellet cell and the
inner clad cell: half-cell pellet conduction + gap conductance + half-cell clad
conduction. The outer convective boundary is likewise a series of half-cell clad
conduction and the coolant film.

Coordinate / indexing notes
---------------------------
Nodes are cell centres: fuel cells 0..n_fuel-1, then clad cells. The centreline
face at r=0 has zero area, so the symmetry BC (dT/dr=0) is satisfied
automatically. Volumes and conductances are per unit axial length (W/m, m^3/m).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.linalg import solve_banded

from ..params.geometry import PinGeometry, pwr_17x17
from ..params.materials import Material, uo2, zircaloy
from ..params.plant import CoolantBC, pwr_nominal

_2PI = 2.0 * math.pi


@dataclass
class RadialPinModel:
    """Finite-volume radial conduction model of a single fuel pin.

    Parameters
    ----------
    geom : PinGeometry
    fuel, clad : Material
    coolant : CoolantBC          (supplies h, T_inf, and h_gap)
    q_volumetric : float         volumetric heat generation in the pellet (W/m^3)
    n_fuel, n_clad : int         number of radial cells in each region
    include_clad : bool          if False, model the pellet alone (validation)
    outer_bc : {'robin','dirichlet'}
    T_surface : float            surface temperature for the Dirichlet case (K)
    """

    geom: PinGeometry = field(default_factory=pwr_17x17)
    fuel: Material = field(default_factory=uo2)
    clad: Material = field(default_factory=zircaloy)
    coolant: CoolantBC = field(default_factory=pwr_nominal)
    q_volumetric: float = 0.0
    n_fuel: int = 40
    n_clad: int = 8
    include_clad: bool = True
    outer_bc: str = "robin"
    T_surface: float | None = None

    # built in __post_init__
    N: int = field(init=False)
    r_center: np.ndarray = field(init=False)
    vol: np.ndarray = field(init=False)
    drf: float = field(init=False)
    drc: float = field(init=False)

    def __post_init__(self) -> None:
        if self.outer_bc not in ("robin", "dirichlet"):
            raise ValueError("outer_bc must be 'robin' or 'dirichlet'")
        if self.outer_bc == "dirichlet" and self.T_surface is None:
            raise ValueError("T_surface required for dirichlet outer_bc")

        g = self.geom
        nf = self.n_fuel
        self.drf = g.r_fuel / nf

        # fuel cell centres and volumes (per unit length)
        i = np.arange(nf)
        rc_fuel = (i + 0.5) * self.drf
        vol_fuel = math.pi * self.drf ** 2 * (2 * i + 1)

        if self.include_clad:
            nc = self.n_clad
            self.drc = (g.r_clad_outer - g.r_clad_inner) / nc
            j = np.arange(nc)
            rc_clad = g.r_clad_inner + (j + 0.5) * self.drc
            r_inner = g.r_clad_inner + j * self.drc
            r_outer = g.r_clad_inner + (j + 1) * self.drc
            vol_clad = math.pi * (r_outer ** 2 - r_inner ** 2)
            self.r_center = np.concatenate([rc_fuel, rc_clad])
            self.vol = np.concatenate([vol_fuel, vol_clad])
        else:
            self.drc = 0.0
            self.r_center = rc_fuel
            self.vol = vol_fuel

        self.N = self.r_center.size

    # ------------------------------------------------------------------ #
    # per-node source and capacitance
    # ------------------------------------------------------------------ #
    def _q_source(self) -> np.ndarray:
        """Volumetric source integrated over each cell (W/m). Fuel only."""
        q = np.zeros(self.N)
        q[: self.n_fuel] = self.q_volumetric * self.vol[: self.n_fuel]
        return q

    def _capacitance(self, T: np.ndarray) -> np.ndarray:
        """rho*c_p*volume for each cell (J/m/K)."""
        cap = np.empty(self.N)
        nf = self.n_fuel
        for idx in range(self.N):
            mat = self.fuel if idx < nf else self.clad
            cap[idx] = mat.rho * mat.cp(T[idx]) * self.vol[idx]
        return cap

    # ------------------------------------------------------------------ #
    # face conductances (per unit length), evaluated at current T
    # ------------------------------------------------------------------ #
    def _conductances(self, T: np.ndarray) -> tuple[np.ndarray, float]:
        g = self.geom
        nf = self.n_fuel
        G = np.zeros(self.N - 1)

        # interior fuel-fuel faces
        for i in range(nf - 1):
            r_face = (i + 1) * self.drf
            ka, kb = self.fuel.k(T[i]), self.fuel.k(T[i + 1])
            k_face = 2.0 * ka * kb / (ka + kb)          # harmonic mean
            G[i] = _2PI * r_face * k_face / self.drf

        if self.include_clad:
            # gap face: half-fuel conduction + gap + half-clad conduction
            g_hf = _2PI * g.r_fuel * self.fuel.k(T[nf - 1]) / (self.drf / 2)
            g_gap = _2PI * g.r_fuel * self.coolant.h_gap
            g_hc = _2PI * g.r_clad_inner * self.clad.k(T[nf]) / (self.drc / 2)
            G[nf - 1] = 1.0 / (1.0 / g_hf + 1.0 / g_gap + 1.0 / g_hc)

            # interior clad-clad faces
            for j in range(self.n_clad - 1):
                idx = nf + j
                r_face = g.r_clad_inner + (j + 1) * self.drc
                ka, kb = self.clad.k(T[idx]), self.clad.k(T[idx + 1])
                k_face = 2.0 * ka * kb / (ka + kb)
                G[idx] = _2PI * r_face * k_face / self.drc

        # outer boundary conductance to the (ghost) boundary value
        last = self.N - 1
        if self.include_clad:
            r_s, dr_half, k_last = g.r_clad_outer, self.drc / 2, self.clad.k(T[last])
        else:
            r_s, dr_half, k_last = g.r_fuel, self.drf / 2, self.fuel.k(T[last])
        g_half = _2PI * r_s * k_last / dr_half

        if self.outer_bc == "robin":
            g_conv = _2PI * r_s * self.coolant.h
            G_out = 1.0 / (1.0 / g_half + 1.0 / g_conv)
        else:  # dirichlet at the surface face
            G_out = g_half
        return G, G_out

    # ------------------------------------------------------------------ #
    # assemble tridiagonal system  A T = b
    # ------------------------------------------------------------------ #
    def _assemble(self, G, G_out, cap_over_dt=None, T_old=None):
        N = self.N
        diag = np.zeros(N)
        upper = np.zeros(N - 1)
        lower = np.zeros(N - 1)
        b = self._q_source()

        for i in range(N - 1):
            diag[i] += G[i]
            diag[i + 1] += G[i]
            upper[i] = -G[i]
            lower[i] = -G[i]

        T_bc = self.coolant.T_inf if self.outer_bc == "robin" else self.T_surface
        diag[-1] += G_out
        b[-1] += G_out * T_bc

        if cap_over_dt is not None:
            diag += cap_over_dt
            b = b + cap_over_dt * T_old
        return diag, lower, upper, b

    @staticmethod
    def _solve_tridiag(diag, lower, upper, b):
        N = diag.size
        ab = np.zeros((3, N))
        ab[0, 1:] = upper        # superdiagonal
        ab[1, :] = diag          # main diagonal
        ab[2, :-1] = lower       # subdiagonal
        return solve_banded((1, 1), ab, b)

    # ------------------------------------------------------------------ #
    # solvers
    # ------------------------------------------------------------------ #
    def solve_steady(self, T_guess: np.ndarray | None = None,
                     tol: float = 1e-8, max_iter: int = 100) -> np.ndarray:
        """Steady-state temperature field. Picard-iterates on k(T)."""
        T = (np.full(self.N, self.coolant.T_inf) if T_guess is None
             else T_guess.copy())
        for _ in range(max_iter):
            G, G_out = self._conductances(T)
            diag, lower, upper, b = self._assemble(G, G_out)
            T_new = self._solve_tridiag(diag, lower, upper, b)
            if np.max(np.abs(T_new - T)) < tol:
                return T_new
            T = T_new
        return T

    def step(self, T_old: np.ndarray, dt: float,
             tol: float = 1e-8, max_iter: int = 100) -> np.ndarray:
        """Advance one backward-Euler timestep of size dt."""
        T = T_old.copy()
        for _ in range(max_iter):
            G, G_out = self._conductances(T)
            cap_over_dt = self._capacitance(T) / dt
            diag, lower, upper, b = self._assemble(G, G_out, cap_over_dt, T_old)
            T_new = self._solve_tridiag(diag, lower, upper, b)
            if np.max(np.abs(T_new - T)) < tol:
                return T_new
            T = T_new
        return T

    def solve_transient(self, T0: np.ndarray, dt: float, t_end: float,
                        store_every: int = 1):
        """Integrate from T0 to t_end with fixed dt (backward Euler).

        Returns (times, T_history) where T_history has shape (n_saved, N).
        """
        n_steps = int(round(t_end / dt))
        times = [0.0]
        hist = [T0.copy()]
        T = T0.copy()
        for s in range(1, n_steps + 1):
            T = self.step(T, dt)
            if s % store_every == 0 or s == n_steps:
                times.append(s * dt)
                hist.append(T.copy())
        return np.array(times), np.array(hist)

    # ------------------------------------------------------------------ #
    # diagnostics
    # ------------------------------------------------------------------ #
    def heat_out(self, T: np.ndarray) -> float:
        """Heat leaving the outer boundary per unit length (W/m)."""
        _, G_out = self._conductances(T)
        T_bc = self.coolant.T_inf if self.outer_bc == "robin" else self.T_surface
        return G_out * (T[-1] - T_bc)

    def heat_generated(self) -> float:
        """Total heat generated per unit length (W/m) = linear heat rate q'."""
        return float(np.sum(self._q_source()))


def analytic_centerline_rise(q_volumetric: float, r_fuel: float, k: float) -> float:
    """Closed-form centreline-minus-surface temperature rise for a solid
    cylinder with uniform q''' and constant k:  dT = q''' r^2 / (4 k)."""
    return q_volumetric * r_fuel ** 2 / (4.0 * k)


def analytic_profile(r: np.ndarray, q_volumetric: float, r_fuel: float,
                     k: float, T_surface: float) -> np.ndarray:
    """Closed-form radial temperature profile T(r) = T_s + q'''(r_f^2 - r^2)/(4k)."""
    return T_surface + q_volumetric * (r_fuel ** 2 - r ** 2) / (4.0 * k)
