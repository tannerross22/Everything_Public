"""Phase-6 demo: PID rod control and SCRAM.

Two scenarios:
  1. LOAD-FOLLOW -- the PID regulating bank tracks a power setpoint reduction
     (1.0 -> 0.85 -> 1.0), moving rods to maneuver power.
  2. SCRAM       -- an over-power command trips the safety supervisor, which
     drives the shutdown rods in and shuts the reactor down.

Run from the project root:
    python scripts/run_rod_control.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from reactorsim.coupling.simulator import PlantSimulator
from reactorsim.control.rod_banks import power_controller
from reactorsim.control.scram import ScramSystem


def load_follow():
    sim = PlantSimulator(); sim.initialize()
    ctrl = power_controller(setpoint=1.0)

    def sp(t):
        if t < 20:
            return 1.0
        if t < 120:
            return 0.85
        return 1.0

    return sim.run_controlled(t_end=220.0, dt=0.05, controller=ctrl, setpoint=sp)


def scram_event():
    sim = PlantSimulator(); sim.initialize()
    ctrl = power_controller(setpoint=1.6, scram=ScramSystem(power_trip=1.4))
    res = sim.run_controlled(t_end=80.0, dt=0.05, controller=ctrl)
    return res, ctrl


def report(lf, sc, ctrl) -> None:
    print("=" * 66)
    print(" Rod control -- load-follow")
    print("=" * 66)
    print(f" setpoint 1.0 -> 0.85 -> 1.0")
    print(f" final power            : {lf.power[-1]:.4f}")
    print(f" rod travel (insertion) : {lf.rod_position.min():.3f} .. {lf.rod_position.max():.3f}")
    print("=" * 66)
    print(" Rod control -- SCRAM")
    print("=" * 66)
    itrip = np.argmax(sc.scram_tripped)
    print(f" trip reason            : {ctrl.scram.trip_reason}")
    print(f" trip time              : {sc.t[itrip]:.2f} s")
    print(f" peak power             : {sc.power.max():.3f}")
    print(f" final power            : {sc.power[-1]:.3e}")
    print(f" final total reactivity : {sc.rho_total[-1]:.4f}  (subcritical)")
    print("=" * 66)


def plot(lf, sc):
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(12, 7))

    # load-follow: power & setpoint
    axes[0, 0].plot(lf.t, lf.power, color="firebrick", label="power")
    axes[0, 0].plot(lf.t, lf.setpoint, ls="--", color="gray", label="setpoint")
    axes[0, 0].set_ylabel("normalized power")
    axes[0, 0].set_title("Load-follow: power tracking")
    axes[0, 0].legend(); axes[0, 0].grid(True, alpha=0.3)

    # load-follow: rod position
    axes[1, 0].plot(lf.t, lf.rod_position, color="steelblue")
    axes[1, 0].set_xlabel("time [s]"); axes[1, 0].set_ylabel("bank insertion")
    axes[1, 0].set_title("Load-follow: regulating bank position")
    axes[1, 0].grid(True, alpha=0.3)

    # scram: power
    axes[0, 1].semilogy(sc.t, sc.power, color="firebrick")
    axes[0, 1].set_ylabel("normalized power (log)")
    axes[0, 1].set_title("SCRAM: power shutdown")
    axes[0, 1].grid(True, which="both", alpha=0.3)

    # scram: rod positions
    axes[1, 1].plot(sc.t, sc.rod_position, color="steelblue", label="regulating")
    axes[1, 1].plot(sc.t, sc.scram_position, color="black", label="shutdown rods")
    axes[1, 1].set_xlabel("time [s]"); axes[1, 1].set_ylabel("insertion")
    axes[1, 1].set_title("SCRAM: rod positions")
    axes[1, 1].legend(); axes[1, 1].grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def main() -> None:
    lf = load_follow()
    sc, ctrl = scram_event()
    report(lf, sc, ctrl)
    answer = input("\nGraph the control scenarios? [y/N]: ").strip().lower()
    if answer in ("y", "yes"):
        import matplotlib.pyplot as plt
        plot(lf, sc)
        plt.show()
    else:
        print("Skipping plot.")


if __name__ == "__main__":
    main()
