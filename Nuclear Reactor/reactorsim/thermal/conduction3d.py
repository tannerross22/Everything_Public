"""3D (r, theta, z) heat conduction in a cylindrical fuel pin (Phase 4).

Generalizes the Phase-2 radial solver to the full cylindrical heat equation

    rho c_p dT/dt = (1/r) d/dr(k r dT/dr)
                  + (1/r^2) d/dtheta(k dT/dtheta)
                  + d/dz(k dT/dz)
                  + q'''

discretized by cell-centred Finite Volume on a structured mesh of Nr x Ntheta x
Nz cells. The genuinely new ingredient versus Phase 3 is *axial conduction*: the
z-levels are no longer independent radial slices but are coupled through the
axial faces, so heat can move along the rod.

Face conductances (per face, SI) for a cell of radial width dr_i, azimuthal
extent dtheta, axial height dz, centred at radius r_i:

    radial    G_r     = k_face * (r_face * dtheta * dz) / dr_centres
    azimuthal G_theta = k_face * (dr_i * dz) / (r_i * dtheta)
    axial     G_z     = k_face * A_rtheta_i / dz       (A_rtheta = cross-section)

The pellet-clad gap is a series resistance on the radial face between the last
fuel cell and the first clad cell (half-pellet conduction + gap conductance +
half-clad conduction). The outer radial boundary is convective (Robin) to the
local coolant temperature; axial ends default to adiabatic (insulated end
plugs). With Ntheta = 1 the azimuthal faces wrap onto themselves and vanish, and
a single z-slice reduces exactly to the Phase-2 radial model.

Coordinate / indexing
---------------------
Flat index p = i + Nr*(j + Ntheta*l)  for radial i, azimuthal j, axial l.
The centreline face at r=0 has zero area, so symmetry (dT/dr=0) is automatic.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve

from ..params.geometry import PinGeometry, pwr_17x17
from ..params.materials import Material, uo2, zircaloy
from ..params.plant import CoolantBC, pwr_nominal


@dataclass
class Conduction3D:
    """Finite-volume (r, theta, z) conduction model of a single pin.

    Boundary inputs that vary with elevation -- the volumetric source, coolant
    temperature, and film coefficient -- may be given as scalars (uniform) or
    as length-Nz arrays.
    """

    geom: PinGeometry = field(default_factory=pwr_17x17)
    fuel: Material = field(default_factory=uo2)
    clad: Material = field(default_factory=zircaloy)
    h_gap: float = field(default_factory=lambda: pwr_nominal().h_gap)

    q_volumetric: float | np.ndarray = 0.0     # W/m^3 in fuel (scalar or [Nz])
    T_coolant: float | np.ndarray = 580.0      # K (scalar or [Nz])
    h_coolant: float | np.ndarray = 34000.0    # W/m^2/K (scalar or [Nz])

    n_fuel: int = 40
    n_clad: int = 8
    n_theta: int = 1
    n_axial: int = 30
    height: float | None = None

    include_clad: bool = True
    outer_bc: str = "robin"          # 'robin' | 'adiabatic' | 'dirichlet'
    T_surface: float | None = None
    axial_bc: str = "adiabatic"      # 'adiabatic' | 'dirichlet'
    T_end: float | None = None

    # built in __post_init__
    Nr: int = field(init=False)
    N: int = field(init=False)

    def __post_init__(self) -> None:
        if self.height is None:
            self.height = self.geom.active_height
        if self.outer_bc not in ("robin", "adiabatic", "dirichlet"):
            raise ValueError("bad outer_bc")
        if self.outer_bc == "dirichlet" and self.T_surface is None:
            raise ValueError("T_surface required for dirichlet outer_bc")
        if self.axial_bc not in ("adiabatic", "dirichlet"):
            raise ValueError("bad axial_bc")
        if self.axial_bc == "dirichlet" and self.T_end is None:
            raise ValueError("T_end required for dirichlet axial_bc")

        g = self.geom
        nf, nc = self.n_fuel, (self.n_clad if self.include_clad else 0)
        self.Nr = nf + nc
        self.dtheta = 2.0 * math.pi / self.n_theta
        self.dz = self.height / self.n_axial
        self.drf = g.r_fuel / nf
        self.drc = ((g.r_clad_outer - g.r_clad_inner) / nc) if nc else 0.0

        # radial cell geometry (per radial index)
        rc = np.empty(self.Nr)
        dr = np.empty(self.Nr)
        Art = np.empty(self.Nr)          # r-theta cross-sectional area of cell
        for i in range(nf):
            r_in, r_out = i * self.drf, (i + 1) * self.drf
            rc[i] = (i + 0.5) * self.drf
            dr[i] = self.drf
            Art[i] = 0.5 * (r_out ** 2 - r_in ** 2) * self.dtheta
        for jc in range(nc):
            i = nf + jc
            r_in = g.r_clad_inner + jc * self.drc
            r_out = r_in + self.drc
            rc[i] = r_in + 0.5 * self.drc
            dr[i] = self.drc
            Art[i] = 0.5 * (r_out ** 2 - r_in ** 2) * self.dtheta
        self.rc, self.dr, self.Art = rc, dr, Art
        self.vol = Art * self.dz          # per-cell volume (m^3)

        self.N = self.Nr * self.n_theta * self.n_axial

        # broadcast elevation-varying inputs to length Nz
        self.q_vol_z = self._as_axial(self.q_volumetric)
        self.Tcool_z = self._as_axial(self.T_coolant)
        self.h_z = self._as_axial(self.h_coolant)

    # ------------------------------------------------------------------ #
    def _as_axial(self, x) -> np.ndarray:
        arr = np.asarray(x, dtype=float)
        if arr.ndim == 0:
            return np.full(self.n_axial, float(arr))
        if arr.size != self.n_axial:
            raise ValueError(f"expected scalar or length-{self.n_axial} array")
        return arr

    def idx(self, i, j, l) -> int:
        return i + self.Nr * (j + self.n_theta * l)

    def _kmat(self, i: int, T: float) -> float:
        return self.fuel.k(T) if i < self.n_fuel else self.clad.k(T)

    @staticmethod
    def _harmonic(a: float, b: float) -> float:
        return 2.0 * a * b / (a + b)

    # ------------------------------------------------------------------ #
    # assembly
    # ------------------------------------------------------------------ #
    def _assemble(self, T: np.ndarray, cap_over_dt=None, T_old=None):
        g = self.geom
        Nr, Nth, Nz = self.Nr, self.n_theta, self.n_axial
        nf = self.n_fuel
        dtheta, dz = self.dtheta, self.dz

        rows: list[int] = []
        cols: list[int] = []
        data: list[float] = []
        diag = np.zeros(self.N)
        b = np.zeros(self.N)

        def couple(p, q, Gf):
            rows.append(p); cols.append(q); data.append(-Gf)
            rows.append(q); cols.append(p); data.append(-Gf)
            diag[p] += Gf
            diag[q] += Gf

        # source term (fuel cells only) and capacitance
        for l in range(Nz):
            qv = self.q_vol_z[l]
            for j in range(Nth):
                for i in range(nf):
                    b[self.idx(i, j, l)] += qv * self.vol[i]

        # --- radial faces ------------------------------------------------
        for l in range(Nz):
            for j in range(Nth):
                for i in range(Nr - 1):
                    p, e = self.idx(i, j, l), self.idx(i + 1, j, l)
                    if i == nf - 1 and self.include_clad:
                        # pellet-clad gap (series resistance)
                        area = g.r_fuel * dtheta * dz
                        g_hf = self.fuel.k(T[p]) * area / (self.drf / 2)
                        g_gap = self.h_gap * area
                        area_c = g.r_clad_inner * dtheta * dz
                        g_hc = self.clad.k(T[e]) * area_c / (self.drc / 2)
                        Gf = 1.0 / (1.0 / g_hf + 1.0 / g_gap + 1.0 / g_hc)
                    else:
                        if i < nf - 1:
                            r_face = (i + 1) * self.drf
                        else:
                            r_face = g.r_clad_inner + (i - nf + 1) * self.drc
                        k_face = self._harmonic(self._kmat(i, T[p]),
                                                self._kmat(i + 1, T[e]))
                        d_centres = 0.5 * (self.dr[i] + self.dr[i + 1])
                        Gf = k_face * (r_face * dtheta * dz) / d_centres
                    couple(p, e, Gf)

        # --- azimuthal faces (only if resolved) -------------------------
        if Nth > 1:
            for l in range(Nz):
                for i in range(Nr):
                    for j in range(Nth):
                        p = self.idx(i, j, l)
                        q = self.idx(i, (j + 1) % Nth, l)
                        k_face = self._harmonic(self._kmat(i, T[p]),
                                                self._kmat(i, T[q]))
                        Gf = k_face * (self.dr[i] * dz) / (self.rc[i] * dtheta)
                        couple(p, q, Gf)

        # --- axial faces -------------------------------------------------
        for l in range(Nz - 1):
            for j in range(Nth):
                for i in range(Nr):
                    p, t = self.idx(i, j, l), self.idx(i, j, l + 1)
                    k_face = self._harmonic(self._kmat(i, T[p]),
                                            self._kmat(i, T[t]))
                    Gf = k_face * self.Art[i] / dz
                    couple(p, t, Gf)

        # --- outer radial boundary --------------------------------------
        if self.outer_bc != "adiabatic":
            i = Nr - 1
            r_s = g.r_clad_outer if self.include_clad else g.r_fuel
            dr_half = self.dr[i] / 2
            for l in range(Nz):
                for j in range(Nth):
                    p = self.idx(i, j, l)
                    area = r_s * dtheta * dz
                    g_half = self._kmat(i, T[p]) * area / dr_half
                    if self.outer_bc == "robin":
                        g_conv = self.h_z[l] * area
                        G_out = 1.0 / (1.0 / g_half + 1.0 / g_conv)
                        T_bc = self.Tcool_z[l]
                    else:  # dirichlet
                        G_out = g_half
                        T_bc = self.T_surface
                    diag[p] += G_out
                    b[p] += G_out * T_bc

        # --- axial end boundaries ---------------------------------------
        if self.axial_bc == "dirichlet":
            for end_l in (0, Nz - 1):
                for j in range(Nth):
                    for i in range(Nr):
                        p = self.idx(i, j, end_l)
                        g_end = self._kmat(i, T[p]) * self.Art[i] / (dz / 2)
                        diag[p] += g_end
                        b[p] += g_end * self.T_end

        # --- transient capacitance --------------------------------------
        if cap_over_dt is not None:
            diag += cap_over_dt
            b += cap_over_dt * T_old

        # assemble sparse matrix
        rows.extend(range(self.N))
        cols.extend(range(self.N))
        data.extend(diag.tolist())
        A = sp.csr_matrix((data, (rows, cols)), shape=(self.N, self.N))
        return A, b

    def _capacitance(self, T: np.ndarray) -> np.ndarray:
        cap = np.empty(self.N)
        for l in range(self.n_axial):
            for j in range(self.n_theta):
                for i in range(self.Nr):
                    mat = self.fuel if i < self.n_fuel else self.clad
                    p = self.idx(i, j, l)
                    cap[p] = mat.rho * mat.cp(T[p]) * self.vol[i]
        return cap

    # ------------------------------------------------------------------ #
    # solvers
    # ------------------------------------------------------------------ #
    def solve_steady(self, T_guess=None, tol: float = 1e-7,
                     max_iter: int = 100) -> np.ndarray:
        T = (np.full(self.N, float(np.mean(self.Tcool_z)))
             if T_guess is None else T_guess.copy())
        for _ in range(max_iter):
            A, b = self._assemble(T)
            T_new = spsolve(A, b)
            if np.max(np.abs(T_new - T)) < tol:
                return T_new
            T = T_new
        return T

    def step(self, T_old, dt, tol: float = 1e-7, max_iter: int = 100):
        T = T_old.copy()
        for _ in range(max_iter):
            cap_over_dt = self._capacitance(T) / dt
            A, b = self._assemble(T, cap_over_dt, T_old)
            T_new = spsolve(A, b)
            if np.max(np.abs(T_new - T)) < tol:
                return T_new
            T = T_new
        return T

    def solve_transient(self, T0, dt, t_end, store_every: int = 1):
        n_steps = int(round(t_end / dt))
        times, hist = [0.0], [T0.copy()]
        T = T0.copy()
        for s in range(1, n_steps + 1):
            T = self.step(T, dt)
            if s % store_every == 0 or s == n_steps:
                times.append(s * dt)
                hist.append(T.copy())
        return np.array(times), np.array(hist)

    # ------------------------------------------------------------------ #
    # views / diagnostics
    # ------------------------------------------------------------------ #
    def reshape(self, T: np.ndarray) -> np.ndarray:
        """Return T as a (Nz, Ntheta, Nr) array for convenient slicing."""
        return T.reshape(self.n_axial, self.n_theta, self.Nr)

    def z_centers(self) -> np.ndarray:
        return (np.arange(self.n_axial) + 0.5) * self.dz

    def centerline(self, T: np.ndarray, j: int = 0) -> np.ndarray:
        """Fuel centreline temperature vs elevation (K)."""
        return self.reshape(T)[:, j, 0]

    def clad_outer(self, T: np.ndarray, j: int = 0) -> np.ndarray:
        return self.reshape(T)[:, j, -1]

    def heat_out(self, T: np.ndarray) -> float:
        """Total heat leaving the outer radial surface (W)."""
        if self.outer_bc == "adiabatic":
            return 0.0
        g = self.geom
        i = self.Nr - 1
        r_s = g.r_clad_outer if self.include_clad else g.r_fuel
        dr_half = self.dr[i] / 2
        Tr = self.reshape(T)
        total = 0.0
        for l in range(self.n_axial):
            for j in range(self.n_theta):
                Tp = Tr[l, j, i]
                area = r_s * self.dtheta * self.dz
                g_half = self._kmat(i, Tp) * area / dr_half
                if self.outer_bc == "robin":
                    g_conv = self.h_z[l] * area
                    G_out = 1.0 / (1.0 / g_half + 1.0 / g_conv)
                    T_bc = self.Tcool_z[l]
                else:
                    G_out, T_bc = g_half, self.T_surface
                total += G_out * (Tp - T_bc)
        return total

    def heat_generated(self) -> float:
        """Total fission power in the modelled pin (W)."""
        per_z = self.q_vol_z * float(np.sum(self.vol[: self.n_fuel])) * self.n_theta
        return float(np.sum(per_z))


# --------------------------------------------------------------------------- #
# coupling helper and analytic references
# --------------------------------------------------------------------------- #
def from_channel(channel, n_fuel: int = 40, n_clad: int = 8,
                 n_theta: int = 1, h_gap: float | None = None,
                 axial_bc: str = "adiabatic") -> Conduction3D:
    """Build a Conduction3D whose axial grid and boundary inputs come from a
    solved CoolantChannel (q'(z) -> q'''(z), T_coolant(z), h(z))."""
    sol = channel.solve()
    if h_gap is None:
        h_gap = pwr_nominal().h_gap
    q_vol_z = channel.geom.q_volumetric_from_linear(sol.q_linear)
    return Conduction3D(
        geom=channel.geom, h_gap=h_gap,
        q_volumetric=q_vol_z, T_coolant=sol.T_coolant, h_coolant=sol.h,
        n_fuel=n_fuel, n_clad=n_clad, n_theta=n_theta,
        n_axial=channel.n_axial, height=channel.axial.height,
        axial_bc=axial_bc,
    )


def analytic_axial_profile(z, q_volumetric: float, height: float,
                           k: float, T_end: float):
    """1D slab conduction with uniform generation and fixed ends:
    T(z) = T_end + q''' z (H - z) / (2k);  peak q''' H^2 / (8k) at z = H/2."""
    z = np.asarray(z, dtype=float)
    return T_end + q_volumetric * z * (height - z) / (2.0 * k)
