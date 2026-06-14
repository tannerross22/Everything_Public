"""Phase-1 validation gates for the point kinetics solver.

Each test checks the numerical solver against an analytic result:
  * zero reactivity         -> steady state (the equilibrium IC is truly at rest)
  * step reactivity         -> asymptotic period matches the inhour-equation root
  * sub-prompt step         -> initial jump matches the prompt-jump approximation
  * negative step           -> power decays with the inhour-predicted period
  * precursor consistency   -> equilibrium relation C_i = beta_i n / (Lambda lambda_i)

Run under pytest for the validation gates, or run the file directly
(`python tests/test_point_kinetics.py`) to be prompted to plot the headline
result -- the power transient versus the analytic inhour period.
"""
import sys
from pathlib import Path

# Allow `import reactorsim` when this file is run directly (pytest uses conftest).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pytest

from reactorsim.params.kinetics import u235
from reactorsim.neutronics import point_kinetics as pk


@pytest.fixture
def p():
    return u235()


def test_equilibrium_is_at_rest(p):
    """With rho = 0 the equilibrium state must have dy/dt = 0."""
    y0 = pk.equilibrium_state(p, n0=1.0)
    dydt = pk.prke_rhs(0.0, y0, pk.constant_reactivity(0.0), p)
    assert np.allclose(dydt, 0.0, atol=1e-12)


def test_steady_state_holds(p):
    """Integrating with zero reactivity keeps power flat."""
    res = pk.solve(pk.constant_reactivity(0.0), (0.0, 100.0), p,
                   t_eval=np.linspace(0, 100, 50))
    assert res.success
    assert np.allclose(res.n, 1.0, rtol=1e-6, atol=1e-8)


def test_precursor_equilibrium_relation(p):
    """The equilibrium IC satisfies C_i = beta_i n / (Lambda lambda_i)."""
    n0 = 3.0
    y0 = pk.equilibrium_state(p, n0=n0)
    C = y0[1:]
    expected = p.beta_i * n0 / (p.Lambda * p.lambda_i)
    assert np.allclose(C, expected, rtol=1e-12)


@pytest.mark.parametrize("rho", [0.0005, 0.001, 0.002])
def test_positive_step_period_matches_inhour(p, rho):
    """Asymptotic growth rate matches the dominant inhour root for a step."""
    omega = pk.stable_period_omega(rho, p)
    assert omega > 0

    # Integrate ~8 time constants so the single growing mode dominates, then
    # fit the slope of ln(n) over the asymptotic tail (last 40%).
    t_end = 8.0 / omega
    t_eval = np.linspace(0.6 * t_end, t_end, 300)
    res = pk.solve(pk.step_reactivity(rho), (0.0, t_end), p, t_eval=t_eval)
    assert res.success

    slope = np.polyfit(res.t, np.log(res.n), 1)[0]
    assert slope == pytest.approx(omega, rel=1e-3)


@pytest.mark.parametrize("rho", [-0.0005, -0.002])
def test_negative_step_period_matches_inhour(p, rho):
    """For negative reactivity power decays at the inhour-predicted rate.

    The asymptotic (slowest) decay mode only emerges after the faster modes
    have died away, so we integrate many time constants of the dominant mode
    before fitting.
    """
    omega = pk.stable_period_omega(rho, p)
    assert omega < 0

    # The next-fastest decay mode is only ~1.8x faster than the dominant one,
    # so it lingers; integrate ~16 time constants and fit only the clean tail.
    t_end = 16.0 / abs(omega)
    t_eval = np.linspace(0.75 * t_end, t_end, 300)
    res = pk.solve(pk.step_reactivity(rho), (0.0, t_end), p, t_eval=t_eval,
                   atol=1e-14)
    assert res.success

    slope = np.polyfit(res.t, np.log(res.n), 1)[0]
    assert slope == pytest.approx(omega, rel=1e-3)


def test_prompt_jump_approximation(p):
    """Just after a sub-prompt step, n/n0 ~= beta / (beta - rho).

    The prompt-jump approximation assumes precursors are momentarily frozen.
    It is accurate only shortly after insertion, so we sample at a small time
    and allow a few-percent tolerance.
    """
    rho = 0.002  # ~0.31$, comfortably sub-prompt (rho < beta)
    res = pk.solve(pk.step_reactivity(rho), (0.0, 0.3), p,
                   t_eval=np.array([0.1]))
    assert res.success
    predicted = p.beta / (p.beta - rho)
    assert res.n[0] == pytest.approx(predicted, rel=0.05)


def test_jacobian_matches_finite_difference(p):
    """Analytic Jacobian agrees with a finite-difference approximation."""
    rho_fn = pk.constant_reactivity(0.001)
    y = pk.equilibrium_state(p, n0=2.0)
    J_analytic = pk.prke_jacobian(0.0, y, rho_fn, p)

    f0 = pk.prke_rhs(0.0, y, rho_fn, p)
    J_fd = np.zeros_like(J_analytic)
    for j in range(y.size):
        dy = np.zeros_like(y)
        h = 1e-6 * max(abs(y[j]), 1.0)
        dy[j] = h
        J_fd[:, j] = (pk.prke_rhs(0.0, y + dy, rho_fn, p) - f0) / h

    assert np.allclose(J_analytic, J_fd, rtol=1e-4, atol=1e-3)


# --------------------------------------------------------------------------- #
# Visualization of the headline result (not a pytest test)
# --------------------------------------------------------------------------- #
def plot_inhour_validation(rho: float = 0.0015):
    """Plot the most important Phase-1 takeaway: the numerically integrated
    power transient for a step reactivity insertion lies exactly on the
    analytic inhour period.

    The reactor power n(t) is shown on a log axis (a straight line there means
    a constant period). Overlaid are the analytic inhour asymptote e^{omega t}
    and the prompt-jump level beta/(beta - rho). Their agreement with the
    solver curve is the validation.
    """
    import matplotlib.pyplot as plt

    p = u235()
    omega = pk.stable_period_omega(rho, p)
    period = 1.0 / omega

    t_end = 8.0 / omega
    t_eval = np.linspace(0.0, t_end, 600)
    res = pk.solve(pk.step_reactivity(rho), (0.0, t_end), p, t_eval=t_eval)

    prompt_jump = p.beta / (p.beta - rho)
    # Inhour asymptote anchored to the late-time solution so only the slope
    # (the period) is being compared, not an arbitrary amplitude.
    anchor = res.n[-1]
    asymptote = anchor * np.exp(omega * (res.t - res.t[-1]))

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.semilogy(res.t, res.n, lw=2, label="point-kinetics solver  n(t)")
    ax.semilogy(res.t, asymptote, "--", lw=1.5,
                label=f"inhour asymptote  e^(omega t),  T = {period:.1f} s")
    ax.axhline(prompt_jump, ls=":", color="gray",
               label=f"prompt jump  beta/(beta-rho) = {prompt_jump:.3f}")

    ax.set_xlabel("time  [s]")
    ax.set_ylabel("normalized power  n / n0")
    ax.set_title(
        f"Point kinetics validation: step rho = {rho:g} "
        f"({rho / p.beta:.2f}$),  U-235"
    )
    ax.legend(loc="upper left")
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    answer = input("Graph the point-kinetics validation result? [y/N]: ").strip().lower()
    if answer in ("y", "yes"):
        import matplotlib.pyplot as plt

        plot_inhour_validation()
        plt.show()
    else:
        print("Skipping plot. (Run `python -m pytest tests/` for the validation gates.)")
