"""Phase-4 validation gates for the 3D (r, theta, z) conduction solver.

  * reduce to 1D     -> a single z-slice reproduces the Phase-2 radial model
  * uniform source   -> all z-slices identical (axial conduction inert)
  * energy balance   -> steady, adiabatic ends: heat out = heat generated
  * axisymmetry      -> with Ntheta>1 and symmetric BC, all theta-slices equal
  * axial conduction -> 1D slab with generation matches the analytic z-parabola
  * axial smoothing  -> coupling lowers the mid-plane peak vs Phase-3 stacked
  * transient        -> relaxes to the steady-state solution
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pytest

from reactorsim.params.geometry import pwr_17x17
from reactorsim.params.materials import constant_material
from reactorsim.params.plant import CoolantBC
from reactorsim.thermal.conduction1d import RadialPinModel
from reactorsim.thermal import conduction3d as c3d
from reactorsim.thermal.conduction3d import Conduction3D, from_channel
from reactorsim.hydraulics.coolant_channel import pwr_channel, solve_pin_channel


def test_reduce_to_1d():
    """A single axial slice with adiabatic ends must match the 1D solver."""
    g = pwr_17x17()
    q = g.q_volumetric_from_linear(17.8e3)
    m1 = RadialPinModel(geom=g, q_volumetric=q,
                        coolant=CoolantBC(h=37000.0, T_inf=580.0))
    T1 = m1.solve_steady()

    m3 = Conduction3D(geom=g, q_volumetric=q, T_coolant=580.0,
                      h_coolant=37000.0, n_axial=1)
    T3 = m3.solve_steady()
    assert np.max(np.abs(T3 - T1)) < 1e-6


def test_uniform_source_axial_invariant():
    """With uniform source and uniform coolant BC, axial conduction carries no
    heat and every z-slice is identical (and equals the 1D solution)."""
    g = pwr_17x17()
    q = g.q_volumetric_from_linear(20.0e3)
    m3 = Conduction3D(geom=g, q_volumetric=q, T_coolant=580.0,
                      h_coolant=35000.0, n_axial=12)
    T = m3.reshape(m3.solve_steady())   # (Nz, Ntheta, Nr)
    ref = T[0, 0]
    for l in range(m3.n_axial):
        assert np.max(np.abs(T[l, 0] - ref)) < 1e-7


def test_energy_balance():
    """Steady state with adiabatic ends: surface heat-out equals generation."""
    c3 = from_channel(pwr_channel())
    T = c3.solve_steady()
    assert c3.heat_out(T) == pytest.approx(c3.heat_generated(), rel=1e-6)


def test_axisymmetry():
    """Resolving the azimuth (Ntheta>1) with symmetric BC leaves every angular
    slice identical."""
    g = pwr_17x17()
    q = g.q_volumetric_from_linear(18.0e3)
    m = Conduction3D(geom=g, q_volumetric=q, T_coolant=580.0, h_coolant=35000.0,
                     n_axial=4, n_theta=4)
    T = m.reshape(m.solve_steady())     # (Nz, Ntheta, Nr)
    for j in range(1, m.n_theta):
        assert np.max(np.abs(T[:, j, :] - T[:, 0, :])) < 1e-7


def test_axial_conduction_matches_analytic_slab():
    """Pure axial conduction (single radial cell, adiabatic outer, fixed ends,
    constant k, uniform generation) matches T(z)=T_end+q''' z(H-z)/(2k)."""
    g = pwr_17x17()
    k = 3.6
    q = 1.0e4
    H = 1.0
    T_end = 580.0
    m = Conduction3D(
        geom=g, fuel=constant_material("c", k=k, rho=10400.0, cp=300.0),
        q_volumetric=q, n_fuel=1, include_clad=False, n_axial=80, height=H,
        outer_bc="adiabatic", axial_bc="dirichlet", T_end=T_end,
    )
    T = m.solve_steady()
    z = m.z_centers()
    T_num = m.centerline(T)
    T_exact = c3d.analytic_axial_profile(z, q, H, k, T_end)
    assert np.max(np.abs(T_num - T_exact)) < 0.5      # K


def test_axial_conduction_lowers_peak_vs_stacked():
    """Axial conduction transports heat away from the hot mid-plane, so the 3D
    peak centreline is slightly below the Phase-3 stacked (uncoupled) peak.
    The effect is small for a long thin rod -- a real physical insight."""
    ch = pwr_channel()
    stacked = solve_pin_channel(ch)
    field3d = from_channel(ch)
    cl3 = field3d.centerline(field3d.solve_steady())

    peak_stacked = stacked.T_centerline.max()
    peak_3d = cl3.max()
    assert peak_3d < peak_stacked                      # axial conduction cools peak
    assert (peak_stacked - peak_3d) < 0.5              # but the effect is small
    assert np.max(np.abs(cl3 - stacked.T_centerline)) < 0.5


def test_transient_relaxes_to_steady():
    g = pwr_17x17()
    q = g.q_volumetric_from_linear(17.8e3)
    m = Conduction3D(geom=g, q_volumetric=q, T_coolant=580.0,
                     h_coolant=35000.0, n_axial=6)
    T_steady = m.solve_steady()
    T0 = np.full(m.N, 580.0)
    _, hist = m.solve_transient(T0, dt=0.1, t_end=40.0, store_every=100)
    assert np.max(np.abs(hist[-1] - T_steady)) < 1.0   # K
