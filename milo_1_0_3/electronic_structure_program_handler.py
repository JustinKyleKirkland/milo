#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Handle calling ESPs and parsing output."""

import os
from typing import Type

from milo_1_0_3 import containers, exceptions
from milo_1_0_3 import enumerations as enums
from milo_1_0_3.program_state import ProgramState


def get_program_handler(program_state: ProgramState) -> Type["GaussianHandler"]:
	"""Return the configured electronic structure program handler.

	Args:
		program_state: The program state containing ESP configuration

	Returns:
		The appropriate handler class for the configured ESP

	Raises:
		ValueError: If the program_id is not recognized
	"""
	if program_state.program_id is enums.ProgramID.GAUSSIAN_16:
		return Gaussian16Handler
	elif program_state.program_id is enums.ProgramID.GAUSSIAN_09:
		return Gaussian09Handler
	else:
		raise ValueError(f'Unknown electronic structure program "{program_state.program_id}"')


class GaussianHandler:
	"""Template handler for Gaussian16Handler and Gaussian09Handler."""

	gaussian_command: str = ""

	@classmethod
	def generate_forces(cls, program_state: ProgramState) -> None:
		"""Perform computation and append forces to list in program state.

		Args:
			program_state: The program state to update with forces
		"""
		route_section = f"# force {program_state.gaussian_header}"
		log_file = cls.call_gaussian(
			route_section, f"{cls.gaussian_command}_{program_state.current_step}", program_state
		)
		cls.parse_forces(log_file, program_state)

	@classmethod
	def call_gaussian(cls, route_section: str, job_name: str, program_state: ProgramState) -> str:
		"""Call Gaussian and return path to the log file.

		Args:
			route_section: The Gaussian route section
			job_name: Name for the job files
			program_state: Program state containing calculation parameters

		Returns:
			Path to the generated log file
		"""
		job_com_file = f"{job_name}.com"
		job_log_file = f"{job_name}.log"
		cls.prepare_com_file(job_com_file, route_section, program_state)
		os.system(f"{cls.gaussian_command} < {job_com_file} > {job_log_file}")
		return job_log_file

	@staticmethod
	def prepare_com_file(file_name: str, route_section: str, program_state: ProgramState) -> None:
		"""Prepare a .com file for a Gaussian run.

		Args:
			file_name: Path to write the com file
			route_section: The Gaussian route section
			program_state: Program state containing calculation parameters
		"""
		with open(file_name, "w") as com_file:
			# Write resource specifications
			if program_state.processor_count is not None:
				com_file.write(f"%nprocshared={program_state.processor_count}\n")
			if program_state.memory_amount is not None:
				com_file.write(f"%mem={program_state.memory_amount}gb\n")

			# Write calculation setup
			com_file.write(f"{route_section}\n\n")
			com_file.write(f"Calculation for time step: {program_state.current_step}\n\n")
			com_file.write(f" {program_state.charge} {program_state.spin}\n")

			# Write atomic coordinates
			for atom, (x, y, z) in zip(program_state.atoms, program_state.structures[-1].as_angstrom()):
				com_file.write(f"  {atom.symbol} {x:10.6f} {y:10.6f} {z:10.6f}\n")
			com_file.write("\n")

			# Write footer if provided
			if program_state.gaussian_footer is not None:
				com_file.write(program_state.gaussian_footer)
			com_file.write("\n\n")

	@classmethod
	def parse_forces(cls, log_file_name: str, program_state: ProgramState) -> None:
		"""Parse forces into program_state from the given log file.

		Args:
			log_file_name: Path to the Gaussian log file
			program_state: Program state to update with parsed forces

		Raises:
			ElectronicStructureProgramError: If the log file indicates calculation failure
		"""
		if not cls.is_log_good(log_file_name):
			raise exceptions.ElectronicStructureProgramError(
				"Gaussian force calculation log file was not valid. Gaussian "
				"returned an error or could not be called correctly."
			)

		forces = containers.Forces()
		energy = containers.Energies()

		with open(log_file_name) as log_file:
			for line in log_file:
				# Parse energy
				if "SCF Done" in line:
					value = float(line.split()[4])
					energy.append(value, enums.EnergyUnits.HARTREE)
					program_state.energies.append(energy)

				# Parse forces
				if "Forces (Hartrees/Bohr)" in line:
					for data_line in log_file:
						if "Cartesian Forces" in data_line:
							program_state.forces.append(forces)
							return

						tokens = data_line.split()
						try:
							# Skip lines that don't start with an atom index
							int(tokens[0])
						except (ValueError, IndexError):
							continue

						x, y, z = map(float, tokens[2:5])
						forces.append(x, y, z, enums.ForceUnits.HARTREE_PER_BOHR)

	@staticmethod
	def is_log_good(log_file_name: str) -> bool:
		"""Return true if the given log file terminated normally.

		Args:
			log_file_name: Path to the Gaussian log file

		Returns:
			True if the calculation completed successfully
		"""
		with open(log_file_name) as log_file:
			return any("Normal termination" in line for line in log_file)


class Gaussian16Handler(GaussianHandler):
	"""Call Gaussian16 and parse output."""

	gaussian_command = "g16"


class Gaussian09Handler(GaussianHandler):
	"""Call Gaussian09 and parse output."""

	gaussian_command = "g09"
