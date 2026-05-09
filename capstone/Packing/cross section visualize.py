"""
Composition-Driven 2D Hardfacing Cross-Section Visualizer
===========================================================
All composition inputs are in WEIGHT PERCENT.
Stereology: Delesse's Law (VOL_TO_AREA_FACTOR = 1.0 by default) — correct
for polished metallographic cross-sections. The 2D area fraction of a phase
in a random polished plane equals its 3D volume fraction.

Placement strategy
------------------
  Large particles : Jittered hexagonal grid. Grid spacing is solved
    analytically from the target area fraction, guaranteeing the target
    is met at any density. Random jitter (JITTER_FRACTION) makes the
    layout look like a real cross-section rather than a crystal.

  Small particles : Random sequential adsorption (RSA) in the gaps left
    by the large particles.

Visual style
------------
  Background   : Dark grey (represents NiCr matrix, like backscatter SEM)
  Large WC-Co  : White fill with diagonal hatch lines (grain contrast)
  Small WC     : Solid white (bright phase, fine particles)

Edit the INPUTS block and run.
"""

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle
import random


# ── INPUTS (all composition in wt%) ──────────────────────────────────────────

# Total blend weight fractions — must sum to 1.0
WT_MATRIX_TOTAL      = 0.40    # wt% NiCr matrix  in the full blend
WT_LARGE_TOTAL       = 0.90*(1-WT_MATRIX_TOTAL)    # wt% large WC-Co  in the full blend
WT_SMALL_TOTAL       = 0.10*(1-WT_MATRIX_TOTAL)    # wt% small WC     in the full blend

# Component densities (g/cm³)
RHO_MATRIX           = 8     # NiCrSiB self-fluxing alloy (NI40 ≈ 8.2–8.5)
RHO_LARGE            = 14.9     # WC-6Co sintered  (WOKA 50512)
RHO_SMALL            = 16.5     # spherical WC fines

# Particle sizes (µm)
D_LARGE_MEAN         = 188.0    # WOKA 50512 median diameter
D_LARGE_SPREAD       = 0.3     # ±20% size variation (uniform)
D_SMALL_MEAN         = 30.0     # small WC fines median
D_SMALL_SPREAD       = 0.2     # ±30% size variation (uniform)

# Stereological conversion factor
# 1.0 = Delesse's Law (correct for polished cross-sections)
# 2/3 = thin-section approximation (conservative)
VOL_TO_AREA_FACTOR   = 1.0

# Window
WINDOW_HEIGHT_IN_LARGE_DIAMETERS = 6
WINDOW_ASPECT        = 1.0      # width / height

# Placement — large particles (jittered hex grid)
JITTER_FRACTION      = 0.5     # 0 = crystalline | 0.5 = fully random
                                 # 0.35–0.45 looks most realistic

# Placement — small particles (RSA)
SMALL_SPACING        = 0.1     # extra gap between smalls (fraction of r_S mean)
LARGE_SMALL_GAP      = 0.1     # extra gap large-to-small  (fraction of r_S mean)
MAX_TRIES_SMALL      = 8000

RANDOM_SEED          = 4

# ── VISUAL STYLE ─────────────────────────────────────────────────────────────

MATRIX_BG_COLOR      = "#3A3A3A"   # dark grey background  — NiCr matrix

LARGE_FACE_COLOR     = "white"     # large particle fill
LARGE_EDGE_COLOR     = "#1A1A1A"   # large particle outline (near-black)
LARGE_HATCH          = "//"        # diagonal hatch lines
LARGE_HATCH_LW       = 0.7        # hatch line width (points)
LARGE_EDGE_LW        = 1.0         # outline line width

SMALL_FACE_COLOR     = "white"     # small particle fill  (solid white)
SMALL_EDGE_COLOR     = "#555555"   # small particle outline (mid-grey so it
                                   #   reads as distinct from large)
SMALL_EDGE_LW        = 0.5

TITLE_COLOR          = "white"
AXIS_COLOR           = "#AAAAAA"
DPI                  = 150


# ── DERIVED CONSTANTS ─────────────────────────────────────────────────────────

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

_wt_sum = WT_MATRIX_TOTAL + WT_LARGE_TOTAL + WT_SMALL_TOTAL
assert abs(_wt_sum - 1.0) < 1e-5, \
    f"Weight fractions must sum to 1.0 (got {_wt_sum:.6f})"

R_L_MEAN    = D_LARGE_MEAN / 2.0
R_S_MEAN    = D_SMALL_MEAN / 2.0
WINDOW_H    = WINDOW_HEIGHT_IN_LARGE_DIAMETERS * D_LARGE_MEAN
WINDOW_W    = WINDOW_H * WINDOW_ASPECT
WINDOW_AREA = WINDOW_W * WINDOW_H


