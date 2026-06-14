"""Phase-5 validation gates for the coupled neutronics+thermal simulator.

  * self-consistent init -> feedback is zero, reactor critical, power steady
  * steady state holds   -> no perturbation keeps n=1 and temperatures flat
  * self-regulation      -> +reactivity settles to a new critical equilibrium
                            where feedback cancels the insertion (rho_total->0)
  * overshoot            -> power peaks above its final value (thermal lag)
  * negative insertion   -> power and temperatures fall; feedback turns positive
  * Doppler dominance    -> fuel-temperature feedback supplies most of the effect
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pytest

from reactorsim.coupling.simulator import PlantSimulator


def _fresh():
    sim = PlantSimulator()
    sim.initialize()
    return sim


def test_initialization_is_critical_and_feedback_zero():
    sim = _fresh()
    assert sim.state[0] == pytest.approx(1.0, rel=1e-12)
    fb = sim.fb.feedback(sim.fb.T_fuel_ref, sim.fb.T_mod_ref)
    assert fb == pytest.approx(0.0, abs=1e-15)


def test_steady_state_holds():
    sim = _fresh()
    res = sim.run(t_end=40.0, dt=0.05, rho_rods=0.0)
    assert np.allclose(res.power, 1.0, atol=1e-5)
    assert abs(res.T_fuel_avg[-1] - res.T_fuel_avg[0]) < 0.01
    assert abs(res.T_coolant[-1] - res.T_coolant[0]) < 0.01


def test_self_regulation_to_new_equilibrium():
    """A positive reactivity insertion settles at a higher power where the
    negative temperature feedback exactly offsets it (reactor returns critical)."""
    rho_in = 1.0e-4
    sim = _fresh()
    res = sim.run(t_end=200.0, dt=0.05, rho_rods=rho_in)

    assert res.power[-1] > 1.0                       # settled above initial power
    assert abs(res.rho_total[-1]) < 3e-6             # back to ~critical
    assert res.rho_feedback[-1] == pytest.approx(-rho_in, rel=0.03)
    assert res.T_fuel_avg[-1] > res.T_fuel_avg[0]    # fuel hotter at higher power


def test_power_overshoots_before_settling():
    """Power rises quickly, then the slower fuel heating (Doppler) pulls it back,
    so the peak exceeds the final steady value."""
    sim = _fresh()
    res = sim.run(t_end=120.0, dt=0.05, rho_rods=1.5e-4)
    assert res.power.max() > res.power[-1] + 1e-4
    assert np.argmax(res.power) < len(res.power) - 1   # peak is not the last point


def test_negative_insertion_lowers_power_and_temperature():
    rho_in = -1.0e-4
    sim = _fresh()
    res = sim.run(t_end=200.0, dt=0.05, rho_rods=rho_in)

    assert res.power[-1] < 1.0
    assert res.T_fuel_avg[-1] < res.T_fuel_avg[0]
    assert res.rho_feedback[-1] > 0                  # positive feedback offsets
    assert abs(res.rho_total[-1]) < 3e-6


def test_doppler_supplies_most_of_the_feedback():
    """With the default coefficients, the prompt fuel (Doppler) feedback is the
    dominant contributor to offsetting an insertion."""
    sim = _fresh()
    res = sim.run(t_end=200.0, dt=0.05, rho_rods=1.0e-4)
    fuel_term = sim.fb.alpha_fuel * (res.T_fuel_avg[-1] - sim.fb.T_fuel_ref)
    mod_term = sim.fb.alpha_mod * (res.T_coolant[-1] - sim.fb.T_mod_ref)
    assert abs(fuel_term) > abs(mod_term)
