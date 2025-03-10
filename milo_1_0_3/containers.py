#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Define container classes for handling physical quantities with units."""

from typing import List, Optional, Tuple, Union

import numpy as np

from milo_1_0_3 import atom
from milo_1_0_3 import enumerations as enums
from milo_1_0_3 import scientific_constants as sc


class Positions:
	"""Container for atomic position data, stored internally in angstroms."""

	def __init__(self) -> None:
		"""Initialize empty positions list."""
		self._positions: List[Tuple[float, float, float]] = []

	def __len__(self) -> int:
		"""Return number of positions stored."""
		return len(self._positions)

	def alter_position(self, index: int, x: float, y: float, z: float, units: enums.DistanceUnits) -> None:
		"""
		Update position at given index.

		Args:
			index: Position to update
			x, y, z: New coordinates
			units: Units of input coordinates
		"""
		factor = self._get_conversion_factor(units)
		self._positions[index] = tuple(i * factor for i in (x, y, z))

	def append(self, x: float, y: float, z: float, units: enums.DistanceUnits) -> None:
		"""
		Add new position.

		Args:
			x, y, z: Coordinates to add
			units: Units of input coordinates
		"""
		factor = self._get_conversion_factor(units)
		self._positions.append(tuple(i * factor for i in (x, y, z)))

	def _get_conversion_factor(self, units: enums.DistanceUnits) -> float:
		"""Get conversion factor from input units to angstroms."""
		if units is enums.DistanceUnits.ANGSTROM:
			return 1.0
		elif units is enums.DistanceUnits.BOHR:
			return sc.BOHR_TO_ANGSTROM
		elif units is enums.DistanceUnits.METER:
			return sc.METER_TO_ANGSTROM
		raise ValueError(f"Unknown distance units: {units}")

	def as_angstrom(
		self, index: Optional[int] = None
	) -> Union[Tuple[float, float, float], List[Tuple[float, float, float]]]:
		"""Get positions in angstroms."""
		return self._positions[index] if index is not None else self._positions

	def as_bohr(self, index=None):
		"""Return the entire list or specific index in bohr radii."""
		factor = sc.ANGSTROM_TO_BOHR
		if index is None:
			return [tuple(i * factor for i in j) for j in self._positions]
		return tuple(i * factor for i in self._positions[index])

	def as_meter(self, index=None):
		"""Return the entire list or specific index in meters."""
		factor = sc.ANGSTROM_TO_METER
		if index is None:
			return [tuple(i * factor for i in j) for j in self._positions]
		return tuple(i * factor for i in self._positions[index])

	@classmethod
	def from_velocity(cls, velocities, change_in_time):
		"""
		Return a displacement given a velocity and a time difference.

		Δx = v * Δt
		"""
		if not (isinstance(velocities, Velocities) and isinstance(change_in_time, Time)):
			raise TypeError(f"Cannot create Positions object from '{type(velocities)}' and '{type(change_in_time)}'.")
		displacement = cls()
		dt = change_in_time.as_second()
		for x, y, z in velocities.as_meter_per_sec():
			displacement.append(x * dt, y * dt, z * dt, units=enums.DistanceUnits.METER)
		return displacement

	@classmethod
	def from_acceleration(cls, acceleration, change_in_time):
		"""
		Return a displacement given an acceleration and a time difference.

		Δx = a*Δt^2
		"""
		if not (isinstance(acceleration, Accelerations) and isinstance(change_in_time, Time)):
			raise TypeError(f"cannot create Positions object from '{type(acceleration)}' and '{type(change_in_time)}'")
		displacement = cls()
		dt2 = change_in_time.as_second() ** 2
		for x, y, z in acceleration.as_meter_per_sec_sqrd():
			displacement.append(x * dt2, y * dt2, z * dt2, units=enums.DistanceUnits.METER)
		return displacement

	def __add__(self, other):
		"""Add operator functionality."""
		if not isinstance(other, Positions):
			return NotImplemented
		total = Positions()
		for (x1, y1, z1), (x2, y2, z2) in zip(self.as_angstrom(), other.as_angstrom()):
			total.append(x1 + x2, y1 + y2, z1 + z2, enums.DistanceUnits.ANGSTROM)
		return total

	def __sub__(self, other):
		"""Subtraction operator functionality."""
		if not isinstance(other, Positions):
			return NotImplemented
		difference = Positions()
		for (x1, y1, z1), (x2, y2, z2) in zip(self.as_angstrom(), other.as_angstrom()):
			difference.append(x1 - x2, y1 - y2, z1 - z2, enums.DistanceUnits.ANGSTROM)
		return difference

	def __mul__(self, other):
		"""Multiplication operator functionality."""
		if not isinstance(other, (int, float)):
			return NotImplemented
		products = Positions()
		for x, y, z in self.as_angstrom():
			products.append(x * other, y * other, z * other, enums.DistanceUnits.ANGSTROM)
		return products

	__rmul__ = __mul__

	def __str__(self):
		"""Return structure as multiline string."""
		strings = []
		for x, y, z in self._positions:
			strings.append(f"{x:10.6f} {y:10.6f} {z:10.6f}")
		return "\n".join(strings)

	def __repr__(self):
		"""Return object representation."""
		return f"<Positions object with {len(self._positions)} atoms.>"


