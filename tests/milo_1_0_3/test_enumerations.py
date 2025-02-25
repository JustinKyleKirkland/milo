#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the enumerations module."""

import unittest
from enum import Enum

from milo_1_0_3 import enumerations as enums


class TestEnumerations(unittest.TestCase):
	"""Test the enumerations module."""

	def test_all_enums_are_enum_class(self):
		"""Test that all enums are proper Enum classes."""
		for enum_class in enums.get_all_enums():
			self.assertTrue(issubclass(enum_class, Enum))

	def test_program_id_aliases(self):
		"""Test that program ID aliases are correct."""
		self.assertEqual(enums.ProgramID.GAUSSIAN_16, enums.ProgramID.G16)
		self.assertEqual(enums.ProgramID.GAUSSIAN_09, enums.ProgramID.G09)

	def test_enum_values_unique(self):
		"""Test that enum values within each enum are unique."""
		for enum_class in enums.get_all_enums():
			values = [member.value for member in enum_class]
			self.assertEqual(len(values), len(set(values)), f"Duplicate values found in {enum_class.__name__}")

	def test_enum_names_match_values(self):
		"""Test specific enum values that need to match exactly."""
		# Test a few critical enums where the exact values matter
		self.assertEqual(enums.ProgramID.GAUSSIAN_16.value, 1)
		self.assertEqual(enums.ProgramID.GAUSSIAN_09.value, 2)

	def test_enum_member_counts(self):
		"""Test that enums have the expected number of members."""
		expected_counts = {
			enums.AccelerationUnits: 1,
			enums.AngleUnits: 2,
			enums.DistanceUnits: 3,
			enums.EnergyBoost: 2,
			enums.EnergyUnits: 4,
			enums.ForceConstantUnits: 2,
			enums.ForceUnits: 4,
			enums.FrequencyUnits: 1,
			enums.GeometryDisplacement: 4,
			enums.MassUnits: 3,
			enums.OscillatorType: 2,
			enums.PhaseDirection: 3,
			enums.ProgramID: 2,  # Changed from 4 to 2 since aliases don't count as unique members
			enums.PropagationAlgorithm: 2,
			enums.RotationalEnergy: 2,
			enums.TimeUnits: 2,
			enums.VelocityUnits: 3,
		}

		for enum_class, expected_count in expected_counts.items():
			actual_count = len(list(enum_class))
			self.assertEqual(
				actual_count,
				expected_count,
				f"Expected {expected_count} members in {enum_class.__name__}, got {actual_count}",
			)


if __name__ == "__main__":
	unittest.main()
