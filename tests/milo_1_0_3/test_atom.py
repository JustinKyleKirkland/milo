#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for atom.py."""

import unittest

from milo_1_0_3.atom import Atom, default_from_number, default_from_symbol, isotope_data


class TestAtom(unittest.TestCase):
	"""Test cases for Atom class."""

	def test_init_valid(self):
		"""Test valid atom initialization."""
		atom = Atom("H", 1, 1, 1.00782503223)
		self.assertEqual(atom.symbol, "H")
		self.assertEqual(atom.atomic_number, 1)
		self.assertEqual(atom.mass_number, 1)
		self.assertEqual(atom.mass, 1.00782503223)

	def test_init_invalid(self):
		"""Test invalid atom initialization."""
		with self.assertRaises(ValueError):
			Atom("", 1, 1, 1.0)  # Empty symbol
		with self.assertRaises(ValueError):
			Atom("H", -1, 1, 1.0)  # Negative atomic number

	def test_symbol_case(self):
		"""Test symbol case normalization."""
		atom = Atom("h", 1, 1, 1.0)
		self.assertEqual(atom.symbol, "H")
		atom = Atom("HE", 2, 4, 4.0)
		self.assertEqual(atom.symbol, "He")

	def test_from_symbol(self):
		"""Test creating atom from symbol."""
		atom = Atom.from_symbol("H")
		self.assertEqual(atom.symbol, "H")
		self.assertEqual(atom.atomic_number, 1)
		self.assertEqual(atom.mass_number, 1)
		self.assertEqual(atom.mass, 1.00782503223)

		# Test deuterium and tritium
		d_atom = Atom.from_symbol("D")
		self.assertEqual(d_atom.symbol, "D")
		self.assertEqual(d_atom.atomic_number, 1)
		self.assertEqual(d_atom.mass_number, 2)

		t_atom = Atom.from_symbol("T")
		self.assertEqual(t_atom.symbol, "T")
		self.assertEqual(t_atom.atomic_number, 1)
		self.assertEqual(t_atom.mass_number, 3)

	def test_from_atomic_number(self):
		"""Test creating atom from atomic number."""
		atom = Atom.from_atomic_number(1)
		self.assertEqual(atom.symbol, "H")
		self.assertEqual(atom.atomic_number, 1)
		self.assertEqual(atom.mass_number, 1)
		self.assertEqual(atom.mass, 1.00782503223)

	def test_from_mass_number(self):
		"""Test creating atom with specific mass number."""
		# Test regular isotope
		atom = Atom.from_symbol_mass_number("C", 13)
		self.assertEqual(atom.symbol, "C")
		self.assertEqual(atom.mass_number, 13)
		self.assertEqual(atom.mass, 13.00335483507)

		# Test default isotope when mass number not found
		atom = Atom.from_symbol_mass_number("C", 999)
		self.assertEqual(atom.symbol, "C")
		self.assertEqual(atom.mass_number, 12)  # Should default to most common isotope
		self.assertEqual(atom.mass, 12.0)

	def test_str_representation(self):
		"""Test string representation."""
		atom = Atom("H", 1, 1, 1.00782503223)
		expected = "H    1.0078250 amu"
		self.assertEqual(str(atom), expected)

	def test_repr_representation(self):
		"""Test repr representation."""
		atom = Atom("H", 1, 1, 1.00782503223)
		expected = "Atom(symbol='H', atomic_number=1, mass_number=1, mass=1.00782503223)"
		self.assertEqual(repr(atom), expected)

	def test_default_data_consistency(self):
		"""Test consistency between default_from_symbol and default_from_number."""
		for symbol, (num, mass_num, mass) in default_from_symbol.items():
			# Check reverse lookup works
			self.assertEqual(default_from_number[num][0], symbol)
			self.assertEqual(default_from_number[num][1], mass_num)
			self.assertEqual(default_from_number[num][2], mass)

	def test_isotope_data_validity(self):
		"""Test validity of isotope data."""
		for (symbol, mass_num), mass in isotope_data.items():
			# Create atom from this isotope data
			atom = Atom.from_symbol_mass_number(symbol, mass_num)
			self.assertEqual(atom.mass, mass)
			self.assertEqual(atom.mass_number, mass_num)

	def test_mass_number_setter(self):
		"""Test mass_number property setter."""
		atom = Atom("H", 1, 1, 1.0)
		atom.mass_number = 2
		self.assertEqual(atom.mass_number, 2)

	def test_mass_setter(self):
		"""Test mass property setter."""
		atom = Atom("H", 1, 1, 1.0)
		atom.mass = 2.0
		self.assertEqual(atom.mass, 2.0)

		# Test float conversion
		atom.mass = 3
		self.assertEqual(atom.mass, 3.0)
		self.assertIsInstance(atom.mass, float)


if __name__ == "__main__":
	unittest.main()
