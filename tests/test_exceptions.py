#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the exceptions module."""

import unittest

from milo_1_0_3 import exceptions


class TestMiloError(unittest.TestCase):
	"""Test the MiloError base class."""

	def test_message_storage(self):
		"""Test that the error message is stored correctly."""
		message = "Test error message"
		error = exceptions.MiloError(message)
		self.assertEqual(error.message, message)

	def test_str_representation(self):
		"""Test that the error converts to string correctly."""
		message = "Test error message"
		error = exceptions.MiloError(message)
		self.assertEqual(str(error), message)


class TestElectronicStructureProgramError(unittest.TestCase):
	"""Test the ElectronicStructureProgramError class."""

	def test_inheritance(self):
		"""Test that the error inherits correctly."""
		error = exceptions.ElectronicStructureProgramError("Test")
		self.assertIsInstance(error, exceptions.MiloError)
		self.assertIsInstance(error, Exception)

	def test_message_handling(self):
		"""Test error message handling."""
		message = "ESP calculation failed"
		error = exceptions.ElectronicStructureProgramError(message)
		self.assertEqual(error.message, message)
		self.assertEqual(str(error), message)


class TestInputError(unittest.TestCase):
	"""Test the InputError class."""

	def test_inheritance(self):
		"""Test that the error inherits correctly."""
		error = exceptions.InputError("Test")
		self.assertIsInstance(error, exceptions.MiloError)
		self.assertIsInstance(error, Exception)

	def test_message_handling(self):
		"""Test error message handling."""
		message = "Invalid input parameter"
		error = exceptions.InputError(message)
		self.assertEqual(error.message, message)
		self.assertEqual(str(error), message)

	def test_raising_error(self):
		"""Test that the error can be raised and caught properly."""
		with self.assertRaises(exceptions.InputError) as context:
			raise exceptions.InputError("Test error")
		self.assertEqual(str(context.exception), "Test error")


if __name__ == "__main__":
	unittest.main()
