"""Phase-1 demo: response of the point kinetics model to a step reactivity
insertion. Prints the prompt jump, the asymptotic period from the inhour
equation, and the measured late-time period for comparison.

Run from the project root:
    python scripts/run_step_insertion.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from reactorsim.params.kinetics import u235
from reactorsim.neutronics import point_kinetics as pk


def main() -> None:
    p = u235()
    rho = 0.0015  # delta-k/k, a sub-prompt step (rho < beta)

    omega = pk.stable_period_omega(rho, p)
    period = 1.0 / omega

    t_end = min(20.0 / omega, 400.0)
    t_eval = np.linspace(0.0, t_end, 500)
    res = pk.solve(pk.step_reactivity(rho), (0.0, t_end), p, t_eval=t_eval)

    prompt_jump_pred = p.beta / (p.beta - rho)
    late = res.t > 0.5 * t_end
    measured_omega = np.polyfit(res.t[late], np.log(res.n[late]), 1)[0]

    print("=" * 60)
    print(" Point kinetics -- step reactivity insertion (U-235)")
    print("=" * 60)
    print(f" beta (total delayed fraction) : {p.beta:.6f}")
    print(f" Lambda (generation time)      : {p.Lambda:.2e} s")
    print(f" inserted reactivity rho       : {rho:.6f}  ({rho / p.beta:.3f}$)")
    print("-" * 60)
    print(f" prompt-jump n/n0 (predicted)  : {prompt_jump_pred:.4f}")
    print(f" stable period (inhour)        : {period:.2f} s  (omega = {omega:.4e} /s)")
    print(f" measured late-time omega      : {measured_omega:.4e} /s")
    print(f" final power n(t_end)          : {res.n[-1]:.3e}  at t = {res.t[-1]:.1f} s")
    print(f" solver                        : {res.message}")
    print("=" * 60)


if __name__ == "__main__":
    main()
