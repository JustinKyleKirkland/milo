#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for parse_xyz.py."""

import io
import os
import tempfile
import unittest

from milo_1_0_3.tools import parse_xyz
from milo_1_0_3.tools.parse_xyz import CoordinateBlock


class TestParseXYZ(unittest.TestCase):
	"""Test cases for parse_xyz.py functions."""

	def setUp(self):
		"""Set up test fixtures."""
		self.test_out_content = """
 Test Gaussian Output
 ------------------
  Coordinates:
 1  2  3  4  5  # This line should be skipped
 H  0.0  0.0  0.0
 O  1.0  0.0  0.0

  SCF Energy: -100.0
  Some other text
  Coordinates:
 1  2  3  4  5  # This line should be skipped
 H  0.1  0.0  0.0
 O  1.1  0.0  0.0
 Normal termination.
"""
		self.expected_xyz_content = """2

H  0.0  0.0  0.0
O  1.0  0.0  0.0
2

H  0.1  0.0  0.0
O  1.1  0.0  0.0
"""

	def test_extract_coordinates(self):
		"""Test extracting coordinate blocks from output file."""
		with io.StringIO(self.test_out_content) as f:
			# Convert generator to list for testing
			blocks = list(parse_xyz.extract_coordinates(f))

		self.assertEqual(len(blocks), 2)
		self.assertEqual(blocks[0].lines, ["H  0.0  0.0  0.0", "O  1.0  0.0  0.0"])
		self.assertEqual(blocks[1].lines, ["H  0.1  0.0  0.0", "O  1.1  0.0  0.0"])

	def test_write_xyz_file(self):
		"""Test writing coordinate blocks to XYZ file."""
		# Create proper CoordinateBlock objects
		blocks = [
			CoordinateBlock(["H  0.0  0.0  0.0", "O  1.0  0.0  0.0"]),
			CoordinateBlock(["H  0.1  0.0  0.0", "O  1.1  0.0  0.0"]),
		]

		with tempfile.TemporaryDirectory() as tmp_dir:
			xyz_path = os.path.join(tmp_dir, "test.xyz")
			# Convert list to iterator
			parse_xyz.write_xyz_file(xyz_path, iter(blocks))

			with open(xyz_path) as f:
				content = f.read()

			self.assertEqual(content, self.expected_xyz_content)

	def test_process_out_file(self):
		"""Test processing a complete output file."""
		with tempfile.TemporaryDirectory() as tmp_dir:
			# Create test output file
			out_path = os.path.join(tmp_dir, "test.out")
			with open(out_path, "w") as f:
				f.write(self.test_out_content)

			# Process the file
			parse_xyz.process_out_file(out_path)

			# Check the result
			xyz_path = out_path[:-4] + ".xyz"
			self.assertTrue(os.path.exists(xyz_path))

			with open(xyz_path) as f:
				content = f.read()

			self.assertEqual(content, self.expected_xyz_content)

	def test_main_integration(self):
		"""Test main function with multiple files."""
		with tempfile.TemporaryDirectory() as tmp_dir:
			# Save current directory
			original_dir = os.getcwd()
			try:
				# Change to temp directory
				os.chdir(tmp_dir)

				# Create test files
				for i in range(2):
					with open(f"test{i}.out", "w") as f:
						f.write(self.test_out_content)

				# Run main
				parse_xyz.main()

				# Check results
				for i in range(2):
					xyz_path = f"test{i}.xyz"
					self.assertTrue(os.path.exists(xyz_path))
					with open(xyz_path) as f:
						content = f.read()
					self.assertEqual(content, self.expected_xyz_content)

			finally:
				# Restore original directory
				os.chdir(original_dir)


if __name__ == "__main__":
	unittest.main()
