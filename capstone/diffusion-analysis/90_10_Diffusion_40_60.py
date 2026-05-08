import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ================= USER SETTINGS =================
csv_file_1 = "flame_spray1.csv"
csv_file_2 = "40_60_Scan_Substrate.csv"
csv_file_3 = "rodweldline2.csv"

num_start_points = 1
num_end_points = 5
# =================================================

def load_and_trim(csv_file, max_distance=100):
    df = pd.read_csv(csv_file)
    distance = df["distance"].values
    fe = df["wt_fe"].values
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

# --- Load ---
dist1, fe1 = load_and_trim(csv_file_1)
dist2, fe2 = load_and_trim(csv_file_2)
dist3, fe3 = load_and_trim(csv_file_3)

# --- User-defined interface points ---
interface_1 = float(input("Enter the interface position (µm) for Sample 1 (Flame Spray 1): "))
interface_2 = float(input("Enter the interface position (µm) for Sample 2 (40_60): "))
interface_3 = float(input("Enter the interface position (µm) for Sample 3 (Rod Weld): "))

# --- Align to interface = 0 ---
dist1_aligned = dist1 - interface_1
dist2_aligned = dist2 - interface_2
dist3_aligned = dist3 - interface_3

# --- Trim to >= -5 ---
mask1 = dist1_aligned >= -5
mask2 = dist2_aligned >= -5
mask3 = dist3_aligned >= -5

dist1_aligned, fe1 = dist1_aligned[mask1], fe1[mask1]
dist2_aligned, fe2 = dist2_aligned[mask2], fe2[mask2]
dist3_aligned, fe3 = dist3_aligned[mask3], fe3[mask3]

# --- Thresholds ---
_, _, fe_90_1, fe_10_1, x_90_1, x_10_1 = compute_thresholds(dist1_aligned, fe1, num_start_points, num_end_points)
_, _, fe_90_2, fe_10_2, x_90_2, x_10_2 = compute_thresholds(dist2_aligned, fe2, num_start_points, num_end_points)
_, _, fe_90_3, fe_10_3, x_90_3, x_10_3 = compute_thresholds(dist3_aligned, fe3, num_start_points, num_end_points)

for label, fe_90, fe_10, x_90, x_10 in [("Flame Spray 1", fe_90_1, fe_10_1, x_90_1, x_10_1),
                                          ("40 HRc 60% WC", fe_90_2, fe_10_2, x_90_2, x_10_2),
                                          ("Rod Weld",      fe_90_3, fe_10_3, x_90_3, x_10_3)]:
    if x_90 is None or x_10 is None:
        print(f"{label}: Could not determine threshold crossings.")
    else:
        print(f"{label} — Interdiffusion width: {abs(x_10 - x_90):.3f} µm")

# ================= PLOT =================
fig, ax = plt.subplots(figsize=(7.5, 4.5))

ax.plot(dist1_aligned, fe1, color='black', label='Flame Spray 1')
ax.plot(dist2_aligned, fe2, color='#378ADD',  label='40 HRc 60% WC')
ax.plot(dist3_aligned, fe3, color='black', linestyle='--', label='Rod Weld')

#for fe_90, fe_10, x_90, x_10 in [(fe_90_1, fe_10_1, x_90_1, x_10_1),
#                                   (fe_90_2, fe_10_2, x_90_2, x_10_2),
#                                   (fe_90_3, fe_10_3, x_90_3, x_10_3)]:
#    if x_90 and x_10:
#        ax.axhline(fe_90, color='black', linestyle='--', linewidth=0.8)
#        ax.axhline(fe_10, color='black', linestyle='--', linewidth=0.8)
#        ax.scatter([x_90, x_10], [fe_90, fe_10], color='black', zorder=3)

ax.set_xlabel("Distance into hardfacing (µm)")
ax.set_ylabel("Fe (wt. fraction)")
ax.set_title("Iron Interdiffusion — EDS Line Scans")
ax.legend()

plt.tight_layout()
plt.show()