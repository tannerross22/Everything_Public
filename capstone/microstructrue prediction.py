"""
Composition-Driven 2D Hardfacing Visualization
================================================
Builds a 2D cross-section visualization of a hardfacing layer where particle
counts are derived from the desired material composition (matrix volume
fraction + particle weight ratio + densities) rather than from a packing
simulation.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import random


# ── INPUTS ────────────────────────────────────────────────────────────────────

# Composition
MATRIX_WT_FRACTION = 0.40      # Fraction of total weight that is matrix
RHO_MATRIX         = 12     # g/cm³ (Density for NiCr binder)

# Particle weight ratio (within the particle phase only -- must sum to 1.0)
WT_LARGE = 0.50
WT_SMALL = 0.50

# --- Large Particle Properties ---
D_LARGE_MEAN       = 187.5      # µm
D_LARGE_STD        = 80      # µm
MIN_LARGE_DIAMETER = 125      # µm (lower bound for sampled diameter)
RHO_LARGE          = 15.8     # g/cm³

# --- Small Particle Properties ---
D_SMALL_MEAN       = 41      # µm
D_SMALL_STD        = 26       # µm
MIN_SMALL_DIAMETER = 15       # µm (lower bound for sampled diameter)
RHO_SMALL          = 16.5      # g/cm³ (can be different from large particles)

# --- Window Size (in microns) ---
WINDOW_W_MICRONS = 2137        # Window width in µm
WINDOW_H_MICRONS = 1274        # Window height in µm

# Stereology
VOL_TO_AREA_FACTOR = 2.0 / 3.0 # 3D volume fraction -> 2D area fraction factor

# Placement parameters
INITIAL_LARGE_SPACING = 0.01   # Initial gap between large particles (as fraction of radius)
INITIAL_SMALL_SPACING = 0.05   # Initial gap between small particles
LARGE_SMALL_GAP       = 0.10   # Gap between large and small particles
RELAX_FACTOR          = 0.4    # Spacing reduction factor on failed placement
MAX_TRIES_PER_PLACEMENT = 3000

RANDOM_SEED = 42

# --- MODIFIED: Visualization for high-contrast black & white style ---
MATRIX_COLOR   = "#333333"       # Dark grey background
LARGE_FACE_COLOR = "white"
LARGE_HATCH    = "++"
LARGE_EDGE_COLOR = "black"
SMALL_FACE_COLOR = "white"
SMALL_EDGE_COLOR = "black"
TEXT_COLOR = "white"
AXIS_COLOR = "#CCCCCC"           # Light grey for axes and ticks
DPI            = 150


# ── DERIVED CONSTANTS ─────────────────────────────────────────────────────────

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

assert abs(WT_LARGE + WT_SMALL - 1.0) < 1e-6, "WT_LARGE + WT_SMALL must equal 1.0"

rho_p_inv = (WT_LARGE / RHO_LARGE) + (WT_SMALL / RHO_SMALL)
RHO_PARTICLE_EFFECTIVE = 1.0 / rho_p_inv

w_m = MATRIX_WT_FRACTION
w_p = 1.0 - w_m
MATRIX_VOL_FRACTION = (w_m / RHO_MATRIX) / (w_m / RHO_MATRIX + w_p / RHO_PARTICLE_EFFECTIVE)

R_L_MEAN = D_LARGE_MEAN / 2.0
R_L_STD = D_LARGE_STD / 2.0
R_L_MIN = MIN_LARGE_DIAMETER / 2.0
R_S_MEAN = D_SMALL_MEAN / 2.0
R_S_STD = D_SMALL_STD / 2.0
R_S_MIN = MIN_SMALL_DIAMETER / 2.0

WINDOW_H = WINDOW_H_MICRONS
WINDOW_W = WINDOW_W_MICRONS
WINDOW_AREA = WINDOW_W * WINDOW_H


# ── COMPOSITION CONVERSIONS ──────────────────────────────────────────────────

def compute_targets():
    inv_rho_L = WT_LARGE / RHO_LARGE
    inv_rho_S = WT_SMALL / RHO_SMALL
    vol_L_of_particles = inv_rho_L / (inv_rho_L + inv_rho_S)
    vol_S_of_particles = 1.0 - vol_L_of_particles

    particles_vf_3d = 1.0 - MATRIX_VOL_FRACTION
    vol_L_3d = particles_vf_3d * vol_L_of_particles
    vol_S_3d = particles_vf_3d * vol_S_of_particles

    area_L_target = vol_L_3d * VOL_TO_AREA_FACTOR
    area_S_target = vol_S_3d * VOL_TO_AREA_FACTOR

    A_per_L = np.pi * R_L_MEAN ** 2
    A_per_S = np.pi * R_S_MEAN ** 2
    n_L = int(round(area_L_target * WINDOW_AREA / A_per_L)) if A_per_L > 0 else 0
    n_S = int(round(area_S_target * WINDOW_AREA / A_per_S)) if A_per_S > 0 else 0

    return {
        "vol_L_3d": vol_L_3d, "vol_S_3d": vol_S_3d,
        "area_L_target": area_L_target, "area_S_target": area_S_target,
        "n_L_target": n_L, "n_S_target": n_S,
    }


# ── PLACEMENT ─────────────────────────────────────────────────────────────────

def sample_radius(mean_r, std_dev, min_r):
    if std_dev > 0:
        return max(np.random.normal(loc=mean_r, scale=std_dev), min_r)
    return max(mean_r, min_r)


def place_particles(n_target, mean_r, std_dev, min_r, existing,
                    same_class_spacing, cross_class_gap, max_tries=MAX_TRIES_PER_PLACEMENT):
    placed = []
    fails = 0
    while len(placed) < n_target and fails < max_tries:
        r = sample_radius(mean_r, std_dev, min_r)
        x = random.uniform(r, WINDOW_W - r)
        y = random.uniform(r, WINDOW_H - r)

        ok = True
        for cx, cy, cr in existing:
            min_d = r + cr + cross_class_gap * min(r, cr)
            if (x - cx) ** 2 + (y - cy) ** 2 < min_d ** 2: ok = False; break
        if ok:
            for cx, cy, cr in placed:
                min_d = r + cr + same_class_spacing * mean_r
                if (x - cx) ** 2 + (y - cy) ** 2 < min_d ** 2: ok = False; break
        if not ok:
            fails += 1
            continue
        placed.append((x, y, r))
        fails = 0
    return placed


def place_with_auto_relax(n_target, mean_r, std_dev, min_r, existing,
                           initial_spacing, cross_class_gap, label=""):
    spacing = initial_spacing
    attempt = 1
    while True:
        placed = place_particles(n_target, mean_r, std_dev, min_r, existing, spacing, cross_class_gap)
        coverage = len(placed) / max(n_target, 1)
        print(f"    [{label} attempt {attempt}, spacing={spacing:.3f}] placed {len(placed)}/{n_target} ({coverage*100:.1f}%)")
        if coverage >= 0.95 or spacing < 1e-3: return placed
        spacing *= RELAX_FACTOR
        attempt += 1


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 68)
    print("  COMPOSITION-DRIVEN 2D HARDFACING VISUALIZATION")
    print("=" * 68)

    t = compute_targets()
    print(f"\n  Window: {WINDOW_W:.0f} x {WINDOW_H:.0f} µm")
    print(f"  Target counts: {t['n_L_target']} large + {t['n_S_target']} small")

    print(f"\n  Placing particles...")
    large = place_with_auto_relax(t["n_L_target"], R_L_MEAN, R_L_STD, R_L_MIN, [],
                                  INITIAL_LARGE_SPACING, 0.0, label="Large")
    small = place_with_auto_relax(t["n_S_target"], R_S_MEAN, R_S_STD, R_S_MIN, large,
                                  INITIAL_SMALL_SPACING, LARGE_SMALL_GAP, label="Small")

    A_L_actual = sum(np.pi * r ** 2 for _, _, r in large) / WINDOW_AREA
    A_S_actual = sum(np.pi * r ** 2 for _, _, r in small) / WINDOW_AREA
    A_total = A_L_actual + A_S_actual

    # --- Render ---
    print("\n  Rendering figure...")
    fig_h = 9
    fig_w = fig_h * (WINDOW_W / WINDOW_H)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    # --- MODIFIED: Set facecolor to match dark background ---
    fig.patch.set_facecolor(MATRIX_COLOR)
    ax.set_facecolor(MATRIX_COLOR)

    # --- MODIFIED: Add circles with new styles ---
    for x, y, r in large:
        ax.add_patch(Circle((x, y), r,
                            facecolor=LARGE_FACE_COLOR,
                            edgecolor=LARGE_EDGE_COLOR,
                            hatch=LARGE_HATCH,
                            linewidth=0.6))
    for x, y, r in small:
        ax.add_patch(Circle((x, y), r,
                            facecolor=SMALL_FACE_COLOR,
                            edgecolor=SMALL_EDGE_COLOR,
                            linewidth=0.5))

    ax.set_xlim(0, WINDOW_W); ax.set_ylim(0, WINDOW_H)
    ax.set_aspect("equal")

    # --- MODIFIED: Set text and axis colors to be visible on dark background ---
    ax.set_xlabel("x (µm)", color=TEXT_COLOR)
    ax.set_ylabel("y (µm)", color=TEXT_COLOR)
    ax.tick_params(colors=AXIS_COLOR)
    ax.set_title(
        f"Hardfacing Cross-Section — Composition-Driven Layout\n"
        f"Matrix {MATRIX_WT_FRACTION*100:.0f}wt% (3D) | Particles {WT_LARGE*100:.0f}/{WT_SMALL*100:.0f} wt% L/S\n"
        f"area: L {A_L_actual*100:.1f}%, S {A_S_actual*100:.1f}%, matrix bg {(1-A_total)*100:.1f}%",
        fontsize=10.5, fontweight="bold", color=TEXT_COLOR
    )
    for sp in ax.spines.values():
        sp.set_color(AXIS_COLOR)

    plt.tight_layout()
    plt.savefig("hardfacing_cross_section_bw.png", dpi=DPI, facecolor=fig.get_facecolor())
    plt.show()
    print("  Saved: hardfacing_cross_section_bw.png")
    print("=" * 68)


if __name__ == "__main__":
    main()