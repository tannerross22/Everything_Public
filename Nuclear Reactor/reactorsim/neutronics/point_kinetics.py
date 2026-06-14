"""Point reactor kinetics equations (PRKE) with six delayed-neutron groups.

State vector y = [n, C_1, ..., C_G] where
    n    -- neutron population (proportional to reactor power), normalized
    C_i  -- delayed-neutron precursor concentration of group i (same units as n)

Governing equations
-------------------
    dn/dt   = (rho(t) - beta)/Lambda * n + sum_i lambda_i * C_i
    dC_i/dt = beta_i/Lambda * n - lambda_i * C_i

Reactivity rho(t, n) is supplied as a callable so the source is pluggable:
constant / step / ramp inputs for Phase-1 validation now, temperature feedback
in Phase 5. The system is stiff (timescales from Lambda ~ 1e-5 s to the slowest
precursor ~ 80 s), so we integrate with an implicit method (BDF) and supply the
analytic Jacobian to keep the solver fast and accurate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.integrate import solve_ivp

from ..params.kinetics import KineticsParams

# A reactivity driver maps (t, n) -> rho. n is passed so feedback models (which
# depend on power/temperature) can use it later; pure time inputs ignore it.
ReactivityFn = Callable[[float, float], float]


# --------------------------------------------------------------------------- #
# Reactivity input drivers (Phase-1 validation helpers)
# --------------------------------------------------------------------------- #
def constant_reactivity(rho: float) -> ReactivityFn:
    """rho(t) = rho for all t."""
    def fn(t: float, n: float) -> float:
        return rho
    return fn


def step_reactivity(rho: float, t_step: float = 0.0) -> ReactivityFn:
    """Zero before t_step, then a constant rho (a step insertion)."""
    def fn(t: float, n: float) -> float:
        return rho if t >= t_step else 0.0
    return fn


def ramp_reactivity(rate: float, t_start: float = 0.0, rho_max: float | None = None) -> ReactivityFn:
    """Linear ramp rho = rate*(t - t_start), optionally clipped at rho_max."""
    def fn(t: float, n: float) -> float:
        if t < t_start:
            return 0.0
        rho = rate * (t - t_start)
        if rho_max is not None:
            rho = min(rho, rho_max) if rate >= 0 else max(rho, rho_max)
        return rho
    return fn


# --------------------------------------------------------------------------- #
# Core PRKE right-hand side and Jacobian
# --------------------------------------------------------------------------- #
def prke_rhs(t: float, y: np.ndarray, rho_fn: ReactivityFn, p: KineticsParams) -> np.ndarray:
    """Right-hand side dy/dt of the point kinetics system."""
    n = y[0]
    C = y[1:]
    rho = rho_fn(t, n)

    dn = (rho - p.beta) / p.Lambda * n + np.dot(p.lambda_i, C)
    dC = p.beta_i / p.Lambda * n - p.lambda_i * C
    return np.concatenate(([dn], dC))


def prke_jacobian(t: float, y: np.ndarray, rho_fn: ReactivityFn, p: KineticsParams) -> np.ndarray:
    """Analytic Jacobian d(dy/dt)/dy.

    Treats rho as locally independent of n (exact for the prescribed-input
    drivers used in Phase 1; an acceptable approximation for the implicit
    solver's Newton iterations once feedback is added).
    """
    G = p.n_groups
    J = np.zeros((G + 1, G + 1))
    rho = rho_fn(t, y[0])

    # d(dn)/dn and d(dn)/dC_i
    J[0, 0] = (rho - p.beta) / p.Lambda
    J[0, 1:] = p.lambda_i

    # d(dC_i)/dn and d(dC_i)/dC_i
    J[1:, 0] = p.beta_i / p.Lambda
    J[1:, 1:] = np.diag(-p.lambda_i)
    return J


# --------------------------------------------------------------------------- #
# Initial condition and solver wrapper
# --------------------------------------------------------------------------- #
def equilibrium_state(p: KineticsParams, n0: float = 1.0) -> np.ndarray:
    """Critical steady state at power level n0.

    Setting dC_i/dt = 0 gives C_i = beta_i * n0 / (Lambda * lambda_i). With
    rho = 0 this also makes dn/dt = 0, so the system starts truly at rest.
    """
    C = p.beta_i * n0 / (p.Lambda * p.lambda_i)
    return np.concatenate(([n0], C))


@dataclass
class KineticsResult:
    """Solver output. t shape (N,); n shape (N,); precursors shape (G, N)."""
    t: np.ndarray
    n: np.ndarray
    precursors: np.ndarray
    success: bool
    message: str


def solve(
    rho_fn: ReactivityFn,
    t_span: tuple[float, float],
    p: KineticsParams,
    y0: np.ndarray | None = None,
    n0: float = 1.0,
    t_eval: np.ndarray | None = None,
    method: str = "BDF",
    rtol: float = 1e-8,
    atol: float = 1e-10,
    max_step: float | None = None,
) -> KineticsResult:
    """Integrate the point kinetics equations over t_span.

    Parameters
    ----------
    rho_fn : ReactivityFn
        Reactivity driver, rho(t, n).
    t_span : (t0, t1)
        Integration interval (s).
    p : KineticsParams
        Delayed-neutron data and generation time.
    y0 : ndarray, optional
        Initial state. Defaults to the critical equilibrium at n0.
    n0 : float
        Power level used to build the default equilibrium initial condition.
    t_eval : ndarray, optional
        Times at which to store the solution.
    method : str
        scipy solver; 'BDF' or 'Radau' recommended for this stiff system.
    """
    if y0 is None:
        y0 = equilibrium_state(p, n0=n0)

    kwargs = dict(
        fun=prke_rhs,
        t_span=t_span,
        y0=y0,
        method=method,
        jac=prke_jacobian,
        args=(rho_fn, p),
        rtol=rtol,
        atol=atol,
        dense_output=False,
    )
    if t_eval is not None:
        kwargs["t_eval"] = t_eval
    if max_step is not None:
        kwargs["max_step"] = max_step

    sol = solve_ivp(**kwargs)
    return KineticsResult(
        t=sol.t,
        n=sol.y[0],
        precursors=sol.y[1:],
        success=sol.success,
        message=sol.message,
    )


# --------------------------------------------------------------------------- #
# Inhour equation -- the analytic reference used for validation
# --------------------------------------------------------------------------- #
def inhour(omega: float, p: KineticsParams) -> float:
    """Reactivity rho corresponding to a stable inverse period omega.

        rho = omega*Lambda + sum_i [ beta_i * omega / (omega + lambda_i) ]

    Inverting this (solving inhour(omega) = rho for omega) gives the asymptotic
    reactor period 1/omega for a step reactivity rho -- the textbook benchmark.
    """
    return omega * p.Lambda + np.sum(p.beta_i * omega / (omega + p.lambda_i))


def stable_period_omega(rho: float, p: KineticsParams) -> float:
    """Dominant (largest real) root omega of the inhour equation for step rho.

    On the interval omega > -lambda_min the inhour function is smooth and
    monotonically increasing, running from -inf (as omega -> -lambda_min from
    above) through 0 (at omega = 0) to +inf. It therefore contains exactly one
    root for any rho, and that root is the largest of all seven -- the mode that
    governs the asymptotic period.

    For rho > 0 the root is positive (unbounded above, so we expand the bracket
    until it straddles the root); for rho < 0 it lies in (-lambda_min, 0).
    """
    from scipy.optimize import brentq

    lam_min = float(np.min(p.lambda_i))
    eps = 1e-12

    if rho == 0:
        return 0.0

    f = lambda w: inhour(w, p) - rho

    if rho > 0:
        lo = eps
        hi = max(lam_min, 1e-6)
        while f(hi) < 0:           # expand until inhour exceeds rho
            hi *= 2.0
    else:
        lo = -lam_min + eps
        hi = -eps

    return brentq(f, lo, hi, xtol=1e-15, rtol=1e-14, maxiter=200)
