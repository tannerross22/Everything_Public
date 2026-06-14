# reactorsim

A PWR thermal-hydraulics and reactor-kinetics simulation, built up one
physics domain at a time. This is an engineering modeling project for
understanding plant dynamics and control.

## Status

| Phase | Module | What it does | State |
|------:|--------|--------------|-------|
| 1 | `neutronics.point_kinetics` | Point reactor kinetics, 6 delayed groups | ✅ done, validated |
| 2 | `thermal.conduction1d` | 1D radial fuel-pin conduction | ✅ done, validated |
| 3 | `hydraulics.coolant_channel` | 1D axial coolant energy balance + convection | ✅ done, validated |
| 4 | `thermal.conduction3d` | 3D (r-θ-z) conduction | ✅ done, validated |
| 5 | `coupling.simulator` | Neutronics ↔ thermal feedback | ✅ done, validated |
| 6 | `control.*` | PID rods (grey/black), SCRAM | ✅ done, validated |
| 6.5 | `neutronics.spatial_kinetics` | 1D axial diffusion kinetics + AO control | ✅ done, validated |
| 7 | `hydraulics.heat_exchanger` | Secondary side / steam generator | ✅ done, validated |

Target plant: PWR, UO₂ fuel, 17×17 assembly geometry. All internal quantities
are strict SI (m, K, W, s, kg).

## Setup

```sh
python -m pip install -r requirements.txt
```

## Run

```sh
python -m pytest tests/ -q             # run the validation gates
python scripts/run_step_insertion.py   # Phase 1 demo: step reactivity transient
python scripts/run_pin_conduction.py   # Phase 2 demo: radial pin temperature profile
python scripts/run_coolant_channel.py  # Phase 3 demo: axial coolant + pin coupling
python scripts/run_conduction3d.py     # Phase 4 demo: 2D (r,z) pin temperature field
python scripts/run_feedback_transient.py  # Phase 5 demo: self-regulation transient
python scripts/run_rod_control.py       # Phase 6 demo: load-follow + SCRAM
python scripts/run_axial_control.py     # Phase 6.5 demo: flux shapes + AO control
python scripts/run_steam_generator.py   # Phase 7 demo: secondary-pressure trade
python scripts/make_animations.py       # render MP4 animations -> animations/
```

## Animations

`scripts/make_animations.py` renders MP4s of the reactor temperature field over
time, reconstructing a 2D (r, z) cross-section heat map from the axial simulator
and overlaying the control-rod bank insertion in the margins:

- `animations/reactor_power_maneuver.mp4` — a power maneuver (banks move together;
  the whole core brightens and dims).
- `animations/reactor_ao_swing.mp4` — an axial-offset swing at constant power
  (banks move differentially; the hot region migrates up and down the core).

MP4 export uses the `imageio-ffmpeg` bundled binary, so no system ffmpeg install
is required.

## Phase 1 — point kinetics

Solves the point reactor kinetics equations

```
dn/dt   = (rho - beta)/Lambda * n + sum_i lambda_i C_i
dC_i/dt = beta_i/Lambda n - lambda_i C_i
```

