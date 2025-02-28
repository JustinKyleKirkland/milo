#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extended functionality for random number generation with reproducible seeds."""

import math
import os
import random
import time
from typing import Final, Optional

# Cache frequently used math functions and constants
_sin = math.sin
_sqrt = math.sqrt
_pi: Final[float] = math.pi
_two_pi: Final[float] = 2 * _pi
_urandom = os.urandom
_random = random.random


class RandomNumberGenerator:
	"""
	Extended functionality from Python's random module with reproducible seeds.

	This class ensures that all random calls throughout the program use the same
	seed, which can be output to allow reproducibility between different runs.

	Performance Notes:
		- Uses cached math functions for improved performance
		- Optimized gaussian generation with pre-calculated constants
		- Efficient seed generation using os.urandom when available
		- Direct access to random.random for uniform distribution
	"""

	__slots__ = ("seed", "rng", "_mu", "_sigma", "_random_func")

	def __init__(self, seed: Optional[int] = None) -> None:
		"""
		Initialize random number generator with optional seed.

		If seed is None or 0, generates a new seed using os.urandom() if available,
		otherwise falls back to using system time and process ID.

		Args:
		    seed: Integer seed for random number generation. If None or 0,
		         a new seed will be generated.
		"""
		self.seed: int = self._generate_seed() if seed is None else seed
		self.rng: random.Random = random.Random(self.seed)
		self._random_func = self.rng.random  # Cache method lookup

		# Pre-calculate constants for gaussian generation
		self._mu: Final[float] = 0.0
		self._sigma: Final[float] = 1 / _sqrt(2)  # σ = 1/√2 for quantum harmonic oscillator

	def _generate_seed(self) -> int:
		"""
		Generate a random seed efficiently.

		Returns:
		    int: A random seed generated either from os.urandom() or
		         from system time and process ID.
		"""
		try:
			# Use 4 bytes instead of 5 for better integer handling
			return int.from_bytes(_urandom(4), byteorder="big")
		except NotImplementedError:
			# Faster time-based fallback
			return hash(f"{os.getpid()}{time.time_ns()}")

	def reset_seed(self, seed: Optional[int] = None) -> None:
		"""
		Reset the random number generator with a new seed.

		Args:
		    seed: New seed value. If None, generates a new random seed.
		"""
		self.__init__(seed)

	def uniform(self) -> float:
		"""
		Generate a uniform random number between 0 and 1.

		Returns:
		    float: Random number from uniform distribution [0, 1).
		"""
		return self._random_func()

	def edge_weighted(self) -> float:
		"""
		Generate an edge-weighted random number between -1 and 1.

		Returns a value from a distribution that favors the edges (-1 and 1)
		over the center. Implemented using sin(2π * uniform).

		Returns:
		    float: Random number from edge-weighted distribution [-1, 1].
		"""
		return _sin(_two_pi * self._random_func())

	def gaussian(self) -> float:
		"""
		Generate a random number from a truncated normal distribution.

		Returns a value from a normal distribution with μ=0 and σ=1/√2,
		truncated to the interval [-1, 1]. The standard deviation matches
		the quantum harmonic oscillator's classical turning points.

		Performance Note:
			Uses pre-calculated constants and optimized rejection sampling.

		References:
		    - https://physicspages.com/pdf/Griffiths%20QM/Griffiths%20Problems%2002.15.pdf
		    - https://phys.libretexts.org/Bookshelves/University_Physics/Book%3A_University_Physics_(OpenStax)/Map%3A_University_Physics_III_-_Optics_and_Modern_Physics_(OpenStax)/07%3A_Quantum_Mechanics/7.06%3A_The_Quantum_Harmonic_Oscillator

		Returns:
		    float: Random number from truncated normal distribution [-1, 1].
		"""
		while True:
			value = self.rng.gauss(self._mu, self._sigma)
			if -1 <= value <= 1:
				return value

	def one_or_neg_one(self) -> int:
		"""
		Generate either 1 or -1 with equal probability.

		Performance Note:
			Uses direct comparison instead of branching.

		Returns:
		    int: Either 1 or -1 with 50/50 probability.
		"""
		return 2 * (self._random_func() >= 0.5) - 1
