"""Phase-6.5 validation gates for the coupled axial plant + AO/power control.

  * coupled steady state holds (power and AO constant)
  * a top-bank insertion tilts the flux bottom-peaked (AO < 0), self-regulated
  * AO control drives the axial offset to a setpoint while holding power
  * power control tracks a power setpoint while holding AO near zero
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pytest

from reactorsim.coupling.axial_simulator import AxialPlantSimulator
from reactorsim.neutronics.spatial_kinetics import AxialKineticsModel
from reactorsim.control.axial_control import power_ao_controller


def _sim(n_axial=12):
    return AxialPlantSimulator(kinetics=AxialKineticsModel(n_axial=n_axial), p0=0.25)


def test_coupled_steady_state_holds():
    sim = _sim(); sim.initialize()
    res = sim.run_fixed(t_end=30.0, dt=0.1)
    assert res.power[-1] == pytest.approx(1.0, abs=2e-4)
    assert abs(res.axial_offset[-1]) < 1e-3


def test_top_bank_insertion_tilts_bottom():
    sim = _sim(); sim.initialize()
    res = sim.run_fixed(t_end=60.0, dt=0.1,
                        p_top=lambda t: 0.25 if t < 5 else 0.4, p_bottom=0.25)
    assert res.axial_offset[-1] < -0.01          # bottom-peaked
    assert res.power[-1] < 1.0                    # extra absorption lowers power


def test_ao_control_tracks_setpoint_holding_power():
    sim = _sim(); sim.initialize()
    ctrl = power_ao_controller(power_setpoint=1.0, ao_setpoint=0.0, p0=0.25)
    res = sim.run_controlled(
        t_end=250.0, dt=0.1, controller=ctrl,
        power_setpoint=lambda t: 1.0,
        ao_setpoint=lambda t: 0.0 if t < 10 else 0.1,
    )
    assert res.axial_offset[-1] == pytest.approx(0.1, abs=0.02)
    assert res.power[-1] == pytest.approx(1.0, abs=0.02)


def test_power_control_tracks_holding_ao():
    sim = _sim(); sim.initialize()
    ctrl = power_ao_controller(power_setpoint=1.0, ao_setpoint=0.0, p0=0.25)
    res = sim.run_controlled(
        t_end=250.0, dt=0.1, controller=ctrl,
        power_setpoint=lambda t: 1.0 if t < 10 else 0.9,
        ao_setpoint=lambda t: 0.0,
    )
    assert res.power[-1] == pytest.approx(0.9, abs=0.02)
    assert abs(res.axial_offset[-1]) < 0.03      # AO held near zero