class Velocities:
	"""
	Extend a list to make xyz momentum data easy to use.

	Always store as meters per second
	"""

	def __init__(self):
		"""Create the internal list that holds velocities."""
		self._velocities = list()

	def __len__(self):
		"""Return the length of _velocities."""
		return len(self._velocities)

	def append(self, x, y, z, units):
		"""Append x, y, z as a tuple to the end of the list."""
		if units is enums.VelocityUnits.METER_PER_SEC:
			factor = 1
		elif units is enums.VelocityUnits.ANGSTROM_PER_FS:
			factor = sc.ANGSTROM_TO_METER * (1 / sc.FEMTOSECOND_TO_SECOND)
		elif units is enums.VelocityUnits.ANGSTROM_PER_SEC:
			factor = sc.ANGSTROM_TO_METER
		else:
			raise ValueError(f"Unknown velocity unit: {units}")
		self._velocities.append(tuple(i * factor for i in (x, y, z)))

	def as_meter_per_sec(self, index=None):
		"""Return the entire list or specific index in m/s."""
		if index is None:
			return self._velocities
		return self._velocities[index]

	def as_angstrom_per_fs(self, index=None):
		"""Return the entire list or specific index in angstrom/fs."""
		factor = sc.METER_TO_ANGSTROM * (1 / sc.SECOND_TO_FEMTOSECOND)
		if index is None:
			return [tuple(i * factor for i in j) for j in self._velocities]
		return tuple(i * factor for i in self._velocities[index])

	def as_angstrom_per_sec(self, index=None):
		"""Return the entire list or specific index in angstrom/s."""
		factor = sc.METER_TO_ANGSTROM
		if index is None:
			return [tuple(i * factor for i in j) for j in self._velocities]
		return tuple(i * factor for i in self._velocities[index])

	@classmethod
	def from_acceleration(cls, acceleration, change_in_time):
		"""
		Return a velocity given an acceleration and a time difference.

		Δv = a*Δt
		"""
		if not (isinstance(acceleration, Accelerations) and isinstance(change_in_time, Time)):
			raise TypeError(
				f"Cannot create Velocities object from '{type(acceleration)}' and '{type(change_in_time)}'."
			)
		displacement = cls()
		dt = change_in_time.as_second()
		for x, y, z in acceleration.as_meter_per_sec_sqrd():
			displacement.append(x * dt, y * dt, z * dt, units=enums.VelocityUnits.METER_PER_SEC)
		return displacement

	def __add__(self, other):
		"""Add operator functionality."""
		if not isinstance(other, Velocities):
			return NotImplemented
		total = Velocities()
		for (x1, y1, z1), (x2, y2, z2) in zip(self.as_meter_per_sec(), other.as_meter_per_sec()):
			total.append(x1 + x2, y1 + y2, z1 + z2, enums.VelocityUnits.METER_PER_SEC)
		return total

	def __sub__(self, other):
		"""Subtraction operator functionality."""
		if not isinstance(other, Velocities):
			return NotImplemented
		difference = Velocities()
		for (x1, y1, z1), (x2, y2, z2) in zip(self.as_meter_per_sec(), other.as_meter_per_sec()):
			difference.append(x1 - x2, y1 - y2, z1 - z2, enums.VelocityUnits.METER_PER_SEC)
		return difference

	def __mul__(self, other):
		"""Multiplication operator functionality."""
		if not isinstance(other, (int, float)):
			return NotImplemented
		products = Velocities()
		for x, y, z in self.as_meter_per_sec():
			products.append(x * other, y * other, z * other, enums.VelocityUnits.METER_PER_SEC)
		return products

	__rmul__ = __mul__

	def __str__(self):
		"""Return structure as multiline string."""
		strings = []
		for x, y, z in self._velocities:
			strings.append(f"{x:10.6f} {y:10.6f} {z:10.6f}")
		return "\n".join(strings)

	def __repr__(self):
		"""Return object representation."""
		return f"<Velocities object with {len(self._velocities)} atoms.>"

	def to_numpy(self) -> np.ndarray:
		"""Convert velocities to a NumPy array.

		Returns:
			NumPy array of shape (n, 3) where n is the number of velocities
		"""
		return np.array(self._velocities)

	@classmethod
	def from_numpy(cls, array: np.ndarray) -> "Velocities":
		"""Create a Velocities instance from a NumPy array.

		Args:
			array: NumPy array of shape (n, 3) containing velocities in m/s

		Returns:
			New Velocities instance
		"""
		instance = cls()
		for row in array:
			instance.append(row[0], row[1], row[2], enums.VelocityUnits.METER_PER_SEC)
		return instance


