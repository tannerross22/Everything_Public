#!/usr/bin/env python3
"""Real-time pygame animation of the ascent phase only (launch -> apogee).

Two modes (set MODE below):
  - "live"   : opens a pygame window and plays back at real time (1 s sim = 1 s wall).
               Press ESC or close the window to quit.
  - "record" : renders frames to ascent_realtime.mp4 at 30 fps (real-time pacing).

The rocket is drawn as a large body (rectangle) + nose cone (triangle) + fins,
filling most of the left panel. It tilts according to the rocket's actual 3D
attitude projected onto the screen plane, so weathercocking oscillations are
visible as the rocket wobbling. The right panel plots theta_down (pitch off
vertical) and theta_around (heading change) vs time, growing as time advances.
"""

import sys
import numpy as np
import pandas as pd
import pygame

MODE = "record"            # "live" or "record"
OUT_VIDEO = "ascent_realtime.mp4"
FPS = 30                   # real-time pacing
WIDTH, HEIGHT = 1280, 720

# Layout: rocket panel on left, time-series panel on right
ROCKET_W = 540
GRAPH_X = ROCKET_W
GRAPH_W = WIDTH - ROCKET_W

# Rocket dimensions in pixels (taking up most of the rocket panel)
BODY_W = 90
BODY_H = 420
NOSE_H = 110
FIN_W = 60
FIN_H = 90

# Colors
BG = (245, 247, 250)
PANEL_DIVIDER = (200, 200, 210)
ROCKET_BODY = (180, 185, 200)
ROCKET_NOSE = (200, 60, 60)
ROCKET_FIN  = (90, 100, 130)
GROUND = (180, 220, 180)
WIND_ARROW = (60, 130, 200)
GRAPH_AXIS = (40, 40, 40)
GRAPH_GRID = (220, 220, 225)
LINE_PITCH = (30, 90, 200)
LINE_HEADING = (220, 110, 30)
TIME_MARKER = (200, 40, 40)
TEXT = (20, 20, 30)

# ---------- Load data ----------
df = pd.read_csv("src/data/output/output.csv").set_index("time [s]")
t_apogee = df["z position [m]"].idxmax()
ascent = df.loc[:t_apogee].copy()
deg = 180.0 / np.pi

t_arr = ascent.index.values.astype(np.float64)
theta_down = ascent["theta down [rad]"].values  # radians
theta_around = ascent["theta around [rad]"].values
theta_around_rel = theta_around - theta_around[0]  # relative to launch heading
alt = ascent["z position [m]"].values
vz = ascent["z velocity [m s^-1]"].values

# Visible 2D tilt: project the body axis onto a fixed view plane.
# Body axis (unit vector): (cos(around)*sin(down), sin(around)*sin(down), cos(down))
# Pick a "view azimuth" so the wobble shows up; we project onto the x-z plane,
# i.e. show the angle between the body axis and the +z axis as seen from +y.
# That is just the signed angle whose sin = cos(around)*sin(down), cos = cos(down).
visible_tilt = np.arctan2(
    np.cos(theta_around) * np.sin(theta_down), np.cos(theta_down)
)  # radians, 0 = upright

t_apogee_val = float(t_arr[-1])


# ---------- Drawing helpers ----------
def transform(pts, center, angle_rad):
    """Rotate body-frame points (origin = rocket CG, +y = up) and translate to screen.
    Pygame y-axis is flipped (down is +)."""
    c, s = np.cos(angle_rad), np.sin(angle_rad)
    out = []
    for x, y in pts:
        xr = x * c - y * s
        yr = x * s + y * c
        out.append((center[0] + xr, center[1] - yr))
    return out


def draw_rocket(surface, center, angle_rad):
    """Draw rocket as nose triangle + body rectangle + two fin triangles.
    angle_rad: 0 = pointing straight up, +ve = leans right."""
    body = [
        (-BODY_W / 2, -BODY_H / 2),
        (BODY_W / 2, -BODY_H / 2),
        (BODY_W / 2, BODY_H / 2),
        (-BODY_W / 2, BODY_H / 2),
    ]
    nose = [
        (-BODY_W / 2, BODY_H / 2),
        (BODY_W / 2, BODY_H / 2),
        (0, BODY_H / 2 + NOSE_H),
    ]
    fin_l = [
        (-BODY_W / 2, -BODY_H / 2),
        (-BODY_W / 2 - FIN_W, -BODY_H / 2 - FIN_H / 2),
        (-BODY_W / 2, -BODY_H / 2 + FIN_H),
    ]
    fin_r = [
        (BODY_W / 2, -BODY_H / 2),
        (BODY_W / 2 + FIN_W, -BODY_H / 2 - FIN_H / 2),
        (BODY_W / 2, -BODY_H / 2 + FIN_H),
    ]

    pygame.draw.polygon(surface, ROCKET_FIN, transform(fin_l, center, angle_rad))
    pygame.draw.polygon(surface, ROCKET_FIN, transform(fin_r, center, angle_rad))
    pygame.draw.polygon(surface, ROCKET_BODY, transform(body, center, angle_rad))
    pygame.draw.polygon(surface, ROCKET_NOSE, transform(nose, center, angle_rad))
    # Outline for crispness
    pygame.draw.polygon(surface, (40, 40, 50),
                        transform(body, center, angle_rad), width=2)
    pygame.draw.polygon(surface, (60, 20, 20),
                        transform(nose, center, angle_rad), width=2)


