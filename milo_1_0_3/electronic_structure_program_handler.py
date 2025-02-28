#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Handle calling ESPs and parsing output."""

import os
from typing import List, Type

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

		Raises:
			exceptions.ElectronicStructureProgramError: If Gaussian execution fails
		"""
		job_com_file = f"{job_name}.com"
		job_log_file = f"{job_name}.log"
		cls.prepare_com_file(job_com_file, route_section, program_state)

		# Use os.system for compatibility with tests
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
		lines: List[str] = []

		# Write resource specifications
		if program_state.processor_count is not None:
			lines.append(f"%nprocshared={program_state.processor_count}")
		if program_state.memory_amount is not None:
			lines.append(f"%mem={program_state.memory_amount}gb")

		# Write calculation setup
		lines.extend(
			[
				route_section,
				"",
				f"Calculation for time step: {program_state.current_step}",
				"",
				f" {program_state.charge} {program_state.spin}",
			]
		)

		# Write atomic coordinates
		lines.extend(
			f"  {atom.symbol} {x:10.6f} {y:10.6f} {z:10.6f}"
			for atom, (x, y, z) in zip(program_state.atoms, program_state.structures[-1].as_angstrom())
		)
		lines.append("")

		# Write footer if provided
		if program_state.gaussian_footer is not None:
			lines.append(program_state.gaussian_footer)
		lines.extend(["", ""])

		# Write all lines at once using open() for test compatibility
		with open(file_name, "w") as f:
			f.write("\n".join(lines))

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

		with open(log_file_name) as f:
			log_contents = f.readlines()

		for i, line in enumerate(log_contents):
			# Parse energy - more efficient string check
			if "SCF Done" in line:
				value = float(line.split()[4])
				energy.append(value, enums.EnergyUnits.HARTREE)
				program_state.energies.append(energy)

			# Parse forces - process block at once when found
			if "Forces (Hartrees/Bohr)" in line:
				for force_line in log_contents[i + 1 :]:
					if "Cartesian Forces" in force_line:
						program_state.forces.append(forces)
						return

					try:
						tokens = force_line.split()
						# Try to convert first token to int to validate line
						if not tokens or not tokens[0].isdigit():
							continue
						x, y, z = map(float, tokens[2:5])
						forces.append(x, y, z, enums.ForceUnits.HARTREE_PER_BOHR)
					except (ValueError, IndexError):
						continue

	@staticmethod
	def is_log_good(log_file_name: str) -> bool:
		"""Return true if the given log file terminated normally.

		Args:
			log_file_name: Path to the Gaussian log file

		Returns:
			True if the calculation completed successfully
		"""
		with open(log_file_name) as f:
			return any("Normal termination" in line for line in f)


class Gaussian16Handler(GaussianHandler):
	"""Call Gaussian16 and parse output."""

	gaussian_command = "g16"


class Gaussian09Handler(GaussianHandler):
	"""Call Gaussian09 and parse output."""

	gaussian_command = "g09"
