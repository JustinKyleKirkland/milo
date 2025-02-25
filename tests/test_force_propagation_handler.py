#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the force propagation handler module."""

import unittest
from unittest.mock import MagicMock, Mock, patch

from milo_1_0_3 import enumerations as enums
from milo_1_0_3.force_propagation_handler import (
	ForcePropagationHandler,
	VelocityVerlet,
	Verlet,
	get_propagation_handler,
)
from milo_1_0_3.program_state import ProgramState


class TestGetPropagationHandler(unittest.TestCase):
	"""Test the get_propagation_handler function."""

	def setUp(self):
		"""Create a program state for testing."""
		self.program_state = ProgramState()

	def test_get_verlet_handler(self):
		"""Test getting Verlet handler."""
		self.program_state.propagation_algorithm = enums.PropagationAlgorithm.VERLET
		handler = get_propagation_handler(self.program_state)
		self.assertEqual(handler, Verlet)

	def test_get_velocity_verlet_handler(self):
		"""Test getting Velocity Verlet handler."""
		self.program_state.propagation_algorithm = enums.PropagationAlgorithm.VELOCITY_VERLET
		handler = get_propagation_handler(self.program_state)
		self.assertEqual(handler, VelocityVerlet)

	def test_invalid_algorithm(self):
		"""Test error raised for invalid algorithm."""
		self.program_state.propagation_algorithm = "invalid"
		with self.assertRaises(ValueError):
			get_propagation_handler(self.program_state)


class TestForcePropagationHandler(unittest.TestCase):
	"""Test the base ForcePropagationHandler class."""

	def setUp(self):
		"""Set up test data."""
		self.program_state = Mock()
		self.program_state.forces = [MagicMock()]
		self.program_state.atoms = []
		self.program_state.accelerations = MagicMock()
		self.program_state.velocities = MagicMock()
		self.program_state.step_size = MagicMock()

	def test_calculate_acceleration(self):
		"""Test acceleration calculation."""
		mock_acceleration = MagicMock()
		with patch("milo_1_0_3.containers.Accelerations.from_forces", return_value=mock_acceleration):
			ForcePropagationHandler._calculate_acceleration(self.program_state)

		self.program_state.accelerations.append.assert_called_with(mock_acceleration)

	def test_calculate_velocity(self):
		"""Test velocity calculation."""
		# Create mock objects
		mock_velocity = MagicMock()
		mock_velocity_result = MagicMock()
		mock_from_accel = MagicMock()
		mock_accel_sum = MagicMock()
		mock_scaled_velocity = MagicMock()
		mock_accel1 = MagicMock()
		mock_accel2 = MagicMock()

		# Configure mocks for the calculation chain
		self.program_state.velocities.__getitem__.return_value = mock_velocity
		self.program_state.accelerations.__getitem__.side_effect = lambda x: {-1: mock_accel1, -2: mock_accel2}[x]
		mock_accel1.__add__.return_value = mock_accel_sum
		mock_from_accel.__mul__.return_value = mock_scaled_velocity
		mock_velocity.__add__.return_value = mock_velocity_result

		# Configure the from_acceleration mock
		with patch("milo_1_0_3.containers.Velocities.from_acceleration", return_value=mock_from_accel):
			ForcePropagationHandler._calculate_velocity(self.program_state)

		# Verify the result was appended
		self.program_state.velocities.append.assert_called_once_with(mock_velocity_result)


class TestVerlet(unittest.TestCase):
	"""Test the Verlet propagation handler."""

	def setUp(self):
		"""Set up test data."""
		self.program_state = Mock()
		self.program_state.forces = [MagicMock()]
		self.program_state.structures = MagicMock()
		self.program_state.velocities = [MagicMock()]
		self.program_state.accelerations = [MagicMock()]
		self.program_state.step_size = MagicMock()
		self.program_state.atoms = []

		# Configure mock structures
		mock_structure = MagicMock()
		mock_structure.__add__ = MagicMock(return_value=mock_structure)
		mock_structure.__mul__ = MagicMock(return_value=mock_structure)
		mock_structure.__sub__ = MagicMock(return_value=mock_structure)
		self.program_state.structures.__len__ = MagicMock(return_value=1)
		self.program_state.structures.__getitem__ = MagicMock(return_value=mock_structure)

	@patch("milo_1_0_3.containers.Positions.from_velocity")
	@patch("milo_1_0_3.containers.Positions.from_acceleration")
	@patch("milo_1_0_3.containers.Accelerations.from_forces")
	def test_first_step(self, mock_from_forces, mock_from_accel, mock_from_vel):
		"""Test first step calculation."""
		mock_structure = MagicMock()
		mock_acceleration = MagicMock()
		mock_from_forces.return_value = mock_acceleration
		mock_from_vel.return_value = mock_structure
		mock_from_accel.return_value = mock_structure
		mock_structure.__add__ = MagicMock(return_value=mock_structure)
		mock_structure.__mul__ = MagicMock(return_value=mock_structure)

		Verlet.run_next_step(self.program_state)

		self.program_state.structures.append.assert_called()


class TestVelocityVerlet(unittest.TestCase):
	"""Test the Velocity Verlet propagation handler."""

	def setUp(self):
		"""Set up test data."""
		self.program_state = Mock()
		self.program_state.forces = [MagicMock()]
		self.program_state.structures = MagicMock()
		self.program_state.velocities = [MagicMock()]
		self.program_state.accelerations = [MagicMock()]
		self.program_state.step_size = MagicMock()
		self.program_state.atoms = []

		# Configure mock structure
		mock_structure = MagicMock()
		mock_structure.__add__ = MagicMock(return_value=mock_structure)
		mock_structure.__mul__ = MagicMock(return_value=mock_structure)
		self.program_state.structures.__len__ = MagicMock(return_value=1)
		self.program_state.structures.__getitem__ = MagicMock(return_value=mock_structure)

	@patch("milo_1_0_3.containers.Positions.from_velocity")
	@patch("milo_1_0_3.containers.Positions.from_acceleration")
	@patch("milo_1_0_3.containers.Accelerations.from_forces")
	def test_step_calculation(self, mock_from_forces, mock_from_accel, mock_from_vel):
		"""Test step calculation."""
		mock_structure = MagicMock()
		mock_acceleration = MagicMock()
		mock_from_forces.return_value = mock_acceleration
		mock_from_vel.return_value = mock_structure
		mock_from_accel.return_value = mock_structure
		mock_structure.__add__ = MagicMock(return_value=mock_structure)
		mock_structure.__mul__ = MagicMock(return_value=mock_structure)

		VelocityVerlet.run_next_step(self.program_state)

		self.program_state.structures.append.assert_called()


if __name__ == "__main__":
	unittest.main()
