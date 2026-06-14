"""Coupled neutronics + thermal plant simulator with reactivity feedback (Phase 5).

This is the per-dt time march. Each domain is advanced over a shared outer
timestep by operator splitting:

  1. read feedback temperatures -> rho_total = rho_rods(t) + Doppler + moderator
  2. advance point kinetics over dt at that reactivity  (matrix-exponential,
     exact for piecewise-constant rho, so the stiff kinetics need no sub-stepping)
  3. map power n -> volumetric heat source, advance the radial fuel-pin
     conduction one implicit (backward-Euler) step -> new fuel temperatures
  4. advance the lumped coolant node one implicit step -> new moderator temp
  5. recompute the feedback temperatures, log, advance t

Thermal model
-------------
The fuel is the Phase-2 radial conduction pin (giving a volume-averaged fuel
temperature for the Doppler feedback and capturing the pellet thermal lag that
makes power overshoot before it settles). The coolant is a single lumped node
representing the channel-average ("moderator") temperature:

    M_c c_p dT_c/dt = Q_in - 2 W c_p (T_c - T_in)

where Q_in is the heat leaving the pin, W = mdot, and the outlet is T_out =
2 T_c - T_in for a linear axial profile. This lumped form is the standard
companion to point kinetics and keeps the loop fast enough for long transients.

The feedback is referenced to the initial steady operating point, so at t=0 the
feedback reactivity is zero and the reactor is critical with rho_rods = 0; any
later rho_rods(t) perturbation reveals the self-regulation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
from scipy.linalg import expm

from ..neutronics.point_kinetics import equilibrium_state
from ..neutronics.reactivity import FeedbackCoefficients, pwr_feedback
from ..params.geometry import PinGeometry, pwr_17x17
from ..params.kinetics import KineticsParams, u235
from ..params.materials import Material, uo2, zircaloy
from ..params.plant import CoolantBC
from ..hydraulics.correlations import WaterProperties, htc, pwr_water
from ..thermal.conduction1d import RadialPinModel


@dataclass
class SimulationResult:
    t: np.ndarray
    power: np.ndarray          # normalized neutron power n (1 = full power)
    rho_total: np.ndarray      # delta-k/k
    rho_feedback: np.ndarray
    rho_rods: np.ndarray
    T_fuel_avg: np.ndarray     # K, volume-averaged fuel temperature
    T_fuel_center: np.ndarray  # K
    T_coolant: np.ndarray      # K, lumped moderator temperature


@dataclass
class ControlledResult(SimulationResult):
    setpoint: np.ndarray = None       # controller setpoint vs time
    rod_position: np.ndarray = None   # regulating bank fractional insertion
    scram_position: np.ndarray = None # shutdown rod fractional insertion
    scram_tripped: np.ndarray = None  # bool, trip latched


@dataclass
class PlantSimulator:
    kin: KineticsParams = field(default_factory=u235)
    fb: FeedbackCoefficients = field(default_factory=pwr_feedback)
    geom: PinGeometry = field(default_factory=pwr_17x17)
    fuel: Material = field(default_factory=uo2)
    clad: Material = field(default_factory=zircaloy)
    water: WaterProperties = field(default_factory=pwr_water)

    mdot: float = 0.335            # coolant mass flow per channel (kg/s)
    T_inlet: float = 563.15        # K
    q_linear_full: float = 17.8e3  # rod-average linear heat rate at n=1 (W/m)
    h_film: float | None = None    # film coefficient (computed if None)
    n_fuel: int = 20
    n_clad: int = 4

    # state (set by initialize)
    pin: RadialPinModel = field(init=False, default=None)
    state: np.ndarray = field(init=False, default=None)   # [n, C1..C6]
    T_fuel: np.ndarray = field(init=False, default=None)
    T_coolant: float = field(init=False, default=0.0)
    t: float = field(init=False, default=0.0)
    q3_full: float = field(init=False, default=0.0)
    Mc_cp: float = field(init=False, default=0.0)
    Wcp: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        g = self.geom
        if self.h_film is None:
            G = self.mdot / g.flow_area
            self.h_film = htc(G, g.hydraulic_diameter, self.water, heating=True)
        # volumetric source at full power
        self.q3_full = g.q_volumetric_from_linear(self.q_linear_full)
        # lumped coolant capacities (total, per rod over the active height)
        H = g.active_height
        M_c = self.water.rho * g.flow_area * H
        self.Mc_cp = M_c * self.water.cp
        self.Wcp = self.mdot * self.water.cp
        self._H = H

    # ------------------------------------------------------------------ #
    def _fuel_average(self, T: np.ndarray) -> float:
        vol = self.pin.vol[: self.n_fuel]
        return float(np.sum(T[: self.n_fuel] * vol) / np.sum(vol))

    def _coolant_steady(self) -> float:
        """Lumped coolant temperature at full power (all generated heat removed)."""
        Q_in = self.q_linear_full * self._H
        return self.T_inlet + Q_in / (2.0 * self.Wcp)

    def initialize(self, n0: float = 1.0) -> None:
        """Set the plant to a self-consistent steady state at power n0 and
        reference the feedback to that operating point (feedback = 0 there)."""
        Tc = self._coolant_steady()
        bc = CoolantBC(h=self.h_film, T_inf=Tc)
        self.pin = RadialPinModel(
            geom=self.geom, fuel=self.fuel, clad=self.clad, coolant=bc,
            q_volumetric=n0 * self.q3_full, n_fuel=self.n_fuel, n_clad=self.n_clad,
        )
        self.T_fuel = self.pin.solve_steady()
        self.T_coolant = Tc
        self.state = equilibrium_state(self.kin, n0=n0)
        self.t = 0.0

        if self.fb.T_fuel_ref is None:
            self.fb.T_fuel_ref = self._fuel_average(self.T_fuel)
        if self.fb.T_mod_ref is None:
            self.fb.T_mod_ref = Tc

    # ------------------------------------------------------------------ #
    def _kinetics_matrix(self, rho: float) -> np.ndarray:
        p = self.kin
        G = p.n_groups
        A = np.zeros((G + 1, G + 1))
        A[0, 0] = (rho - p.beta) / p.Lambda
        A[0, 1:] = p.lambda_i
        A[1:, 0] = p.beta_i / p.Lambda
        A[1:, 1:] = np.diag(-p.lambda_i)
        return A

    def _advance_kinetics(self, y: np.ndarray, rho: float, dt: float) -> np.ndarray:
        # Exact for constant rho over dt: y(t+dt) = expm(A dt) y(t).
        return expm(self._kinetics_matrix(rho) * dt) @ y

    def _advance_coolant(self, Tc: float, q_out_per_length: float, dt: float) -> float:
        # Backward Euler on  Mc_cp dTc/dt = Q_in - 2 W cp (Tc - T_in).
        Q_in = q_out_per_length * self._H
        a = self.Mc_cp / dt
        return (a * Tc + Q_in + 2.0 * self.Wcp * self.T_inlet) / (a + 2.0 * self.Wcp)

    # ------------------------------------------------------------------ #
    def step(self, dt: float, rho_rods: float = 0.0) -> None:
        T_fuel_avg = self._fuel_average(self.T_fuel)
        rho = rho_rods + self.fb.feedback(T_fuel_avg, self.T_coolant)

        # neutronics
        self.state = self._advance_kinetics(self.state, rho, dt)
        n = self.state[0]

        # fuel conduction (implicit step at the new power)
        self.pin.q_volumetric = n * self.q3_full
        self.pin.coolant = CoolantBC(h=self.h_film, T_inf=self.T_coolant)
        self.T_fuel = self.pin.step(self.T_fuel, dt)

        # coolant node
        q_out = self.pin.heat_out(self.T_fuel)
        self.T_coolant = self._advance_coolant(self.T_coolant, q_out, dt)

        self.t += dt

    def run(self, t_end: float, dt: float,
            rho_rods: Callable[[float], float] | float = 0.0) -> SimulationResult:
        """Integrate to t_end. rho_rods may be a constant or a function of t."""
        if self.state is None:
            self.initialize()
        rod_fn = rho_rods if callable(rho_rods) else (lambda t: rho_rods)

        n_steps = int(round(t_end / dt))
        rec = {k: [] for k in
               ("t", "power", "rho_total", "rho_feedback", "rho_rods",
                "T_fuel_avg", "T_fuel_center", "T_coolant")}

        def log(rod):
            Tfa = self._fuel_average(self.T_fuel)
            fb = self.fb.feedback(Tfa, self.T_coolant)
            rec["t"].append(self.t)
            rec["power"].append(self.state[0])
            rec["rho_feedback"].append(fb)
            rec["rho_rods"].append(rod)
            rec["rho_total"].append(rod + fb)
            rec["T_fuel_avg"].append(Tfa)
            rec["T_fuel_center"].append(self.T_fuel[0])
            rec["T_coolant"].append(self.T_coolant)

        log(rod_fn(self.t))
        for _ in range(n_steps):
            rod = rod_fn(self.t)
            self.step(dt, rho_rods=rod)
            log(rod_fn(self.t))

        return SimulationResult(**{k: np.array(v) for k, v in rec.items()})


    def measurements(self) -> dict:
        """Current plant measurements available to a controller."""
        return {
            "t": self.t,
            "power": self.state[0],
            "T_fuel_avg": self._fuel_average(self.T_fuel),
            "T_fuel_center": self.T_fuel[0],
            "T_coolant": self.T_coolant,
        }

    def run_controlled(self, t_end: float, dt: float, controller,
                       setpoint=None) -> ControlledResult:
        """Integrate with a rod controller in the loop.

        controller : object with reset() and step(dt, meas) -> rho_rods
        setpoint   : optional callable(t) updating controller.pid.setpoint
        """
        if self.state is None:
            self.initialize()
        controller.reset()

        keys = ("t", "power", "rho_total", "rho_feedback", "rho_rods",
                "T_fuel_avg", "T_fuel_center", "T_coolant",
                "setpoint", "rod_position", "scram_position", "scram_tripped")
        rec = {k: [] for k in keys}

        def log(rho_rod):
            Tfa = self._fuel_average(self.T_fuel)
            fb = self.fb.feedback(Tfa, self.T_coolant)
            rec["t"].append(self.t)
            rec["power"].append(self.state[0])
            rec["rho_feedback"].append(fb)
            rec["rho_rods"].append(rho_rod)
            rec["rho_total"].append(rho_rod + fb)
            rec["T_fuel_avg"].append(Tfa)
            rec["T_fuel_center"].append(self.T_fuel[0])
            rec["T_coolant"].append(self.T_coolant)
            rec["setpoint"].append(controller.pid.setpoint)
            rec["rod_position"].append(controller.bank.position)
            rec["scram_position"].append(controller.scram.position)
            rec["scram_tripped"].append(controller.scram.tripped)

        n_steps = int(round(t_end / dt))
        log(0.0)
        for _ in range(n_steps):
            if setpoint is not None:
                controller.pid.setpoint = setpoint(self.t)
            rho_rod = controller.step(dt, self.measurements())
            self.step(dt, rho_rods=rho_rod)
            log(rho_rod)

        arr = {k: np.array(v) for k, v in rec.items()}
        return ControlledResult(**arr)


def pwr_simulator() -> PlantSimulator:
    sim = PlantSimulator()
    sim.initialize()
    return sim
