#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for parse_frequencies.py."""

import io
import unittest
from unittest.mock import patch

from milo_1_0_3 import exceptions, program_state
from milo_1_0_3.tools import parse_frequencies


class TestParseFrequencies(unittest.TestCase):
	"""Test cases for parse_frequencies.py functions."""

	def setUp(self):
		"""Set up test fixtures."""
		self.program_state = program_state.ProgramState()

	def test_parse_gaussian_header_valid(self):
		"""Test parsing valid Gaussian header."""
		test_input = """
 ******************************************
 Gaussian 16:  ES64L-G16RevA.03 25-Dec-2016
                 4-Jan-2023
 ******************************************
 %chk=test.chk
 ---------------
 # opt freq=(hpmodes) b3lyp/6-31g(d)
 ---------------
"""
		with io.StringIO(test_input) as f:
			parse_frequencies.parse_gaussian_header(f, self.program_state)
			self.assertEqual(self.program_state.gaussian_header, "b3lyp/6-31g(d)")

	def test_parse_gaussian_header_no_hpmodes(self):
		"""Test parsing header without hpmodes raises error."""
		test_input = """
 ******************************************
 # opt freq b3lyp/6-31g(d)
 ---------------
"""
		with io.StringIO(test_input) as f:
			with self.assertRaises(exceptions.InputError):
				parse_frequencies.parse_gaussian_header(f, self.program_state)

	def test_parse_charge_spin_valid(self):
		"""Test parsing valid charge and spin."""
		test_input = """
 Symbolic Z-matrix:
 Charge =  0 Multiplicity = 1
"""
		with io.StringIO(test_input) as f:
			parse_frequencies.parse_gaussian_charge_spin(f, self.program_state)
			self.assertEqual(self.program_state.charge, 0)
			self.assertEqual(self.program_state.spin, 1)

	def test_print_section(self):
		"""Test section printing format."""
		output = io.StringIO()
		parse_frequencies.print_section(output, "test", "content")
		expected = "$test\ncontent\n$end\n\n"
		self.assertEqual(output.getvalue(), expected)

	@patch("milo_1_0_3.tools.parse_frequencies.datetime")
	def test_print_output_comment(self, mock_datetime):
		"""Test comment section printing."""
		mock_datetime.now.return_value.strftime.return_value = "01-Jan-2023 at 00:00:00"

		input_file = io.StringIO()
		input_file.name = "test.log"
		output = io.StringIO()

		parse_frequencies.print_output_comment(input_file, output)
		expected = "$comment\n    Frequency and molecule data parsed from test.log 01-Jan-2023 at 00:00:00\n$end\n\n"
		self.assertEqual(output.getvalue(), expected)


if __name__ == "__main__":
	unittest.main()
