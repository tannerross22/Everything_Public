import pandas as pd
import numpy as np

# ─── SET YOUR SCALE FACTOR HERE ───────────────────────────────────────────────
PIXELS_PER_MICRON = 1.434  # <-- change this to your known value
# ──────────────────────────────────────────────────────────────────────────────

# Load the CSV
df = pd.read_csv("flame_1.csv")  # <-- change to your actual filename

# Rename columns for clarity
df.columns = ["X_px", "Y_dev_px"]

# Convert to microns
df["X_um"] = df["X_px"] / PIXELS_PER_MICRON
df["Y_dev_um"] = df["Y_dev_px"] / PIXELS_PER_MICRON

# Stats
max_pos = df["Y_dev_um"].max()
max_neg = df["Y_dev_um"].min()
max_abs = df["Y_dev_um"].abs().max()
std_dev = df["Y_dev_um"].std()
mean_check = df["Y_dev_um"].mean()  # should be ~0 if macro worked correctly

print(f"Mean deviation:          {mean_check:.4f} µm  (should be ~0)")
print(f"Standard deviation:     ±{std_dev:.3f} µm")
print(f"Max positive deviation: +{max_pos:.3f} µm")
print(f"Max negative deviation:  {max_neg:.3f} µm")
print(f"Max absolute deviation:  {max_abs:.3f} µm")

# Save converted CSV
df[["X_um", "Y_dev_um"]].to_csv("profile_microns.csv", index=False)
print("\nSaved: profile_microns.csv")