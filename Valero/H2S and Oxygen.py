from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =========================
# 1. TIME BASES
# =========================
seconds_per_day = 24 * 3600
t_flow = np.arange(0, seconds_per_day, 10)

# =========================
# 2. SYNTHETIC DATA
# =========================
np.random.seed(42)

base_flow = 120  # mol/s

flow = (
    base_flow
    + 15 * np.sin(2 * np.pi * t_flow / (6 * 3600))
    + 8 * np.sin(2 * np.pi * t_flow / (1 * 3600))
    + np.random.normal(0, 3, len(t_flow))
)
flow = np.clip(flow, 60, 180)

h2s = (
    0.85
    + 0.05 * np.sin(2 * np.pi * t_flow / (8 * 3600))
    + np.random.normal(0, 0.01, len(t_flow))
)
h2s = np.clip(h2s, 0.7, 0.95)

df = pd.DataFrame({
    "t": t_flow,
    "flow": flow,
    "h2s": h2s
})

# analyzer lag (5 min rolling mean)
df["h2s_an"] = df["h2s"].rolling(30, min_periods=1).mean()

# =========================
# 3. STOICH
# =========================
burn_fraction = 1/3

h2s_mol = df["flow"] * df["h2s"]

o2_ideal = h2s_mol * burn_fraction * 1.5
o2_actual = (df["flow"] * df["h2s_an"]) * burn_fraction * 1.5

# air
air_frac = 0.21
air_ideal = o2_ideal / air_frac
air_actual = o2_actual / air_frac

# convert to SCFM
air_ideal_scfm = air_ideal * 2118.88
air_actual_scfm = air_actual * 2118.88

df["air_ideal"] = air_ideal_scfm
df["air_actual"] = air_actual_scfm

# =========================
# 4. PLOTS (downsample for clarity)
# =========================
step = 60  # 10 min plotting resolution

t_hr = df["t"][::step] / 3600
h2s_plot = df["h2s"][::step]

plt.figure()
plt.plot(t_hr, h2s_plot)
plt.title("H2S Composition (mole fraction)")
plt.xlabel("Time (hr)")
plt.ylabel("H2S fraction")
plt.tight_layout()

plt.figure()
plt.plot(t_hr, df["air_ideal"][::step], label="Ideal air (instant H2S)")
plt.plot(t_hr, df["air_actual"][::step], label="Actual air (analyzer lag)")
plt.title("Air Flow Control: Ideal vs Analyzer-Lagged")
plt.xlabel("Time (hr)")
plt.ylabel("Air flow (SCFM)")
plt.legend()
plt.tight_layout()

plt.show()

df.head()