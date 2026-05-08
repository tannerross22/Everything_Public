"""
Bimodal Particle Packing Visualizer
====================================
Builds a 2D visualization of a bimodal hard-particle packing in a rectangular
window, mimicking how WOKA 50512 (large WC-Co pellets) and small spherical WC
fines might pack together inside a hardfacing layer.

Two-phase algorithm
-------------------
Phase 1 — LARGE particles (tangent propagation):
    Seed one circle in a corner. Each new circle is placed tangent to a
    randomly chosen existing circle at a random angle. Reject if it overlaps
    anything else or escapes the window. Continues until N consecutive failures
    indicate the structure has jammed.

Phase 2 — SMALL particles (rejection sampling):
    Repeatedly drop random small circles into the domain. Keep any that fit
    in the gaps without overlapping. Continues until N consecutive failures
    indicate the gaps are saturated.

A spatial hash grid accelerates collision checks so the script stays fast
even with thousands of circles.

Edit the INPUTS block and run.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import random
from collections import defaultdict

# ── INPUTS ────────────────────────────────────────────────────────────────────

# Particle sizes (median diameters in µm)
D_LARGE_MEAN     = 188.0       # WOKA 50512 median
D_LARGE_SPREAD   = 0.20        # ±20% size variation around the mean
D_SMALL_MEAN     = 30.0        # spherical WC fines median
D_SMALL_SPREAD   = 0.30        # ±30% size variation around the mean

# Window: measured in "large-diameter units" tall
WINDOW_HEIGHT_IN_LARGE_DIAMETERS = 20
WINDOW_ASPECT_RATIO              = 1.0     # width / height (1.0 = square)

# Algorithm limits
MAX_LARGE_ATTEMPTS  = 50_000
MAX_LARGE_FAILS     = 5_000      # stop large phase after this many consecutive misses
MAX_SMALL_ATTEMPTS  = 200_000
MAX_SMALL_FAILS     = 10_000     # stop small phase after this many consecutive misses

RANDOM_SEED         = 42

# Visualization
LARGE_COLOR  = "#2980B9"
LARGE_EDGE   = "#1B4F72"
SMALL_COLOR  = "#E67E22"
SMALL_EDGE   = "#7E3F0E"
BG_COLOR     = "#FAFAFA"
DPI          = 150


# ── DERIVED CONSTANTS ─────────────────────────────────────────────────────────

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

R_L_MEAN = D_LARGE_MEAN / 2.0
R_S_MEAN = D_SMALL_MEAN / 2.0

WINDOW_H = WINDOW_HEIGHT_IN_LARGE_DIAMETERS * D_LARGE_MEAN
WINDOW_W = WINDOW_H * WINDOW_ASPECT_RATIO

# Spatial hash grid: cell size = largest possible particle diameter so any
# overlap check needs to look at most 9 neighboring cells.
GRID_CELL = D_LARGE_MEAN * (1 + D_LARGE_SPREAD)


# ── SPATIAL HASH GRID ─────────────────────────────────────────────────────────

class SpatialGrid:
    """
    A uniform-grid spatial hash for fast circle-overlap queries.

    Each circle is registered into the cell containing its center. Lookups
    return all circles in the 3x3 neighborhood of cells around a query point,
    which is sufficient as long as cell_size >= max particle diameter.
    """

    def __init__(self, cell_size: float):
        self.cell  = cell_size
        self.cells = defaultdict(list)

    def _key(self, x: float, y: float):
        return (int(x // self.cell), int(y // self.cell))

    def insert(self, x: float, y: float, r: float):
        self.cells[self._key(x, y)].append((x, y, r))

    def neighbors(self, x: float, y: float):
        ix, iy = self._key(x, y)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                bucket = self.cells.get((ix + dx, iy + dy))
                if bucket:
                    yield from bucket


# ── GEOMETRY HELPERS ──────────────────────────────────────────────────────────

def sample_radius(mean_r: float, spread: float) -> float:
    """Uniform sample in mean_r * (1 ± spread)."""
    return mean_r * (1.0 + spread * (2.0 * random.random() - 1.0))


def overlaps(x: float, y: float, r: float, grid: SpatialGrid,
             tol: float = 1e-6) -> bool:
    """True if a circle at (x,y,r) overlaps any circle already in the grid."""
    for cx, cy, cr in grid.neighbors(x, y):
        rsum = r + cr - tol
        if (x - cx) ** 2 + (y - cy) ** 2 < rsum * rsum:
            return True
    return False


def in_window(x: float, y: float, r: float) -> bool:
    """True if circle is fully inside the window."""
    return (r <= x <= WINDOW_W - r) and (r <= y <= WINDOW_H - r)


# ── PHASE 1: LARGE PARTICLES (tangent propagation) ───────────────────────────

def place_large_particles():
    grid    = SpatialGrid(GRID_CELL)
    circles = []

    # Seed in the top-right corner so growth fans inward
    seed_r = sample_radius(R_L_MEAN, D_LARGE_SPREAD)
    seed_x = WINDOW_W - seed_r - 1.0
    seed_y = WINDOW_H - seed_r - 1.0
    circles.append((seed_x, seed_y, seed_r))
    grid.insert(seed_x, seed_y, seed_r)

    attempts  = 0
    fail_run  = 0

    while attempts < MAX_LARGE_ATTEMPTS and fail_run < MAX_LARGE_FAILS:
        attempts += 1

        # Anchor: a randomly chosen existing circle
        ax, ay, ar = random.choice(circles)
        # Candidate: tangent to anchor at a random angle
        new_r  = sample_radius(R_L_MEAN, D_LARGE_SPREAD)
        theta  = random.uniform(0.0, 2.0 * np.pi)
        d      = ar + new_r
        nx     = ax + d * np.cos(theta)
        ny     = ay + d * np.sin(theta)

        if not in_window(nx, ny, new_r):
            fail_run += 1; continue
        if overlaps(nx, ny, new_r, grid):
            fail_run += 1; continue

        circles.append((nx, ny, new_r))
        grid.insert(nx, ny, new_r)
        fail_run = 0

    return circles, grid, attempts


# ── PHASE 2: SMALL PARTICLES (rejection sampling) ────────────────────────────

def place_small_particles(grid: SpatialGrid):
    """
    Drops small particles into random positions in the domain. Keeps any that
    fit without overlapping existing circles (large or small). The provided
    grid already contains the large particles and is updated as small
    particles are added.
    """
    circles  = []
    attempts = 0
    fail_run = 0

    while attempts < MAX_SMALL_ATTEMPTS and fail_run < MAX_SMALL_FAILS:
        attempts += 1
        new_r = sample_radius(R_S_MEAN, D_SMALL_SPREAD)
        nx    = random.uniform(new_r, WINDOW_W - new_r)
        ny    = random.uniform(new_r, WINDOW_H - new_r)

        if overlaps(nx, ny, new_r, grid):
            fail_run += 1; continue

        circles.append((nx, ny, new_r))
        grid.insert(nx, ny, new_r)
        fail_run = 0

    return circles, attempts


# ── METRICS ───────────────────────────────────────────────────────────────────

def area_fraction(circles, total_area: float) -> float:
    return sum(np.pi * r * r for _, _, r in circles) / total_area


# ── PLOT ──────────────────────────────────────────────────────────────────────

def render(large, small, save_path: str = "bimodal_packing_visual.png"):
    total_area = WINDOW_W * WINDOW_H
    af_L = area_fraction(large, total_area)
    af_S = area_fraction(small, total_area)
    af_total = af_L + af_S

    fig_h = 9
    fig_w = fig_h * WINDOW_ASPECT_RATIO
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(BG_COLOR)

    for x, y, r in large:
        ax.add_patch(Circle((x, y), r, facecolor=LARGE_COLOR,
                            edgecolor=LARGE_EDGE, linewidth=0.6))
    for x, y, r in small:
        ax.add_patch(Circle((x, y), r, facecolor=SMALL_COLOR,
                            edgecolor=SMALL_EDGE, linewidth=0.25))

    ax.set_xlim(0, WINDOW_W)
    ax.set_ylim(0, WINDOW_H)
    ax.set_aspect("equal")
    ax.set_xlabel("x (µm)", fontsize=10)
    ax.set_ylabel("y (µm)", fontsize=10)
    ax.set_title(
        f"Bimodal Packing  —  d_L = {D_LARGE_MEAN:.0f} µm,  d_S = {D_SMALL_MEAN:.0f} µm,"
        f"  u = {D_LARGE_MEAN/D_SMALL_MEAN:.1f}\n"
        f"{len(large)} large + {len(small)} small  |  "
        f"Area fractions: large {af_L*100:.1f}%, small {af_S*100:.1f}%, total {af_total*100:.1f}%",
        fontsize=11, fontweight="bold"
    )
    for sp in ax.spines.values():
        sp.set_linewidth(1.0); sp.set_color("#444")

    plt.tight_layout()
    plt.savefig(save_path, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.show()
    return af_L, af_S, af_total


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 64)
    print("  BIMODAL PARTICLE PACKING VISUALIZER")
    print("=" * 64)
    print(f"  Window:           {WINDOW_W:.0f} × {WINDOW_H:.0f} µm")
    print(f"  Large diameter:   {D_LARGE_MEAN:.0f} µm  (±{D_LARGE_SPREAD*100:.0f}%)")
    print(f"  Small diameter:   {D_SMALL_MEAN:.0f} µm  (±{D_SMALL_SPREAD*100:.0f}%)")
    print(f"  Size ratio u:     {D_LARGE_MEAN/D_SMALL_MEAN:.2f}")

    print("\n  Phase 1: placing large particles (tangent propagation)...")
    large, grid, n_attempts_L = place_large_particles()
    print(f"    placed {len(large)} large particles ({n_attempts_L} attempts)")

    print("  Phase 2: placing small particles (rejection sampling)...")
    small, n_attempts_S = place_small_particles(grid)
    print(f"    placed {len(small)} small particles ({n_attempts_S} attempts)")

    print("\n  Rendering figure...")
    af_L, af_S, af_total = render(large, small)

    print("\n" + "=" * 64)
    print(f"  Large area fraction:    {af_L*100:.2f}%")
    print(f"  Small area fraction:    {af_S*100:.2f}%")
    print(f"  Total packed fraction:  {af_total*100:.2f}%")
    print("=" * 64)
    print(
        "\n  Note: 2D area fractions run ~10–15% higher than 3D volume\n"
        "  fractions for the same packing logic, so this 2D figure is a\n"
        "  qualitative visualization, not a direct prediction of the 3D\n"
        "  Furnas/Brouwers result."
    )