class Accelerations:
	"""
	Extend a list to make xyz acceleration data easy to use.

	Always store as meters per second squared
	"""

	def __init__(self):
		"""Create the internal list that holds accelerations."""
		self._accelerations = list()

	def __len__(self):
		"""Return the length of _accelerations."""
		return len(self._accelerations)

	def append(self, x, y, z, units):
		"""Append x, y, z as a tuple to the end of the list."""
		if units is enums.AccelerationUnits.METER_PER_SEC_SQRD:
			factor = 1
		else:
			raise ValueError(f"Unknown Acceleration units: {units}")
		self._accelerations.append(tuple(i * factor for i in (x, y, z)))

	def as_meter_per_sec_sqrd(self, index=None):
		"""Return the entire list or specific index in m/s^2."""
		if index is None:
			return self._accelerations
		return self._accelerations[index]

	@classmethod
	def from_forces(cls, forces, atoms):
		"""
		Return an acceleration given forces and a masses.

		F = ma --> a = F / m
		"""
		if not (isinstance(forces, Forces) and isinstance(atoms, list) and isinstance(atoms[0], atom.Atom)):
			raise TypeError(f"Cannot create Accelerations object from'{type(forces)}' and '{type(atoms)}'.")
		accelerations = cls()
		atom_masses_kg = [element.mass * sc.AMU_TO_KG for element in atoms]
		for mass, (x, y, z) in zip(atom_masses_kg, forces.as_newton()):
			accelerations.append(x / mass, y / mass, z / mass, enums.AccelerationUnits.METER_PER_SEC_SQRD)
		return accelerations

	def __add__(self, other):
		"""Add operator functionality."""
		if not isinstance(other, Accelerations):
			return NotImplemented
		total = Accelerations()
		for (x1, y1, z1), (x2, y2, z2) in zip(self.as_meter_per_sec_sqrd(), other.as_meter_per_sec_sqrd()):
			total.append(x1 + x2, y1 + y2, z1 + z2, enums.AccelerationUnits.METER_PER_SEC_SQRD)
		return total

	def __sub__(self, other):
		"""Subtraction operator functionality."""
		if not isinstance(other, Accelerations):
			return NotImplemented
		difference = Accelerations()
		for (x1, y1, z1), (x2, y2, z2) in zip(self.as_meter_per_sec_sqrd(), other.as_meter_per_sec_sqrd()):
			difference.append(x1 - x2, y1 - y2, z1 - z2, enums.AccelerationUnits.METER_PER_SEC_SQRD)
		return difference

	def __mul__(self, other):
		"""Multiplication operator functionality."""
		if not isinstance(other, (int, float)):
			return NotImplemented
		products = Accelerations()
		for x, y, z in self.as_meter_per_sec_sqrd():
			products.append(x * other, y * other, z * other, enums.AccelerationUnits.METER_PER_SEC_SQRD)
		return products

	__rmul__ = __mul__

	def __str__(self):
		"""Return structure as multiline string."""
		strings = []
		for x, y, z in self._accelerations:
			strings.append(f"{x:10.6f} {y:10.6f} {z:10.6f}")
		return "\n".join(strings)

	def __repr__(self):
		"""Return object representation."""
		return f"<Accelerations object with {len(self._accelerations)} atoms.>"

	def to_numpy(self) -> np.ndarray:
		"""Convert accelerations to a NumPy array.

		Returns:
			NumPy array of shape (n, 3) where n is the number of accelerations
		"""
		return np.array(self._accelerations)

	@classmethod
	def from_numpy(cls, array: np.ndarray) -> "Accelerations":
		"""Create an Accelerations instance from a NumPy array.

		Args:
			array: NumPy array of shape (n, 3) containing accelerations in m/s^2

		Returns:
			New Accelerations instance
		"""
		instance = cls()
		for row in array:
			instance.append(row[0], row[1], row[2], enums.AccelerationUnits.METER_PER_SEC_SQRD)
		return instance


