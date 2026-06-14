"""Phase-6.5 validation gates for the 1D axial spatial kinetics.

  * criticality search   -> reference k_eff = 1
  * fundamental mode      -> symmetric cosine, AO ~ 0
  * steady state holds     -> flux and power constant at the reference
  * reduces to point kinetics -> uniform insertion matches the point-kinetics model
  * rod worth              -> monotonic, S-curve-like, full insertion calibrated
  * rod insertion tilts flux -> top rod gives bottom-peaked flux (AO < 0)
  * axial offset           -> correct sign for a constructed top-heavy shape
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pytest
from scipy.linalg import eigh

from reactorsim.neutronics.spatial_kinetics import AxialKineticsModel
from reactorsim.neutronics import point_kinetics as pk
from reactorsim.params.kinetics import u235


def test_criticality_search():
    m = AxialKineticsModel(n_axial=20)
    assert m.k_ref == pytest.approx(1.0, abs=1e-9)


def test_fundamental_mode_symmetric_cosine():
    m = AxialKineticsModel(n_axial=20)
    phi = m.phi_ref
    assert m.axial_offset(phi) == pytest.approx(0.0, abs=1e-9)
    zc = m.z - m.height / 2
    cos = np.cos(np.pi * zc / (m.height + 2 * m.extrapolation))
    cos /= cos.mean()
    assert np.max(np.abs(phi - cos) / cos) < 2e-3


def test_steady_state_holds():
    m = AxialKineticsModel(n_axial=16)
    y = m.initial_state()
    sig = m.Sigma_a * np.ones(m.n_axial)
    for _ in range(100):
        y = m.advance(y, sig, 0.05)
    phi, _ = m.split(y)
    assert m.total_power(phi) == pytest.approx(1.0, rel=1e-6)
    assert abs(m.axial_offset(phi)) < 1e-9


def test_reduces_to_point_kinetics():
    """A spatially uniform reactivity insertion reproduces point kinetics."""
    m = AxialKineticsModel(n_axial=16)
    p = u235()
    rho = 0.0015
    sig = m.Sigma_a * np.ones(m.n_axial) - rho * m.nuSigma_f
    assert m.reactivity(sig) == pytest.approx(rho, rel=1e-4)

    ts = np.arange(0, 20.001, 0.02)
    y = m.initial_state()
    P = []
    for _ in ts:
        P.append(m.total_power(m.split(y)[0]))
        y = m.advance(y, sig, 0.02)
    ref = pk.solve(pk.step_reactivity(rho), (0, 20), p, t_eval=ts)
    assert P[-1] == pytest.approx(ref.n[-1], rel=1e-3)


def test_rod_worth_monotonic_and_calibrated():
    m = AxialKineticsModel(n_axial=20)
    W = 0.02
    worths = []
    for pos in np.linspace(0.1, 1.0, 10):
        sig = m.Sigma_a * np.ones(m.n_axial) + m.rod_sigma(pos, W, from_top=True)
        worths.append(-m.reactivity(sig))
    worths = np.array(worths)
    assert np.all(np.diff(worths) > 0)                  # monotonic
    assert worths[-1] == pytest.approx(W, rel=0.02)     # full insertion calibrated


def test_rod_insertion_tilts_flux():
    """Inserting a bank from the top suppresses the upper flux -> AO < 0."""
    m = AxialKineticsModel(n_axial=20)
    sig = m.Sigma_a * np.ones(m.n_axial) + m.rod_sigma(0.4, 0.02, from_top=True)
    M = np.diag(sig) - m.D * m.Lap
    _, evecs = eigh(M)
    phi = evecs[:, 0]
    if phi.mean() < 0:
        phi = -phi
    assert m.axial_offset(phi) < -1e-3


def test_axial_offset_sign():
    m = AxialKineticsModel(n_axial=10)
    phi = np.ones(10)
    assert m.axial_offset(phi) == pytest.approx(0.0, abs=1e-12)
    phi_top = np.linspace(0.5, 1.5, 10)     # increasing with z = top-heavy
    assert m.axial_offset(phi_top) > 0
