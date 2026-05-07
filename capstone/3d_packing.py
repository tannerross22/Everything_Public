"""
Gravitational Sphere Deposition Packing Simulator
==================================================
Implementation of the dropping/rolling algorithm from Shi & Zhang (2008),
"Simulation of random packing of spherical particles with different size
distributions", Appl. Phys. A 92:621–626.

This produces *physical* random loose packing (~0.58 monosize, ~0.60–0.625
bimodal) rather than the loose ballistic-deposition values (~0.45) you'd get
from pure tangent-propagation. The key difference is that each new sphere
finds a stable resting position by rolling under "gravity" until it touches
three other spheres (or the floor) in a stable configuration.

Algorithm summary
-----------------
1. Pick a random (x, y) and drop a new sphere from above.
2. It descends in -z until it hits the floor or another sphere (1st contact).
3. If on a sphere, roll in the vertical plane through that sphere's center
   until 2nd contact or floor.
4. With two contacts, roll along the "double contact circle" (intersection of
   the two constraint spheres around each contact) until 3rd contact or floor.
5. Check stability: the sphere is stable iff its xy projection lies inside
   the triangle of its three contact points. If unstable, drop the oldest
   contact and continue rolling on the remaining two.
6. Periodic boundaries on the four vertical walls eliminate edge effects.

Underspecified details I had to design
--------------------------------------
* Bisection at contact: when an arc-step finds an overlap, bisect between
  the previous (clear) angle and the current (overlap) angle to find the
  exact tangent position.
* "Most unstable rolling direction" when stability check fails: I drop the
  oldest of the three contacts and continue rolling on the two newest. This
  is a simple heuristic; the paper's "most steeply descending" criterion
  could be implemented but is rarely needed in practice.
* Periodic image handling during rolling: I use the minimum-image convention
  for relative positions and iterate over the 3x3 set of xy-images when
  checking for collisions.

Edit the INPUTS block and run.
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from collections import defaultdict
import random
import time


# ── INPUTS ────────────────────────────────────────────────────────────────────

# Particle sizes (median diameters in µm)
D_LARGE_MEAN     = 188.0
D_LARGE_SPREAD   = 0.20         # ±20% size variation
D_SMALL_MEAN     = 30.0
D_SMALL_SPREAD   = 0.30         # ±30% size variation

# Densities (g/cm³)
RHO_LARGE        = 14.9         # WC-6Co sintered
RHO_SMALL        = 16.5         # spherical WC fines

# Box: dimensionless units = multiples of D_LARGE_MEAN
# Shi-Zhang recommend a box at least 30x30x35 in units of small-particle radii;
# here we set it in large-diameter units. Note that at high size ratios
# (u >> 1) the small-particle count needed for a meaningful volume share
# scales as u^3, so each large diameter of box length adds ~250 small spheres.
# 3-4 large diameters per side gives a usable visualization in a few minutes.
BOX_X_DIAMS      = 3
BOX_Y_DIAMS      = 3
BOX_Z_DIAMS      = 4

# How many particles to deposit before stopping. The simulation stops earlier
# if the heap reaches the top of the box.
TARGET_PARTICLES = 800
SMALL_VOL_FRACTION = 0.20       # Target ratio of small-particle volume to total
                                 # carbide volume in the deposited blend.
                                 # Small particles take much less volume each,
                                 # so a 20% target volume share corresponds to
                                 # ~250x as many small particles as large ones.
                                 # Brouwers/Furnas predicts ~25 vol% small for
                                 # u≈6, so 0.20–0.25 is the realistic range.

# Algorithm parameters
ARC_STEPS        = 240          # angular resolution when rolling
MAX_REROLLS      = 12           # stability search depth
RANDOM_SEED      = 42

# Visualization
SHOW_PLOT        = True
CUTAWAY          = True         # hide one octant for visibility
SPHERE_FACETS    = 12           # mesh resolution per drawn sphere
DPI              = 130


# ── DERIVED CONSTANTS ─────────────────────────────────────────────────────────

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

LX = BOX_X_DIAMS * D_LARGE_MEAN
LY = BOX_Y_DIAMS * D_LARGE_MEAN
LZ = BOX_Z_DIAMS * D_LARGE_MEAN

R_L_MEAN = D_LARGE_MEAN / 2.0
R_S_MEAN = D_SMALL_MEAN / 2.0
R_MAX    = R_L_MEAN * (1.0 + D_LARGE_SPREAD)

EPS = 1e-9


# ── SPATIAL HASH GRID ─────────────────────────────────────────────────────────

class SpatialGrid:
    """3D uniform-cell spatial hash for fast neighbor queries."""

    def __init__(self, cell: float):
        self.cell  = cell
        self.cells = defaultdict(list)

    def _key(self, x, y, z):
        return (int(x // self.cell), int(y // self.cell), int(z // self.cell))

    def insert(self, idx, x, y, z):
        self.cells[self._key(x, y, z)].append(idx)

    def neighbors(self, x, y, z):
        ix, iy, iz = self._key(x, y, z)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    bucket = self.cells.get((ix + dx, iy + dy, iz + dz))
                    if bucket:
                        yield from bucket


# ── GLOBAL STATE ──────────────────────────────────────────────────────────────

# spheres[i] = (x, y, z, r)
spheres: list = []
grid = SpatialGrid(cell=2.2 * R_MAX)


# ── HELPER FUNCTIONS ──────────────────────────────────────────────────────────

def wrap_xy(x: float, y: float):
    return x % LX, y % LY


def sample_radius(mean_r: float, spread: float) -> float:
    return mean_r * (1.0 + spread * (2.0 * random.random() - 1.0))


def candidates_near(x: float, y: float, z: float, search_r: float):
    """All sphere indices within search_r of (x,y,z), considering periodic xy."""
    seen = set()
    # Iterate over periodic images of the query point
    for dx_img in (-LX, 0, LX):
        for dy_img in (-LY, 0, LY):
            qx, qy = x + dx_img, y + dy_img
            for j in grid.neighbors(qx, qy, z):
                seen.add(j)
    return seen


def min_image_delta(x1, y1, x2, y2):
    """Min-image (dx, dy) from (x2,y2) to (x1,y1)."""
    dx = x1 - x2
    dy = y1 - y2
    dx -= LX * round(dx / LX)
    dy -= LY * round(dy / LY)
    return dx, dy


# ── DROPPING (PHASE 1 OF DEPOSIT) ─────────────────────────────────────────────

def drop_straight_down(x: float, y: float, r: float):
    """
    Drop sphere of radius r from high z down at (x,y). Returns (z_final, idx)
    where idx is the sphere index hit, or None if it lands on the floor.
    """
    best_z   = r
    best_idx = None

    # We need to consider all spheres whose xy column-distance is < r + sr
    # Use periodic images. Brute force is O(N) but acceptable since this is
    # called once per deposit attempt.
    for j, (sx, sy, sz, sr) in enumerate(spheres):
        rsum_sq = (r + sr) ** 2
        # Only consider images whose xy column is within reach
        for dx_img in (-LX, 0, LX):
            for dy_img in (-LY, 0, LY):
                rx, ry = sx + dx_img, sy + dy_img
                d_xy_sq = (x - rx) ** 2 + (y - ry) ** 2
                if d_xy_sq >= rsum_sq:
                    continue
                z_contact = sz + np.sqrt(rsum_sq - d_xy_sq)
                if z_contact > best_z + EPS:
                    best_z   = z_contact
                    best_idx = j

    return best_z, best_idx


# ── ROLLING ON ONE SPHERE ─────────────────────────────────────────────────────

def roll_on_one(B_pos, rB, A_idx):
    """
    Sphere B (at B_pos, radius rB) rests on sphere A. Roll B in the vertical
    plane through A's center until B contacts another sphere (or floor) or
    reaches directly below A.
    Returns (new_pos, contact_idx) or (new_pos, None) if it rolls off to the floor.
    """
    Ax, Ay, Az, rA = spheres[A_idx]
    R = rA + rB

    # Angle phi (xy direction from A to B, fixed during this roll)
    dx, dy = min_image_delta(B_pos[0], B_pos[1], Ax, Ay)
    dz = B_pos[2] - Az

    phi = np.arctan2(dy, dx)
    horiz = np.sqrt(dx * dx + dy * dy)
    theta_now = np.arctan2(horiz, dz)  # current polar angle from +z axis

    # Sweep theta from theta_now to pi (directly below A)
    thetas = np.linspace(theta_now, np.pi, ARC_STEPS + 1)

    prev_pos = (B_pos[0], B_pos[1], B_pos[2])
    for k in range(1, len(thetas)):
        theta = thetas[k]
        nx = Ax + R * np.sin(theta) * np.cos(phi)
        ny = Ay + R * np.sin(theta) * np.sin(phi)
        nz = Az + R * np.cos(theta)
        nx, ny = wrap_xy(nx, ny)

        # Floor check
        if nz < rB - EPS:
            # Bisect for exact floor crossing
            lo, hi = thetas[k - 1], thetas[k]
            for _ in range(30):
                mid = 0.5 * (lo + hi)
                mz  = Az + R * np.cos(mid)
                if mz < rB:
                    hi = mid
                else:
                    lo = mid
            mx = Ax + R * np.sin(lo) * np.cos(phi)
            my = Ay + R * np.sin(lo) * np.sin(phi)
            mz = Az + R * np.cos(lo)
            mx, my = wrap_xy(mx, my)
            return (mx, my, max(mz, rB)), None

        # Sphere contact check (with grid acceleration)
        hit_idx = None
        cands = candidates_near(nx, ny, nz, R_MAX + rB)
        for j in cands:
            if j == A_idx:
                continue
            sx, sy, sz, sr = spheres[j]
            rsum = rB + sr
            ddx, ddy = min_image_delta(nx, ny, sx, sy)
            d2 = ddx * ddx + ddy * ddy + (nz - sz) ** 2
            if d2 < rsum * rsum - EPS:
                hit_idx = j
                break

        if hit_idx is not None:
            # Bisect for tangent position
            sx, sy, sz, sr = spheres[hit_idx]
            rsum = rB + sr
            lo_t, hi_t = thetas[k - 1], thetas[k]
            for _ in range(30):
                mid = 0.5 * (lo_t + hi_t)
                mx  = Ax + R * np.sin(mid) * np.cos(phi)
                my  = Ay + R * np.sin(mid) * np.sin(phi)
                mz  = Az + R * np.cos(mid)
                mx_w, my_w = wrap_xy(mx, my)
                ddx, ddy = min_image_delta(mx_w, my_w, sx, sy)
                d2 = ddx * ddx + ddy * ddy + (mz - sz) ** 2
                if d2 < rsum * rsum:
                    hi_t = mid
                else:
                    lo_t = mid
            mx = Ax + R * np.sin(lo_t) * np.cos(phi)
            my = Ay + R * np.sin(lo_t) * np.sin(phi)
            mz = Az + R * np.cos(lo_t)
            mx, my = wrap_xy(mx, my)
            return (mx, my, mz), hit_idx

        prev_pos = (nx, ny, nz)

    # Reached theta = pi (directly below A) without contact — should be at floor
    return prev_pos, None


# ── ROLLING ON TWO SPHERES ────────────────────────────────────────────────────

def roll_on_two(B_pos, rB, A_idx, C_idx):
    """
    B rests on A and C. Roll B along the circle that is the intersection of
    spheres of radii (rA+rB) around A and (rC+rB) around C, decreasing z,
    until contact with a third sphere/floor or the bottom of the circle is
    reached.
    Returns (new_pos, contact_idx) or (None, None) if the constraint fails.
    """
    Ax, Ay, Az, rA = spheres[A_idx]
    Cx, Cy, Cz, rC = spheres[C_idx]

    # Min-image C relative to A
    dxC, dyC = min_image_delta(Cx, Cy, Ax, Ay)
    A_pos = np.array([Ax, Ay, Az])
    C_img = np.array([Ax + dxC, Ay + dyC, Cz])
    R1, R2 = rA + rB, rC + rB
    d_AC = np.linalg.norm(C_img - A_pos)

    # Validate the geometry
    if d_AC > R1 + R2 - EPS or d_AC < abs(R1 - R2) + EPS:
        return None, None

    a = (d_AC ** 2 + R1 ** 2 - R2 ** 2) / (2 * d_AC)
    h_sq = R1 ** 2 - a ** 2
    if h_sq <= EPS:
        return None, None
    h = np.sqrt(h_sq)

    # Circle center and basis
    n_AC = (C_img - A_pos) / d_AC
    cc   = A_pos + a * n_AC
    helper = (np.array([1.0, 0.0, 0.0]) if abs(n_AC[0]) < 0.9
              else np.array([0.0, 1.0, 0.0]))
    e1 = np.cross(n_AC, helper); e1 /= np.linalg.norm(e1)
    e2 = np.cross(n_AC, e1)

    # Current B angle on the circle
    dxB, dyB = min_image_delta(B_pos[0], B_pos[1], Ax, Ay)
    rel = np.array([Ax + dxB, Ay + dyB, B_pos[2]]) - cc
    theta_now = np.arctan2(np.dot(rel, e2), np.dot(rel, e1))

    # Pick rolling direction (decreasing z)
    dz_dtheta = h * (-np.sin(theta_now) * e1[2] + np.cos(theta_now) * e2[2])
    sign = -1.0 if dz_dtheta > 0 else 1.0

    prev_z = B_pos[2]
    prev_pos = (B_pos[0], B_pos[1], B_pos[2])

    for k in range(1, ARC_STEPS + 1):
        theta = theta_now + sign * (k * np.pi / ARC_STEPS)
        cand  = cc + h * (np.cos(theta) * e1 + np.sin(theta) * e2)
        nx_w, ny_w = wrap_xy(cand[0], cand[1])
        nz = cand[2]

        # Stop if we've passed the bottom of the circle
        if nz > prev_z + EPS:
            return prev_pos, None

        # Floor
        if nz < rB - EPS:
            return (nx_w, ny_w, rB), None

        # Third-sphere contact
        cands = candidates_near(nx_w, ny_w, nz, R_MAX + rB)
        hit_idx = None
        for j in cands:
            if j == A_idx or j == C_idx:
                continue
            sx, sy, sz, sr = spheres[j]
            rsum = rB + sr
            ddx, ddy = min_image_delta(nx_w, ny_w, sx, sy)
            d2 = ddx * ddx + ddy * ddy + (nz - sz) ** 2
            if d2 < rsum * rsum - EPS:
                hit_idx = j
                break

        if hit_idx is not None:
            return prev_pos, hit_idx

        prev_pos = (nx_w, ny_w, nz)
        prev_z = nz

    return prev_pos, None


# ── STABILITY ─────────────────────────────────────────────────────────────────

def is_stable(B_pos, rB, contact_indices):
    """
    Sphere B is stable iff its xy projection lies inside the triangle formed
    by its three contact points (so gravity passes through the support base).
    """
    if len(contact_indices) < 3:
        return False

    pts_xy = []
    for idx in contact_indices:
        sx, sy, sz, sr = spheres[idx]
        dx, dy = min_image_delta(sx, sy, B_pos[0], B_pos[1])
        d_vec  = np.array([dx, dy, sz - B_pos[2]])
        n      = np.linalg.norm(d_vec)
        if n < EPS:
            return False
        cp = np.array(B_pos) + rB * d_vec / n
        pts_xy.append(cp[:2])

    p = np.array(B_pos[:2])
    A, B, C = pts_xy
    v0, v1, v2 = C - A, B - A, p - A
    d00, d01, d11 = np.dot(v0, v0), np.dot(v0, v1), np.dot(v1, v1)
    d20, d21      = np.dot(v2, v0), np.dot(v2, v1)
    denom = d00 * d11 - d01 * d01
    if abs(denom) < 1e-12:
        return False
    v = (d11 * d20 - d01 * d21) / denom
    w = (d00 * d21 - d01 * d20) / denom
    return v >= -EPS and w >= -EPS and (1 - v - w) >= -EPS


# ── DEPOSIT ONE SPHERE ────────────────────────────────────────────────────────

def deposit_sphere(rB):
    """Drop one sphere and return its final resting position, or None on fail."""
    x = random.uniform(0.0, LX)
    y = random.uniform(0.0, LY)

    # Phase 1: drop straight down
    z1, c1 = drop_straight_down(x, y, rB)
    if c1 is None:
        return (x, y, rB)
    pos = (x, y, z1)

    # Phase 2: roll on first contact
    pos, c2 = roll_on_one(pos, rB, c1)
    if c2 is None:
        return pos

    # Phase 3: roll on two contacts, looking for a stable triple
    contacts = [c1, c2]
    for _ in range(MAX_REROLLS):
        new_pos, c3 = roll_on_two(pos, rB, contacts[-2], contacts[-1])
        if new_pos is None:
            return pos
        pos = new_pos
        if c3 is None:
            return pos  # rolled off to floor or past bottom

        triple = [contacts[-2], contacts[-1], c3]
        if is_stable(pos, rB, triple):
            return pos

        # Unstable: drop the oldest contact and keep rolling on the newest two
        contacts = [contacts[-1], c3]

    return pos


# ── MAIN SIMULATION LOOP ──────────────────────────────────────────────────────

def run():
    print("=" * 68)
    print("  SHI-ZHANG GRAVITATIONAL DEPOSITION PACKING")
    print("=" * 68)
    print(f"  Box:              {LX:.0f} × {LY:.0f} × {LZ:.0f} µm  ({LX*LY*LZ/1e9:.3f} mm³)")
    print(f"  Large diameter:   {D_LARGE_MEAN:.0f} µm  (±{D_LARGE_SPREAD*100:.0f}%)   ρ = {RHO_LARGE} g/cm³")
    print(f"  Small diameter:   {D_SMALL_MEAN:.0f} µm  (±{D_SMALL_SPREAD*100:.0f}%)   ρ = {RHO_SMALL} g/cm³")
    print(f"  Size ratio u:     {D_LARGE_MEAN / D_SMALL_MEAN:.2f}")
    print(f"  Target particles: {TARGET_PARTICLES}")
    # Convert target volume fraction → count ratio.
    # Large sphere volume / small sphere volume = (R_L_MEAN / R_S_MEAN)^3
    # If we want V_S / V_total = SMALL_VOL_FRACTION, then
    #   N_S * v_s / (N_S * v_s + N_L * v_L) = SMALL_VOL_FRACTION
    # → N_S / N_L = SMALL_VOL_FRACTION / (1 - SMALL_VOL_FRACTION) * (v_L / v_s)
    vol_ratio = (R_L_MEAN / R_S_MEAN) ** 3
    n_s_per_n_l = (SMALL_VOL_FRACTION / max(1 - SMALL_VOL_FRACTION, 1e-6)) * vol_ratio
    p_small = n_s_per_n_l / (1 + n_s_per_n_l)   # probability each draw is small

    print(f"  Target small vol frac: {SMALL_VOL_FRACTION*100:.0f}%  →  "
          f"N_small/N_large ≈ {n_s_per_n_l:.0f}  (P(small) = {p_small:.3f})")
    print(f"\n  Depositing... (this can take a few minutes)\n")

    t0 = time.time()
    n_large = 0
    n_small = 0
    last_print = t0

    for i in range(TARGET_PARTICLES):
        # Pick particle size by volume-based probability
        if random.random() < p_small:
            r = sample_radius(R_S_MEAN, D_SMALL_SPREAD)
            is_large = False
        else:
            r = sample_radius(R_L_MEAN, D_LARGE_SPREAD)
            is_large = True

        pos = deposit_sphere(r)
        if pos is None or pos[2] >= LZ - r:
            # Heap reached the top — stop
            print(f"    Reached top of box at i={i}; stopping.")
            break

        spheres.append((pos[0], pos[1], pos[2], r))
        grid.insert(len(spheres) - 1, pos[0], pos[1], pos[2])
        if is_large: n_large += 1
        else:        n_small += 1

        now = time.time()
        if now - last_print > 5.0:
            print(f"    [{now-t0:>5.1f}s] placed {len(spheres)}/{TARGET_PARTICLES}  "
                  f"(L={n_large}, S={n_small})")
            last_print = now

    elapsed = time.time() - t0
    print(f"\n  Total deposited: {len(spheres)} ({n_large} large + {n_small} small)  "
          f"in {elapsed:.1f}s")

    # ── Compute volume and mass fractions ─────────────────────────────────────
    # Use only the bulk (exclude the loose top "halo") for fair density
    z_top = max(s[2] for s in spheres)
    z_max = max(z_top - 2 * R_L_MEAN, R_L_MEAN)
    bulk_idx = [i for i, s in enumerate(spheres) if s[2] < z_max]
    bulk = [spheres[i] for i in bulk_idx]

    V_box_bulk = LX * LY * z_max

    V_L = sum((4/3) * np.pi * r**3 for x, y, z, r in bulk if r > (R_L_MEAN + R_S_MEAN) / 2)
    V_S = sum((4/3) * np.pi * r**3 for x, y, z, r in bulk if r <= (R_L_MEAN + R_S_MEAN) / 2)
    V_total = V_L + V_S

    vf_L = V_L / V_box_bulk
    vf_S = V_S / V_box_bulk
    vf_total = vf_L + vf_S

    # Mass fractions
    mass_L = (V_L / 1e12) * RHO_LARGE
    mass_S = (V_S / 1e12) * RHO_SMALL
    total_mass = mass_L + mass_S

    print("\n" + "=" * 68)
    print("  RESULTS  (bulk, z < {:.1f} µm; {} of {} spheres counted)".format(
        z_max, len(bulk), len(spheres)))
    print("=" * 68)
    print(f"\n  Volume fractions of the bulk box:")
    print(f"    Large:     {vf_L*100:>6.2f} %")
    print(f"    Small:     {vf_S*100:>6.2f} %")
    print(f"    Total:     {vf_total*100:>6.2f} %    (void = {(1-vf_total)*100:.2f} %)")

    if V_total > 0:
        print(f"\n  Volume fractions of the SOLID phase only:")
        print(f"    Large:     {V_L/V_total*100:>6.2f} %")
        print(f"    Small:     {V_S/V_total*100:>6.2f} %")

    if total_mass > 0:
        print(f"\n  Mass fractions  (ρ_L = {RHO_LARGE}, ρ_S = {RHO_SMALL} g/cm³):")
        print(f"    Large:     {mass_L/total_mass*100:>6.2f} wt%   ({mass_L*1000:>7.3f} mg)")
        print(f"    Small:     {mass_S/total_mass*100:>6.2f} wt%   ({mass_S*1000:>7.3f} mg)")
        print(f"    Total:     {total_mass*1000:>7.3f} mg in bulk volume")

    print("\n  Reference: Shi & Zhang (2008) report ~0.578 monosize, ~0.585–0.625")
    print("             bimodal depending on size ratio and composition.")

    # ── Render ───────────────────────────────────────────────────────────────
    if SHOW_PLOT:
        print("\n  Rendering 3D figure...")
        render_packing(z_max)


def render_packing(z_max: float):
    fig = plt.figure(figsize=(10, 10))
    fig.patch.set_facecolor("white")
    ax  = fig.add_subplot(111, projection="3d")

    u = np.linspace(0, 2 * np.pi, SPHERE_FACETS)
    v = np.linspace(0,     np.pi, SPHERE_FACETS)
    su = np.outer(np.cos(u), np.sin(v))
    sv = np.outer(np.sin(u), np.sin(v))
    sw = np.outer(np.ones_like(u), np.cos(v))

    def keep(x, y, z):
        if not CUTAWAY:
            return True
        return not (x > LX * 0.55 and y > LY * 0.55)

    threshold = (R_L_MEAN + R_S_MEAN) / 2

    for x, y, z, r in spheres:
        if not keep(x, y, z):
            continue
        color = "#2980B9" if r > threshold else "#E67E22"
        alpha = 0.92 if r > threshold else 0.55
        ax.plot_surface(
            x + r * su, y + r * sv, z + r * sw,
            color=color, alpha=alpha,
            linewidth=0, antialiased=True, shade=True
        )

    ax.set_xlim(0, LX); ax.set_ylim(0, LY); ax.set_zlim(0, LZ)
    ax.set_xlabel("x (µm)"); ax.set_ylabel("y (µm)"); ax.set_zlabel("z (µm)")
    ax.set_box_aspect((LX, LY, LZ))
    ax.view_init(elev=22, azim=35)

    n_L = sum(1 for _, _, _, r in spheres if r > threshold)
    n_S = sum(1 for _, _, _, r in spheres if r <= threshold)
    title = ("Gravitational Deposition Packing"
             + (" (cutaway)" if CUTAWAY else "")
             + f"\n{n_L} large + {n_S} small  |  "
             + f"u = {D_LARGE_MEAN/D_SMALL_MEAN:.1f}")
    ax.set_title(title, fontsize=11, fontweight="bold")

    plt.tight_layout()
    plt.savefig("gravity_packing.png", dpi=DPI, bbox_inches="tight",
                facecolor="white")
    plt.show()


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run()