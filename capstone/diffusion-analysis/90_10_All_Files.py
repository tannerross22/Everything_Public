import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ================= USER SETTINGS =================
csv_files = [
    "S1 - raw.csv",
    "S2 - raw.csv",
    "S3 - raw.csv",
    "S4 - raw.csv",
    "S5 - raw.csv",
    "S6 - raw.csv",
    "S7 - raw.csv",
    "S8 - raw.csv",
]

num_start_points = 1
num_end_points = 5
fe_threshold_pct = 5.0   # Fe % at which the "bulk hardfacing" region begins
# =================================================

def load_and_trim(csv_file, max_distance=200):
    df = pd.read_csv(csv_file)
    distance = df["distance"].values
    fe = df["fe"].values
    mask = distance <= max_distance
    return distance[mask], fe[mask]

def find_crossing(x, y, target):
    for i in range(len(y) - 1):
        if (y[i] >= target and y[i+1] <= target) or (y[i] <= target and y[i+1] >= target):
            return x[i] + (target - y[i]) * (x[i+1] - x[i]) / (y[i+1] - y[i])
    return None

def compute_diffusion_width(distance, fe, num_start_points, num_end_points):
    fe_initial = np.mean(fe[:num_start_points])
    fe_final = np.mean(fe[-num_end_points:])
    fe_90 = fe_final + 0.90 * (fe_initial - fe_final)
    fe_10 = fe_final + 0.10 * (fe_initial - fe_final)
    x_90 = find_crossing(distance, fe, fe_90)
    x_10 = find_crossing(distance, fe, fe_10)
    width = abs(x_10 - x_90) if (x_90 is not None and x_10 is not None) else None
    return fe_initial, fe_final, fe_90, fe_10, x_90, x_10, width

def compute_bulk_dilution(distance, fe, fe_threshold_frac, fe_powder_frac, fe_base_frac):
    """Average Fe in the bulk hardfacing region (beyond the threshold crossing) and compute dilution.
    Dilution = (%cladding - %powder) / (%base_metal - %powder)
    """
    x_thresh = find_crossing(distance, fe, fe_threshold_frac)
    if x_thresh is None:
        return None, None, None
    bulk_mask = distance > x_thresh
    if not np.any(bulk_mask):
        return x_thresh, None, None
    avg_bulk_fe = np.mean(fe[bulk_mask])
    denom = fe_base_frac - fe_powder_frac
    dilution = (avg_bulk_fe - fe_powder_frac) / denom if denom != 0 else None
    return x_thresh, avg_bulk_fe, dilution

# ================= MAIN =================
samples = [f"S{i+1}" for i in range(len(csv_files))]

# --- Load all samples ---
data = [load_and_trim(f) for f in csv_files]

# --- Collect powder iron input ---
while True:
    raw_powder = input("Enter % iron in the hardfacing powder: ").strip()
    try:
        iron_powder_pct = float(raw_powder)
        if not (0 <= iron_powder_pct <= 100):
            print("  ✗ Value must be between 0 and 100. Try again.")
            continue
        break
    except ValueError:
        print("  ✗ Could not parse value. Enter a number (e.g. 3.5). Try again.")
iron_powder_frac = iron_powder_pct / 100.0
fe_threshold_frac = fe_threshold_pct / 100.0
print(f"  Powder Fe: {iron_powder_pct:.2f}%  |  Bulk threshold: {fe_threshold_pct:.1f}%")

# --- Collect interface inputs ---
print(f"\nEnter interface positions (µm) for {', '.join(samples)} — comma-separated:")
print(f"  Example: 120.5, 98.3, 134.1, 110.0, 125.7, 101.2, 118.4, 107.9")

while True:
    raw = input("> ").strip()
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != len(samples):
        print(f"  ✗ Got {len(parts)} value(s), expected {len(samples)}. Try again.")
        continue
    try:
        interfaces = [float(p) for p in parts]
        break
    except ValueError as e:
        print(f"  ✗ Could not parse a value: {e}. Try again.")

for name, val in zip(samples, interfaces):
    print(f"  {name}: {val} µm")

# --- Align, trim, compute ---
results = []
aligned_data = []

