import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

# ── CONFIG ─────────────────────────────────────
CSV_PATH = "40_60_line.csv"
WINDOW   = 3

# Figure
FIGSIZE      = (10, 6)
DPI          = 300

# Font
FONT_FAMILY  = "DejaVu Sans"        # "serif", "sans-serif", "monospace"
FONT_SIZE    = 22             # base font size
TITLE_SIZE   = 24
LABEL_SIZE   = 22
TICK_SIZE    = 21
LEGEND_SIZE  = 14

# Lines
LINE_WIDTH   = 1
LINE_STYLE   = "-"            # "-", "--", "-.", ":"
MARKER       = None           # None, "o", "s", "^", etc.
MARKER_SIZE  = 1

# Threshold lines
THRESH_COLOR = "black"
THRESH_STYLE = "--"
THRESH_WIDTH = 2

# Axes
SPINE_WIDTH  = 2
TICK_DIR     = "in"           # "in", "out", "inout"
TICK_WIDTH   = 1
TICK_LENGTH  = 4
GRID         = False
# ───────────────────────────────────────────────

df = pd.read_csv(CSV_PATH)
df.columns = df.columns.str.strip()
distance = df["Distance (um)"].values

for col in ["Si", "Cr", "Fe", "Ni"]:
    df[col] = df[col].rolling(window=WINDOW, center=True, min_periods=1).mean()

fe = df["Fe"].values

fe_interp = interp1d(distance, fe, kind="linear")
d_fine = np.linspace(distance.min(), distance.max(), 10_000)
fe_fine = fe_interp(d_fine)

fe_min, fe_max = fe.min(), fe.max()
thresh_low  = fe_min + 0.05 * (fe_max - fe_min)
thresh_high = fe_min + 0.95 * (fe_max - fe_min)

def first_crossing(x, y, threshold):
    for i in range(len(y) - 1):
        if (y[i] - threshold) * (y[i+1] - threshold) < 0:
            frac = (threshold - y[i]) / (y[i+1] - y[i])
            return x[i] + frac * (x[i+1] - x[i])
    return None

d_low  = first_crossing(d_fine, fe_fine, thresh_low)
d_high = first_crossing(d_fine, fe_fine, thresh_high)

if d_low and d_high:
    print(f"5%  crossing : {d_low:.2f} um")
    print(f"95% crossing : {d_high:.2f} um")
    print(f"Interdiffusion zone width: {abs(d_high - d_low):.2f} um")

# Apply global font settings
plt.rcParams.update({
    "font.family":       FONT_FAMILY,
    "font.size":         FONT_SIZE,
    "axes.titlesize":    TITLE_SIZE,
    "axes.labelsize":    LABEL_SIZE,
    "xtick.labelsize":   TICK_SIZE,
    "ytick.labelsize":   TICK_SIZE,
    "legend.fontsize":   LEGEND_SIZE,
    "axes.linewidth":    SPINE_WIDTH,
    "xtick.direction":   TICK_DIR,
    "ytick.direction":   TICK_DIR,
    "xtick.major.width": TICK_WIDTH,
    "ytick.major.width": TICK_WIDTH,
    "xtick.major.size":  TICK_LENGTH,
    "ytick.major.size":  TICK_LENGTH,
    "axes.grid":         GRID,
})

fig, ax = plt.subplots(figsize=FIGSIZE)

for col in ["Si", "Cr", "Fe", "Ni"]:
    ax.plot(distance, df[col].values, label=col,
            linewidth=LINE_WIDTH, linestyle=LINE_STYLE,
            marker=MARKER, markersize=MARKER_SIZE)

ax.axhline(thresh_low,  color=THRESH_COLOR, linestyle=THRESH_STYLE, linewidth=THRESH_WIDTH, label="5% / 95% Fe")
ax.axhline(thresh_high, color=THRESH_COLOR, linestyle=THRESH_STYLE, linewidth=THRESH_WIDTH)

ax.set_xlabel("Distance (µm)")
ax.set_ylabel("Composition (at. fraction)")
ax.legend(frameon=True)
plt.tight_layout()
plt.savefig("hardfacing_diffusion.png", dpi=DPI)
plt.show()