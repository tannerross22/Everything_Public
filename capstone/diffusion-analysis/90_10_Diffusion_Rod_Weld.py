import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ================= USER SETTINGS =================
csv_file = "rodweldline2.csv"  # <-- change this
num_start_points = 20         # matrix plateau points
num_end_points = 5           # final plateau points
# =================================================

# Load CSV (use delimiter='\t' if needed)
df = pd.read_csv(csv_file)
# df = pd.read_csv(csv_file, delimiter='\t')

distance = df["distance"].values
fe = df["wt_fe"].values

max_distance = 100
mask = distance <= max_distance

distance = distance[mask]
fe = fe[mask]

# --- Plateau averages ---
fe_initial = np.mean(fe[:num_start_points])
fe_final = np.mean(fe[-num_end_points:])

# --- 90–10 thresholds ---
fe_90 = fe_final + 0.95 * (fe_initial - fe_final)
fe_10 = fe_final + 0.05 * (fe_initial - fe_final)

# --- Crossing finder with interpolation ---
def find_crossing(x, y, target):
    for i in range(len(y) - 1):
        if (y[i] >= target and y[i+1] <= target) or (y[i] <= target and y[i+1] >= target):
            return x[i] + (target - y[i]) * (x[i+1] - x[i]) / (y[i+1] - y[i])
    return None

# ================================================
# START SEARCH AFTER MATRIX PLATEAU
# ================================================

distance_trim = distance[num_start_points:]
fe_trim = fe[num_start_points:]

x_90 = find_crossing(distance_trim, fe_trim, fe_90)
x_10 = find_crossing(distance_trim, fe_trim, fe_10)

if x_90 is None or x_10 is None:
    print("Could not determine both threshold crossings.")
else:
    width = abs(x_10 - x_90)

    print(f"Initial Fe plateau: {fe_initial:.4f}")
    print(f"Final Fe plateau: {fe_final:.4f}")
    print(f"90% threshold: {fe_90:.4f}")
    print(f"10% threshold: {fe_10:.4f}")
    print(f"Interdiffusion width: {width:.3f} µm")

    # ================= PLOT =================
    plt.figure(figsize=(10,6))

    # Fe profile (black)
    plt.plot(distance, fe, color='black')

    # Threshold lines (red dashed)
    plt.axhline(fe_90, color='red', linestyle='--', linewidth=1.5)
    plt.axhline(fe_10, color='red', linestyle='--', linewidth=1.5)

    # Start/stop markers (black)
    plt.scatter(x_90, fe_90, color='black', zorder=3)
    plt.scatter(x_10, fe_10, color='black', zorder=3)

    plt.xlabel("Distance (µm)")
    plt.ylabel("Fe (wt. fraction)")
    plt.title("Rod Weld Iron Interdiffusion")

    plt.show()