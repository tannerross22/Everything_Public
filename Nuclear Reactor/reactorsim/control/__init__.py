"""Control: rod-based reactivity control and safety supervision (Phase 6).

  pid       -- generic PID with anti-windup, derivative-on-measurement, clamping
  rod_worth -- S-curve integral rod worth and a rate-limited control-rod bank
  rod_banks -- the regulating-bank controller assembly (PID + bank + SCRAM)
  scram     -- the over-temperature / over-power safety supervisor

The PID drives the grey/black regulating bank to maneuver power within the
self-regulating envelope established in Phase 5. SCRAM is a separate supervisor
that overrides the controller. (Axial-offset control is deferred until the model
has axial/spatial neutronics -- point kinetics has no axial flux to regulate.)
"""
