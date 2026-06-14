"""Phase-3 demo: thermally-closed single pin in a coolant subchannel.

Marches the coolant up the channel (Dittus-Boelter film coefficient), runs the
radial conduction solve at every elevation, and reports / plots the axial
temperature profiles. Shows the classic hot-spot shift above the core mid-plane.

Run from the project root:
    python scripts/run_coolant_channel.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from reactorsim.hydraulics.coolant_channel import pwr_channel, solve_pin_channel


def report() -> None:
    ch = pwr_channel()
    field = solve_pin_channel(ch)
    sol = field.channel
    z = sol.z
    H = ch.axial.height

    print("=" * 64)
    print(" Coolant channel + coupled pin  (nominal PWR subchannel)")
    print("=" * 64)
    print(f" mass flux G            : {ch.mass_flux:10.1f} kg/m2/s")
    print(f" Reynolds / Prandtl     : {sol.Re:10.3e} / {sol.Pr:.3f}")
    print(f" hydraulic diameter     : {ch.geom.hydraulic_diameter*1e3:10.3f} mm")
    print(f" film coefficient h     : {sol.h[0]:10.0f} W/m2/K")
    print("-" * 64)
    print(f" inlet  / outlet T      : {sol.T_inlet-273.15:7.1f} / {sol.T_outlet-273.15:7.1f} C")
    print(f" coolant temperature rise: {sol.T_outlet-sol.T_inlet:9.2f} K")
    print(f" channel power           : {sol.power()/1e3:9.2f} kW/rod")
    print("-" * 64)
    zc = z[np.argmax(field.T_centerline)]
    zk = z[np.argmax(field.T_clad_outer)]
    print(f" peak fuel centreline   : {field.T_centerline.max()-273.15:7.1f} C  at z = {zc:.2f} m")
    print(f" peak clad outer surface: {field.T_clad_outer.max()-273.15:7.1f} C  at z = {zk:.2f} m")
    print(f" core mid-plane         : {H/2:.2f} m  (note both peaks lie above it)")
    print("=" * 64)
    return field


def plot_axial(field):
    """Axial temperature profiles, with fuel centreline on a second axis."""
    import matplotlib.pyplot as plt

    sol = field.channel
    z = sol.z
    H = z[-1] + (z[1] - z[0]) / 2

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(z, sol.T_coolant - 273.15, "-", color="steelblue", label="coolant bulk")
    ax.plot(z, field.T_clad_outer - 273.15, "-", color="darkorange", label="clad outer surface")
    ax.set_xlabel("elevation z  [m]")
    ax.set_ylabel("temperature  [C]  (coolant / clad)")
    ax.axvline(H / 2, ls=":", color="gray", label="core mid-plane")

    ax2 = ax.twinx()
    ax2.plot(z, field.T_centerline - 273.15, "-", color="firebrick",
             label="fuel centreline")
    ax2.set_ylabel("temperature  [C]  (fuel centreline)", color="firebrick")
    ax2.tick_params(axis="y", labelcolor="firebrick")

    lines, labels = ax.get_legend_handles_labels()
    l2, lab2 = ax2.get_legend_handles_labels()
    ax.legend(lines + l2, labels + lab2, loc="upper left")
    ax.set_title("Axial temperature profiles -- hot spot shifts above mid-plane")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def main() -> None:
    field = report()
    answer = input("\nGraph the axial temperature profiles? [y/N]: ").strip().lower()
    if answer in ("y", "yes"):
        import matplotlib.pyplot as plt

        plot_axial(field)
        plt.show()
    else:
        print("Skipping plot.")


if __name__ == "__main__":
    main()
