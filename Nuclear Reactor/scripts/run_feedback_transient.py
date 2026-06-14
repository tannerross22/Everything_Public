"""Phase-5 demo: coupled neutronics + thermal transient with reactivity feedback.

Starts a critical PWR at full power, inserts a small step of positive rod
reactivity, and shows the passive self-regulation: power overshoots, the fuel
heats, Doppler feedback pushes reactivity back down, and the plant settles at a
new steady power where feedback cancels the insertion.

Run from the project root:
    python scripts/run_feedback_transient.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from reactorsim.coupling.simulator import PlantSimulator

RHO_IN = 1.5e-4   # step reactivity insertion (delta-k/k); 15 pcm, ~0.023$


def simulate():
    sim = PlantSimulator()
    sim.initialize()
    res = sim.run(t_end=150.0, dt=0.05, rho_rods=RHO_IN)
    return sim, res


def report(sim, res) -> None:
    print("=" * 66)
    print(" Coupled feedback transient -- step reactivity insertion")
    print("=" * 66)
    print(f" inserted rho_rods       : {RHO_IN:.2e}  ({RHO_IN/sim.kin.beta:.3f}$)")
    print(f" peak power              : {res.power.max():.4f}  at t = {res.t[np.argmax(res.power)]:.2f} s")
    print(f" final power             : {res.power[-1]:.4f}")
    print("-" * 66)
    print(f" final feedback reactivity: {res.rho_feedback[-1]:.3e}  (offsets the insertion)")
    print(f" final total reactivity   : {res.rho_total[-1]:.3e}  (~0: back to critical)")
    print("-" * 66)
    print(f" fuel avg temp rise       : {res.T_fuel_avg[-1]-res.T_fuel_avg[0]:6.2f} K")
    print(f" coolant temp rise        : {res.T_coolant[-1]-res.T_coolant[0]:6.2f} K")
    print("=" * 66)


def plot(res):
    """Power and reactivity vs time (the classic self-regulation picture)."""
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)

    ax1.plot(res.t, res.power, color="firebrick", lw=2)
    ax1.axhline(1.0, ls=":", color="gray")
    ax1.set_ylabel("normalized power  n")
    ax1.set_title("Passive self-regulation after a +reactivity step")
    ax1.grid(True, alpha=0.3)

    ax2.plot(res.t, res.rho_rods * 1e5, label="rods (inserted)", color="steelblue")
    ax2.plot(res.t, res.rho_feedback * 1e5, label="temperature feedback", color="darkorange")
    ax2.plot(res.t, res.rho_total * 1e5, label="total", color="black", lw=2)
    ax2.axhline(0.0, ls=":", color="gray")
    ax2.set_xlabel("time  [s]")
    ax2.set_ylabel("reactivity  [pcm]")
    ax2.legend(loc="center right")
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def main() -> None:
    sim, res = simulate()
    report(sim, res)
    answer = input("\nGraph the power & reactivity transient? [y/N]: ").strip().lower()
    if answer in ("y", "yes"):
        import matplotlib.pyplot as plt

        plot(res)
        plt.show()
    else:
        print("Skipping plot.")


if __name__ == "__main__":
    main()