class Forces:
	"""
	Extend a list to make xyz forces data easy to use.

	Always store as Newtons
	"""

	def __init__(self):
		"""Create the internal list that holds forces."""
		self._forces = list()

	def __len__(self):
		"""Return the length of _forces."""
		return len(self._forces)

	def append(self, x, y, z, units):
		"""Append x, y, z as a tuple to the end of the list."""
		if units is enums.ForceUnits.NEWTON:
			factor = 1
		elif units is enums.ForceUnits.DYNE:
			factor = sc.DYNE_TO_NEWTON
		elif units is enums.ForceUnits.MILLIDYNE:
			factor = sc.FROM_MILLI * sc.DYNE_TO_NEWTON
		elif units is enums.ForceUnits.HARTREE_PER_BOHR:
			factor = sc.HARTREE_PER_BOHR_TO_NEWTON
		else:
			raise ValueError(f"Unknown Force units: {units}")
		self._forces.append(tuple(i * factor for i in (x, y, z)))

	def as_newton(self, index=None):
		"""Return the entire list or specific index in newtons."""
		if index is None:
			return self._forces
		return self._forces[index]

	def as_dyne(self, index=None):
		"""Return the entire list or specific index in dyne."""
		factor = sc.NEWTON_TO_DYNE
		if index is None:
			return [tuple(i * factor for i in j) for j in self._forces]
		return tuple(i * factor for i in self._forces[index])

	def as_millidyne(self, index=None):
		"""Return the entire list or specific index in millidyne."""
		factor = sc.NEWTON_TO_DYNE * sc.TO_MILLI
		if index is None:
			return [tuple(i * factor for i in j) for j in self._forces]
		return tuple(i * factor for i in self._forces[index])

	def as_hartree_per_bohr(self, index=None):
		"""Return the entire list or specific index in hartree/bohr."""
		factor = sc.NEWTON_TO_HARTREE_PER_BOHR
		if index is None:
			return [tuple(i * factor for i in j) for j in self._forces]
		return tuple(i * factor for i in self._forces[index])

	def __add__(self, other):
		"""Add operator functionality."""
		if not isinstance(other, Forces):
			return NotImplemented
		total = Forces()
		for (x1, y1, z1), (x2, y2, z2) in zip(self.as_newton(), other.as_newton()):
			total.append(x1 + x2, y1 + y2, z1 + z2, enums.ForceUnits.NEWTON)
		return total

	def __sub__(self, other):
		"""Subtraction operator functionality."""
		if not isinstance(other, Forces):
			return NotImplemented
		difference = Forces()
		for (x1, y1, z1), (x2, y2, z2) in zip(self.as_newton(), other.as_newton()):
			difference.append(x1 - x2, y1 - y2, z1 - z2, enums.ForceUnits.NEWTON)
		return difference

	def __mul__(self, other):
		"""Multiplication operator functionality."""
		if not isinstance(other, (int, float)):
			return NotImplemented
		products = Forces()
		for x, y, z in self.as_newton():
			products.append(x * other, y * other, z * other, enums.ForceUnits.NEWTON)
		return products

	__rmul__ = __mul__

	def __str__(self):
		"""Return structure as multiline string."""
		strings = []
		for x, y, z in self._forces:
			strings.append(f"{x:10.6f}{y:10.6f}{z:10.6f}")
		return "\n".join(strings)

	def __repr__(self):
		"""Return object representation."""
		return f"<Forces object with {len(self._forces)} atoms.>"


