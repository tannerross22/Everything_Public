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

fe_powder_baseline = 0.035  # nominal Fe in powder at zero dilution — adjust as needed
integration_cap = 100      # µm from interface to integrate over
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

def compute_thresholds(distance, fe, num_start_points, num_end_points):
    fe_initial = np.mean(fe[:num_start_points])
    fe_final = np.mean(fe[-num_end_points:])
    fe_90 = fe_final + 0.95 * (fe_initial - fe_final)
    fe_10 = fe_final + 0.05 * (fe_initial - fe_final)
    x_90 = find_crossing(distance, fe, fe_90)
    x_10 = find_crossing(distance, fe, fe_10)
    return fe_initial, fe_final, fe_90, fe_10, x_90, x_10

def compute_dilution_proxy(distance, fe, baseline, cap):
    mask = (distance >= 0) & (distance <= cap)
    x = distance[mask]
    y = fe[mask]
    excess = np.maximum(y - baseline, 0)
    return np.trapezoid(excess, x)

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

# Confirm parsed values
for name, val in zip(samples, interfaces):
    print(f"  {name}: {val} µm")

# --- Align, trim, compute ---
results = []
aligned_data = []

for (dist, fe), interface, name in zip(data, interfaces, samples):
    dist_aligned = dist - interface
    mask = dist_aligned >= -5
    dist_aligned, fe = dist_aligned[mask], fe[mask]

    _, _, fe_90, fe_10, x_90, x_10 = compute_thresholds(dist_aligned, fe, num_start_points, num_end_points)
    width = abs(x_10 - x_90) if (x_90 and x_10) else None
    proxy = compute_dilution_proxy(dist_aligned, fe, fe_powder_baseline, integration_cap)

    results.append({"name": name, "width": width, "proxy": proxy})
    aligned_data.append((dist_aligned, fe))

    print(f"{name} — Diffusion width: {width:.3f} µm | Dilution proxy (area): {proxy:.3f}" if width else
          f"{name} — Diffusion width: N/A | Dilution proxy (area): {proxy:.3f}")

# ================= PLOT 1: EDS profiles =================
fig, ax = plt.subplots(figsize=(7.5, 4.5))

colors = plt.cm.tab10(np.linspace(0, 0.8, len(samples)))
for (dist_aligned, fe), name, color in zip(aligned_data, samples, colors):
    ax.plot(dist_aligned, fe, label=name, color=color)

ax.axvline(integration_cap, color='black', linestyle=':', linewidth=1, label=f'{integration_cap} µm cap')
ax.axhline(fe_powder_baseline, color='black', linestyle='--', linewidth=1, label='Powder baseline')
ax.set_xlim(left=-5)
ax.set_xlabel("Distance into hardfacing (µm)")
ax.set_ylabel("Fe (wt. fraction)")
ax.set_title("Laser Samples — Fe EDS Profiles")
ax.legend(fontsize=8)
plt.tight_layout()

# ================= PLOT 2: Dilution proxy bar chart =================
fig2, ax2 = plt.subplots(figsize=(7, 4))

sorted_results = sorted(results, key=lambda r: r["proxy"])
sorted_names = [r["name"] for r in sorted_results]
sorted_proxies = [r["proxy"] for r in sorted_results]
sorted_colors = [colors[samples.index(r["name"])] for r in sorted_results]

ax2.bar(sorted_names, sorted_proxies, color=sorted_colors)
ax2.set_xlabel("Sample")
ax2.set_ylabel("Dilution proxy (excess Fe·µm)")
ax2.set_title("Laser Samples — Fe Area Dilution Proxy")
plt.tight_layout()
plt.show()