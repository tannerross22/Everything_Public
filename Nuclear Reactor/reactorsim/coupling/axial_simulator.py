"""Coupled axial (spatial) neutronics + per-node thermal simulator (Phase 6.5).

Like the Phase-5 point-kinetics simulator, but the neutronics is the 1D axial
diffusion kinetics (so the flux *shape* is a dynamic state) and the thermal model
is resolved per axial node:

  * each node has a lumped fuel temperature  Cf dT_f/dt = q'(z) dz - UA(T_f - T_c)
  * coolant marches up the channel (upwind):
        Cc dT_c/dt = UA(T_f - T_c) + W c_p (T_c,below - T_c)

Each node's temperatures perturb its local absorption cross-section (calibrated
to the Phase-5 feedback coefficients), so a flux tilt changes the feedback
asymmetrically and vice-versa. This makes the axial offset a genuine dynamic,
controllable output.

Reactivity is referenced to the steady operating point per node (feedback = 0
there), so the plant starts critical with the regulating banks parked mid-band.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from ..neutronics.spatial_kinetics import AxialKineticsModel
from ..neutronics.reactivity import FeedbackCoefficients, pwr_feedback
from ..params.geometry import PinGeometry, pwr_17x17
from ..params.materials import Material, uo2
from ..hydraulics.correlations import WaterProperties, pwr_water


@dataclass
class AxialResult:
    t: np.ndarray
    power: np.ndarray
    axial_offset: np.ndarray
    T_fuel_avg: np.ndarray
    T_coolant_out: np.ndarray
    p_top: np.ndarray
    p_bottom: np.ndarray
    setpoint_power: np.ndarray = None
    setpoint_ao: np.ndarray = None
    z: np.ndarray = None
    flux_snapshots: np.ndarray = None     # (n_snap, N) if requested
    snapshot_times: np.ndarray = None


@dataclass
class AxialPlantSimulator:
    kinetics: AxialKineticsModel = field(default_factory=AxialKineticsModel)
    fb: FeedbackCoefficients = field(default_factory=pwr_feedback)
    geom: PinGeometry = field(default_factory=pwr_17x17)
    water: WaterProperties = field(default_factory=pwr_water)
    fuel: Material = field(default_factory=uo2)

    mdot: float = 0.335
    T_inlet: float = 563.15
    q_linear_full: float = 17.8e3
    UA_per_length: float = 51.6        # fuel->coolant conductance (W/m/K)

    rod_worth_top: float = 0.020       # full-insertion worth of each bank
    rod_worth_bottom: float = 0.020
    p0: float = 0.25                   # parked insertion (tips near the ends)

    # state
    y: np.ndarray = field(init=False, default=None)
    T_fuel: np.ndarray = field(init=False, default=None)
    T_coolant: np.ndarray = field(init=False, default=None)
    t: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        N = self.kinetics.n_axial
        self.dz = self.kinetics.dz
        self.N = N
        cp_f = self.fuel.cp(900.0)
        self.Cf_node = self.fuel.rho * self.geom.fuel_area * cp_f * self.dz
        self.UA_node = self.UA_per_length * self.dz
        self.Cc_node = self.water.rho * self.geom.flow_area * self.dz * self.water.cp
        self.Wcp = self.mdot * self.water.cp

    # ------------------------------------------------------------------ #
    def initialize(self) -> None:
        k = self.kinetics
        # make the reference critical WITH the banks parked at p0: the parked
        # rods' absorption is folded into the criticality search (the core holds
        # excess reactivity that the parked rods suppress).
        sigma_park = (k.Sigma_a
                      + k.rod_sigma(self.p0, self.rod_worth_top, from_top=True)
                      + k.rod_sigma(self.p0, self.rod_worth_bottom, from_top=False))
        k.set_reference_absorption(sigma_park)
        phi = k.phi_ref
        q = self.q_linear_full * phi          # W/m per node
        # steady coolant march and fuel temperatures
        Tc = np.empty(self.N)
        prev = self.T_inlet
        for i in range(self.N):
            Tc[i] = prev + q[i] * self.dz / self.Wcp
            prev = Tc[i]
        Tf = Tc + q / self.UA_per_length
        self.T_coolant = Tc.copy()
        self.T_fuel = Tf.copy()
        self.T_fuel_ref = Tf.copy()
        self.T_mod_ref = Tc.copy()
        self.y = k.initial_state()
        self.t = 0.0

    # ------------------------------------------------------------------ #
    def _sigma_a(self, p_top: float, p_bottom: float) -> np.ndarray:
        k = self.kinetics
        ds = (k.rod_sigma(p_top, self.rod_worth_top, from_top=True)
              + k.rod_sigma(p_bottom, self.rod_worth_bottom, from_top=False))
        ds += k.feedback_sigma(self.T_fuel - self.T_fuel_ref,
                               self.T_coolant - self.T_mod_ref,
                               self.fb.alpha_fuel, self.fb.alpha_mod)
        return k.Sigma_a + ds

    def _advance_thermal(self, phi: np.ndarray, dt: float) -> None:
        q = self.q_linear_full * phi
        # fuel (implicit, uses current coolant)
        af = self.Cf_node / dt
        Tf_new = (af * self.T_fuel + q * self.dz + self.UA_node * self.T_coolant) \
            / (af + self.UA_node)
        # coolant (implicit upwind, sweep bottom -> top)
        ac = self.Cc_node / dt
        Tc_new = np.empty(self.N)
        below = self.T_inlet
        for i in range(self.N):
            Tc_new[i] = (ac * self.T_coolant[i] + self.UA_node * Tf_new[i]
                         + self.Wcp * below) / (ac + self.UA_node + self.Wcp)
            below = Tc_new[i]
        self.T_fuel, self.T_coolant = Tf_new, Tc_new

    def step(self, dt: float, p_top: float, p_bottom: float) -> None:
        sigma = self._sigma_a(p_top, p_bottom)
        self.y = self.kinetics.advance(self.y, sigma, dt)
        phi, _ = self.kinetics.split(self.y)
        self._advance_thermal(phi, dt)
        self.t += dt

    # ------------------------------------------------------------------ #
    def measurements(self) -> dict:
        phi, _ = self.kinetics.split(self.y)
        return {
            "t": self.t,
            "power": self.kinetics.total_power(phi),
            "axial_offset": self.kinetics.axial_offset(phi),
            "T_fuel_avg": float(self.T_fuel.mean()),
            "T_coolant_out": float(self.T_coolant[-1]),
        }

    def _run(self, t_end, dt, control, snapshots=None) -> AxialResult:
        if self.y is None:
            self.initialize()
        keys = ("t", "power", "axial_offset", "T_fuel_avg", "T_coolant_out",
                "p_top", "p_bottom", "setpoint_power", "setpoint_ao")
        rec = {k: [] for k in keys}
        snaps, snap_t = [], []
        snap_set = set(snapshots or [])

        def log(p_top, p_bottom, spp, spa):
            m = self.measurements()
            rec["t"].append(self.t)
            rec["power"].append(m["power"])
            rec["axial_offset"].append(m["axial_offset"])
            rec["T_fuel_avg"].append(m["T_fuel_avg"])
            rec["T_coolant_out"].append(m["T_coolant_out"])
            rec["p_top"].append(p_top)
            rec["p_bottom"].append(p_bottom)
            rec["setpoint_power"].append(spp)
            rec["setpoint_ao"].append(spa)

        n_steps = int(round(t_end / dt))
        p_top, p_bottom, spp, spa = control(self.measurements(), first=True)
        log(p_top, p_bottom, spp, spa)
        for _ in range(n_steps):
            p_top, p_bottom, spp, spa = control(self.measurements())
            self.step(dt, p_top, p_bottom)
            for st in list(snap_set):
                if self.t >= st:
                    phi, _ = self.kinetics.split(self.y)
                    snaps.append(phi.copy()); snap_t.append(self.t)
                    snap_set.discard(st)
            log(p_top, p_bottom, spp, spa)

        arr = {k: np.array(v) for k, v in rec.items()}
        return AxialResult(
            **arr, z=self.kinetics.z,
            flux_snapshots=np.array(snaps) if snaps else None,
            snapshot_times=np.array(snap_t) if snap_t else None,
        )

    def run_fixed(self, t_end, dt, p_top=None, p_bottom=None,
                  snapshots=None) -> AxialResult:
        """Run with fixed or time-scheduled bank positions (no controller)."""
        pt = p_top if callable(p_top) else (lambda t: self.p0 if p_top is None else p_top)
        pb = p_bottom if callable(p_bottom) else (lambda t: self.p0 if p_bottom is None else p_bottom)

        def control(meas, first=False):
            return pt(meas["t"]), pb(meas["t"]), None, None

        return self._run(t_end, dt, control, snapshots)

    def run_controlled(self, t_end, dt, controller,
                       power_setpoint=None, ao_setpoint=None,
                       snapshots=None) -> AxialResult:
        controller.reset()

        def control(meas, first=False):
            if power_setpoint is not None:
                controller.power_pid.setpoint = power_setpoint(meas["t"])
            if ao_setpoint is not None:
                controller.ao_pid.setpoint = ao_setpoint(meas["t"])
            if first:
                return (controller.p_top, controller.p_bottom,
                        controller.power_pid.setpoint, controller.ao_pid.setpoint)
            p_top, p_bottom = controller.step(dt, meas)
            return p_top, p_bottom, controller.power_pid.setpoint, controller.ao_pid.setpoint

        return self._run(t_end, dt, control, snapshots)
