"""Coupling: the per-timestep orchestration that turns the separate physics
domains into a transient plant simulation.

Phase 5 couples neutronics (point kinetics) to a thermal model with temperature
reactivity feedback -- no controller yet, just the passive self-regulation.
Phase 6 adds the PID rod control on top of this loop.
"""