with the six-group Keepin delayed-neutron data for U-235. The system is stiff
(timescales from Λ ≈ 2e-5 s to the slowest precursor ≈ 80 s), so it is
integrated implicitly (`scipy`'s BDF) with an analytic Jacobian.

Reactivity is supplied as a pluggable `rho(t, n)` callable; Phase 1 ships
constant / step / ramp drivers. Temperature feedback plugs in here at Phase 5.

**Validation** (`tests/test_point_kinetics.py`): zero-reactivity steady state,
prompt-jump approximation `n/n0 = beta/(beta - rho)`, and asymptotic period
matched against the dominant root of the **inhour equation** for both positive
and negative step insertions.

## Phase 2 — 1D radial conduction

Solves the cylindrical heat equation in the fuel pin

```
rho c_p dT/dt = (1/r) d/dr ( k r dT/dr ) + q'''(r)
```

across UO₂ pellet → He gap (a contact conductance, not a meshed layer) →
Zircaloy clad → coolant (convective Robin BC). Cell-centred **finite volume**
(energy-conserving), solved as a tridiagonal system; temperature-dependent UO₂
conductivity `k(T)` handled by Picard iteration. Both steady-state and transient
(backward-Euler) solves are available.

At nominal average power (q' = 17.8 kW/m) it predicts a ~855 °C centerline with
the characteristic large temperature drop across the gas gap.

**Validation** (`tests/test_conduction1d.py`): constant-k pellet matched to the
analytic profile `T(r) = T_s + q'''(r_f² − r²)/(4k)` and centerline rise;
full-stack steady-state energy balance (generation = surface heat flux);
monotonic profile; transient relaxation to the steady solution; and the
temperature-dependent-k centerline running hotter than constant-k.

## Phase 3 — axial coolant channel + convection

Marches the coolant up one subchannel by the energy balance
`ṁ cₚ dT_c/dz = q'(z)`, with the rod-surface film coefficient `h` from the
**Dittus-Boelter** correlation (`Nu = 0.023 Re⁰·⁸ Pr⁰·⁴`) evaluated at the
subchannel mass flux and hydraulic diameter. An `AxialPowerShape` (chopped
cosine, `thermal/power_shape.py`) supplies `q'(z)`. `solve_pin_channel()` then
runs the Phase-2 radial conduction at every elevation with the *local* coolant
temperature and `h`, producing the full 2D (r, z) field of a thermally-closed
pin.

At nominal conditions: G ≈ 3800 kg/m²s, Re ≈ 5.3×10⁵, h ≈ 37 kW/m²K, ~35 K
coolant rise, 65 kW/rod. Because the coolant heats as it rises, the peak clad
temperature lands above the core mid-plane — the classic hot-spot shift.

**Validation** (`tests/test_coolant.py`): Re/Pr/Dittus-Boelter vs hand
calculation; `h` in the PWR range; channel enthalpy rise = total deposited
power; coolant monotonically increasing; axial shape normalized to unit average;
and the coupled field showing the clad/fuel peaks above the mid-plane.

## Phase 4 — 3D (r, θ, z) conduction

Generalizes the conduction solver to the full cylindrical heat equation on an
`Nr × Nθ × Nz` finite-volume mesh, assembled as a sparse system. The new physics
is **axial conduction**, coupling the z-levels that Phase 3 treated as
independent slices. The azimuth defaults to `Nθ = 1` (axisymmetric — a symmetric
single pin has no θ-gradient) but is fully implemented. `from_channel()` builds
the model with `q'''(z)`, `T_coolant(z)`, `h(z)` taken from a solved coolant
channel; outer boundary is convective (Robin), axial ends adiabatic by default.

For a long thin rod, axial conduction is a tiny correction (it lowers the peak
centerline by ~0.005 K), which quantitatively confirms Phase 3's independent-
slice approximation was well justified.

**Validation** (`tests/test_conduction3d.py`): a single z-slice reproduces the
Phase-2 1D model (to ~1e-9 K); uniform source leaves all slices identical;
adiabatic-end energy balance; azimuthal symmetry with `Nθ>1`; a pure-axial slab
matched to the analytic `T(z)=T_end+q'''z(H−z)/(2k)`; axial conduction lowering
the mid-plane peak vs the stacked model; and transient relaxation to steady.

## Phase 5 — neutronics ↔ thermal feedback coupling

The per-`dt` time march (`coupling/simulator.py`). Each step: read feedback
temps → `rho_total = rho_rods(t) + Doppler + moderator` → advance point kinetics
(matrix-exponential, exact for piecewise-constant ρ — no sub-stepping) → map
power to `q'''` and step the radial fuel conduction → step a lumped coolant
("moderator") node → recompute feedback. The feedback (`neutronics/reactivity.py`)
is referenced to the initial operating point, so the plant starts critical and
any `rho_rods(t)` perturbation reveals the passive **self-regulation**.

A +15 pcm step makes power overshoot to ~1.024, then the fuel heats (~5.5 K),
Doppler feedback builds to −15 pcm, and the plant settles at a new steady power
(~1.013) with total reactivity back to ~0 — no controller involved.

**Validation** (`tests/test_simulator.py`): self-consistent critical init with
zero feedback; steady state holds; positive insertion settles to a new
equilibrium where feedback cancels it (`rho_total→0`); power overshoot from the
thermal lag; negative insertion lowers power/temperature; Doppler dominates the
feedback.

## Phase 6 — PID rod control + SCRAM

The control layer driving the `rho_rods(t)` input from Phase 5.
- `control/pid.py` — PID with derivative-on-measurement, output clamping, and
  conditional-integration anti-windup.
- `control/rod_worth.py` — the S-curve integral rod worth
  `W(p)=W_tot[p − sin(2πp)/2π]` (differential worth peaks mid-stroke), its
  inverse, and a rate-limited `ControlRodBank` with grey/black factories.
- `control/scram.py` — an independent safety supervisor that latches a trip on
  over-power / over-temperature and slams the shutdown rods in.
- `control/rod_banks.py` — the `RodController` assembly (PID + bank + SCRAM),
  reactivity referenced to the parked mid-band position; `PlantSimulator.
  run_controlled()` puts it in the loop.

Demonstrated: load-follow power tracking (1.0→0.85→1.0, settled error <1%) and a
SCRAM that caps an over-power excursion and drives the plant to ~−8600 pcm.

**Validation** (`tests/test_control.py`): PID sign/tracking/anti-windup; rod-worth
endpoints, monotonicity, mid-stroke differential peak, and inverse round-trip;
bank rate limiting; SCRAM trip/latch on power and temperature; closed-loop power
tracking; and SCRAM shutdown.

## Phase 6.5 — axial (spatial) neutronics + axial-offset control

Upgrades point kinetics to **1D axial one-group diffusion kinetics**
(`neutronics/spatial_kinetics.py`): finite volume in z with 6 delayed groups per
node, a criticality search that scales `νΣ_f` so the reference (with banks
parked) is critical, and per-node temperature feedback mapped onto `Σ_a`. The
diffusion coefficient is set to a realistic ~8 cm migration length. Now the axial
flux *shape* is a dynamic state, so:
- the cosine fundamental mode emerges (matches `cos` to <0.2%);
- partial rod worth emerges as an S-curve with realistic flux redistribution;
- the model reduces to point kinetics under a uniform insertion (to ~1e-3);
- **axial offset** `AO = (P_top−P_bot)/(P_top+P_bot)` is controllable.

`coupling/axial_simulator.py` couples it to per-node lumped fuel + advective
coolant. `control/axial_control.py` does MIMO control with two banks: **mean
insertion → power, differential insertion → axial offset**. The demo drives AO
to ±0.12 while holding power flat (<5% blip), with the banks moving
differentially. *(Xenon — the classic driver of axial instability — is a noted
future addition.)*

**Validation** (`tests/test_spatial_kinetics.py`, `tests/test_axial_control.py`):
criticality, symmetric fundamental mode, steady hold, reduction to point
kinetics, monotonic S-curve worth, rod-induced flux tilt; and coupled steady
hold, AO setpoint tracking holding power, and power tracking holding AO.

## Phase 7 — steam generator / secondary side

Closes the plant loop. `hydraulics/steam_tables.py` provides saturated-water
properties; `hydraulics/heat_exchanger.py` models the steam generator as an
**evaporator** (primary single-phase, secondary boiling at T_sat) with matching
**effectiveness-NTU and LMTD** methods, sizing (`required_UA`), a closed
`PrimaryLoop` (SG duty = core power fixes the hot/cold-leg temps), and a
saturated **Rankine** efficiency estimate.

The secondary pressure is a design choice: it sets the boiling temperature, which
trades off against heat-transfer area, cycle efficiency, and steam moisture. The
demo sweeps it to show the trade; the default 6.9 MPa (T_sat 285 °C) reproduces a
real PWR — 3411 MW duty, 1900 kg/s steam, ~32% efficiency, primary 324→289.5 °C
(consistent with the Phase-3 primary side).

**Validation** (`tests/test_heat_exchanger.py`): steam-table consistency;
effectiveness-NTU = LMTD; primary and steam-rate energy balances; UA sizing
inversion and the infeasible-pinch case; the pressure trade (UA↑, efficiency↑,
quality↓ with pressure); the approach-temperature design rule; and the closed
primary loop landing in the PWR temperature range.
