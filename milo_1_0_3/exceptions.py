#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Define Milo specific exceptions.

This module contains custom exceptions used throughout the Milo package
to provide more specific error handling and clearer error messages.
"""


class MiloError(Exception):
	"""Base class for all Milo-specific exceptions."""

	def __init__(self, message: str) -> None:
		"""Create an exception with given message.

		Args:
			message: The error message to display
		"""
		super().__init__(message)
		self.message = message


class ElectronicStructureProgramError(MiloError):
	"""Raised when the electronic structure program returns an error.

	This exception is raised when there are issues with running or getting
	results from electronic structure programs like Gaussian.
	"""

	pass


class InputError(MiloError):
	"""Raised when input file or parameters are not valid.

	This exception is raised when there are issues with the input data,
	such as missing required parameters or invalid values.
	"""

	pass