# ── COMPOSITION CONVERSIONS ──────────────────────────────────────────────────

def wt_to_vol(wt_m, wt_l, wt_s, rho_m, rho_l, rho_s):
    """
    Three-component weight → volume fraction conversion.
    vol_i / vol_total = (wt_i / rho_i) / Σ(wt_j / rho_j)
    """
    a = wt_m / rho_m
    b = wt_l / rho_l
    c = wt_s / rho_s
    t = a + b + c
    return a/t, b/t, c/t


def vol_to_wt(vol_m, vol_l, vol_s, rho_m, rho_l, rho_s):
    """Three-component volume → weight fraction conversion."""
    masses = [vol_m * rho_m, vol_l * rho_l, vol_s * rho_s]
    t = sum(masses)
    return tuple(m / t for m in masses)


def compute_targets():
    vol_m, vol_l, vol_s = wt_to_vol(
        WT_MATRIX_TOTAL, WT_LARGE_TOTAL, WT_SMALL_TOTAL,
        RHO_MATRIX, RHO_LARGE, RHO_SMALL
    )
    area_l = vol_l * VOL_TO_AREA_FACTOR
    area_s = vol_s * VOL_TO_AREA_FACTOR
    wt_part = WT_LARGE_TOTAL + WT_SMALL_TOTAL
    return dict(
        vol_m=vol_m, vol_l=vol_l, vol_s=vol_s,
        area_l=area_l, area_s=area_s,
        n_l=int(round(area_l * WINDOW_AREA / (np.pi * R_L_MEAN**2))),
        n_s=int(round(area_s * WINDOW_AREA / (np.pi * R_S_MEAN**2))),
        wt_l_of_part=WT_LARGE_TOTAL / wt_part,
        wt_s_of_part=WT_SMALL_TOTAL / wt_part,
    )


def sample_radius(mean_r, spread):
    return mean_r * (1.0 + spread * (2.0 * random.random() - 1.0))


# ── LARGE PARTICLE PLACEMENT: JITTERED HEX GRID ──────────────────────────────

def hex_col_spacing(area_target, r_mean):
    """
    Column spacing such that circles of r_mean at each hex grid point
    cover exactly area_target of the plane.
    Derivation: pi*r² / ((√3/2)*col²) = area_target
    """
    return np.sqrt(np.pi * r_mean**2 / (area_target * np.sqrt(3) / 2))


def place_large_hex(area_target):
    col = hex_col_spacing(area_target, R_L_MEAN)
    row = col * np.sqrt(3) / 2
    gap = (col - 2 * R_L_MEAN) / 2
    jit = JITTER_FRACTION * max(gap, 0.0)

    placed = []
    r_idx  = 0
    y      = R_L_MEAN

    while y < WINDOW_H + row:
        x = R_L_MEAN + ((col / 2) if r_idx % 2 == 1 else 0.0)
        while x < WINDOW_W + col:
            r  = sample_radius(R_L_MEAN, D_LARGE_SPREAD)
            px = max(r, min(WINDOW_W - r, x + random.uniform(-jit, jit)))
            py = max(r, min(WINDOW_H - r, y + random.uniform(-jit, jit)))

            ok = all(
                (px - cx)**2 + (py - cy)**2 >= (r + cr)**2
                for cx, cy, cr in placed
            )
            if ok and r <= px <= WINDOW_W - r and r <= py <= WINDOW_H - r:
                placed.append((px, py, r))
            x += col

        y     += row
        r_idx += 1

    return placed


# ── SMALL PARTICLE PLACEMENT: RSA ────────────────────────────────────────────

def place_small_rsa(large, area_target):
    n_tgt  = int(round(area_target * WINDOW_AREA / (np.pi * R_S_MEAN**2)))
    placed = []
    fails  = 0

    while len(placed) < n_tgt and fails < MAX_TRIES_SMALL:
        r  = sample_radius(R_S_MEAN, D_SMALL_SPREAD)
        x  = random.uniform(r, WINDOW_W - r)
        y  = random.uniform(r, WINDOW_H - r)

        ok = all(
            (x - cx)**2 + (y - cy)**2 >=
            (r + cr + LARGE_SMALL_GAP * r)**2
            for cx, cy, cr in large
        )
        if ok:
            ok = all(
                (x - cx)**2 + (y - cy)**2 >=
                (r + cr + SMALL_SPACING * R_S_MEAN)**2
                for cx, cy, cr in placed
            )

        if not ok:
            fails += 1
            continue

        placed.append((x, y, r))
        fails = 0

    return placed, n_tgt


