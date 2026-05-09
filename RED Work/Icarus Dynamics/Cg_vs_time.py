import math
import numpy as np
import matplotlib.pyplot as plt

# ── Tunable parameters ──────────────────────────────────────────────────────
TOTAL_LENGTH_IN          = 126.5
ID_IN                    = 5.5
M_ETOH_KG                = 6.912
M_N2O_KG                 = 29.420
MDOT_TOTAL               = 3.543
OF_RATIO                 = 4.25
RHO_N2O_LIQ              = 727.0
RHO_N2O_VAP              = 165.0
RHO_ETOH                 = 789.0
M_DRY_LBM                = 115.0
CG_DRY_FROM_TIP_IN       = 104.0
TANK_BOTTOM_FROM_TIP_IN  = 157.0
ROCKET_LENGTH_IN         = 173.0
DT                       = 0.01
# ─────────────────────────────────────────────────────────────────────────────

M_DRY_KG  = M_DRY_LBM * 0.453592
ID_M      = ID_IN * 0.0254
A_M2      = math.pi / 4 * ID_M**2

mdot_etoh = MDOT_TOTAL / (1 + OF_RATIO)
mdot_n2o  = MDOT_TOTAL - mdot_etoh
burn_time = 30

print(f"mdot EtOH = {mdot_etoh:.4f} kg/s")
print(f"mdot N2O  = {mdot_n2o:.4f} kg/s")
print(f"Burn time = {burn_time:.2f} s")
print(f"Dry mass  = {M_DRY_KG:.2f} kg ({M_DRY_LBM:.1f} lbm)")

times      = np.arange(0, burn_time + DT, DT)
cg_rocket  = np.zeros(len(times))
cg_prop    = np.zeros(len(times))
cg_etoh    = np.zeros(len(times))
cg_n2o     = np.zeros(len(times))
cg_pist    = np.zeros(len(times))
m_etoh_arr = np.zeros(len(times))
m_n2o_arr  = np.zeros(len(times))

for i, t in enumerate(times):
    m_etoh = max(M_ETOH_KG - mdot_etoh * t, 0.0)
    m_n2o  = max(M_N2O_KG  - mdot_n2o  * t, 0.0)

    # EtOH: top fixed at 126.5", piston ascends from below
    vol_etoh_m3    = m_etoh / RHO_ETOH
    len_etoh_in    = (vol_etoh_m3 / A_M2) / 0.0254
    piston_loc_in  = TOTAL_LENGTH_IN - len_etoh_in
    cg_etoh_tank   = piston_loc_in + len_etoh_in / 2.0

    # N2O: fills 0 to piston_loc; liquid on bottom, vapor above
    vol_n2o_total_m3 = piston_loc_in * 0.0254 * A_M2
    vol_n2o_liq_m3   = m_n2o / RHO_N2O_LIQ
    vol_n2o_vap_m3   = max(vol_n2o_total_m3 - vol_n2o_liq_m3, 0.0)

    len_n2o_liq_in = (vol_n2o_liq_m3 / A_M2) / 0.0254
    len_n2o_vap_in = (vol_n2o_vap_m3 / A_M2) / 0.0254

    cg_n2o_liq_tank = len_n2o_liq_in / 2.0
    cg_n2o_vap_tank = len_n2o_liq_in + len_n2o_vap_in / 2.0

    m_n2o_vap           = vol_n2o_vap_m3 * RHO_N2O_VAP
    m_n2o_total_in_tank = m_n2o + m_n2o_vap

    if m_n2o_total_in_tank > 0:
        cg_n2o_tank = (m_n2o * cg_n2o_liq_tank + m_n2o_vap * cg_n2o_vap_tank) / m_n2o_total_in_tank
    else:
        cg_n2o_tank = 0.0

    # Convert tank-bottom ref → nose-tip ref
    cg_etoh_tip = TANK_BOTTOM_FROM_TIP_IN - cg_etoh_tank
    cg_n2o_tip  = TANK_BOTTOM_FROM_TIP_IN - cg_n2o_tank
    cg_pist_tip = TANK_BOTTOM_FROM_TIP_IN - piston_loc_in

    # Propellant-only CG from tip
    m_prop_total = m_etoh + m_n2o_total_in_tank
    if m_prop_total > 0:
        cg_prop_tip = (m_etoh * cg_etoh_tip + m_n2o_total_in_tank * cg_n2o_tip) / m_prop_total
    else:
        cg_prop_tip = cg_n2o_tip

    # Whole rocket CG from tip
    m_total  = M_DRY_KG + m_prop_total
    cg_tip   = (M_DRY_KG * CG_DRY_FROM_TIP_IN + m_prop_total * cg_prop_tip) / m_total

    cg_rocket[i]  = cg_tip
    cg_prop[i]    = cg_prop_tip
    cg_etoh[i]    = cg_etoh_tip
    cg_n2o[i]     = cg_n2o_tip
    cg_pist[i]    = cg_pist_tip
    m_etoh_arr[i] = m_etoh
    m_n2o_arr[i]  = m_n2o

