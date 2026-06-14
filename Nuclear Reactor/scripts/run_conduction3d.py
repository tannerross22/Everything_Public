"""Phase-4 demo: full 2D (r, z) temperature field of a fuel pin with axial
conduction, coupled to the Phase-3 coolant channel.

Reports the peak temperatures and the (small) effect of axial conduction versus
the uncoupled stacked-slice model, then optionally plots the (r, z) temperature
map.

Run from the project root:
    python scripts/run_conduction3d.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from reactorsim.hydraulics.coolant_channel import pwr_channel, solve_pin_channel
from reactorsim.thermal.conduction3d import from_channel


def compute():
    ch = pwr_channel()
    stacked = solve_pin_channel(ch)
    model = from_channel(ch)
    T = model.solve_steady()
    return ch, model, T, stacked


def report(ch, model, T, stacked) -> None:
    cl = model.centerline(T)
    co = model.clad_outer(T)
    z = model.z_centers()
    H = model.height
    print("=" * 66)
    print(" 3D (r, z) pin conduction, coupled to coolant channel")
    print("=" * 66)
    print(f" mesh                    : Nr={model.Nr}  Ntheta={model.n_theta}  Nz={model.n_axial}  (N={model.N})")
    print(f" peak fuel centreline    : {cl.max()-273.15:7.1f} C  at z = {z[np.argmax(cl)]:.2f} m")
    print(f" peak clad outer surface : {co.max()-273.15:7.1f} C  at z = {z[np.argmax(co)]:.2f} m")
    print(f" core mid-plane          : {H/2:.2f} m")
    print("-" * 66)
    print(f" heat generated          : {model.heat_generated()/1e3:8.2f} kW")
    print(f" heat removed at surface : {model.heat_out(T)/1e3:8.2f} kW")
    print("-" * 66)
    dpeak = stacked.T_centerline.max() - cl.max()
    print(f" axial-conduction effect on peak centreline : {dpeak:.4f} K lower")
    print(f"   (small: a long thin rod is dominated by radial transport)")
    print("=" * 66)


def plot_field(model, T):
    """2D (r, z) temperature map of the pin."""
    import matplotlib.pyplot as plt

    Tr = model.reshape(T)[:, 0, :]      # (Nz, Nr)
    r_mm = model.rc * 1e3
    z = model.z_centers()

    fig, ax = plt.subplots(figsize=(7.5, 6))
    pcm = ax.pcolormesh(r_mm, z, Tr - 273.15, shading="auto", cmap="inferno")
    cb = fig.colorbar(pcm, ax=ax)
    cb.set_label("temperature  [C]")

    # mark the pellet outer radius (gap location)
    ax.axvline(model.geom.r_fuel * 1e3, color="cyan", lw=1, ls="--",
               label="pellet surface / gap")
    ax.set_xlabel("radius  [mm]")
    ax.set_ylabel("elevation z  [m]")
    ax.set_title("Fuel pin temperature field  T(r, z)")
    ax.legend(loc="upper right")
    fig.tight_layout()
    return fig


def main() -> None:
    ch, model, T, stacked = compute()
    report(ch, model, T, stacked)
    answer = input("\nGraph the (r, z) temperature field? [y/N]: ").strip().lower()
    if answer in ("y", "yes"):
        import matplotlib.pyplot as plt

        plot_field(model, T)
        plt.show()
    else:
        print("Skipping plot.")


if __name__ == "__main__":
    main()
