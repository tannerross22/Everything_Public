import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

# --- Load CSV ---
file_path = "QE.csv"
df = pd.read_csv(file_path, skiprows=1)

# Extract the first two columns (2θ and Intensity)
x = df.iloc[:, 0]
y = df.iloc[:, 1]

# --- Plot setup ---
plt.figure(figsize=(10, 6))
plt.plot(x, y, color='black', linewidth=1)

# --- Formatting ---
plt.xlabel("Length (m)", fontsize=14, fontweight='bold', color='black')
plt.ylabel("Height (m)", fontsize=14, fontweight='bold', color='black')
plt.tick_params(direction='out', length=6, width=1.5, colors='black', labelsize=12)

# Force y-axis scientific notation
ax = plt.gca()
ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
ax.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))

# Black border
for spine in ax.spines.values():
    spine.set_color('black')
    spine.set_linewidth(1.5)

plt.title("")  # no chart title
plt.tight_layout()
plt.show()
