"""Phase-2 validation gates for the 1D radial conduction solver.

Checks against analytic results and conservation laws:
  * constant-k pellet, Dirichlet surface -> matches T(r)=T_s+q'''(r_f^2-r^2)/(4k)
  * centreline rise                      -> q''' r_f^2 / (4k)
  * full pin steady state                -> energy balance (gen = heat out)
  * full pin                             -> temperature monotonically decreasing
  * transient                            -> relaxes to the steady-state solution
  * temperature-dependent k              -> hotter centre than constant-k(T_s)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pytest

from reactorsim.params.geometry import pwr_17x17
from reactorsim.params.materials import constant_material, uo2, zircaloy
from reactorsim.params.plant import pwr_nominal
from reactorsim.thermal import conduction1d as c1d
from reactorsim.thermal.conduction1d import RadialPinModel


def _const_k_fuel(k=3.6):
    return constant_material("UO2-const", k=k, rho=10400.0, cp=300.0)


def test_constant_k_matches_analytic_profile():
    """Pellet alone, constant k, fixed surface temperature: the full radial
    profile must match the parabolic analytic solution."""
    g = pwr_17x17()
    k = 3.6
    q = 3.0e8
    T_s = 580.0
    model = RadialPinModel(
        geom=g, fuel=_const_k_fuel(k), q_volumetric=q,
        n_fuel=80, include_clad=False, outer_bc="dirichlet", T_surface=T_s,
    )
    T = model.solve_steady()
    T_exact = c1d.analytic_profile(model.r_center, q, g.r_fuel, k, T_s)
    assert np.max(np.abs(T - T_exact)) < 0.5      # K, tightens with more cells


def test_centerline_rise_matches_analytic():
    """Centre-minus-surface rise matches q''' r_f^2 / (4k)."""
    g = pwr_17x17()
    k = 4.0
    q = 2.5e8
    T_s = 600.0
    model = RadialPinModel(
        geom=g, fuel=_const_k_fuel(k), q_volumetric=q,
        n_fuel=120, include_clad=False, outer_bc="dirichlet", T_surface=T_s,
    )
    T = model.solve_steady()
    rise = T[0] - T_s
    expected = c1d.analytic_centerline_rise(q, g.r_fuel, k)
    assert rise == pytest.approx(expected, rel=2e-3)


def test_full_stack_energy_balance():
    """At steady state, heat generated equals heat leaving the outer surface."""
    g = pwr_17x17()
    q = g.q_volumetric_from_linear(17.8e3)   # 17.8 kW/m average PWR rod
    model = RadialPinModel(geom=g, q_volumetric=q)  # full UO2/gap/Zircaloy stack
    T = model.solve_steady()
    assert model.heat_out(T) == pytest.approx(model.heat_generated(), rel=1e-6)


def test_full_stack_monotonic_decreasing():
    """Temperature decreases from centreline outward through fuel and clad."""
    g = pwr_17x17()
    q = g.q_volumetric_from_linear(20.0e3)
    model = RadialPinModel(geom=g, q_volumetric=q)
    T = model.solve_steady()
    assert np.all(np.diff(T) < 0)
    # Sanity: centreline well above coolant, surface only modestly above it.
    assert T[0] > 900.0
    assert T[-1] < T[0]
    assert T[-1] > pwr_nominal().T_inf


def test_transient_relaxes_to_steady():
    """Starting from a uniform field, the transient converges to solve_steady."""
    g = pwr_17x17()
    q = g.q_volumetric_from_linear(17.8e3)
    model = RadialPinModel(geom=g, q_volumetric=q)
    T_steady = model.solve_steady()

    T0 = np.full(model.N, pwr_nominal().T_inf)
    _, hist = model.solve_transient(T0, dt=0.05, t_end=40.0, store_every=50)
    T_final = hist[-1]
    assert np.max(np.abs(T_final - T_steady)) < 1.0   # K


def test_temperature_dependent_k_is_hotter():
    """With real UO2 k(T) (which falls as T rises), the centreline is hotter
    than a constant-k solve evaluated at the surface temperature."""
    g = pwr_17x17()
    q = g.q_volumetric_from_linear(25.0e3)

    real = RadialPinModel(geom=g, fuel=uo2(), q_volumetric=q)
    T_real = real.solve_steady()

    k_at_surface = uo2().k(T_real[real.n_fuel - 1])
    const = RadialPinModel(
        geom=g, fuel=_const_k_fuel(k_at_surface), q_volumetric=q,
    )
    T_const = const.solve_steady()
    assert T_real[0] > T_const[0]
