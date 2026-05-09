# Adapter to provide pnoise1 functionality using opensimplex
# This avoids the need for C++ compiler for the noise package

try:
    from noise import pnoise1
except ImportError:
    from opensimplex import OpenSimplex
    import numpy as np

    _opensimplex_instances = {}

    def pnoise1(x, octaves=1, persistence=0.5, lacunarity=2.0, repeatx=None, base=None, noise_seed=None):
        """
        Perlin-like noise using OpenSimplex as fallback.
        Provides compatibility with the noise library's pnoise1 function.

        Args:
            x: Input value
            octaves: Number of octaves (fractal iterations)
            persistence: How much each octave contributes to the result
            lacunarity: Frequency multiplier for each octave
            repeatx: Repeat period (optional, ignored in opensimplex)
            base: Base amplitude (optional)
            noise_seed: Random seed for reproducibility

        Returns:
            Noise value roughly in range [-1, 1]
        """

        # Create or retrieve noise generator with seed
        seed = noise_seed if noise_seed is not None else 0
        if seed not in _opensimplex_instances:
            _opensimplex_instances[seed] = OpenSimplex(seed=int(seed))

        simplex = _opensimplex_instances[seed]

        # Generate fractal Brownian motion (fBm) using multiple octaves
        value = 0.0
        amplitude = base if base is not None else 1.0
        frequency = 1.0
        max_value = 0.0

        for _ in range(octaves):
            # Get OpenSimplex noise value (returns -1 to 1)
            octave_value = simplex.noise2(x * frequency, x * frequency)
            value += octave_value * amplitude
            max_value += amplitude

            amplitude *= persistence
            frequency *= lacunarity

        # Normalize to roughly -1 to 1 range
        if max_value > 0:
            value /= max_value

        return value
