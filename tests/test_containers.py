#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for containers.py."""

import unittest

from milo_1_0_3 import enumerations as enums
from milo_1_0_3 import scientific_constants as sc
from milo_1_0_3.containers import ForceConstants, Forces, Masses, Positions, Time, Velocities


class TestPositions(unittest.TestCase):
	"""Test cases for Positions class."""

	def setUp(self):
		"""Set up test fixtures."""
		self.positions = Positions()
		self.test_coords = (1.0, 2.0, 3.0)

	def test_append_angstrom(self):
		"""Test appending coordinates in angstroms."""
		self.positions.append(*self.test_coords, units=enums.DistanceUnits.ANGSTROM)
		self.assertEqual(self.positions.as_angstrom(0), self.test_coords)

	def test_append_bohr(self):
		"""Test appending coordinates in bohr."""
		self.positions.append(*self.test_coords, units=enums.DistanceUnits.BOHR)
		expected = tuple(x * sc.BOHR_TO_ANGSTROM for x in self.test_coords)
		self.assertTupleAlmostEqual(self.positions.as_angstrom(0), expected)

	def test_append_meter(self):
		"""Test appending coordinates in meters."""
		self.positions.append(*self.test_coords, units=enums.DistanceUnits.METER)
		expected = tuple(x * 1e10 for x in self.test_coords)  # meter to angstrom
		self.assertTupleAlmostEqual(self.positions.as_angstrom(0), expected)

	def test_alter_position(self):
		"""Test altering existing position."""
		self.positions.append(1.0, 1.0, 1.0, units=enums.DistanceUnits.ANGSTROM)
		self.positions.alter_position(0, *self.test_coords, enums.DistanceUnits.ANGSTROM)
		self.assertEqual(self.positions.as_angstrom(0), self.test_coords)

	def test_invalid_units(self):
		"""Test handling of invalid units."""
		with self.assertRaises(ValueError):
			self.positions.append(1.0, 1.0, 1.0, "invalid")

	def assertTupleAlmostEqual(self, first, second, places=7):
		"""Assert that all elements in two tuples are almost equal."""
		self.assertEqual(len(first), len(second))
		for a, b in zip(first, second):
			self.assertAlmostEqual(a, b, places=places)


class TestVelocities(unittest.TestCase):
	"""Test cases for Velocities class."""

	def setUp(self):
		"""Set up test fixtures."""
		self.velocities = Velocities()
		self.test_vel = (1.0, 2.0, 3.0)

	def test_append_meter_per_sec(self):
		"""Test appending velocities in m/s."""
		self.velocities.append(*self.test_vel, units=enums.VelocityUnits.METER_PER_SEC)
		self.assertEqual(self.velocities.as_meter_per_sec(0), self.test_vel)

	def test_append_angstrom_per_fs(self):
		"""Test appending velocities in Å/fs."""
		self.velocities.append(*self.test_vel, units=enums.VelocityUnits.ANGSTROM_PER_FS)
		expected = tuple(x * 1e5 for x in self.test_vel)  # Å/fs to m/s
		self.assertTupleAlmostEqual(self.velocities.as_meter_per_sec(0), expected)

	def test_from_acceleration(self):
		"""Test creating velocities from acceleration."""
		from milo_1_0_3.containers import Accelerations

		accel = Accelerations()
		accel.append(1.0, 2.0, 3.0, enums.AccelerationUnits.METER_PER_SEC_SQRD)
		time = Time(2.0, enums.TimeUnits.SECOND)

		vel = Velocities.from_acceleration(accel, time)
		expected = (2.0, 4.0, 6.0)  # v = a*t
		self.assertTupleAlmostEqual(vel.as_meter_per_sec(0), expected)

	def test_arithmetic_operations(self):
		"""Test arithmetic operations between velocities."""
		v1 = Velocities()
		v2 = Velocities()
		v1.append(1.0, 2.0, 3.0, enums.VelocityUnits.METER_PER_SEC)
		v2.append(2.0, 3.0, 4.0, enums.VelocityUnits.METER_PER_SEC)

		# Test addition
		v_sum = v1 + v2
		self.assertTupleAlmostEqual(v_sum.as_meter_per_sec(0), (3.0, 5.0, 7.0))

		# Test subtraction
		v_diff = v2 - v1
		self.assertTupleAlmostEqual(v_diff.as_meter_per_sec(0), (1.0, 1.0, 1.0))

		# Test multiplication
		v_mult = v1 * 2
		self.assertTupleAlmostEqual(v_mult.as_meter_per_sec(0), (2.0, 4.0, 6.0))

	def assertTupleAlmostEqual(self, first, second, places=7):
		"""Assert that all elements in two tuples are almost equal."""
		self.assertEqual(len(first), len(second))
		for a, b in zip(first, second):
			self.assertAlmostEqual(a, b, places=places)


