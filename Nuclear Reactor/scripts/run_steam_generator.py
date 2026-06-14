"""Phase-7 demo: steam generator, plant heat balance, and the secondary-pressure
design trade.

Prints the design-point heat balance and the closed primary loop, then sweeps
the secondary pressure to show *why* it is chosen: raising it lifts cycle
efficiency but demands far more heat-transfer area (UA) and makes the steam
wetter -- until the saturation temperature crowds the primary hot leg and the
duty becomes infeasible.

Run from the project root:
    python scripts/run_steam_generator.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from reactorsim.hydraulics import steam_tables as st
from reactorsim.hydraulics.heat_exchanger import (
    pwr_steam_generator, required_UA, PrimaryLoop, rankine_cycle,
    secondary_pressure_for_approach,
)

CORE_POWER = 3400e6
CMIN = 18000 * 5500.0
T_HOT_IN = 597.15          # 324 C hot leg
P_COND = 0.006e6           # condenser ~ 0.006 MPa


def report() -> None:
    sg = pwr_steam_generator()
    loop = PrimaryLoop(core_power=CORE_POWER, mdot_primary=18000, cp_primary=5500,
                       UA=sg.UA, secondary_pressure=sg.secondary_pressure).solve()
    rc = rankine_cycle(sg.secondary_pressure, P_COND)

    print("=" * 66)
    print(" Steam generator design point  (P_secondary = 6.9 MPa)")
    print("=" * 66)
    print(f" secondary saturation temp : {sg.T_sat-273.15:7.1f} C")
    print(f" SG effectiveness / NTU    : {sg.effectiveness:7.3f} / {sg.NTU:.2f}")
    print(f" thermal duty              : {sg.duty()/1e6:7.0f} MW")
    print(f" steam production          : {sg.steam_rate():7.0f} kg/s")
    print("-" * 66)
    print(" Closed primary loop:")
    print(f"   hot leg  : {loop['T_hot']-273.15:6.1f} C")
    print(f"   cold leg : {loop['T_cold']-273.15:6.1f} C   (= core inlet)")
    print(f"   average  : {loop['T_avg']-273.15:6.1f} C   approach = {loop['approach']:.1f} C")
    print("-" * 66)
    print(" Secondary cycle:")
    print(f"   thermal efficiency      : {rc.efficiency*100:5.1f} %")
    print(f"   turbine exit quality    : {rc.turbine_exit_quality:5.3f}")
    print("=" * 66)


def sweep():
    pressures = np.linspace(4.0e6, 8.5e6, 40)
    Tsat, UA, eta, x_exit = [], [], [], []
    for P in pressures:
        Ts = st.T_sat(P)
        Tsat.append(Ts - 273.15)
        try:
            UA.append(required_UA(CORE_POWER, CMIN, T_HOT_IN, Ts) / 1e8)
        except ValueError:
            UA.append(np.nan)            # infeasible: T_sat too close to hot leg
        rc = rankine_cycle(P, P_COND)
        eta.append(rc.efficiency * 100)
        x_exit.append(rc.turbine_exit_quality)
    return (pressures / 1e6, np.array(Tsat), np.array(UA),
            np.array(eta), np.array(x_exit))


def plot(data):
    import matplotlib.pyplot as plt

    P, Tsat, UA, eta, x_exit = data
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    axes[0, 0].plot(P, Tsat, color="firebrick")
    axes[0, 0].axhline(T_HOT_IN - 273.15, ls=":", color="gray",
                       label=f"primary hot leg {T_HOT_IN-273.15:.0f} C")
    axes[0, 0].set_ylabel("secondary T_sat [C]"); axes[0, 0].legend()
    axes[0, 0].set_title("Pressure sets the boiling temperature")

    axes[0, 1].plot(P, UA, color="steelblue")
    axes[0, 1].set_ylabel("required UA [1e8 W/K]")
    axes[0, 1].set_title("...higher pressure -> much more heat-transfer area")

    axes[1, 0].plot(P, eta, color="seagreen")
    axes[1, 0].set_xlabel("secondary pressure [MPa]"); axes[1, 0].set_ylabel("cycle efficiency [%]")
    axes[1, 0].set_title("...but higher efficiency")

    axes[1, 1].plot(P, x_exit, color="darkorange")
    axes[1, 1].axhline(0.88, ls=":", color="gray", label="~moisture limit")
    axes[1, 1].set_xlabel("secondary pressure [MPa]"); axes[1, 1].set_ylabel("turbine exit quality")
    axes[1, 1].set_title("...and wetter steam (erosion)"); axes[1, 1].legend()

    for ax in axes.ravel():
        ax.axvline(6.9, ls="--", color="black", alpha=0.4)
        ax.grid(True, alpha=0.3)
    fig.suptitle("Choosing the secondary pressure: the design trade (dashed = 6.9 MPa)")
    fig.tight_layout()
    return fig


def main() -> None:
    report()
    answer = input("\nGraph the secondary-pressure design trade? [y/N]: ").strip().lower()
    if answer in ("y", "yes"):
        import matplotlib.pyplot as plt
        plot(sweep())
        plt.show()
    else:
        print("Skipping plot.")


if __name__ == "__main__":
    main()
