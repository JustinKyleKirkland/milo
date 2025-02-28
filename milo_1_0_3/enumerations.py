#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Define all enumerations used throughout the program.

This module contains all the enumeration classes used to represent various units
and configuration options in the program. Using enums helps prevent errors from
typos and provides better type safety than strings.

Example:
    from milo_1_0_3 import enumerations as enums
    my_var = enums.ProgramID.GAUSSIAN_16
"""

from enum import Enum, auto
from typing import List, Type


# Unit-related enumerations
class AccelerationUnits(Enum):
	"""Units for measuring acceleration."""

	METER_PER_SEC_SQRD = auto()


class AngleUnits(Enum):
	"""Units for measuring angles."""

	RADIANS = auto()
	DEGREES = auto()


class DistanceUnits(Enum):
	"""Units for measuring distance."""

	ANGSTROM = auto()
	BOHR = auto()
	METER = auto()


class EnergyUnits(Enum):
	"""Units for measuring energy."""

	JOULE = auto()
	KCAL_PER_MOLE = auto()
	MILLIDYNE_ANGSTROM = auto()
	HARTREE = auto()


class ForceConstantUnits(Enum):
	"""Units for measuring force constants."""

	NEWTON_PER_METER = auto()
	MILLIDYNE_PER_ANGSTROM = auto()


class ForceUnits(Enum):
	"""Units for measuring force."""

	NEWTON = auto()
	DYNE = auto()
	MILLIDYNE = auto()
	HARTREE_PER_BOHR = auto()


class FrequencyUnits(Enum):
	"""Units for measuring frequency."""

	RECIP_CM = auto()


class MassUnits(Enum):
	"""Units for measuring mass."""

	AMU = auto()
	KILOGRAM = auto()
	GRAM = auto()


class TimeUnits(Enum):
	"""Units for measuring time."""

	SECOND = auto()
	FEMTOSECOND = auto()


class VelocityUnits(Enum):
	"""Units for measuring velocity."""

	METER_PER_SEC = auto()
	ANGSTROM_PER_FS = auto()
	ANGSTROM_PER_SEC = auto()


# Configuration enumerations
class EnergyBoost(Enum):
	"""Configuration for energy boost usage."""

	OFF = auto()
	ON = auto()


class GeometryDisplacement(Enum):
	"""Methods for initial structure equilibrium displacement."""

	NONE = auto()
	EDGE_WEIGHTED = auto()
	GAUSSIAN_DISTRIBUTION = auto()
	UNIFORM = auto()


class OscillatorType(Enum):
	"""Methods for treating harmonic oscillator."""

	QUASICLASSICAL = auto()
	CLASSICAL = auto()


class PhaseDirection(Enum):
	"""Options for phase directions."""

	BRING_TOGETHER = auto()
	PUSH_APART = auto()
	RANDOM = auto()


class ProgramID(Enum):
	"""Supported electronic structure programs."""

	GAUSSIAN_16 = 1
	G16 = 1  # Alias for GAUSSIAN_16
	GAUSSIAN_09 = 2
	G09 = 2  # Alias for GAUSSIAN_09


class PropagationAlgorithm(Enum):
	"""Algorithms for force propagation."""

	VERLET = auto()
	VELOCITY_VERLET = auto()


class RotationalEnergy(Enum):
	"""Configuration for adding rotational energy."""

	YES = auto()
	NO = auto()


def get_all_enums() -> List[Type[Enum]]:
	"""Return a list of all enumeration classes in this module.

	Returns:
		List[Type[Enum]]: List of all Enum classes defined in this module
	"""
	return [
		cls
		for name, cls in globals().items()
		if isinstance(cls, type) and issubclass(cls, Enum) and cls.__module__ == __name__
	]
