#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for the RandomNumberGenerator class."""

import math
import statistics
import unittest

from milo_1_0_3.random_number_generator import RandomNumberGenerator


class TestRandomNumberGenerator(unittest.TestCase):
	"""Test suite for RandomNumberGenerator class."""

	def setUp(self):
		"""Set up test fixtures."""
		self.fixed_seed = 12345
		self.rng = RandomNumberGenerator(seed=self.fixed_seed)
		self.sample_size = 10000

	def test_seed_reproducibility(self):
		"""Test that the same seed produces the same sequence."""
		rng1 = RandomNumberGenerator(seed=self.fixed_seed)
		rng2 = RandomNumberGenerator(seed=self.fixed_seed)

		# Generate sequences
		seq1 = [rng1.uniform() for _ in range(100)]
		seq2 = [rng2.uniform() for _ in range(100)]

		self.assertEqual(seq1, seq2)

	def test_uniform_distribution(self):
		"""Test uniform distribution properties."""
		samples = [self.rng.uniform() for _ in range(self.sample_size)]

		# Test range
		self.assertTrue(all(0 <= x < 1 for x in samples))

		# Test mean (should be close to 0.5)
		mean = statistics.mean(samples)
		self.assertAlmostEqual(mean, 0.5, delta=0.05)

	def test_edge_weighted_distribution(self):
		"""Test edge-weighted distribution properties."""
		samples = [self.rng.edge_weighted() for _ in range(self.sample_size)]

		# Test range
		self.assertTrue(all(-1 <= x <= 1 for x in samples))

		# Test mean (should be close to 0)
		mean = statistics.mean(samples)
		self.assertAlmostEqual(mean, 0, delta=0.05)

		# Test that distribution favors edges
		# Count samples near edges vs center
		edge_count = sum(1 for x in samples if abs(x) > 0.8)
		center_count = sum(1 for x in samples if abs(x) < 0.2)
		self.assertGreater(edge_count, center_count)

	def test_gaussian_distribution(self):
		"""Test truncated gaussian distribution properties."""
		samples = [self.rng.gaussian() for _ in range(self.sample_size)]

		# Test range
		self.assertTrue(all(-1 <= x <= 1 for x in samples))

		# Test mean (should be close to 0)
		mean = statistics.mean(samples)
		self.assertAlmostEqual(mean, 0, delta=0.05)

		# Test standard deviation (should be close to 1/√2 but slightly less due to truncation)
		std_dev = statistics.stdev(samples)
		self.assertLess(std_dev, 1 / math.sqrt(2))
		self.assertGreater(std_dev, 0.5)

	def test_one_or_neg_one(self):
		"""Test one_or_neg_one distribution."""
		samples = [self.rng.one_or_neg_one() for _ in range(self.sample_size)]

		# Test that only returns 1 or -1
		self.assertTrue(all(x in {-1, 1} for x in samples))

		# Test roughly equal distribution
		ones = sum(1 for x in samples if x == 1)
		neg_ones = sum(1 for x in samples if x == -1)
		ratio = ones / neg_ones
		self.assertAlmostEqual(ratio, 1.0, delta=0.1)

	def test_reset_seed(self):
		"""Test reset_seed functionality."""
		# Generate sequence
		seq1 = [self.rng.uniform() for _ in range(100)]

		# Reset seed and generate new sequence
		self.rng.reset_seed(self.fixed_seed)
		seq2 = [self.rng.uniform() for _ in range(100)]

		self.assertEqual(seq1, seq2)

	def test_different_seeds(self):
		"""Test that different seeds produce different sequences."""
		rng1 = RandomNumberGenerator(seed=self.fixed_seed)
		rng2 = RandomNumberGenerator(seed=self.fixed_seed + 1)

		seq1 = [rng1.uniform() for _ in range(100)]
		seq2 = [rng2.uniform() for _ in range(100)]

		self.assertNotEqual(seq1, seq2)


if __name__ == "__main__":
	unittest.main()