def area_fraction(circles):
    return sum(np.pi * r**2 for _, _, r in circles) / WINDOW_AREA


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 68)
    print("  HARDFACING CROSS-SECTION — COMPOSITION DRIVEN")
    print("=" * 68)

    t = compute_targets()

    print(f"\n  INPUT  (wt%):")
    print(f"    NiCr matrix   {WT_MATRIX_TOTAL*100:>5.1f}   ρ = {RHO_MATRIX} g/cm³")
    print(f"    Large WC-Co   {WT_LARGE_TOTAL*100:>5.1f}   ρ = {RHO_LARGE} g/cm³")
    print(f"    Small WC      {WT_SMALL_TOTAL*100:>5.1f}   ρ = {RHO_SMALL} g/cm³")

    print(f"\n  DERIVED 3D VOL%  (density-corrected):")
    print(f"    NiCr matrix   {t['vol_m']*100:>5.2f}")
    print(f"    Large WC-Co   {t['vol_l']*100:>5.2f}")
    print(f"    Small WC      {t['vol_s']*100:>5.2f}")
    print(f"    (Matrix lighter → larger vol% than wt%)")

    col_sp  = hex_col_spacing(t['area_l'], R_L_MEAN)
    half_gp = (col_sp - 2 * R_L_MEAN) / 2

    print(f"\n  2D AREA TARGETS  (factor = {VOL_TO_AREA_FACTOR:.2f}, Delesse):")
    print(f"    Large   {t['area_l']*100:>5.2f}%   → ~{t['n_l']} particles")
    print(f"    Small   {t['area_s']*100:>5.2f}%   → ~{t['n_s']} particles")
    print(f"    BG      {(1-t['area_l']-t['area_s'])*100:>5.2f}%")

    if half_gp < 0:
        print(f"\n  ⚠  TARGET TOO DENSE — would require overlapping particles.")
        print(f"     Max theoretical (tangent hex): 90.7% area.")
        print(f"     Reduce carbide wt% or increase particle size.")
        return

    print(f"\n  Hex grid: col = {col_sp:.1f} µm  |  gap = {2*half_gp:.1f} µm  |  "
          f"jitter ±{JITTER_FRACTION*half_gp:.1f} µm")

    print(f"\n  Placing large particles...")
    large = place_large_hex(t['area_l'])
    af_l  = area_fraction(large)
    print(f"    {len(large)} placed  →  {af_l*100:.2f}%  (target {t['area_l']*100:.2f}%)")

    print(f"  Placing small particles...")
    small, n_s_tgt = place_small_rsa(large, t['area_s'])
    af_s  = area_fraction(small)
    print(f"    {len(small)}/{n_s_tgt} placed  →  {af_s*100:.2f}%  (target {t['area_s']*100:.2f}%)")

    # ── Back-calculate achieved wt% ───────────────────────────────────────────
    inv_f      = 1.0 / VOL_TO_AREA_FACTOR
    vol_l_ach  = af_l  * inv_f
    vol_s_ach  = af_s  * inv_f
    vol_m_ach  = 1.0 - vol_l_ach - vol_s_ach

    wt_m_ach, wt_l_ach, wt_s_ach = vol_to_wt(
        vol_m_ach, vol_l_ach, vol_s_ach,
        RHO_MATRIX, RHO_LARGE, RHO_SMALL
    )
    wt_part_ach = wt_l_ach + wt_s_ach
    wt_l_part   = wt_l_ach / wt_part_ach if wt_part_ach > 0 else 0
    wt_s_part   = wt_s_ach / wt_part_ach if wt_part_ach > 0 else 0

    print("\n" + "=" * 68)
    print("  ACHIEVED COMPOSITION")
    print("=" * 68)
    print(f"\n  {'Component':<22} {'Achieved wt%':>13}   {'Target wt%':>11}   {'Error':>7}")
    print(f"  {'─'*60}")
    print(f"  {'NiCr matrix':<22} {wt_m_ach*100:>12.2f}%   "
          f"{WT_MATRIX_TOTAL*100:>10.1f}%   {(wt_m_ach-WT_MATRIX_TOTAL)*100:>+6.2f}%")
    print(f"  {'Large WC-Co':<22} {wt_l_ach*100:>12.2f}%   "
          f"{WT_LARGE_TOTAL*100:>10.1f}%   {(wt_l_ach-WT_LARGE_TOTAL)*100:>+6.2f}%")
    print(f"  {'Small WC':<22} {wt_s_ach*100:>12.2f}%   "
          f"{WT_SMALL_TOTAL*100:>10.1f}%   {(wt_s_ach-WT_SMALL_TOTAL)*100:>+6.2f}%")
    print(f"\n  Particle phase split:")
    print(f"  {'Large (of carbides)':<22} {wt_l_part*100:>12.2f}%   "
          f"{t['wt_l_of_part']*100:>10.1f}%")
    print(f"  {'Small (of carbides)':<22} {wt_s_part*100:>12.2f}%   "
          f"{t['wt_s_of_part']*100:>10.1f}%")

    # ── Render ────────────────────────────────────────────────────────────────
    print(f"\n  Rendering figure...")

    # Bump up hatch line density via rcParams before drawing
    matplotlib.rcParams['hatch.linewidth'] = LARGE_HATCH_LW

    fig_h = 9
    fig_w = fig_h * WINDOW_ASPECT
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.patch.set_facecolor(MATRIX_BG_COLOR)
    ax.set_facecolor(MATRIX_BG_COLOR)

    # Large particles — hatched
    for x, y, r in large:
        ax.add_patch(Circle(
            (x, y), r,
            facecolor  = LARGE_FACE_COLOR,
            edgecolor  = LARGE_EDGE_COLOR,
            hatch      = LARGE_HATCH,
            linewidth  = LARGE_EDGE_LW,
            zorder     = 2,
        ))

    # Small particles — solid white, on top
    for x, y, r in small:
        ax.add_patch(Circle(
            (x, y), r,
            facecolor  = SMALL_FACE_COLOR,
            edgecolor  = SMALL_EDGE_COLOR,
            linewidth  = SMALL_EDGE_LW,
            zorder     = 3,
        ))

    ax.set_xlim(0, WINDOW_W)
    ax.set_ylim(0, WINDOW_H)
    ax.set_aspect("equal")

    # Axis styling for dark background
    ax.set_xlabel("x (µm)", fontsize=10, color=AXIS_COLOR)
    ax.set_ylabel("y (µm)", fontsize=10, color=AXIS_COLOR)
    ax.tick_params(colors=AXIS_COLOR)
    for sp in ax.spines.values():
        sp.set_edgecolor(AXIS_COLOR)
        sp.set_linewidth(0.8)

    # Legend
    legend_handles = [
        mpatches.Patch(
            facecolor=LARGE_FACE_COLOR, edgecolor=LARGE_EDGE_COLOR,
            hatch=LARGE_HATCH, linewidth=LARGE_EDGE_LW,
            label=f"Large WC-Co  d={D_LARGE_MEAN:.0f}µm  "
                  f"({wt_l_ach*100:.1f} wt% achieved)"
        ),
        mpatches.Patch(
            facecolor=SMALL_FACE_COLOR, edgecolor=SMALL_EDGE_COLOR,
            linewidth=SMALL_EDGE_LW,
            label=f"Small WC  d={D_SMALL_MEAN:.0f}µm  "
                  f"({wt_s_ach*100:.1f} wt% achieved)"
        ),
        mpatches.Patch(
            facecolor=MATRIX_BG_COLOR, edgecolor=AXIS_COLOR,
            linewidth=0.6,
            label=f"NiCr matrix  ({wt_m_ach*100:.1f} wt% achieved)"
        ),
    ]
    leg = ax.legend(
        handles    = legend_handles,
        loc        = "upper right",
        fontsize   = 8.5,
        framealpha = 0.25,
        frameon    = True,
        edgecolor  = AXIS_COLOR,
        facecolor  = "#2A2A2A",
        labelcolor = "white",
    )

    # Title
    ax.set_title(
        f"Hardfacing Cross-Section  —  Composition-Driven  "
        f"(Jittered Hex + RSA,  Delesse factor = {VOL_TO_AREA_FACTOR:.1f})\n"
        f"Input:     Matrix {WT_MATRIX_TOTAL*100:.1f} wt%  |  "
        f"Large {WT_LARGE_TOTAL*100:.1f} wt%  |  "
        f"Small {WT_SMALL_TOTAL*100:.1f} wt%\n"
        f"Achieved:  Matrix {wt_m_ach*100:.1f} wt%  |  "
        f"Large {wt_l_ach*100:.1f} wt%  |  "
        f"Small {wt_s_ach*100:.1f} wt%   "
        f"[{len(large)} L + {len(small)} S]",
        fontsize  = 10,
        fontweight= "bold",
        color     = TITLE_COLOR,
        pad       = 10,
    )

    plt.tight_layout()
    out = "hardfacing_cross_section.png"
    plt.savefig(
        out, dpi=DPI, bbox_inches="tight",
        facecolor=MATRIX_BG_COLOR
    )
    plt.show()
    print(f"  Saved: {out}")
    print("=" * 68)


if __name__ == "__main__":
    main()