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

# ================= MAIN =================
samples = [f"S{i+1}" for i in range(len(csv_files))]

# --- Load all samples ---
data = [load_and_trim(f) for f in csv_files]

# --- Collect interface inputs ---
print(f"Enter interface positions (µm) for {', '.join(samples)} — comma-separated:")
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

    results.append({"name": name, "width": width, "x_90": x_90, "x_10": x_10,
                    "fe_90": fe_90, "fe_10": fe_10})
    aligned_data.append((dist_aligned, fe))

    if width:
        print(f"{name} — x_90: {x_90:.2f} µm | x_10: {x_10:.2f} µm | Diffusion width: {width:.3f} µm")
    else:
        print(f"{name} — Diffusion width: N/A (crossing not found)")

# ================= PLOT 1: EDS profiles with 90/10 markers =================
fig, ax = plt.subplots(figsize=(7.5, 4.5))

colors = plt.cm.tab10(np.linspace(0, 0.8, len(samples)))
for (dist_aligned, fe), result, color in zip(aligned_data, results, colors):
    ax.plot(dist_aligned, fe, label=result["name"], color=color)
    if result["x_90"] is not None:
        ax.axvline(result["x_90"], color=color, linestyle='--', linewidth=0.8, alpha=0.6)
    if result["x_10"] is not None:
        ax.axvline(result["x_10"], color=color, linestyle=':', linewidth=0.8, alpha=0.6)

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

plt.show()