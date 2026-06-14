"""Phase-6 validation gates for the control layer.

PID:        sign/zero behaviour, first-order tracking, anti-windup
Rod worth:  S-curve endpoints/monotonicity, differential-worth peak, inverse
Rod bank:   rate-limited motion
SCRAM:      trips and latches on power / temperature, drives rods in
Closed loop: power setpoint tracking; SCRAM shuts the reactor down
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pytest

from reactorsim.control.pid import PID
from reactorsim.control import rod_worth as rw
from reactorsim.control.rod_worth import ControlRodBank, black_bank, grey_bank
from reactorsim.control.scram import ScramSystem
from reactorsim.control.rod_banks import power_controller
from reactorsim.coupling.simulator import PlantSimulator


# --- PID ------------------------------------------------------------------ #
def test_pid_zero_error_zero_output():
    pid = PID(Kp=1.0, Ki=0.0, Kd=0.0, setpoint=5.0)
    assert pid.update(5.0, 0.1) == pytest.approx(0.0)


def test_pid_proportional_sign():
    pid = PID(Kp=2.0, setpoint=1.0)
    assert pid.update(0.5, 0.1) == pytest.approx(2.0 * 0.5)   # below setpoint -> +
    assert PID(Kp=2.0, setpoint=1.0).update(1.5, 0.1) < 0     # above -> -


def test_pid_tracks_first_order_plant():
    """PI control drives a simple first-order plant y' = -a y + b u to setpoint."""
    a, b = 0.5, 1.0
    pid = PID(Kp=2.0, Ki=1.0, setpoint=3.0)
    y, dt = 0.0, 0.05
    for _ in range(4000):
        u = pid.update(y, dt)
        y += dt * (-a * y + b * u)
    assert y == pytest.approx(3.0, abs=1e-2)


def test_pid_antiwindup_bounded_integral():
    """While saturated, the integral must not wind up without bound."""
    pid = PID(Kp=1.0, Ki=10.0, setpoint=100.0, out_min=-1.0, out_max=1.0)
    for _ in range(1000):
        out = pid.update(0.0, 0.1)
        assert out <= 1.0 + 1e-12
    # integral is held in check (would be ~1e5 without anti-windup)
    assert abs(pid.integral) < 10.0


# --- rod worth ------------------------------------------------------------ #
def test_integral_worth_endpoints_and_midpoint():
    W = 0.02
    assert rw.integral_worth(0.0, W) == pytest.approx(0.0)
    assert rw.integral_worth(1.0, W) == pytest.approx(W)
    assert rw.integral_worth(0.5, W) == pytest.approx(0.5 * W)


def test_integral_worth_monotonic():
    W = 0.02
    p = np.linspace(0, 1, 200)
    vals = np.array([rw.integral_worth(pi, W) for pi in p])
    assert np.all(np.diff(vals) >= -1e-15)


def test_differential_worth_peaks_midstroke():
    W = 0.02
    d = np.array([rw.differential_worth(pi, W) for pi in np.linspace(0, 1, 101)])
    assert np.argmax(d) == 50                      # peak at p = 0.5
    assert rw.differential_worth(0.0, W) == pytest.approx(0.0)
    assert rw.differential_worth(1.0, W) == pytest.approx(0.0, abs=1e-12)


def test_worth_inverse_roundtrip():
    W = 0.018
    for p in (0.1, 0.3, 0.5, 0.7, 0.9):
        Wp = rw.integral_worth(p, W)
        assert rw.insertion_for_worth(Wp, W) == pytest.approx(p, abs=1e-9)


def test_bank_rate_limit():
    bank = ControlRodBank("b", total_worth=0.02, position=0.5, max_speed=0.01)
    bank.move_toward(1.0, dt=1.0)                  # wants +0.5, limited to +0.01
    assert bank.position == pytest.approx(0.51)


def test_black_stronger_than_grey():
    assert black_bank().total_worth > grey_bank().total_worth


# --- SCRAM ---------------------------------------------------------------- #
def test_scram_trips_on_power_and_latches():
    s = ScramSystem(power_trip=1.5)
    meas = dict(power=1.0, T_fuel_avg=900.0, T_coolant=580.0)
    s.update(0.1, meas)
    assert not s.tripped
    meas["power"] = 1.6
    s.update(0.1, meas)
    assert s.tripped and "power" in s.trip_reason
    # latches even when the signal returns to normal
    meas["power"] = 1.0
    s.update(0.1, meas)
    assert s.tripped


def test_scram_trips_on_temperature_and_inserts():
    s = ScramSystem(T_fuel_trip=1200.0)
    meas = dict(power=1.0, T_fuel_avg=1300.0, T_coolant=580.0)
    rho0 = s.update(0.1, meas)
    assert s.tripped and "T_fuel" in s.trip_reason
    # rods drive in over time -> increasingly negative reactivity
    for _ in range(20):
        rho = s.update(0.1, meas)
    assert rho < rho0
    assert s.position == pytest.approx(1.0, abs=1e-6)


# --- closed loop ---------------------------------------------------------- #
def test_closed_loop_power_tracking():
    """Controller tracks a power setpoint reduction."""
    sim = PlantSimulator(); sim.initialize()
    ctrl = power_controller(setpoint=1.0)
    sp = lambda t: 1.0 if t < 10 else 0.85
    res = sim.run_controlled(t_end=200.0, dt=0.05, controller=ctrl, setpoint=sp)
    assert res.power[-1] == pytest.approx(0.85, abs=5e-3)
    assert not res.scram_tripped[-1]


def test_closed_loop_scram_shuts_down():
    """An over-power command trips SCRAM, which shuts the reactor down."""
    sim = PlantSimulator(); sim.initialize()
    from reactorsim.control.scram import ScramSystem
    ctrl = power_controller(setpoint=1.6, scram=ScramSystem(power_trip=1.4))
    res = sim.run_controlled(t_end=120.0, dt=0.05, controller=ctrl)
    assert res.scram_tripped[-1]
    assert res.power.max() <= 1.45                 # trip caps the excursion
    assert res.power[-1] < 0.05                    # shut down
    assert res.rho_total[-1] < -0.02              # deeply subcritical