for (dist, fe), interface, name in zip(data, interfaces, samples):
    dist_aligned = dist - interface
    mask = dist_aligned >= -5
    dist_aligned, fe = dist_aligned[mask], fe[mask]

    fe_initial, fe_final, fe_90, fe_10, x_90, x_10, width = compute_diffusion_width(
        dist_aligned, fe, num_start_points, num_end_points
    )

    fe_base_frac = np.mean(fe[:num_start_points])  # substrate Fe from first data points

    x_thresh, avg_bulk_fe, dilution = compute_bulk_dilution(
        dist_aligned, fe, fe_threshold_frac, iron_powder_frac, fe_base_frac
    )

    results.append({"name": name, "width": width, "x_90": x_90, "x_10": x_10,
                    "fe_90": fe_90, "fe_10": fe_10,
                    "x_thresh": x_thresh, "avg_bulk_fe": avg_bulk_fe,
                    "fe_base_frac": fe_base_frac, "dilution": dilution})
    aligned_data.append((dist_aligned, fe))

    width_str = f"{width:.3f} µm" if width else "N/A"
    base_str  = f"{fe_base_frac*100:.2f}%"
    bulk_str  = f"{avg_bulk_fe*100:.2f}%" if avg_bulk_fe is not None else "N/A"
    dil_str   = f"{dilution*100:.2f}%" if dilution is not None else "N/A"
    print(f"{name} — Diffusion width: {width_str} | Base Fe: {base_str} | Avg bulk Fe: {bulk_str} | Dilution: {dil_str}")

# ================= PLOT 1: EDS profiles with 90/10 markers =================
fig, ax = plt.subplots(figsize=(7.5, 4.5))

colors = plt.cm.tab10(np.linspace(0, 0.8, len(samples)))
for (dist_aligned, fe), result, color in zip(aligned_data, results, colors):
    ax.plot(dist_aligned, fe, label=result["name"], color=color)
    if result["x_90"] is not None:
        ax.axvline(result["x_90"], color=color, linestyle='--', linewidth=0.8, alpha=0.6)
    if result["x_10"] is not None:
        ax.axvline(result["x_10"], color=color, linestyle=':', linewidth=0.8, alpha=0.6)
    if result["x_thresh"] is not None:
        ax.axvline(result["x_thresh"], color=color, linestyle='-.', linewidth=0.8, alpha=0.5)

ax.set_xlim(left=-5)
ax.set_xlabel("Distance into hardfacing (µm)")
ax.set_ylabel("Fe (wt. fraction)")
ax.set_title("Laser Samples — Fe EDS Profiles (90/10% crossings)")
ax.legend(fontsize=8)
plt.tight_layout()

# ================= PLOT 2: Diffusion width bar chart (low to high) =================
fig2, ax2 = plt.subplots(figsize=(7, 4))

sorted_results = sorted([r for r in results if r["width"] is not None], key=lambda r: r["width"])
sorted_names = [r["name"] for r in sorted_results]
sorted_widths = [r["width"] for r in sorted_results]
sorted_colors = [colors[samples.index(r["name"])] for r in sorted_results]

ax2.bar(sorted_names, sorted_widths, color=sorted_colors)
ax2.set_xlabel("Sample")
ax2.set_ylabel("Diffusion width (µm)")
ax2.set_title("Laser Samples — 90/10% Diffusion Width")
plt.tight_layout()

# ================= PLOT 3: Dilution bar chart =================
dilution_results = [r for r in results if r["dilution"] is not None]
if dilution_results:
    fig3, ax3 = plt.subplots(figsize=(7, 4))
    sorted_dil = sorted(dilution_results, key=lambda r: r["dilution"])
    dil_names  = [r["name"] for r in sorted_dil]
    dil_vals   = [r["dilution"] * 100 for r in sorted_dil]
    dil_colors = [colors[samples.index(r["name"])] for r in sorted_dil]
    ax3.bar(dil_names, dil_vals, color=dil_colors)
    ax3.set_xlabel("Sample")
    ax3.set_ylabel("Dilution (%)")
    ax3.set_title(f"Laser Samples — Dilution (powder Fe: {iron_powder_pct:.1f}%, bulk beyond {fe_threshold_pct:.0f}% threshold)")
    plt.tight_layout()

plt.show()