def draw_wind_arrow(surface, center, length=60):
    """Decorative arrow showing 'wind' coming from the side (the rocket weathercocks
    into the wind, i.e. tips upwind)."""
    x0, y0 = center[0] - 220, center[1] - 250
    x1, y1 = x0 + length, y0
    pygame.draw.line(surface, WIND_ARROW, (x0, y0), (x1, y1), 3)
    pygame.draw.polygon(surface, WIND_ARROW,
                        [(x1, y1), (x1 - 10, y1 - 6), (x1 - 10, y1 + 6)])


def draw_graph(surface, current_idx, font_sm):
    """Plot theta_down and theta_around vs time, with current-time marker."""
    margin_l, margin_r, margin_t, margin_b = 70, 30, 50, 60
    gx0 = GRAPH_X + margin_l
    gy0 = margin_t
    gw = GRAPH_W - margin_l - margin_r
    gh = HEIGHT - margin_t - margin_b

    # Axis ranges
    t_min, t_max = float(t_arr[0]), float(t_arr[-1])
    pitch_deg = theta_down * deg
    head_deg = theta_around_rel * deg
    th_min = min(pitch_deg.min(), head_deg.min()) - 3
    th_max = max(pitch_deg.max(), head_deg.max()) + 3

    def to_px(t, th):
        x = gx0 + (t - t_min) / (t_max - t_min) * gw
        y = gy0 + gh - (th - th_min) / (th_max - th_min) * gh
        return int(x), int(y)

    # Background box
    pygame.draw.rect(surface, (255, 255, 255), (gx0, gy0, gw, gh))
    pygame.draw.rect(surface, GRAPH_AXIS, (gx0, gy0, gw, gh), 2)

    # Y gridlines + ticks every 5°
    th_tick_lo = int(np.floor(th_min / 5) * 5)
    th_tick_hi = int(np.ceil(th_max / 5) * 5) + 1
    for th in range(th_tick_lo, th_tick_hi, 5):
        if th < th_min or th > th_max:
            continue
        _, y = to_px(t_min, th)
        pygame.draw.line(surface, GRAPH_GRID, (gx0, y), (gx0 + gw, y), 1)
        if th == 0:
            pygame.draw.line(surface, (140, 140, 140), (gx0, y), (gx0 + gw, y), 1)
        label = font_sm.render(f"{th}", True, GRAPH_AXIS)
        surface.blit(label, (gx0 - 35, y - 9))

    # X gridlines + ticks every 10 s
    for tt in range(0, int(t_max) + 1, 10):
        x, _ = to_px(tt, th_min)
        pygame.draw.line(surface, GRAPH_GRID, (x, gy0), (x, gy0 + gh), 1)
        label = font_sm.render(f"{tt}", True, GRAPH_AXIS)
        surface.blit(label, (x - 8, gy0 + gh + 6))

    # Plot curves up to current_idx
    if current_idx >= 1:
        idx_end = current_idx + 1
        pts_pitch = [to_px(t_arr[i], pitch_deg[i]) for i in range(idx_end)]
        pts_head = [to_px(t_arr[i], head_deg[i]) for i in range(idx_end)]
        if len(pts_pitch) >= 2:
            pygame.draw.lines(surface, LINE_PITCH, False, pts_pitch, 3)
            pygame.draw.lines(surface, LINE_HEADING, False, pts_head, 3)

    # Current time marker (vertical bar)
    x_now, _ = to_px(t_arr[current_idx], 0)
    pygame.draw.line(surface, TIME_MARKER, (x_now, gy0), (x_now, gy0 + gh), 2)

    # Axis labels
    surface.blit(font_sm.render("Time (s)", True, GRAPH_AXIS),
                 (gx0 + gw // 2 - 25, gy0 + gh + 28))
    yax = font_sm.render("Angle (deg)", True, GRAPH_AXIS)
    yax = pygame.transform.rotate(yax, 90)
    surface.blit(yax, (gx0 - 60, gy0 + gh // 2 - 35))

    # Legend
    legend_y = gy0 + 8
    pygame.draw.line(surface, LINE_PITCH, (gx0 + 12, legend_y + 6),
                     (gx0 + 40, legend_y + 6), 3)
    surface.blit(font_sm.render("theta_down (pitch off vertical)",
                                True, GRAPH_AXIS), (gx0 + 48, legend_y))
    pygame.draw.line(surface, LINE_HEADING, (gx0 + 12, legend_y + 26),
                     (gx0 + 40, legend_y + 26), 3)
    surface.blit(font_sm.render("theta_around (heading - launch heading)",
                                True, GRAPH_AXIS), (gx0 + 48, legend_y + 20))


def draw_status(surface, idx, sim_t, font_lg, font_md):
    """Status readout in upper-left of the rocket panel."""
    title = font_lg.render("5DOF Rocket — Ascent (real time)", True, TEXT)
    surface.blit(title, (16, 12))
    lines = [
        f"t = {sim_t:6.2f} s",
        f"altitude = {alt[idx] / 1000:6.2f} km",
        f"vz       = {vz[idx]:6.1f} m/s",
        f"pitch off vertical = {theta_down[idx] * deg:6.2f} deg",
        f"heading change     = {theta_around_rel[idx] * deg:+6.2f} deg",
    ]
    for i, line in enumerate(lines):
        surface.blit(font_md.render(line, True, TEXT), (16, 50 + i * 24))


def render_frame(surface, idx, sim_t, fonts):
    surface.fill(BG)

    # Ground line at the bottom of the rocket panel
    pygame.draw.rect(surface, GROUND, (0, HEIGHT - 30, ROCKET_W, 30))

    # Rocket centered in left panel
    rocket_center = (ROCKET_W // 2, HEIGHT // 2 + 30)
    draw_rocket(surface, rocket_center, visible_tilt[idx])

    # Wind direction indicator (decorative; wind blows from the +x side toward -x,
    # so a stable rocket weathercocks INTO the wind, i.e. tips toward +x = right.)
    draw_wind_arrow(surface, rocket_center)
    surface.blit(fonts["sm"].render("wind", True, WIND_ARROW),
                 (rocket_center[0] - 220, rocket_center[1] - 270))

    # Status
    draw_status(surface, idx, sim_t, fonts["lg"], fonts["md"])

    # Divider
    pygame.draw.line(surface, PANEL_DIVIDER,
                     (ROCKET_W, 0), (ROCKET_W, HEIGHT), 2)

    # Time-series plot
    draw_graph(surface, idx, fonts["sm"])


# ---------- Main ----------
def run_live():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("5DOF Rocket — Ascent (live)")
    clock = pygame.time.Clock()
    fonts = {
        "lg": pygame.font.SysFont("arial", 22, bold=True),
        "md": pygame.font.SysFont("consolas", 18),
        "sm": pygame.font.SysFont("arial", 14),
    }

    start_real = pygame.time.get_ticks() / 1000.0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        sim_t = pygame.time.get_ticks() / 1000.0 - start_real
        if sim_t >= t_apogee_val:
            sim_t = t_apogee_val
            running = False

        idx = int(np.searchsorted(t_arr, sim_t, side="right") - 1)
        idx = max(0, min(idx, len(t_arr) - 1))

        render_frame(screen, idx, sim_t, fonts)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


def run_record():
    import imageio.v2 as imageio

    pygame.init()
    # Off-screen surface (no display required for recording)
    surface = pygame.Surface((WIDTH, HEIGHT))
    fonts = {
        "lg": pygame.font.SysFont("arial", 22, bold=True),
        "md": pygame.font.SysFont("consolas", 18),
        "sm": pygame.font.SysFont("arial", 14),
    }

    n_frames = int(np.ceil(t_apogee_val * FPS)) + 1
    print(f"Rendering {n_frames} frames at {FPS} fps "
          f"({n_frames / FPS:.1f} s real time) -> {OUT_VIDEO}", flush=True)

    writer = imageio.get_writer(OUT_VIDEO, fps=FPS, codec="libx264",
                                quality=8, pixelformat="yuv420p",
                                macro_block_size=1)
    try:
        for k in range(n_frames):
            sim_t = min(k / FPS, t_apogee_val)
            idx = int(np.searchsorted(t_arr, sim_t, side="right") - 1)
            idx = max(0, min(idx, len(t_arr) - 1))

            render_frame(surface, idx, sim_t, fonts)

            arr = pygame.surfarray.array3d(surface)  # (W, H, 3) in pygame's order
            arr = np.transpose(arr, (1, 0, 2))       # -> (H, W, 3) for imageio
            writer.append_data(arr)

            if k % 60 == 0:
                print(f"  frame {k}/{n_frames}  (sim t = {sim_t:5.1f} s)",
                      flush=True)
    finally:
        writer.close()
        pygame.quit()
    print(f"Done -> {OUT_VIDEO}")


if __name__ == "__main__":
    if MODE == "live":
        run_live()
    elif MODE == "record":
        run_record()
    else:
        print(f"Unknown MODE: {MODE!r}", file=sys.stderr)
        sys.exit(1)