class TestForces(unittest.TestCase):
	"""Test cases for Forces class."""

	def setUp(self):
		"""Set up test fixtures."""
		self.forces = Forces()
		self.test_force = (1.0, 2.0, 3.0)

	def test_append_newton(self):
		"""Test appending forces in newtons."""
		self.forces.append(*self.test_force, units=enums.ForceUnits.NEWTON)
		self.assertEqual(self.forces.as_newton(0), self.test_force)

	def test_append_millidyne(self):
		"""Test appending forces in millidynes."""
		self.forces.append(*self.test_force, units=enums.ForceUnits.MILLIDYNE)
		expected = tuple(x * 1e-8 for x in self.test_force)  # millidyne to newton
		self.assertTupleAlmostEqual(self.forces.as_newton(0), expected)

	def test_arithmetic_operations(self):
		"""Test arithmetic operations between forces."""
		f1 = Forces()
		f2 = Forces()
		f1.append(1.0, 2.0, 3.0, enums.ForceUnits.NEWTON)
		f2.append(2.0, 3.0, 4.0, enums.ForceUnits.NEWTON)

		# Test addition
		f_sum = f1 + f2
		self.assertTupleAlmostEqual(f_sum.as_newton(0), (3.0, 5.0, 7.0))

		# Test multiplication
		f_mult = f1 * 2
		self.assertTupleAlmostEqual(f_mult.as_newton(0), (2.0, 4.0, 6.0))

	def assertTupleAlmostEqual(self, first, second, places=7):
		"""Assert that all elements in two tuples are almost equal."""
		self.assertEqual(len(first), len(second))
		for a, b in zip(first, second):
			self.assertAlmostEqual(a, b, places=places)


class TestForceConstants(unittest.TestCase):
	"""Test cases for ForceConstants class."""

	def setUp(self):
		"""Set up test fixtures."""
		self.force_constants = ForceConstants()
		self.test_fc = (1.0, 2.0, 3.0)

	def test_append_newton_per_meter(self):
		"""Test appending force constants in N/m."""
		self.force_constants.append(self.test_fc, units=enums.ForceConstantUnits.NEWTON_PER_METER)
		self.assertEqual(self.force_constants.as_newton_per_meter(0), self.test_fc)

	def test_append_millidyne_per_angstrom(self):
		"""Test appending force constants in mdyne/Å."""
		self.force_constants.append(self.test_fc, units=enums.ForceConstantUnits.MILLIDYNE_PER_ANGSTROM)
		expected = tuple(x * 0.1 for x in self.test_fc)  # mdyne/Å to N/m
		self.assertTupleAlmostEqual(self.force_constants.as_newton_per_meter(0), expected)

	def assertTupleAlmostEqual(self, first, second, places=7):
		"""Assert that all elements in two tuples are almost equal."""
		self.assertEqual(len(first), len(second))
		for a, b in zip(first, second):
			self.assertAlmostEqual(a, b, places=places)


class TestMasses(unittest.TestCase):
	"""Test cases for Masses class."""

	def setUp(self):
		"""Set up test fixtures."""
		self.masses = Masses()
		self.test_mass = 12.0

	def test_append_amu(self):
		"""Test appending mass in atomic mass units."""
		self.masses.append(self.test_mass, units=enums.MassUnits.AMU)
		self.assertEqual(self.masses.as_amu(0), self.test_mass)

	def test_append_kilogram(self):
		"""Test appending mass in kilograms."""
		self.masses.append(self.test_mass, units=enums.MassUnits.KILOGRAM)
		expected = self.test_mass * sc.KG_TO_AMU
		self.assertAlmostEqual(self.masses.as_amu(0), expected)

	def test_append_gram(self):
		"""Test appending mass in grams."""
		self.masses.append(self.test_mass, units=enums.MassUnits.GRAM)
		expected = self.test_mass * sc.TO_KILO * sc.KG_TO_AMU
		self.assertAlmostEqual(self.masses.as_amu(0), expected, delta=1e15)


class TestTime(unittest.TestCase):
	"""Test cases for Time class."""

	def setUp(self):
		"""Set up test fixtures."""
		self.test_time = 1.0

	def test_init_second(self):
		"""Test initialization with seconds."""
		time = Time(self.test_time, unit=enums.TimeUnits.SECOND)
		self.assertEqual(time.as_second(), self.test_time)

	def test_init_femtosecond(self):
		"""Test initialization with femtoseconds."""
		time = Time(self.test_time, unit=enums.TimeUnits.FEMTOSECOND)
		expected = self.test_time * sc.FEMTOSECOND_TO_SECOND
		self.assertAlmostEqual(time.as_second(), expected)

	def test_invalid_units(self):
		"""Test handling of invalid units."""
		with self.assertRaises(ValueError):
			Time(1.0, unit="invalid")

	def test_conversions(self):
		"""Test time unit conversions."""
		time = Time(1.0, unit=enums.TimeUnits.SECOND)
		self.assertEqual(time.as_second(), 1.0)
		self.assertEqual(time.as_femtosecond(), 1e15)


if __name__ == "__main__":
	unittest.main()