class Frequencies:
	"""
	Extend a list to make frequency data easy to use.

	Always store as RECIP_CM
	"""

	def __init__(self):
		"""Create the internal list that holds forces."""
		self._frequencies = list()

	def __len__(self):
		"""Return the length of _frequencies."""
		return len(self._frequencies)

	def append(self, frequency, units):
		"""Append frequency to the end of the list."""
		if units is enums.FrequencyUnits.RECIP_CM:
			factor = 1
		else:
			raise ValueError(f"Unknown frequency units: {units}")
		self._frequencies.append(frequency * factor)

	def as_recip_cm(self, index=None):
		"""Return the entire list or specific index in cm^-1."""
		if index is None:
			return self._frequencies
		return self._frequencies[index]

	def __str__(self):
		"""Return structure as multiline string."""
		strings = []
		for frequency in self._frequencies:
			strings.append(f"{frequency:10.6f}")
		return "\n".join(strings)

	def __repr__(self):
		"""Return object representation."""
		return f"<Frequency object with {len(self._frequencies)} vibrational modes.>"


class ForceConstants:
	"""Container for force constant data, stored internally in N/m."""

	__slots__ = ("_force_constants", "_numpy_array")

	def __init__(self):
		"""Initialize empty force constants list."""
		self._force_constants = []
		self._numpy_array = None  # Cache for numpy array representation

	def append(self, force_constant, units):
		"""Append force constant to the list.

		Args:
			force_constant: Either a float (converted to (x,x,x) tuple) or a tuple of 3 floats
			units: Units enum for the force constant
		"""
		if units is enums.ForceConstantUnits.NEWTON_PER_METER:
			factor = 1.0
		elif units is enums.ForceConstantUnits.MILLIDYNE_PER_ANGSTROM:
			factor = 0.1  # Convert mdyne/Å to N/m
		else:
			raise ValueError(f"Unknown force constant units: {units}")

		# Handle both single float and tuple inputs
		if isinstance(force_constant, (int, float)):
			force_constant = (force_constant,) * 3

		# Store in N/m using a tuple for immutability
		self._force_constants.append(tuple(x * factor for x in force_constant))
		self._numpy_array = None  # Invalidate cache

	def as_newton_per_meter(self, index=None):
		"""Return the entire list or specific index in N/m."""
		if index is None:
			return self._force_constants
		return self._force_constants[index]

	def as_millidyne_per_angstrom(self, index=None):
		"""Return the entire list or specific index in millidyne/angstrom."""
		# Convert from N/m back to mdyne/Å
		factor = 10.0  # Inverse of the 0.1 factor used in append()
		if index is None:
			return [tuple(x * factor for x in fc) for fc in self._force_constants]
		return tuple(x * factor for x in self._force_constants[index])

	def to_numpy(self) -> np.ndarray:
		"""Convert force constants to a NumPy array.

		Returns:
			NumPy array of shape (n, 3) where n is the number of force constants
		"""
		if self._numpy_array is None:
			self._numpy_array = np.array(self._force_constants, dtype=np.float64)
		return self._numpy_array

	@classmethod
	def from_numpy(cls, array: np.ndarray) -> "ForceConstants":
		"""Create a ForceConstants instance from a NumPy array.

		Args:
			array: NumPy array of shape (n, 3) containing force constants in N/m

		Returns:
			New ForceConstants instance
		"""
		instance = cls()
		for row in array:
			instance.append(tuple(row), enums.ForceConstantUnits.NEWTON_PER_METER)
		return instance

	def __str__(self) -> str:
		"""Return structure as multiline string."""
		return "\n".join(f"{fc[0]:10.6f} {fc[1]:10.6f} {fc[2]:10.6f}" for fc in self._force_constants)

	def __repr__(self) -> str:
		"""Return object representation."""
		return f"<ForceConstants object with {len(self._force_constants)} force constants.>"

	def __len__(self) -> int:
		"""Return number of force constants."""
		return len(self._force_constants)

	def __getitem__(self, index):
		"""Get force constant at index."""
		return self._force_constants[index]

	def __iter__(self):
		"""Iterate over force constants."""
		return iter(self._force_constants)


class Masses:
	"""Container for mass data, stored internally in AMU."""

	def __init__(self):
		"""Initialize empty masses list."""
		self._masses = []

	def append(self, mass, units):
		"""Append mass to the list."""
		if units is enums.MassUnits.AMU:
			factor = 1.0
		elif units is enums.MassUnits.KILOGRAM:
			factor = sc.KG_TO_AMU
		elif units is enums.MassUnits.GRAM:
			factor = sc.TO_KILO * sc.KG_TO_AMU
		else:
			raise ValueError(f"Unknown mass units: {units}")
		self._masses.append(mass * factor)

	def as_amu(self, index=None):
		"""Return the entire list or specific index in amu."""
		if index is None:
			return self._masses
		return self._masses[index]

	def as_kilogram(self, index=None):
		"""Return the entire list or specific index in kg."""
		factor = sc.AMU_TO_KG
		if index is None:
			return [i * factor for i in self._masses]
		return self._masses[index] * factor

	def as_gram(self, index=None):
		"""Return the entire list or specific index in grams."""
		factor = sc.AMU_TO_KG * sc.FROM_KILO
		if index is None:
			return [i * factor for i in self._masses]
		return self._masses[index] * factor

	def __str__(self):
		"""Return structure as multiline string."""
		strings = []
		for mass in self._masses:
			strings.append(f"{mass:10.6f}")
		return "\n".join(strings)

	def __repr__(self):
		"""Return object representation."""
		return f"<Mass object with {len(self._masses)} masses.>"


