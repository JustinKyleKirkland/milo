#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the force propagation handler module."""

import unittest
from unittest.mock import MagicMock, Mock, patch

import numpy as np

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
		# Configure step_size mock to handle comparisons
		step_size_mock = MagicMock()
		step_size_mock.__le__ = lambda x, y: False  # Make step_size > 0
		self.program_state.step_size = step_size_mock

		# Clear caches before each test
		ForcePropagationHandler._acceleration_cache.clear()
		ForcePropagationHandler._velocity_cache.clear()

	def test_calculate_acceleration_caching(self):
		"""Test acceleration calculation with caching."""
		mock_acceleration = MagicMock()
		mock_numpy_array = np.array([[1.0, 2.0, 3.0]])

		# First call - should calculate and cache
		with patch(
			"milo_1_0_3.containers.Accelerations.from_forces", return_value=mock_acceleration
		) as mock_from_forces:
			with patch.object(mock_acceleration, "to_numpy", return_value=mock_numpy_array):
				ForcePropagationHandler._calculate_acceleration(self.program_state)
				mock_from_forces.assert_called_once()

		# Second call - should use cache
		with patch("milo_1_0_3.containers.Accelerations.from_forces") as mock_from_forces:
			ForcePropagationHandler._calculate_acceleration(self.program_state)
			mock_from_forces.assert_not_called()

	def test_calculate_velocity_caching(self):
		"""Test velocity calculation with caching."""
		mock_velocity = MagicMock()
		mock_numpy_array = np.array([[1.0, 2.0, 3.0]])

		# Configure mocks
		self.program_state.velocities.__getitem__.return_value = mock_velocity
		self.program_state.accelerations.__getitem__.side_effect = lambda x: MagicMock()

		# First call - should calculate and cache
		with patch("milo_1_0_3.containers.Velocities.from_acceleration", return_value=mock_velocity) as mock_from_accel:
			with patch.object(mock_velocity, "to_numpy", return_value=mock_numpy_array):
				ForcePropagationHandler._calculate_velocity(self.program_state)
				mock_from_accel.assert_called_once()

		# Second call - should use cache
		with patch("milo_1_0_3.containers.Velocities.from_acceleration") as mock_from_accel:
			ForcePropagationHandler._calculate_velocity(self.program_state)
			mock_from_accel.assert_not_called()

	def test_cache_cleanup(self):
		"""Test cache cleanup when size exceeds limit."""
		# Create many different program states to fill cache
		for i in range(1100):
			program_state = Mock()
			program_state.forces = [MagicMock()]
			program_state.atoms = []
			program_state.accelerations = MagicMock()

			mock_acceleration = MagicMock()
			mock_numpy_array = np.array([[float(i), 2.0, 3.0]])

			with patch("milo_1_0_3.containers.Accelerations.from_forces", return_value=mock_acceleration):
				with patch.object(mock_acceleration, "to_numpy", return_value=mock_numpy_array):
					ForcePropagationHandler._calculate_acceleration(program_state)

		# Cache should have been cleared at least once
		self.assertLess(len(ForcePropagationHandler._acceleration_cache), 1100)

	def test_validate_program_state(self):
		"""Test program state validation."""
		# Test missing forces
		program_state = Mock()
		program_state.forces = []
		program_state.atoms = [Mock()]
		program_state.step_size = 1.0
		with self.assertRaises(ValueError) as cm:
			ForcePropagationHandler._validate_program_state(program_state)
		self.assertEqual(str(cm.exception), "No forces available in program state")

		# Test missing atoms
		program_state.forces = [Mock()]
		program_state.atoms = []
		with self.assertRaises(ValueError) as cm:
			ForcePropagationHandler._validate_program_state(program_state)
		self.assertEqual(str(cm.exception), "No atoms defined in program state")

		# Test invalid step size
		program_state.atoms = [Mock()]
		program_state.step_size = 0
		with self.assertRaises(ValueError) as cm:
			ForcePropagationHandler._validate_program_state(program_state)
		self.assertEqual(str(cm.exception), "Step size must be positive")


class TestVerlet(unittest.TestCase):
	"""Test the Verlet propagation handler."""

	def setUp(self):
		"""Set up test data."""
		self.program_state = Mock()
		self.program_state.forces = [MagicMock()]
		self.program_state.structures = MagicMock()
		self.program_state.velocities = [MagicMock()]
		self.program_state.accelerations = [MagicMock()]
		# Configure step_size mock to handle comparisons
		step_size_mock = MagicMock()
		step_size_mock.__le__ = lambda x, y: False  # Make step_size > 0
		self.program_state.step_size = step_size_mock
		self.program_state.atoms = [Mock()]

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
		"""Test first step calculation with validation."""
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
		# Configure step_size mock to handle comparisons
		step_size_mock = MagicMock()
		step_size_mock.__le__ = lambda x, y: False  # Make step_size > 0
		self.program_state.step_size = step_size_mock
		self.program_state.atoms = [Mock()]

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
		"""Test step calculation with validation."""
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
