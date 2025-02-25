#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scientific constants and unit conversions used throughout Milo.

This module provides fundamental physical constants and common unit conversions
used in scientific calculations. All values are in SI units unless otherwise noted.
"""

from typing import Final

# Fundamental Physical Constants
# ----------------------------
#: Planck's constant (J⋅s)
h: Final[float] = 6.62607015e-34

#: Speed of light (cm/s)
c: Final[float] = 29979245800

#: Avogadro's number (particles/mol)
AVOGADROS_NUMBER: Final[float] = 6.02214076e23

#: Gas constant (kcal/(mol⋅K))
GAS_CONSTANT_KCAL: Final[float] = 0.00198720425864083

#: Classical energy level spacing (cm^-1)
CLASSICAL_SPACING: Final[int] = 2


# Metric Prefix Conversions
# -----------------------
#: Conversion factor from kilo (×10³)
FROM_KILO: Final[float] = 1.0e3
#: Conversion factor to kilo (×10⁻³)
TO_KILO: Final[float] = 1 / FROM_KILO

#: Conversion factor to milli (×10³)
TO_MILLI: Final[float] = 1.0e3
#: Conversion factor from milli (×10⁻³)
FROM_MILLI: Final[float] = 1 / TO_MILLI

#: Conversion factor to centi (×10²)
TO_CENTI: Final[float] = 1.0e2
#: Conversion factor from centi (×10⁻²)
FROM_CENTI: Final[float] = 1 / TO_CENTI


# Particle/Mole Conversions
# -----------------------
#: Convert from moles to number of particles
MOLE_TO_PARTICLE: Final[float] = AVOGADROS_NUMBER
#: Convert from number of particles to moles
PARTICLE_TO_MOLE: Final[float] = 1 / AVOGADROS_NUMBER


# Distance Conversions
# ------------------
#: Convert from Ångström to meter (×10⁻¹⁰)
ANGSTROM_TO_METER: Final[float] = 1.0e-10
#: Convert from meter to Ångström (×10¹⁰)
METER_TO_ANGSTROM: Final[float] = 1 / ANGSTROM_TO_METER

#: Convert from Bohr to Ångström
BOHR_TO_ANGSTROM: Final[float] = 0.52917721090380
#: Convert from Ångström to Bohr
ANGSTROM_TO_BOHR: Final[float] = 1 / BOHR_TO_ANGSTROM


# Mass Conversions
# --------------
#: Convert from atomic mass units to kilograms
AMU_TO_KG: Final[float] = 1.66053878e-27
#: Convert from kilograms to atomic mass units
KG_TO_AMU: Final[float] = 1 / AMU_TO_KG


# Force Conversions
# ---------------
#: Convert from Hartree/Bohr to Newton
HARTREE_PER_BOHR_TO_NEWTON: Final[float] = 8.2387234983e-8
#: Convert from Newton to Hartree/Bohr
NEWTON_TO_HARTREE_PER_BOHR: Final[float] = 1 / HARTREE_PER_BOHR_TO_NEWTON

#: Convert from Newton to dyne (×10⁵)
NEWTON_TO_DYNE: Final[float] = 1.0e5
#: Convert from dyne to Newton (×10⁻⁵)
DYNE_TO_NEWTON: Final[float] = 1 / NEWTON_TO_DYNE


# Time Conversions
# --------------
#: Convert from seconds to femtoseconds (×10¹⁵)
SECOND_TO_FEMTOSECOND: Final[float] = 1.0e15
#: Convert from femtoseconds to seconds (×10⁻¹⁵)
FEMTOSECOND_TO_SECOND: Final[float] = 1 / SECOND_TO_FEMTOSECOND


# Energy Conversions
# ----------------
#: Convert from calories to Joules
CALORIE_TO_JOULE: Final[float] = 4.184
#: Convert from Joules to calories
JOULE_TO_CALORIE: Final[float] = 1 / CALORIE_TO_JOULE

#: Convert from Joules to kcal/mol
JOULE_TO_KCAL_PER_MOLE: Final[float] = TO_KILO * JOULE_TO_CALORIE / PARTICLE_TO_MOLE
#: Convert from kcal/mol to Joules
KCAL_PER_MOLE_TO_JOULE: Final[float] = 1 / JOULE_TO_KCAL_PER_MOLE

#: Convert from Joules to millidyne-Ångström
JOULE_TO_MILLIDYNE_ANGSTROM: Final[float] = TO_MILLI * NEWTON_TO_DYNE * METER_TO_ANGSTROM
#: Convert from millidyne-Ångström to Joules
MILLIDYNE_ANGSTROM_TO_JOULE: Final[float] = 1 / JOULE_TO_MILLIDYNE_ANGSTROM

#: Convert from Hartree to Joules
HARTREE_TO_JOULE: Final[float] = 4.359744722207185e-18
#: Convert from Joules to Hartree
JOULE_TO_HARTREE: Final[float] = 1 / HARTREE_TO_JOULE
