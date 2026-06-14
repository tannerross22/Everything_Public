"""Reactivity feedback model (Phase 5).

The total reactivity driving the point kinetics is the sum of an externally
imposed term (control-rod worth, supplied by the simulator / Phase-6 controller)
and the temperature feedbacks:

    rho_total = rho_rods + alpha_fuel*(T_fuel - T_fuel_ref)
                         + alpha_mod *(T_mod  - T_mod_ref)

  * alpha_fuel -- the *Doppler* coefficient. Negative: as the fuel heats, U-238
    resonance absorption broadens and captures more neutrons. This is the prompt,
    always-present passive safety feedback (it acts the instant fuel temperature
    rises, before heat even reaches the coolant).
  * alpha_mod  -- the moderator temperature coefficient. Negative in a properly
    designed PWR: as the water heats it expands / becomes less dense, moderating
    less effectively.

Both coefficients are taken constant here (a linear model about a reference
state). The Doppler feedback is physically closer to alpha*(sqrt(T)-sqrt(T_ref));
a `doppler_sqrt` option provides that refinement.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class FeedbackCoefficients:
    """Temperature reactivity coefficients and their reference temperatures.

    Coefficients are in delta-k/k per kelvin (1 pcm = 1e-5). Reference
    temperatures default to None and are set by the simulator at initialization
    so that feedback is exactly zero at the chosen operating point.
    """
    alpha_fuel: float = -2.5e-5    # Doppler coefficient (~ -2.5 pcm/K)
    alpha_mod: float = -5.0e-5     # moderator coefficient (~ -5 pcm/K)
    T_fuel_ref: float | None = None
    T_mod_ref: float | None = None
    doppler_sqrt: bool = False

    def fuel_term(self, T_fuel: float) -> float:
        if self.doppler_sqrt:
            return self.alpha_fuel * (math.sqrt(T_fuel) - math.sqrt(self.T_fuel_ref))
        return self.alpha_fuel * (T_fuel - self.T_fuel_ref)

    def mod_term(self, T_mod: float) -> float:
        return self.alpha_mod * (T_mod - self.T_mod_ref)

    def feedback(self, T_fuel: float, T_mod: float) -> float:
        """Total temperature-feedback reactivity."""
        return self.fuel_term(T_fuel) + self.mod_term(T_mod)


def pwr_feedback() -> FeedbackCoefficients:
    return FeedbackCoefficients()
