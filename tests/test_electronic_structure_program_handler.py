#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the electronic structure program handler."""

import unittest
from unittest.mock import mock_open, patch

from milo_1_0_3 import containers, exceptions
from milo_1_0_3 import enumerations as enums
from milo_1_0_3.electronic_structure_program_handler import (
	Gaussian09Handler,
	Gaussian16Handler,
	GaussianHandler,
	get_program_handler,
)
from milo_1_0_3.program_state import ProgramState


class TestGetProgramHandler(unittest.TestCase):
	"""Test the get_program_handler function."""

	def setUp(self):
		"""Create a program state for testing."""
		self.program_state = ProgramState()

	def test_get_gaussian16_handler(self):
		"""Test getting Gaussian 16 handler."""
		self.program_state.program_id = enums.ProgramID.GAUSSIAN_16
		handler = get_program_handler(self.program_state)
		self.assertEqual(handler, Gaussian16Handler)

	def test_get_gaussian09_handler(self):
		"""Test getting Gaussian 09 handler."""
		self.program_state.program_id = enums.ProgramID.GAUSSIAN_09
		handler = get_program_handler(self.program_state)
		self.assertEqual(handler, Gaussian09Handler)

	def test_invalid_program_id(self):
		"""Test error raised for invalid program ID."""
		self.program_state.program_id = "invalid"
		with self.assertRaises(ValueError):
			get_program_handler(self.program_state)


class TestGaussianHandler(unittest.TestCase):
	"""Test the GaussianHandler class."""

	def setUp(self):
		"""Set up test data."""
		self.program_state = ProgramState()
		self.program_state.current_step = 0
		self.program_state.gaussian_header = "test header"
		self.program_state.charge = 0
		self.program_state.spin = 1
		self.program_state.processor_count = 4
		self.program_state.memory_amount = 8
		self.program_state.gaussian_footer = "test footer"

		# Add a structure with one atom
		positions = containers.Positions()
		positions.append(0.0, 0.0, 0.0, enums.DistanceUnits.ANGSTROM)
		self.program_state.structures.append(positions)

	@patch("os.system")
	def test_call_gaussian(self, mock_system):
		"""Test calling Gaussian."""
		route_section = "# force test"
		job_name = "test_job"

		with patch("builtins.open", mock_open()) as mock_file:
			log_file = GaussianHandler.call_gaussian(route_section, job_name, self.program_state)

		self.assertEqual(log_file, "test_job.log")
		mock_system.assert_called_once()
		mock_file.assert_called_once_with("test_job.com", "w")

	def test_is_log_good(self):
		"""Test log file validation."""
		# Test successful log
		good_log_content = "some output\nNormal termination\nmore output"
		with patch("builtins.open", mock_open(read_data=good_log_content)):
			self.assertTrue(GaussianHandler.is_log_good("test.log"))

		# Test failed log
		bad_log_content = "some output\nError occurred\nmore output"
		with patch("builtins.open", mock_open(read_data=bad_log_content)):
			self.assertFalse(GaussianHandler.is_log_good("test.log"))

	def test_parse_forces(self):
		"""Test parsing forces from log file."""
		log_content = """
		SCF Done: E(RHF) = -76.0 A.U.
		Forces (Hartrees/Bohr)
		1    1    0.0  0.1  0.2
		Cartesian Forces
		Normal termination
		"""

		with patch("builtins.open", mock_open(read_data=log_content)):
			GaussianHandler.parse_forces("test.log", self.program_state)

		self.assertEqual(len(self.program_state.forces), 1)
		self.assertEqual(len(self.program_state.energies), 1)

	def test_parse_forces_bad_log(self):
		"""Test error raised for bad log file."""
		with patch("builtins.open", mock_open(read_data="Error output")):
			with self.assertRaises(exceptions.ElectronicStructureProgramError):
				GaussianHandler.parse_forces("test.log", self.program_state)


if __name__ == "__main__":
	unittest.main()
