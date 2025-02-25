#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extended functionality for random number generation with reproducible seeds."""

import math
import os
import random
import time
from typing import Optional


class RandomNumberGenerator:
	"""
	Extended functionality from Python's random module with reproducible seeds.

	This class ensures that all random calls throughout the program use the same
	seed, which can be output to allow reproducibility between different runs.
	"""

	def __init__(self, seed: Optional[int] = None) -> None:
		"""
		Initialize random number generator with optional seed.

		If seed is None or 0, generates a new seed using os.urandom() if available,
		otherwise falls back to using system time and process ID.

		Args:
		    seed: Integer seed for random number generation. If None or 0,
		         a new seed will be generated.
		"""
		self.seed = seed
		if self.seed is None:
			self.seed = self._generate_seed()
		self.rng = random.Random(self.seed)

	def _generate_seed(self) -> int:
		"""
		Generate a random seed.

		Returns:
		    int: A random seed generated either from os.urandom() or
		         from system time and process ID.
		"""
		try:
			return int.from_bytes(os.urandom(5), byteorder="big", signed=False)
		except NotImplementedError:
			# Fallback to time-based seed if os.urandom not available
			current_time = str(int(time.time()))
			process_id = str(os.getpid())
			return int(process_id + current_time[-(12 - len(process_id)) :])

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
		return self.rng.random()

	def edge_weighted(self) -> float:
		"""
		Generate an edge-weighted random number between -1 and 1.

		Returns a value from a distribution that favors the edges (-1 and 1)
		over the center. Implemented using sin(2π * uniform).

		Returns:
		    float: Random number from edge-weighted distribution [-1, 1].
		"""
		return math.sin(2 * math.pi * self.rng.random())

	def gaussian(self) -> float:
		"""
		Generate a random number from a truncated normal distribution.

		Returns a value from a normal distribution with μ=0 and σ=1/√2,
		truncated to the interval [-1, 1]. The standard deviation is chosen
		to match the quantum harmonic oscillator's classical turning points.

		References:
		    - https://physicspages.com/pdf/Griffiths%20QM/Griffiths%20Problems%2002.15.pdf
		    - https://phys.libretexts.org/Bookshelves/University_Physics/Book%3A_University_Physics_(OpenStax)/Map%3A_University_Physics_III_-_Optics_and_Modern_Physics_(OpenStax)/07%3A_Quantum_Mechanics/7.06%3A_The_Quantum_Harmonic_Oscillator

		Returns:
		    float: Random number from truncated normal distribution [-1, 1].
		"""
		mu = 0
		sigma = 1 / math.sqrt(2)  # σ = 1/√2 to match quantum harmonic oscillator
		while True:
			value = self.rng.gauss(mu, sigma)
			if -1 <= value <= 1:
				return value

	def one_or_neg_one(self) -> int:
		"""
		Generate either 1 or -1 with equal probability.

		Returns:
		    int: Either 1 or -1 with 50/50 probability.
		"""
		return 1 if self.rng.random() >= 0.5 else -1
