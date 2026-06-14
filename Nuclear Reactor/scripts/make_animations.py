"""Render MP4 animations of the reactor temperature field with rod positions.

Two scenarios are driven on the Phase-6.5 axial plant simulator (spatial flux +
per-node thermal + two control-rod banks):

  reactor_power_maneuver.mp4 -- a power maneuver (banks move together; the whole
      core brightens and dims as power rises and falls).
  reactor_ao_swing.mp4       -- an axial-offset swing at constant power (banks
      move differentially; the hot region migrates up and down the core).

Each frame shows a 2D (r, z) cross-section temperature heat map of the fuel pin
(reconstructed from the local power and coolant temperature by a radial
conduction lookup), with the top and bottom control-rod banks drawn in the
margins at their current insertion depth.

Run from the project root:
    python scripts/make_animations.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import imageio_ffmpeg
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle

matplotlib.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()

from reactorsim.coupling.axial_simulator import AxialPlantSimulator
from reactorsim.neutronics.spatial_kinetics import AxialKineticsModel
from reactorsim.control.axial_control import power_ao_controller
from reactorsim.params.geometry import pwr_17x17
from reactorsim.params.plant import CoolantBC
from reactorsim.thermal.conduction1d import RadialPinModel

H_FILM = 37000.0
N_FUEL, N_CLAD = 16, 4


# --------------------------------------------------------------------------- #
# radial temperature-rise lookup: dT(r) = T(r) - T_coolant for a given q'
# --------------------------------------------------------------------------- #
def build_radial_lookup(q_max, T_ref=580.0, n_q=50):
    geom = pwr_17x17()
    q_grid = np.linspace(0.0, q_max, n_q)
    table = []
    r_center = None
    for ql in q_grid:
        m = RadialPinModel(
            geom=geom, coolant=CoolantBC(h=H_FILM, T_inf=T_ref),
            q_volumetric=geom.q_volumetric_from_linear(ql),
            n_fuel=N_FUEL, n_clad=N_CLAD,
        )
        T = m.solve_steady()
        if r_center is None:
            r_center = m.r_center
        table.append(T - T_ref)
    return q_grid, np.array(table), r_center      # table: (n_q, Nr)


def reconstruct(q_prime, T_coolant, q_grid, dT_table):
    """Build the (Nz, Nr) temperature field from per-node linear power and
    coolant temperature using the radial lookup."""
    Nz = q_prime.size
    Nr = dT_table.shape[1]
    dT = np.empty((Nz, Nr))
    for j in range(Nr):
        dT[:, j] = np.interp(q_prime, q_grid, dT_table[:, j])
    return T_coolant[:, None] + dT


# --------------------------------------------------------------------------- #
# run a scenario, collecting per-frame fields
# --------------------------------------------------------------------------- #
def run_scenario(power_sp, ao_sp, t_end, dt=0.1, frame_every=12, n_axial=24):
    sim = AxialPlantSimulator(kinetics=AxialKineticsModel(n_axial=n_axial), p0=0.25)
    sim.initialize()
    ctrl = power_ao_controller(power_setpoint=1.0, ao_setpoint=0.0, p0=0.25)
    ctrl.reset()
    qlf = sim.q_linear_full

    frames = {"t": [], "qp": [], "Tc": [], "p_top": [], "p_bot": [],
              "power": [], "ao": []}

    def snap(p_top, p_bot):
        phi, _ = sim.kinetics.split(sim.y)
        frames["t"].append(sim.t)
        frames["qp"].append(sim.kinetics.linear_power(phi, qlf))
        frames["Tc"].append(sim.T_coolant.copy())
        frames["p_top"].append(p_top)
        frames["p_bot"].append(p_bot)
        frames["power"].append(sim.kinetics.total_power(phi))
        frames["ao"].append(sim.kinetics.axial_offset(phi))

    n_steps = int(round(t_end / dt))
    snap(ctrl.p_top, ctrl.p_bottom)
    for s in range(1, n_steps + 1):
        ctrl.power_pid.setpoint = power_sp(sim.t)
        ctrl.ao_pid.setpoint = ao_sp(sim.t)
        p_top, p_bot = ctrl.step(dt, sim.measurements())
        sim.step(dt, p_top, p_bot)
        if s % frame_every == 0:
            snap(p_top, p_bot)

    return {k: np.array(v) for k, v in frames.items()}, sim.kinetics.height


# --------------------------------------------------------------------------- #
# animate
# --------------------------------------------------------------------------- #
def animate(scenario, frames, height, out_path, title, fps=20):
    q_max = 1.3 * frames["qp"].max()
    q_grid, dT_table, r_center = build_radial_lookup(q_max)
    r_mm = r_center * 1e3
    r_out = r_mm[-1]

    # reconstruct all fields, find global colour range
    fields = [reconstruct(frames["qp"][i], frames["Tc"][i], q_grid, dT_table) - 273.15
              for i in range(frames["t"].size)]
    vmin = min(f.min() for f in fields)
    vmax = max(f.max() for f in fields)

    def mirror(field):
        return np.hstack([field[:, ::-1], field])

    fig, ax = plt.subplots(figsize=(7.2, 7.4))
    im = ax.imshow(mirror(fields[0]), origin="lower", aspect="auto",
                   extent=[-r_out, r_out, 0, height], cmap="inferno",
                   vmin=vmin, vmax=vmax)
    cb = fig.colorbar(im, ax=ax, pad=0.12)
    cb.set_label("temperature [C]")
    ax.set_xlim(-r_out - 3.0, r_out + 3.0)
    ax.set_xlabel("radius [mm]   (control rods at margins)")
    ax.set_ylabel("elevation z [m]")

    # rod travel outlines + inserted (dark) patches
    x_top = r_out + 0.6                  # top bank drawn on the right margin
    x_bot = -r_out - 2.0                 # bottom bank on the left margin
    rw = 1.4
    ax.add_patch(Rectangle((x_top, 0), rw, height, fc="none", ec="0.5", lw=0.8))
    ax.add_patch(Rectangle((x_bot, 0), rw, height, fc="none", ec="0.5", lw=0.8))
    top_rod = Rectangle((x_top, height), rw, 0, fc="0.15", ec="0.3")
    bot_rod = Rectangle((x_bot, 0), rw, 0, fc="0.15", ec="0.3")
    ax.add_patch(top_rod)
    ax.add_patch(bot_rod)
    ax.text(x_top + rw / 2, height * 0.5, "top bank", rotation=90,
            ha="center", va="center", fontsize=8, color="0.35")
    ax.text(x_bot + rw / 2, height * 0.5, "bottom bank", rotation=90,
            ha="center", va="center", fontsize=8, color="0.35")
    ax.set_title(title, pad=12)

    txt = ax.text(0.02, 0.98, "", transform=ax.transAxes, va="top",
                  color="white", fontsize=9, family="monospace",
                  bbox=dict(fc="black", alpha=0.4, ec="none"))

    def update(i):
        im.set_data(mirror(fields[i]))
        p_top, p_bot = frames["p_top"][i], frames["p_bot"][i]
        # top bank inserts downward from the top
        top_rod.set_y(height * (1 - p_top))
        top_rod.set_height(height * p_top)
        # bottom bank inserts upward from the bottom
        bot_rod.set_height(height * p_bot)
        txt.set_text(
            f"t = {frames['t'][i]:6.1f} s\n"
            f"power = {frames['power'][i]:.3f}\n"
            f"AO    = {frames['ao'][i]:+.3f}\n"
            f"top   = {p_top:.2f}\n"
            f"bottom= {p_bot:.2f}"
        )
        return im, top_rod, bot_rod, txt

    ani = animation.FuncAnimation(fig, update, frames=frames["t"].size,
                                  blit=False, interval=1000 / fps)
    writer = animation.FFMpegWriter(fps=fps, bitrate=2800)
    ani.save(out_path, writer=writer, dpi=110)
    plt.close(fig)


def main():
    outdir = Path(__file__).resolve().parent.parent / "animations"
    outdir.mkdir(exist_ok=True)

    # Scenario 1: power maneuver (1.0 -> 1.15 -> 0.85 -> 1.0), AO held at 0
    def pwr_sp(t):
        if t < 15: return 1.0
        if t < 70: return 1.15
        if t < 130: return 0.85
        return 1.0
    print("running power-maneuver scenario...")
    f1, H = run_scenario(pwr_sp, lambda t: 0.0, t_end=190.0)
    print(f"  {f1['t'].size} frames; rendering MP4...")
    animate("power", f1, H, str(outdir / "reactor_power_maneuver.mp4"),
            "Reactor temperature -- power maneuver")
    print(f"  wrote {outdir / 'reactor_power_maneuver.mp4'}")

    # Scenario 2: axial-offset swing (0 -> +0.15 -> -0.15 -> 0), power held at 1.0
    def ao_sp(t):
        if t < 20: return 0.0
        if t < 90: return 0.15
        if t < 160: return -0.15
        return 0.0
    print("running AO-swing scenario...")
    f2, H = run_scenario(lambda t: 1.0, ao_sp, t_end=220.0)
    print(f"  {f2['t'].size} frames; rendering MP4...")
    animate("ao", f2, H, str(outdir / "reactor_ao_swing.mp4"),
            "Reactor temperature -- axial-offset swing (power held)")
    print(f"  wrote {outdir / 'reactor_ao_swing.mp4'}")


if __name__ == "__main__":
    main()
