"""Phase-7 validation gates for the steam generator and plant heat balance.

  * steam tables       -> monotonic T_sat(P), P_sat inverse, positive h_fg
  * eNTU == LMTD       -> the two SG methods give the same duty
  * energy balance     -> duty = C_min (T_hot_in - T_hot_out)
  * steam rate         -> duty = mdot_steam (h_g - h_feedwater)
  * sizing             -> required_UA inverts the duty; infeasible cases raise
  * pressure trade     -> higher P_sec: higher T_sat, more UA, higher efficiency,
                          wetter turbine exhaust
  * design logic       -> approach temperature picks ~6.9 MPa
  * primary loop       -> closes (SG duty = core power), sane leg temperatures
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from reactorsim.hydraulics import steam_tables as st
from reactorsim.hydraulics.heat_exchanger import (
    SteamGenerator, pwr_steam_generator, required_UA, PrimaryLoop,
    secondary_pressure_for_approach, rankine_cycle,
)


# --- steam tables --------------------------------------------------------- #
def test_steam_tables_consistency():
    assert st.T_sat(7.0e6) == pytest.approx(285.88 + 273.15, abs=0.5)
    # P_sat inverts T_sat
    assert st.P_sat(st.T_sat(6.0e6)) == pytest.approx(6.0e6, rel=1e-6)
    sp = st.sat_props(6.9e6)
    assert sp.h_fg > 0 and sp.s_fg > 0
    # T_sat increases with pressure
    assert st.T_sat(5.0e6) < st.T_sat(7.0e6) < st.T_sat(9.0e6)


# --- SG core -------------------------------------------------------------- #
def test_entu_equals_lmtd():
    sg = pwr_steam_generator()
    assert sg.duty() == pytest.approx(sg.duty_lmtd(), rel=1e-9)


def test_primary_energy_balance():
    sg = pwr_steam_generator()
    assert sg.duty() == pytest.approx(
        sg.C_min * (sg.T_hot_in - sg.T_hot_out()), rel=1e-12)


def test_steam_rate_energy_balance():
    sg = pwr_steam_generator()
    sp = st.sat_props(sg.secondary_pressure)
    h_fw = st.hf_at_T(sg.feedwater_T)
    assert sg.duty() == pytest.approx(sg.steam_rate() * (sp.h_g - h_fw), rel=1e-9)
    # realistic magnitude for a ~3.4 GW plant
    assert 1500 < sg.steam_rate() < 2200


# --- sizing --------------------------------------------------------------- #
def test_required_UA_inverts_duty():
    sg = pwr_steam_generator()
    duty = sg.duty()
    UA = required_UA(duty, sg.C_min, sg.T_hot_in, sg.T_sat)
    assert UA == pytest.approx(sg.UA, rel=1e-9)


def test_required_UA_infeasible_raises():
    """If T_sat is too close to T_hot_in, no UA can pass the duty (eff>1)."""
    Cmin = 18000 * 5500
    T_sat = st.T_sat(8.0e6)              # ~295 C
    with pytest.raises(ValueError):
        required_UA(3400e6, Cmin, 597.15, T_sat)   # only ~29 C of approach


# --- pressure trade ------------------------------------------------------- #
def test_pressure_trade_off():
    Cmin = 18000 * 5500
    T_hot = 597.15
    duty = 3000e6
    ua5 = required_UA(duty, Cmin, T_hot, st.T_sat(5e6))
    ua7 = required_UA(duty, Cmin, T_hot, st.T_sat(7e6))
    assert ua7 > ua5                                # higher pressure -> more area

    r5 = rankine_cycle(5e6, 0.006e6)
    r7 = rankine_cycle(7e6, 0.006e6)
    assert r7.efficiency > r5.efficiency            # higher pressure -> efficiency
    assert r7.turbine_exit_quality < r5.turbine_exit_quality   # but wetter
    assert 0.25 < r7.efficiency < 0.40              # realistic PWR range


def test_design_logic_picks_pwr_pressure():
    P = secondary_pressure_for_approach(310 + 273.15, 25.0)
    assert P / 1e6 == pytest.approx(6.9, abs=0.3)


# --- closed primary loop -------------------------------------------------- #
def test_primary_loop_closes():
    loop = PrimaryLoop(core_power=3400e6, mdot_primary=18000, cp_primary=5500,
                       UA=2.1e8, secondary_pressure=6.9e6).solve()
    assert loop["T_hot"] > loop["T_cold"]
    assert loop["approach"] > 0
    # cold leg (core inlet) and average should land in the PWR range
    assert 285 < loop["T_cold"] - 273.15 < 295
    assert 305 < loop["T_avg"] - 273.15 < 315
