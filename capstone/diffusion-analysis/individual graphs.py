import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ================= USER SETTINGS =================
csv_files = {
    "S1": "S1 - raw.csv",
    "S2": "S2 - raw.csv",
    "S3": "S3 - raw.csv",
    "S4": "S4 - raw.csv",
    "S5": "S5 - raw.csv",
    "S6": "S6 - raw.csv",
    "S7": "S7 - raw.csv",
    "S8": "S8 - raw.csv",
}

fe_powder_baseline = 0.0305
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

# --- Ask which samples to plot ---
print("Available samples:", ", ".join(csv_files.keys()))
selection = input("Enter sample names to plot (comma-separated, e.g. S1,S3): ")
selected = [s.strip() for s in selection.split(",")]

# --- Collect interface inputs ---
interfaces = {}
print("\nEnter the interface position (µm) for each selected sample:")
for name in selected:
    interfaces[name] = float(input(f"  {name}: "))

# ================= PLOT =================
fig, ax = plt.subplots(figsize=(9, 5))

colors = plt.cm.tab10(np.linspace(0, 0.8, len(selected)))

for name, color in zip(selected, colors):
    dist, fe = load_and_trim(csv_files[name])

    dist_aligned = dist - interfaces[name]
    mask = dist_aligned >= -5
    dist_aligned, fe = dist_aligned[mask], fe[mask]

    _, _, fe_90, fe_10, x_90, x_10 = compute_thresholds(dist_aligned, fe, num_start_points, num_end_points)

    ax.plot(dist_aligned, fe, label=name, color=color)

    if x_90 and x_10:
        width = abs(x_10 - x_90)
        ax.axhline(fe_90, color=color, linestyle='--', linewidth=1)
        ax.axhline(fe_10, color=color, linestyle='--', linewidth=1)
        ax.scatter([x_90, x_10], [fe_90, fe_10], color=color, zorder=3)
        print(f"{name} — Diffusion width: {width:.3f} µm")

        # Calculate average iron past 5% point
        mask_past_5pct = dist_aligned >= x_10
        fe_past_5pct = fe[mask_past_5pct]
        if len(fe_past_5pct) > 0:
            avg_fe_past_5pct = np.mean(fe_past_5pct)
            print(f"{name} — Average Fe past 5% point: {avg_fe_past_5pct:.4f} wt. fraction")
    else:
        print(f"{name} — Could not determine threshold crossings.")

ax.axhline(fe_powder_baseline, color='black', linestyle=':', linewidth=1, label='Powder baseline')
ax.set_xlim(left=-5)
ax.set_xlabel("Distance into hardfacing (µm)")
ax.set_ylabel("Fe (wt. fraction)")
ax.set_title("Laser Samples — Fe Diffusion Detail")
ax.legend(fontsize=8)
plt.tight_layout()
plt.show()