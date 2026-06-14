"""1D axial coolant-channel energy balance, and its coupling to the fuel pin.

Coolant marches up a single subchannel, absorbing the heat the rod sheds:

    mdot * c_p * dT_c/dz = q'(z)

At steady state this integrates to

    T_c(z) = T_in + (1 / (mdot c_p)) * integral_0^z q'(z') dz'.

The convective film coefficient h on the rod surface comes from the
Dittus-Boelter correlation evaluated at the subchannel mass flux and hydraulic
diameter (see hydraulics.correlations).

Coupling to the pin: the channel is sliced into axial nodes; at each elevation we
run the Phase-2 radial conduction solve with the *local* coolant temperature and
h as the convective boundary condition, and the *local* linear heat rate as the
source. The result is the full 2D (r, z) temperature field of a thermally-closed
pin. Because the coolant heats as it rises while the power profile is symmetric
about the mid-plane, the hottest clad and fuel temperatures occur *above* the
core mid-plane -- a hallmark of real rods that this model reproduces.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..params.geometry import PinGeometry, pwr_17x17
from ..params.materials import Material, uo2, zircaloy
from ..params.plant import CoolantBC, pwr_nominal
from ..thermal.conduction1d import RadialPinModel
from ..thermal.power_shape import AxialPowerShape
from .correlations import WaterProperties, htc, pwr_water, reynolds


@dataclass
class ChannelSolution:
    z: np.ndarray            # cell-centre elevations (m)
    z_faces: np.ndarray      # cell-face elevations (m), length M+1
    T_coolant: np.ndarray    # cell bulk coolant temperature (K)
    T_faces: np.ndarray      # face coolant temperature (K); T_faces[0] = inlet
    h: np.ndarray            # convective coefficient per cell (W/m^2/K)
    q_linear: np.ndarray     # linear heat rate per cell (W/m)
    Re: float                # subchannel Reynolds number
    Pr: float                # coolant Prandtl number

    @property
    def T_inlet(self) -> float:
        return float(self.T_faces[0])

    @property
    def T_outlet(self) -> float:
        return float(self.T_faces[-1])

    def power(self) -> float:
        """Total power deposited in the channel per rod (W)."""
        dz = self.z_faces[1] - self.z_faces[0]
        return float(np.sum(self.q_linear) * dz)


@dataclass
class CoolantChannel:
    geom: PinGeometry = field(default_factory=pwr_17x17)
    water: WaterProperties = field(default_factory=pwr_water)
    axial: AxialPowerShape | None = None
    mdot: float = 0.335                # coolant mass flow per channel (kg/s)
    T_inlet: float = 563.15            # core inlet temperature (K), ~290 C
    q_linear_avg: float = 17.8e3       # rod-average linear heat rate (W/m)
    n_axial: int = 40

    def __post_init__(self) -> None:
        if self.axial is None:
            self.axial = AxialPowerShape(height=self.geom.active_height)

    @property
    def mass_flux(self) -> float:
        """G = mdot / flow_area (kg/m^2/s)."""
        return self.mdot / self.geom.flow_area

    def solve(self) -> ChannelSolution:
        H = self.axial.height
        M = self.n_axial
        dz = H / M
        z_faces = np.linspace(0.0, H, M + 1)
        z = 0.5 * (z_faces[:-1] + z_faces[1:])

        q_lin = self.axial.q_linear(z, self.q_linear_avg)

        # March the bulk temperature up the channel (energy balance per cell).
        T_faces = np.empty(M + 1)
        T_faces[0] = self.T_inlet
        mc = self.mdot * self.water.cp
        for k in range(M):
            T_faces[k + 1] = T_faces[k] + q_lin[k] * dz / mc
        T_coolant = 0.5 * (T_faces[:-1] + T_faces[1:])

        # Convective coefficient. With constant properties h is uniform, but we
        # store per-cell so temperature-dependent properties can plug in later.
        G = self.mass_flux
        Dh = self.geom.hydraulic_diameter
        Re = reynolds(G, Dh, self.water.mu)
        h_val = htc(G, Dh, self.water, heating=True)
        h = np.full(M, h_val)

        return ChannelSolution(
            z=z, z_faces=z_faces, T_coolant=T_coolant, T_faces=T_faces,
            h=h, q_linear=q_lin, Re=Re, Pr=self.water.Pr,
        )


@dataclass
class PinFieldSolution:
    channel: ChannelSolution
    r_center: np.ndarray         # radial node positions (m)
    T_field: np.ndarray          # shape (M_axial, N_radial), temperature (K)
    n_fuel: int

    @property
    def T_centerline(self) -> np.ndarray:
        """Fuel centreline temperature vs elevation (K)."""
        return self.T_field[:, 0]

    @property
    def T_clad_outer(self) -> np.ndarray:
        """Clad outer-surface temperature vs elevation (K)."""
        return self.T_field[:, -1]

    @property
    def T_pellet_surface(self) -> np.ndarray:
        return self.T_field[:, self.n_fuel - 1]


def solve_pin_channel(
    channel: CoolantChannel,
    fuel: Material | None = None,
    clad: Material | None = None,
    h_gap: float | None = None,
    n_fuel: int = 40,
    n_clad: int = 8,
) -> PinFieldSolution:
    """Solve the coupled coolant channel + radial conduction at every elevation.

    Returns the full (r, z) temperature field of the pin.
    """
    fuel = fuel or uo2()
    clad = clad or zircaloy()
    if h_gap is None:
        h_gap = pwr_nominal().h_gap

    sol = channel.solve()
    M = sol.z.size
    fields = []
    r_center = None
    for k in range(M):
        bc = CoolantBC(h=float(sol.h[k]), T_inf=float(sol.T_coolant[k]), h_gap=h_gap)
        q_vol = channel.geom.q_volumetric_from_linear(float(sol.q_linear[k]))
        model = RadialPinModel(
            geom=channel.geom, fuel=fuel, clad=clad, coolant=bc,
            q_volumetric=q_vol, n_fuel=n_fuel, n_clad=n_clad,
        )
        T = model.solve_steady()
        if r_center is None:
            r_center = model.r_center
        fields.append(T)

    return PinFieldSolution(
        channel=sol, r_center=r_center, T_field=np.array(fields), n_fuel=n_fuel,
    )


def pwr_channel() -> CoolantChannel:
    """Default nominal PWR coolant channel."""
    return CoolantChannel()
