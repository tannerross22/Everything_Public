import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import random

# ── INPUTS ─────────────────────────────────────────

MATRIX_WT_FRACTION = 0.40
RHO_MATRIX = 10.42

WT_LARGE = 0.60
WT_SMALL = 0.40

D_LARGE_MEAN = 187.5
D_LARGE_STD = 80
MIN_LARGE_DIAMETER = 125
RHO_LARGE = 15.8

D_SMALL_MEAN = 41
D_SMALL_STD = 26
MIN_SMALL_DIAMETER = 15
RHO_SMALL = 16.5

WINDOW_W = 2137
WINDOW_H = 1274
WINDOW_AREA = WINDOW_W * WINDOW_H

VOL_TO_AREA_FACTOR = 2.0 / 3.0

INITIAL_LARGE_SPACING = 0.01
INITIAL_SMALL_SPACING = 0.05
LARGE_SMALL_GAP = 0.10
RELAX_FACTOR = 0.4
MAX_TRIES = 3000

BIAS_TO_LARGE = 0.7
N_RUNS = 20
RANDOM_SEED = 42

# ── SETUP ─────────────────────────────────────────

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

R_L_MEAN = D_LARGE_MEAN / 2
R_L_STD = D_LARGE_STD / 2
R_L_MIN = MIN_LARGE_DIAMETER / 2

R_S_MEAN = D_SMALL_MEAN / 2
R_S_STD = D_SMALL_STD / 2
R_S_MIN = MIN_SMALL_DIAMETER / 2

rho_p_inv = (WT_LARGE / RHO_LARGE) + (WT_SMALL / RHO_SMALL)
RHO_PARTICLE_EFFECTIVE = 1.0 / rho_p_inv

w_m = MATRIX_WT_FRACTION
w_p = 1 - w_m

MATRIX_VOL_FRACTION = (w_m / RHO_MATRIX) / (
    (w_m / RHO_MATRIX) + (w_p / RHO_PARTICLE_EFFECTIVE)
)

# ── TARGET AREAS ──────────────────────────────────

def compute_targets():
    inv_rho_L = WT_LARGE / RHO_LARGE
    inv_rho_S = WT_SMALL / RHO_SMALL

    vol_L_frac = inv_rho_L / (inv_rho_L + inv_rho_S)
    vol_S_frac = 1 - vol_L_frac

    vf_particles = 1 - MATRIX_VOL_FRACTION

    vol_L = vf_particles * vol_L_frac
    vol_S = vf_particles * vol_S_frac

    area_L = vol_L * VOL_TO_AREA_FACTOR * WINDOW_AREA
    area_S = vol_S * VOL_TO_AREA_FACTOR * WINDOW_AREA

    return area_L, area_S

# ── HELPERS ───────────────────────────────────────

def sample_radius(mean, std, rmin):
    return max(np.random.normal(mean, std), rmin)

def sample_near_large(large, r):
    xl, yl, rl = random.choice(large)
    angle = random.uniform(0, 2*np.pi)
    dist = rl + r + random.uniform(0, 0.5*rl)
    return xl + dist*np.cos(angle), yl + dist*np.sin(angle)

# ── AREA-BASED PLACEMENT ──────────────────────────

def place_until_area(target_area, mean_r, std_r, min_r,
                     existing, same_spacing, cross_gap,
                     bias=False):

    placed = []
    total_area = 0
    fails = 0

    while total_area < target_area and fails < MAX_TRIES:

        r = sample_radius(mean_r, std_r, min_r)

        if bias and existing and random.random() < BIAS_TO_LARGE:
            x, y = sample_near_large(existing, r)
        else:
            x = random.uniform(r, WINDOW_W - r)
            y = random.uniform(r, WINDOW_H - r)

        ok = True

        for cx, cy, cr in existing:
            if (x-cx)**2 + (y-cy)**2 < (r+cr+cross_gap*min(r,cr))**2:
                ok = False; break

        if ok:
            for cx, cy, cr in placed:
                if (x-cx)**2 + (y-cy)**2 < (r+cr+same_spacing*mean_r)**2:
                    ok = False; break

        if not ok:
            fails += 1
            continue

        placed.append((x,y,r))
        total_area += np.pi*r*r
        fails = 0

    return placed

# ── METRICS ───────────────────────────────────────

def compute_metrics(large, small):

    d_LL = []
    for i,(x1,y1,r1) in enumerate(large):
        for j,(x2,y2,r2) in enumerate(large):
            if i>=j: continue
            d = np.sqrt((x1-x2)**2 + (y1-y2)**2) - (r1+r2)
            d_LL.append(d)

    small_near = 0
    for xs,ys,rs in small:
        for xl,yl,rl in large:
            if np.sqrt((xs-xl)**2 + (ys-yl)**2) < rl+rs+0.2*rl:
                small_near += 1
                break

    return {
        "mean_LL_gap": np.mean(d_LL) if d_LL else 0,
        "small_fill_frac": small_near / max(len(small),1)
    }

# ── SINGLE RUN ────────────────────────────────────

def generate_structure(area_L, area_S):

    large = place_until_area(area_L, R_L_MEAN, R_L_STD, R_L_MIN,
                             [], INITIAL_LARGE_SPACING, 0.0)

    small = place_until_area(area_S, R_S_MEAN, R_S_STD, R_S_MIN,
                             large, INITIAL_SMALL_SPACING,
                             LARGE_SMALL_GAP, bias=True)

    return large, small

# ── MONTE CARLO ───────────────────────────────────

def monte_carlo():

    area_L, area_S = compute_targets()

    results = []

    for _ in range(N_RUNS):
        large, small = generate_structure(area_L, area_S)
        results.append(compute_metrics(large, small))

    avg = {k: np.mean([r[k] for r in results]) for k in results[0]}
    return avg, large, small

# ── PLOT ──────────────────────────────────────────

def plot_structure(large, small):

    fig, ax = plt.subplots(figsize=(10,6))

    ax.set_facecolor("#333333")

    for x,y,r in large:
        ax.add_patch(Circle((x,y), r, facecolor="white",
                            edgecolor="black", hatch="++", lw=0.6))
    for x,y,r in small:
        ax.add_patch(Circle((x,y), r, facecolor="white",
                            edgecolor="black", lw=0.5))

    ax.set_xlim(0, WINDOW_W)
    ax.set_ylim(0, WINDOW_H)
    ax.set_aspect("equal")

    plt.tight_layout()
    plt.show()

# ── MAIN ──────────────────────────────────────────

def main():
    avg_metrics, large, small = monte_carlo()

    print("\nAvg Metrics:")
    for k,v in avg_metrics.items():
        print(f"{k}: {v:.4f}")

    plot_structure(large, small)

if __name__ == "__main__":
    main()