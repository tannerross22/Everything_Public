"""reactorsim -- a PWR thermal-hydraulics and reactor-kinetics simulation.

Build order (each phase independently testable):
    Phase 1  neutronics.point_kinetics   -- point reactor kinetics  (THIS PHASE)
    Phase 2  thermal.conduction1d        -- 1D radial fuel-pin conduction
    Phase 3  hydraulics.coolant_channel  -- 1D axial coolant energy balance
    Phase 4  thermal.conduction3d        -- 3D (r-theta-z) conduction
    Phase 5  coupling.simulator          -- neutronics <-> thermal feedback
    Phase 6  control.*                   -- PID rods, banks, SCRAM
    Phase 7  hydraulics.heat_exchanger   -- secondary side / steam generator

All internal quantities are strict SI (m, K, W, s, kg). Convert only at I/O.
"""

__version__ = "0.1.0"
