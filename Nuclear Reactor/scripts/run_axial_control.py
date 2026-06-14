"""Phase-6.5 demo: axial (spatial) neutronics with axial-offset control.

Scenario A -- flux shapes: park the banks, then insert the top bank and watch the
axial flux tilt toward the bottom (the shape is now a dynamic state).

Scenario B -- AO control: drive the axial offset to a setpoint while the power
controller holds total power, using two banks (mean insertion -> power,
differential insertion -> axial offset).

Run from the project root:
    python scripts/run_axial_control.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from reactorsim.coupling.axial_simulator import AxialPlantSimulator
from reactorsim.neutronics.spatial_kinetics import AxialKineticsModel
from reactorsim.control.axial_control import power_ao_controller


def flux_shapes():
    sim = AxialPlantSimulator(kinetics=AxialKineticsModel(n_axial=24), p0=0.25)
    sim.initialize()
    res = sim.run_fixed(t_end=60.0, dt=0.1,
                        p_top=lambda t: 0.25 if t < 5 else 0.45, p_bottom=0.25,
                        snapshots=[0.0, 60.0])
    return sim, res


def ao_control():
    sim = AxialPlantSimulator(kinetics=AxialKineticsModel(n_axial=24), p0=0.25)
    sim.initialize()
    ctrl = power_ao_controller(power_setpoint=1.0, ao_setpoint=0.0, p0=0.25)
    res = sim.run_controlled(
        t_end=300.0, dt=0.1, controller=ctrl,
        power_setpoint=lambda t: 1.0,
        ao_setpoint=lambda t: 0.0 if t < 20 else (0.12 if t < 160 else -0.12),
    )
    return res


def report(fs_sim, fs, ao) -> None:
    print("=" * 66)
    print(" Axial spatial kinetics + axial-offset control")
    print("=" * 66)
    print(f" mesh: {fs_sim.kinetics.n_axial} axial nodes, "
          f"migration length ~{np.sqrt(fs_sim.kinetics.D/fs_sim.kinetics.Sigma_a)*100:.1f} cm")
    print(f" flux tilt: AO {fs.axial_offset[0]:+.3f} (parked) -> "
          f"{fs.axial_offset[-1]:+.3f} (top bank inserted)")
    print("-" * 66)
    print(" AO control (setpoint 0 -> +0.12 -> -0.12, power held at 1.0):")
    print(f"   final AO    = {ao.axial_offset[-1]:+.3f}")
    print(f"   final power = {ao.power[-1]:.4f}")
    print(f"   max |power excursion| during AO swings = "
          f"{np.max(np.abs(ao.power-1.0)):.4f}")
    print("=" * 66)


def plot(fs, ao):
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8))

    # flux shapes
    z = fs.z
    for phi, t in zip(fs.flux_snapshots, fs.snapshot_times):
        axes[0].plot(phi, z, label=f"t={t:.0f}s  AO={ (phi[z>=z.mean()].sum()-phi[z<z.mean()].sum())/phi.sum():+.2f}")
    axes[0].set_xlabel("normalized flux"); axes[0].set_ylabel("elevation z [m]")
    axes[0].set_title("Axial flux shape tilts with rod insertion")
    axes[0].legend(); axes[0].grid(True, alpha=0.3)

    # AO control: AO vs setpoint
    axes[1].plot(ao.t, ao.axial_offset, color="darkorange", label="axial offset")
    axes[1].plot(ao.t, ao.setpoint_ao, ls="--", color="gray", label="AO setpoint")
    axes[1].set_xlabel("time [s]"); axes[1].set_ylabel("axial offset")
    axes[1].set_title("AO control tracks setpoint")
    axes[1].legend(); axes[1].grid(True, alpha=0.3)

    # AO control: power held + bank positions
    axes[2].plot(ao.t, ao.power, color="firebrick", label="power")
    axes[2].plot(ao.t, ao.p_top, color="steelblue", label="top bank")
    axes[2].plot(ao.t, ao.p_bottom, color="seagreen", label="bottom bank")
    axes[2].set_xlabel("time [s]"); axes[2].set_ylabel("power / bank insertion")
    axes[2].set_title("Power held while banks move differentially")
    axes[2].legend(); axes[2].grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def main() -> None:
    fs_sim, fs = flux_shapes()
    ao = ao_control()
    report(fs_sim, fs, ao)
    answer = input("\nGraph the axial flux shapes and AO control? [y/N]: ").strip().lower()
    if answer in ("y", "yes"):
        import matplotlib.pyplot as plt
        plot(fs, ao)
        plt.show()
    else:
        print("Skipping plot.")


if __name__ == "__main__":
    main()
