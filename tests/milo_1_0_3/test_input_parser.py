#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the input parser module."""

import unittest

from milo_1_0_3 import exceptions
from milo_1_0_3.enumerations import EnergyBoost
from milo_1_0_3.input_parser import parse_input
from milo_1_0_3.program_state import ProgramState


class TestInputParser(unittest.TestCase):
	"""Test the input parser functionality."""

	def setUp(self):
		"""Set up test data."""
		self.program_state = ProgramState()
		self.basic_input = [
			"$job",
			"gaussian_header m06 6-31g(d,p)",
			"$end",
			"$molecule",
			"0 1",
			"H  0.0  0.0  0.0",
			"H  0.0  0.0  0.74",
			"$end",
		]

	def test_parse_basic_input(self):
		"""Test parsing of basic valid input."""
		parse_input(self.basic_input, self.program_state)

		self.assertEqual(self.program_state.gaussian_header, "m06 6-31g(d,p)")
		self.assertEqual(self.program_state.charge, 0)
		self.assertEqual(self.program_state.spin, 1)
		self.assertEqual(len(self.program_state.atoms), 2)
		self.assertEqual(self.program_state.atoms[0].symbol, "H")

	def test_missing_required_section(self):
		"""Test error raised for missing required section."""
		input_without_job = [
			"$molecule",
			"0 1",
			"H  0.0  0.0  0.0",
			"$end",
		]

		with self.assertRaises(exceptions.InputError) as context:
			parse_input(input_without_job, self.program_state)
		self.assertIn("Could not find $job section", str(context.exception))

	def test_duplicate_section(self):
		"""Test error raised for duplicate sections."""
		input_with_duplicate = self.basic_input + [
			"$molecule",
			"0 1",
			"H  0.0  0.0  0.0",
			"$end",
		]

		with self.assertRaises(exceptions.InputError) as context:
			parse_input(input_with_duplicate, self.program_state)
		self.assertIn("Multiple $molecule sections", str(context.exception))

	def test_mutually_exclusive_sections(self):
		"""Test error raised for mutually exclusive sections."""
		input_with_exclusive = self.basic_input + [
			"$velocities",
			"1.0 2.0 3.0",
			"$end",
			"$frequency_data",
			"1.0 2.0 3.0",
			"$end",
		]

		with self.assertRaises(exceptions.InputError) as context:
			parse_input(input_with_exclusive, self.program_state)
		self.assertIn("are mutually exclusive", str(context.exception))

	def test_invalid_input_type(self):
		"""Test error raised for invalid input type."""
		with self.assertRaises(exceptions.InputError):
			parse_input(42, self.program_state)

	def test_comment_handling(self):
		"""Test proper handling of comments."""
		input_with_comments = [
			"$job",
			"gaussian_header m06 6-31g(d,p)  # This is a comment",
			"$end",
			"$molecule  # Another comment",
			"0 1",
			"H  0.0  0.0  0.0  # Hydrogen atom",
			"$end",
		]

		parse_input(input_with_comments, self.program_state)
		self.assertEqual(self.program_state.gaussian_header, "m06 6-31g(d,p)")

	def test_job_section_parameters(self):
		"""Test parsing of various job section parameters."""
		input_with_params = [
			"$job",
			"gaussian_header m06 6-31g(d,p)",
			"temperature 350.0",
			"max_steps 1000",
			"step_size 0.5",
			"$end",
			"$molecule",
			"0 1",
			"H 0 0 0",
			"$end",
		]

		parse_input(input_with_params, self.program_state)

		self.assertEqual(self.program_state.temperature, 350.0)
		self.assertEqual(self.program_state.max_steps, 1000)
		self.assertEqual(self.program_state.step_size.as_femtosecond(), 0.5)

	def test_invalid_job_parameter(self):
		"""Test error raised for invalid job parameter."""
		input_with_invalid = self.basic_input.copy()
		input_with_invalid.insert(1, "invalid_param 123")

		with self.assertRaises(exceptions.InputError) as context:
			parse_input(input_with_invalid, self.program_state)
		self.assertIn("Invalid parameter", str(context.exception))

	def test_energy_boost_parameter(self):
		"""Test parsing of energy boost parameter."""
		# Test energy boost off
		input_off = self.basic_input.copy()
		input_off.insert(1, "energy_boost off")
		parse_input(input_off, self.program_state)
		self.assertEqual(self.program_state.energy_boost, EnergyBoost.OFF)

		# Test energy boost on with range
		input_on = self.basic_input.copy()
		input_on.insert(1, "energy_boost on 10.0 20.0")
		parse_input(input_on, self.program_state)
		self.assertEqual(self.program_state.energy_boost, EnergyBoost.ON)
		self.assertEqual(self.program_state.energy_boost_min, 10.0)
		self.assertEqual(self.program_state.energy_boost_max, 20.0)

		# Test invalid format
		input_invalid = self.basic_input.copy()
		input_invalid.insert(1, "energy_boost on")
		with self.assertRaises(exceptions.InputError):
			parse_input(input_invalid, self.program_state)

	def test_fixed_mode_direction_parameter(self):
		"""Test parsing of fixed mode direction parameter."""
		# Test valid mode direction
		input_valid = self.basic_input.copy()
		input_valid.insert(1, "fixed_mode_direction 1 1")
		parse_input(input_valid, self.program_state)
		self.assertEqual(self.program_state.fixed_mode_directions[1], 1)

		# Test invalid mode number
		input_invalid_mode = self.basic_input.copy()
		input_invalid_mode.insert(1, "fixed_mode_direction 0 1")
		with self.assertRaises(exceptions.InputError):
			parse_input(input_invalid_mode, self.program_state)

		# Test invalid direction
		input_invalid_dir = self.basic_input.copy()
		input_invalid_dir.insert(1, "fixed_mode_direction 1 2")
		with self.assertRaises(exceptions.InputError):
			parse_input(input_invalid_dir, self.program_state)

	def test_current_step_parameter(self):
		"""Test parsing of current step parameter."""
		# Test valid step
		input_valid = self.basic_input.copy()
		input_valid.insert(1, "current_step 42")
		parse_input(input_valid, self.program_state)
		self.assertEqual(self.program_state.current_step, 42)

		# Test invalid step
		input_invalid = self.basic_input.copy()
		input_invalid.insert(1, "current_step abc")
		with self.assertRaises(exceptions.InputError):
			parse_input(input_invalid, self.program_state)

	def test_gaussian_header_parameter(self):
		"""Test parsing of gaussian header parameter."""
		input_valid = self.basic_input.copy()
		header = "b3lyp/6-31g(d) opt freq"
		input_valid[1] = f"gaussian_header {header}"
		parse_input(input_valid, self.program_state)
		self.assertEqual(self.program_state.gaussian_header, header)

	def test_gaussian_footer_section(self):
		"""Test parsing of gaussian footer section."""
		input_with_footer = self.basic_input.copy()
		footer_content = ["$gaussian_footer", "Some footer content", "More content", "$end"]
		input_with_footer.extend(footer_content)
		parse_input(input_with_footer, self.program_state)
		self.assertIn("Some footer content", self.program_state.gaussian_footer)
		self.assertIn("More content", self.program_state.gaussian_footer)

	def test_frequency_data_section(self):
		"""Test parsing of frequency data section."""
		input_with_freq = self.basic_input.copy()
		freq_data = [
			"$frequency_data",
			# Format: frequency reduced_mass force_constant coordinates_for_each_atom
			"1000.0 1.0 0.5 0.1 0.2 0.3 0.4 0.5 0.6",  # Single force constant value
			"$end",
		]
		input_with_freq.extend(freq_data)
		parse_input(input_with_freq, self.program_state)

		self.assertEqual(self.program_state.frequencies.as_recip_cm(0), 1000.0)
		self.assertEqual(self.program_state.reduced_masses.as_amu(0), 1.0)
		# Force constant is converted to a tuple internally
		force_constant = self.program_state.force_constants.as_millidyne_per_angstrom(0)
		self.assertEqual(len(force_constant), 3)  # Should be a tuple of 3 values
		self.assertAlmostEqual(force_constant[0], 0.5)
		self.assertAlmostEqual(force_constant[1], 0.5)
		self.assertAlmostEqual(force_constant[2], 0.5)

		# Check displacements for both atoms
		displacements = self.program_state.mode_displacements[0].as_angstrom()
		self.assertEqual(displacements[0], (0.1, 0.2, 0.3))  # First H atom
		self.assertEqual(displacements[1], (0.4, 0.5, 0.6))  # Second H atom


if __name__ == "__main__":
	unittest.main()
