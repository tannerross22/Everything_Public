import pandas as pd
import matplotlib.pyplot as plt
import glob

# --- Settings ---
# Add your CSV filenames here (or use a wildcard like "*.csv")
file_paths = [
    "Cu_5% CW.csv",
    "Cu_25% CW.csv",
    "Cu_50% CW.csv",
    "Cu_72% CW.csv"
]

# Optional: use glob to automatically load all CSVs in a folder
# file_paths = glob.glob("data/*.csv")

# --- Plot setup ---
plt.figure(figsize=(10, 6))

for file_path in file_paths:
    # Read CSV, skip first row
    df = pd.read_csv(file_path, skiprows=1)

    # Extract first two columns (2θ and Intensity)
    theta = df.iloc[:, 0]
    intensity = df.iloc[:, 1]

    # Plot each spectrum
    label = file_path.split("/")[-1].replace(".csv", "")
    plt.plot(theta, intensity, linewidth=1.2, label=label)

# --- Formatting ---
plt.xlabel("2θ (°)", fontsize=14, fontweight='bold', color='black')
plt.ylabel("Intensity (cps)", fontsize=14, fontweight='bold', color='black')
plt.tick_params(direction='out', length=6, width=1.5, colors='black', labelsize=12)

# Black border
for spine in plt.gca().spines.values():
    spine.set_color('black')
    spine.set_linewidth(1.5)

plt.legend(frameon=False, fontsize=12)
plt.tight_layout()
plt.show()
