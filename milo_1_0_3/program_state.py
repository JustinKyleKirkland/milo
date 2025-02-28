#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Store data used throughout the simulation."""

from dataclasses import dataclass, field
from functools import cached_property
from typing import Dict, List, Optional, Tuple

from milo_1_0_3 import containers
from milo_1_0_3 import enumerations as enums
from milo_1_0_3 import random_number_generator as rng
from milo_1_0_3.atom import Atom


@dataclass
class ProgramState:
	"""Contain all the data used throughout the simulation."""

	# Basic job configuration
	job_name: Optional[str] = None
	number_atoms: Optional[int] = None
	spin: Optional[int] = None
	charge: Optional[int] = None
	atoms: List[Atom] = field(default_factory=list)
	temperature: float = 298.15  # kelvin

	# Simulation control
	current_step: int = 0
	step_size: containers.Time = field(default_factory=lambda: containers.Time(1.00, enums.TimeUnits.FEMTOSECOND))
	max_steps: Optional[int] = None

	# Structure data
	input_structure: containers.Positions = field(default_factory=containers.Positions)
	structures: List[containers.Positions] = field(default_factory=list)
	velocities: List[containers.Velocities] = field(default_factory=list)
	forces: List[containers.Forces] = field(default_factory=list)
	accelerations: List[containers.Accelerations] = field(default_factory=list)
	energies: List[float] = field(default_factory=list)

	# Propagation configuration
	propagation_algorithm: enums.PropagationAlgorithm = enums.PropagationAlgorithm.VERLET
	oscillator_type: enums.OscillatorType = enums.OscillatorType.QUASICLASSICAL
	add_rotational_energy: enums.RotationalEnergy = enums.RotationalEnergy.NO
	geometry_displacement_type: enums.GeometryDisplacement = enums.GeometryDisplacement.NONE
	phase_direction: enums.PhaseDirection = enums.PhaseDirection.RANDOM
	phase: Optional[Tuple[int, int]] = None

	# Mode configuration
	fixed_mode_directions: Dict[int, int] = field(default_factory=dict)
	fixed_vibrational_quanta: Dict[int, int] = field(default_factory=dict)

	# Frequency data
	frequencies: containers.Frequencies = field(default_factory=containers.Frequencies)
	mode_displacements: List[List[containers.Positions]] = field(default_factory=list)
	force_constants: containers.ForceConstants = field(default_factory=containers.ForceConstants)
	reduced_masses: containers.Masses = field(default_factory=containers.Masses)
	zero_point_energy: Optional[float] = None
	zero_point_correction: Optional[float] = None

	# Energy boost configuration
	energy_boost: enums.EnergyBoost = enums.EnergyBoost.OFF
	energy_boost_min: Optional[float] = None
	energy_boost_max: Optional[float] = None

	# Random number generation
	random: rng.RandomNumberGenerator = field(default_factory=rng.RandomNumberGenerator)

	# Program configuration
	program_id: enums.ProgramID = enums.ProgramID.GAUSSIAN_16
	gaussian_header: Optional[str] = None
	gaussian_footer: Optional[str] = None
	processor_count: Optional[int] = None
	memory_amount: Optional[str] = None
	output_xyz_file: bool = True

	@cached_property
	def total_energy(self) -> float:
		"""Calculate and cache the total energy of the system."""
		return sum(self.energies) if self.energies else 0.0

	@cached_property
	def has_frequency_data(self) -> bool:
		"""Check if frequency data is available."""
		return len(self.frequencies) > 0

	@cached_property
	def system_mass(self) -> float:
		"""Calculate and cache the total mass of the system."""
		return sum(atom.mass for atom in self.atoms)

	def reset_cache(self) -> None:
		"""Reset all cached properties when state changes."""
		# Delete all cached properties
		for attr in ["total_energy", "has_frequency_data", "system_mass"]:
			try:
				delattr(self, attr)
			except AttributeError:
				pass
