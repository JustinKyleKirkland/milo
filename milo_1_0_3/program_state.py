#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Store data used throughout the simulation."""

from typing import Dict, List, Optional, Tuple

from milo_1_0_3 import containers
from milo_1_0_3 import enumerations as enums
from milo_1_0_3 import random_number_generator as rng
from milo_1_0_3.atom import Atom


class ProgramState:
	"""Contain all the data used throughout the simulation."""

	def __init__(self) -> None:
		"""Create all variables and sets some to default values."""
		# Basic job configuration
		self.job_name: Optional[str] = None
		self.number_atoms: Optional[int] = None
		self.spin: Optional[int] = None
		self.charge: Optional[int] = None
		self.atoms: List[Atom] = []
		self.temperature: float = 298.15  # kelvin

		# Simulation control
		self.current_step: int = 0  # current_step is 0 for the first step
		self.step_size: containers.Time = containers.Time(1.00, enums.TimeUnits.FEMTOSECOND)
		self.max_steps: Optional[int] = None  # If None, no limit

		# Structure data
		self.input_structure: containers.Positions = containers.Positions()
		self.structures: List[containers.Positions] = []
		self.velocities: List[containers.Velocities] = []
		self.forces: List[containers.Forces] = []
		self.accelerations: List[containers.Accelerations] = []
		self.energies: List[float] = []

		# Propagation configuration
		self.propagation_algorithm: enums.PropagationAlgorithm = enums.PropagationAlgorithm.VERLET
		self.oscillator_type: enums.OscillatorType = enums.OscillatorType.QUASICLASSICAL
		self.add_rotational_energy: enums.RotationalEnergy = enums.RotationalEnergy.NO
		self.geometry_displacement_type: enums.GeometryDisplacement = enums.GeometryDisplacement.NONE
		self.phase_direction: enums.PhaseDirection = enums.PhaseDirection.RANDOM
		self.phase: Optional[Tuple[int, int]] = None

		# Mode configuration
		self.fixed_mode_directions: Dict[int, int] = {}  # maps mode number to 1 or -1
		self.fixed_vibrational_quanta: Dict[int, int] = {}  # maps mode number to quanta

		# Frequency data
		self.frequencies: containers.Frequencies = containers.Frequencies()
		self.mode_displacements: List[List[containers.Positions]] = []  # mode[frequency index][atom index]
		self.force_constants: containers.ForceConstants = containers.ForceConstants()
		self.reduced_masses: containers.Masses = containers.Masses()
		self.zero_point_energy: Optional[float] = None
		self.zero_point_correction: Optional[float] = None

		# Energy boost configuration
		self.energy_boost: enums.EnergyBoost = enums.EnergyBoost.OFF
		self.energy_boost_min: Optional[float] = None
		self.energy_boost_max: Optional[float] = None

		# Random number generation
		self.random: rng.RandomNumberGenerator = rng.RandomNumberGenerator()

		# Program configuration
		self.program_id: enums.ProgramID = enums.ProgramID.GAUSSIAN_16
		self.gaussian_header: Optional[str] = None
		self.gaussian_footer: Optional[str] = None
		self.processor_count: Optional[int] = None
		self.memory_amount: Optional[str] = None
		self.output_xyz_file: bool = True
