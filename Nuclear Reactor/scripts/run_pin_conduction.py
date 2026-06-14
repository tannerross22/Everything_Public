"""Phase-2 demo: steady-state radial temperature profile of a single PWR fuel
pin (UO2 pellet -> He gap -> Zircaloy clad -> coolant).

Prints centreline / surface / clad temperatures and the energy balance, then
optionally plots the radial temperature profile.

Run from the project root:
    python scripts/run_pin_conduction.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from reactorsim.params.geometry import pwr_17x17
from reactorsim.params.plant import pwr_nominal
from reactorsim.thermal.conduction1d import RadialPinModel


def build(q_linear: float) -> tuple[RadialPinModel, np.ndarray]:
    g = pwr_17x17()
    model = RadialPinModel(geom=g, q_volumetric=g.q_volumetric_from_linear(q_linear))
    return model, model.solve_steady()


def report(q_linear: float) -> None:
    model, T = build(q_linear)
    nf = model.n_fuel
    cool = pwr_nominal()
    print("=" * 64)
    print(f" Fuel pin radial conduction -- q' = {q_linear/1e3:.1f} kW/m")
    print("=" * 64)
    print(f" fuel centreline temperature : {T[0]:8.1f} K  ({T[0]-273.15:7.1f} C)")
    print(f" pellet surface temperature  : {T[nf-1]:8.1f} K  ({T[nf-1]-273.15:7.1f} C)")
    print(f" clad outer temperature      : {T[-1]:8.1f} K  ({T[-1]-273.15:7.1f} C)")
    print(f" bulk coolant temperature    : {cool.T_inf:8.1f} K  ({cool.T_inf-273.15:7.1f} C)")
    print("-" * 64)
    print(f" heat generated  q'          : {model.heat_generated()/1e3:8.3f} kW/m")
    print(f" heat removed at surface     : {model.heat_out(T)/1e3:8.3f} kW/m")
    print("=" * 64)


def plot_profile(q_linear: float = 17.8e3):
    """Radial temperature profile, with the fuel / gap / clad regions marked."""
    import matplotlib.pyplot as plt

    g = pwr_17x17()
    model, T = build(q_linear)
    nf = model.n_fuel
    r_mm = model.r_center * 1e3

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(r_mm[:nf], T[:nf], "-o", ms=3, label="fuel (UO2)")
    ax.plot(r_mm[nf:], T[nf:], "-s", ms=3, label="clad (Zircaloy)")

    # mark the gap as a shaded band between pellet surface and clad inner radius
    ax.axvspan(g.r_fuel * 1e3, g.r_clad_inner * 1e3, color="0.85",
               label="He gap")
    ax.axhline(pwr_nominal().T_inf, ls=":", color="steelblue",
               label=f"coolant {pwr_nominal().T_inf:.0f} K")

    ax.set_xlabel("radius  [mm]")
    ax.set_ylabel("temperature  [K]")
    ax.set_title(f"PWR fuel pin radial temperature profile  (q' = {q_linear/1e3:.1f} kW/m)")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def main() -> None:
    report(17.8e3)   # average rod
    report(44.0e3)   # peak rod

    answer = input("\nGraph the radial temperature profile? [y/N]: ").strip().lower()
    if answer in ("y", "yes"):
        import matplotlib.pyplot as plt

        plot_profile(17.8e3)
        plt.show()
    else:
        print("Skipping plot.")


if __name__ == "__main__":
    main()
