#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the ProgramState class."""

import unittest

from milo_1_0_3 import enumerations as enums
from milo_1_0_3.program_state import ProgramState


class TestProgramState(unittest.TestCase):
	"""Test the ProgramState class."""

	def setUp(self):
		"""Create a program state object for testing."""
		self.state = ProgramState()

	def test_initial_values(self):
		"""Test that the initial values are set correctly."""
		# Basic job configuration
		self.assertIsNone(self.state.job_name)
		self.assertIsNone(self.state.number_atoms)
		self.assertIsNone(self.state.spin)
		self.assertIsNone(self.state.charge)
		self.assertEqual(self.state.atoms, [])
		self.assertEqual(self.state.temperature, 298.15)

		# Simulation control
		self.assertEqual(self.state.current_step, 0)
		self.assertEqual(self.state.step_size.as_femtosecond(), 1.00)
		self.assertIsNone(self.state.max_steps)

		# Structure data
		self.assertEqual(len(self.state.structures), 0)
		self.assertEqual(len(self.state.velocities), 0)
		self.assertEqual(len(self.state.forces), 0)
		self.assertEqual(len(self.state.accelerations), 0)
		self.assertEqual(len(self.state.energies), 0)

		# Propagation configuration
		self.assertEqual(self.state.propagation_algorithm, enums.PropagationAlgorithm.VERLET)
		self.assertEqual(self.state.oscillator_type, enums.OscillatorType.QUASICLASSICAL)
		self.assertEqual(self.state.add_rotational_energy, enums.RotationalEnergy.NO)
		self.assertEqual(self.state.geometry_displacement_type, enums.GeometryDisplacement.NONE)
		self.assertEqual(self.state.phase_direction, enums.PhaseDirection.RANDOM)
		self.assertIsNone(self.state.phase)

		# Mode configuration
		self.assertEqual(self.state.fixed_mode_directions, {})
		self.assertEqual(self.state.fixed_vibrational_quanta, {})

		# Energy boost configuration
		self.assertEqual(self.state.energy_boost, enums.EnergyBoost.OFF)
		self.assertIsNone(self.state.energy_boost_min)
		self.assertIsNone(self.state.energy_boost_max)

		# Program configuration
		self.assertEqual(self.state.program_id, enums.ProgramID.GAUSSIAN_16)
		self.assertIsNone(self.state.gaussian_header)
		self.assertIsNone(self.state.gaussian_footer)
		self.assertIsNone(self.state.processor_count)
		self.assertIsNone(self.state.memory_amount)
		self.assertTrue(self.state.output_xyz_file)


if __name__ == "__main__":
	unittest.main()
