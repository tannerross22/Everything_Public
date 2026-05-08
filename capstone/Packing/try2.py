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
RHO_MATRIX         = 10.34     # g/cm³ (Density for NiCr binder)

# Particle weight ratio (within the particle phase only -- must sum to 1.0)
WT_LARGE = 0.77
WT_SMALL = 0.23

# --- Large Particle Properties ---
D_LARGE_MEAN       = 69.0      # µm
D_LARGE_STD        = 68.0      # µm
MIN_LARGE_DIAMETER = 25.0      # µm (lower bound for sampled diameter)
RHO_LARGE          = 16.4      # g/cm³

# --- Small Particle Properties ---
D_SMALL_MEAN       = 15.0      # µm
D_SMALL_STD        = 5.0       # µm
MIN_SMALL_DIAMETER = 5.0       # µm (lower bound for sampled diameter)
RHO_SMALL          = 15.8      # g/cm³ (can be different from large particles)

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

# Visualization
LARGE_COLOR    = "#2980B9"
LARGE_EDGE     = "#1B4F72"
SMALL_COLOR    = "#E67E22"
SMALL_EDGE     = "#7E3F0E"
MATRIX_COLOR   = "#E8E8E0"
DPI            = 150


# ── DERIVED CONSTANTS ─────────────────────────────────────────────────────────

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

assert abs(WT_LARGE + WT_SMALL - 1.0) < 1e-6, "WT_LARGE + WT_SMALL must equal 1.0"

# Calculate effective density of the particle phase for accurate vol% conversion
rho_p_inv = (WT_LARGE / RHO_LARGE) + (WT_SMALL / RHO_SMALL)
RHO_PARTICLE_EFFECTIVE = 1.0 / rho_p_inv

# Convert matrix weight fraction to volume fraction using effective particle density
w_m = MATRIX_WT_FRACTION
w_p = 1.0 - w_m
MATRIX_VOL_FRACTION = (w_m / RHO_MATRIX) / (w_m / RHO_MATRIX + w_p / RHO_PARTICLE_EFFECTIVE)

# Radii from diameters
R_L_MEAN = D_LARGE_MEAN / 2.0
R_L_STD = D_LARGE_STD / 2.0
R_L_MIN = MIN_LARGE_DIAMETER / 2.0
R_S_MEAN = D_SMALL_MEAN / 2.0
R_S_STD = D_SMALL_STD / 2.0
R_S_MIN = MIN_SMALL_DIAMETER / 2.0

# Window dimensions
WINDOW_H = WINDOW_H_MICRONS
WINDOW_W = WINDOW_W_MICRONS
WINDOW_AREA = WINDOW_W * WINDOW_H

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

# ── COMPOSITION CONVERSIONS ──────────────────────────────────────────────────

def compute_targets():
    """
    Convert composition inputs into target particle counts for the window.
    """
    # Step 1: weight ratio -> volume ratio within the particle phase
    inv_rho_L = WT_LARGE / RHO_LARGE
    inv_rho_S = WT_SMALL / RHO_SMALL
    vol_L_of_particles = inv_rho_L / (inv_rho_L + inv_rho_S)
    vol_S_of_particles = 1.0 - vol_L_of_particles

    # Step 2: total 3D volume fractions
    particles_vf_3d = 1.0 - MATRIX_VOL_FRACTION
    vol_L_3d = particles_vf_3d * vol_L_of_particles
    vol_S_3d = particles_vf_3d * vol_S_of_particles

    # Step 3: 2D area fractions
    area_L_target = vol_L_3d * VOL_TO_AREA_FACTOR
    area_S_target = vol_S_3d * VOL_TO_AREA_FACTOR

    # Step 4: target particle counts
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

def sample_radius(mean_r: float, std_dev: float, min_r: float) -> float:
    """Sample a radius from a normal distribution, clipped at min_r."""
    if std_dev > 0:
        return max(np.random.normal(loc=mean_r, scale=std_dev), min_r)
    return max(mean_r, min_r)