cg_rocket_0 = cg_rocket[0]

import pandas as pd

df = pd.DataFrame({
    'time_s': times,
    'cg_from_tip_in': cg_rocket
})
df.to_csv('rocket_cg_vs_time.csv', index=False)
print("CSV saved to rocket_cg_vs_time.csv")

print(f"\nRocket CG at ignition:  {cg_rocket[0]:.2f} in from tip")
print(f"Rocket CG at burnout:   {cg_rocket[-1]:.2f} in from tip")
print(f"Total CG shift:         {cg_rocket[-1] - cg_rocket[0]:.2f} in")
min_idx = np.argmin(cg_rocket)
print(f"Minimum rocket CG:      {cg_rocket[min_idx]:.2f} in at t = {times[min_idx]:.2f} s")

# ── Figure 1: Absolute CG locations from nose tip ────────────────────────────
fig1, ax1 = plt.subplots(figsize=(7.5, 4.5))
ax1.plot(times, cg_rocket, 'k',   lw=1.8, label='Whole rocket CG')
ax1.plot(times, cg_prop,   'k--', lw=1.2, label='Propellant CG only')
ax1.axhline(CG_DRY_FROM_TIP_IN, color='k', lw=0.8, linestyle=':', label=f'Dry CG ({CG_DRY_FROM_TIP_IN}" from tip)')
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Distance from nose tip (in)')
ax1.set_title('Rocket CG vs Time')
ax1.legend(fontsize=9)
ax1.grid(True, linewidth=0.5)
ax1.set_xlim([0, burn_time])
ax1.invert_yaxis()

# ── Figure 2: CG deviation from ignition ─────────────────────────────────────
fig2, ax2 = plt.subplots(figsize=(7.5, 4.5))
ax2.plot(times, cg_rocket - cg_rocket_0, 'k',   lw=1.8, label='Whole rocket CG')
ax2.plot(times, cg_prop   - cg_prop[0],  'k--', lw=1.2, label='Propellant CG only')
ax2.axhline(0, color='k', lw=0.5)
ax2.set_xlabel('Time (s)')
ax2.set_ylabel('ΔCG from ignition (in)')
ax2.set_title('CG Deviation from Ignition (positive = toward tail)')
ax2.legend(fontsize=9)
ax2.grid(True, linewidth=0.5)
ax2.set_xlim([0, burn_time])

# ── Figure 3: Propellant mass vs time ────────────────────────────────────────
fig3, ax3 = plt.subplots(figsize=(7.5, 4.5))
ax3.plot(times, m_etoh_arr,               'k--', lw=1.2, label='EtOH liquid (kg)')
ax3.plot(times, m_n2o_arr,                'k:',  lw=1.2, label='N₂O liquid (kg)')
ax3.plot(times, m_etoh_arr + m_n2o_arr,   'k',   lw=1.8, label='Total liquid (kg)')
ax3.set_xlabel('Time (s)')
ax3.set_ylabel('Mass (kg)')
ax3.set_title('Propellant Mass vs Time')
ax3.legend(fontsize=9)
ax3.grid(True, linewidth=0.5)
ax3.set_xlim([0, burn_time])


import pandas as pd
from scipy.interpolate import interp1d

# ── Load CP data ──────────────────────────────────────────────────────────────
cp_df = pd.read_csv('CPvstime.csv', header=None, names=['time_s', 'cp_from_tip_in'])
cp_df = cp_df.dropna()  # drop NaN rows
cp_df = cp_df[cp_df['time_s'] <= burn_time]  # clip to burn time only

# ── Interpolate CG onto CP time grid ─────────────────────────────────────────
cg_interp = interp1d(times, cg_rocket, kind='linear', bounds_error=False, fill_value='extrapolate')
cg_at_cp_times = cg_interp(cp_df['time_s'].values)

# ── Stability caliber = (CG - CP) / diameter ─────────────────────────────────
# Both CG and CP are from tip, so CP > CG means stable (CP further aft)
DIAMETER_IN = 6.0  # <-- update this to your rocket's outer diameter
calibers = (cp_df['cp_from_tip_in'].values - cg_at_cp_times) / DIAMETER_IN

# ── Figure 4: Stability calibers vs time ─────────────────────────────────────
fig4, ax4 = plt.subplots(figsize=(7.5, 4.5))
ax4.plot(cp_df['time_s'].values, calibers, 'k', lw=1.8)
ax4.set_xlabel('Time (s)')
ax4.set_ylabel('Stability (calibers)')
ax4.set_title('Stability Calibers vs Time')
ax4.legend(fontsize=9)
ax4.grid(True, linewidth=0.5)
ax4.set_xlim([0, 30])

plt.show()
plt.show()