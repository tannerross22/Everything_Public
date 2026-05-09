import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ── TUNABLE PARAMETERS ────────────────────────────────────────────────────────
CSV_FILE        = "DOE 1 Official Tracker - Sheet5.csv"
FIGSIZE         = (7.5, 4.5)
DPI             = 300
MARKER_SIZE     = 40
MARKER_STYLE    = 'o'
EDGE_LINE_WIDTH = 0.8
FIT_LINE_WIDTH  = 1.5
FIT_ALPHA       = 0.9
FIT_LINESTYLE   = '-'
ALPHA           = 0.85
OUTPUT_FILE     = "crack_density_plot.png"

# Colors per group
COLOR_CU    = "#4e9ad4"
COLOR_40    = "#f4a460"
COLOR_60    = "#6dbf6d"
COLOR_ROD   = "#e63946"
COLOR_FLAME = "#9b59b6"
# ──────────────────────────────────────────────────────────────────────────────

df = pd.read_csv(CSV_FILE)
df.replace("#VALUE!", np.nan, inplace=True)
df = df.apply(pd.to_numeric, errors='coerce')

x = df["Displacement"]

# Define which columns belong to each group
matrix_groups = {
    "Cu":    (["Cu50", "Cu60", "Cu70"], COLOR_CU),
    "40":    (["4050", "4060", "4070"], COLOR_40),
    "60":    (["6050", "6060", "6070"], COLOR_60),
    "Rod":   (["ROD"],                  COLOR_ROD),
    "Flame": (["FLAME"],                COLOR_FLAME),
}

fig, ax = plt.subplots(figsize=FIGSIZE)

for label, (cols, color) in matrix_groups.items():
    available_cols = [c for c in cols if c in df.columns]
    y_avg = df[available_cols].mean(axis=1)

    mask = y_avg.notna() & x.notna()
    xi = x[mask].values
    yi = y_avg[mask].values

    # Scatter averaged points
    ax.scatter(xi, yi, label=label, color=color,
               s=MARKER_SIZE, marker=MARKER_STYLE,
               linewidths=EDGE_LINE_WIDTH, edgecolors='black', alpha=ALPHA, zorder=3)

    # Origin-constrained quadratic fit: y = ax^2 + bx (no intercept)
    # Build design matrix with x^2 and x columns, then solve via least squares
    if len(xi) >= 2:
        A = np.column_stack([xi ** 2, xi])
        coeffs, _, _, _ = np.linalg.lstsq(A, yi, rcond=None)
        a, b = coeffs
        x_fit = np.linspace(0, xi.max(), 300)
        y_fit = a * x_fit ** 2 + b * x_fit
        ax.plot(x_fit, y_fit, color=color, linewidth=FIT_LINE_WIDTH,
                linestyle=FIT_LINESTYLE, alpha=FIT_ALPHA, zorder=2)

ax.set_xlabel("Displacement (inches)", fontsize=11)
ax.set_ylabel("Crack Density (cracks/inch)", fontsize=11)
ax.tick_params(axis='both', labelsize=9)
ax.grid(True, linestyle='--', linewidth=0.4, alpha=0.5)

handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels, fontsize=8, frameon=True,
          loc='upper left', ncol=1, columnspacing=0.8, handletextpad=0.4)

plt.tight_layout()
plt.savefig(OUTPUT_FILE, dpi=DPI, bbox_inches='tight')
plt.show()
print(f"Saved to {OUTPUT_FILE}")