class Time:
	"""
	Extend an float for easy usage of time data.

	Always store in seconds
	"""

	def __init__(self, time, unit=enums.TimeUnits.SECOND):
		"""Create a time object."""
		if unit is enums.TimeUnits.SECOND:
			self.time = time
		elif unit is enums.TimeUnits.FEMTOSECOND:
			self.time = time * sc.FEMTOSECOND_TO_SECOND
		else:
			raise ValueError(f"Unknown Time units: {unit}")

	def as_second(self):
		"""Return the value in seconds."""
		return self.time

	def as_femtosecond(self):
		"""Return the value in femtoseconds."""
		return self.time * sc.SECOND_TO_FEMTOSECOND

	def __str__(self):
		"""Return structure as string."""
		return f"{self.time} seconds"

	def __repr__(self):
		"""Return object representation."""
		return f"Time({self.time})"


class Energies:
	"""
	Extend a list to make energy data easy to use.

	Always store as Joules
	"""

	def __init__(self):
		"""Create the internal list that holds energies."""
		self._energies = list()

	def __len__(self):
		"""Return the length of _energies."""
		return len(self._energies)

	def append(self, energy, units):
		"""Append energy to the end of the list."""
		if units is enums.EnergyUnits.JOULE:
			factor = 1
		elif units is enums.EnergyUnits.KCAL_PER_MOLE:
			factor = sc.KCAL_PER_MOLE_TO_JOULE
		elif units is enums.EnergyUnits.MILLIDYNE_ANGSTROM:
			factor = sc.MILLIDYNE_ANGSTROM_TO_JOULE
		elif units is enums.EnergyUnits.HARTREE:
			factor = sc.HARTREE_TO_JOULE
		else:
			raise ValueError(f"Unknown Energy Units: {units}")
		self._energies.append(energy * factor)

	def alter_energy(self, index, energy, units):
		"""Set the energy at index to new value."""
		if units is enums.EnergyUnits.JOULE:
			factor = 1
		elif units is enums.EnergyUnits.KCAL_PER_MOLE:
			factor = sc.KCAL_PER_MOLE_TO_JOULE
		elif units is enums.EnergyUnits.MILLIDYNE_ANGSTROM:
			factor = sc.MILLIDYNE_ANGSTROM_TO_JOULE
		elif units is enums.EnergyUnits.HARTREE:
			factor = sc.HARTREE_TO_JOULE
		else:
			raise ValueError(f"Unknown Energy Units: {units}")
		self._energies[index] = energy * factor

	def as_joules(self, index=None):
		"""Return the entire list or specific index in joules."""
		if index is None:
			return self._energies
		return self._energies[index]

	def as_kcal_per_mole(self, index=None):
		"""Return the entire list or specific index in kcal/mol."""
		factor = sc.JOULE_TO_KCAL_PER_MOLE
		if index is None:
			return [i * factor for i in self._energies]
		return self._energies[index] * factor

	def as_millidyne_angstrom(self, index=None):
		"""Return the entire list or specific index in mdyne*angstrom."""
		factor = sc.JOULE_TO_MILLIDYNE_ANGSTROM
		if index is None:
			return [i * factor for i in self._energies]
		return self._energies[index] * factor

	def as_hartree(self, index=None):
		"""Return the entire list or specific index in hartrees."""
		factor = sc.JOULE_TO_HARTREE
		if index is None:
			return [i * factor for i in self._energies]
		return self._energies[index] * factor

	def __str__(self):
		"""Return structure as multiline string."""
		strings = []
		for energy in self._energies:
			strings.append(f"{energy:10.6f}")
		return "\n".join(strings)

	def __repr__(self):
		"""Return object representation."""
		return f"<Energies object with {len(self._energies)} energies.>"