def place_particles(n_target, mean_r, std_dev, min_r, existing,
                    same_class_spacing, cross_class_gap,
                    max_tries=MAX_TRIES_PER_PLACEMENT):
    placed = []
    fails = 0
    while len(placed) < n_target and fails < max_tries:
        r = sample_radius(mean_r, std_dev, min_r)
        x = random.uniform(r, WINDOW_W - r)
        y = random.uniform(r, WINDOW_H - r)

        ok = True
        # Cross-class check (vs existing particles)
        for cx, cy, cr in existing:
            min_d = r + cr + cross_class_gap * min(r, cr)
            if (x - cx) ** 2 + (y - cy) ** 2 < min_d ** 2:
                ok = False
                break
        # Same-class check
        if ok:
            for cx, cy, cr in placed:
                min_d = r + cr + same_class_spacing * mean_r
                if (x - cx) ** 2 + (y - cy) ** 2 < min_d ** 2:
                    ok = False
                    break
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
        placed = place_particles(n_target, mean_r, std_dev, min_r, existing,
                                  spacing, cross_class_gap)
        coverage = len(placed) / max(n_target, 1)
        print(f"    [{label} attempt {attempt}, spacing={spacing:.3f}] "
              f"placed {len(placed)}/{n_target}  ({coverage*100:.1f}%)")
        if coverage >= 0.95 or spacing < 1e-3:
            return placed
        spacing *= RELAX_FACTOR
        attempt += 1


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 68)
    print("  COMPOSITION-DRIVEN 2D HARDFACING VISUALIZATION")
    print("=" * 68)

    print(f"\n  Composition inputs (by Weight):")
    print(f"    Matrix wt%:         {MATRIX_WT_FRACTION*100:.1f}%")
    print(f"    Particle wt% (L/S): {WT_LARGE*100:.1f}% / {WT_SMALL*100:.1f}%")
    print(f"    (Implied Matrix vol%): {MATRIX_VOL_FRACTION*100:.1f}% (3D)")

    t = compute_targets()

    print(f"\n  Derived 3D volume fractions of the total:")
    print(f"    Matrix:  {MATRIX_VOL_FRACTION*100:>5.2f}%")
    print(f"    Large:   {t['vol_L_3d']*100:>5.2f}%")
    print(f"    Small:   {t['vol_S_3d']*100:>5.2f}%")

    print(f"\n  2D area-fraction targets (factor = {VOL_TO_AREA_FACTOR:.3f}):")
    print(f"    Large:   {t['area_L_target']*100:>5.2f}%")
    print(f"    Small:   {t['area_S_target']*100:>5.2f}%")

    print(f"\n  Window: {WINDOW_W:.0f} x {WINDOW_H:.0f} µm")
    print(f"  Target counts: {t['n_L_target']} large + {t['n_S_target']} small")

    print(f"\n  Placing particles...")
    large = place_with_auto_relax(t["n_L_target"], R_L_MEAN, R_L_STD, R_L_MIN, [],
                                  INITIAL_LARGE_SPACING, 0.0, label="Large")
    small = place_with_auto_relax(t["n_S_target"], R_S_MEAN, R_S_STD, R_S_MIN, large,
                                  INITIAL_SMALL_SPACING, LARGE_SMALL_GAP, label="Small")

    # --- Verification ---
    A_L_actual = sum(np.pi * r ** 2 for _, _, r in large) / WINDOW_AREA
    A_S_actual = sum(np.pi * r ** 2 for _, _, r in small) / WINDOW_AREA
    A_total = A_L_actual + A_S_actual

    # --- Render ---
    print("\n  Rendering figure...")
    fig_h = 9
    fig_w = fig_h * (WINDOW_W / WINDOW_H)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))


    inv_factor = 1.0 / VOL_TO_AREA_FACTOR
    vol_L_implied = A_L_actual * inv_factor
    vol_S_implied = A_S_actual * inv_factor
    matrix_vol_implied = 1.0 - (vol_L_implied + vol_S_implied)

    mass_L = vol_L_implied * RHO_LARGE
    mass_S = vol_S_implied * RHO_SMALL
    mass_matrix = matrix_vol_implied * RHO_MATRIX
    total_particle_mass = mass_L + mass_S
    total_mass = total_particle_mass + mass_matrix
    matrix_wt_implied = mass_matrix / total_mass if total_mass > 0 else 0

    print("\n" + "=" * 68)
    print("  VERIFICATION — what the rendered image actually represents")
    print("=" * 68)
    print(f"\n  2D area fractions (achieved vs target):")
    print(f"    Large:    {A_L_actual*100:>5.2f}%   (target {t['area_L_target']*100:.2f}%)")
    print(f"    Small:    {A_S_actual*100:>5.2f}%   (target {t['area_S_target']*100:.2f}%)")
    print(f"    Total:    {A_total*100:>5.2f}%")
    print(f"\n  Implied 3D volume fractions:")
    print(f"    Matrix:   {matrix_vol_implied*100:>5.2f}%   (target {MATRIX_VOL_FRACTION*100:.1f}%)")
    print(f"\n  Implied total weight fractions:")
    print(f"    Matrix:   {matrix_wt_implied*100:>5.2f} wt%   (target {MATRIX_WT_FRACTION*100:.0f} wt%)")

    # --- MODIFIED: Set text and axis colors to be visible on dark background ---
    ax.set_xlabel("x (µm)", color=TEXT_COLOR)
    ax.set_ylabel("y (µm)", color=TEXT_COLOR)
    ax.tick_params(colors=AXIS_COLOR)
    ax.set_title(
        f"Hardfacing Cross-Section — Composition-Driven Layout\n"
        f"Matrix {MATRIX_WT_FRACTION * 100:.0f}wt% (3D) | Particles {WT_LARGE * 100:.0f}/{WT_SMALL * 100:.0f} wt% L/S\n"
        f"area: L {A_L_actual * 100:.1f}%, S {A_S_actual * 100:.1f}%, matrix bg {(1 - A_total) * 100:.1f}%",
        fontsize=10.5, fontweight="bold", color=TEXT_COLOR
    )
    for sp in ax.spines.values():
        sp.set_linewidth(1.0); sp.set_color("#444")

    plt.tight_layout()
    plt.savefig("hardfacing_cross_section_two_sizes.png", dpi=DPI,
                bbox_inches="tight", facecolor="white")
    plt.show()
    print("  Saved: hardfacing_cross_section_two_sizes.png")
    print("=" * 68)


if __name__ == "__main__":
    main()