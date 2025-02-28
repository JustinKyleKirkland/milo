#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse input file and populate a ProgramState object.

This module handles parsing of input files and configuration of program state.
It validates input sections, parameters, and their values according to defined rules.
"""

import io
import os
from copy import deepcopy
from functools import lru_cache
from typing import IO, Dict, List, Set, Tuple, Union

from milo_1_0_3 import atom, containers, exceptions
from milo_1_0_3 import enumerations as enums
from milo_1_0_3.program_state import ProgramState


class InputRules:
	"""Define rules and defaults for input parsing."""

	REQUIRED_SECTIONS: Set[str] = {
		"$job",
		"$molecule",
	}

	NO_DUPLICATE_SECTIONS: Set[str] = {
		"$molecule",
		"$isotope",
		"$velocities",
		"$frequency_data",
		"$gaussian_footer",
	}

	MUTUALLY_EXCLUSIVE_SECTIONS: Tuple[Set[str], ...] = ({"$velocities", "$frequency_data"},)

	REQUIRED_JOB_PARAMETERS: Set[str] = {"gaussian_header"}

	ALLOWED_DUPLICATE_PARAMETERS: Set[str] = {
		"fixed_mode_direction",
		"fixed_vibrational_quanta",
	}

	MUTUALLY_EXCLUSIVE_JOB_PARAMETERS: Tuple[Set[str], ...] = (
		{"gaussian_header", "qchem_options"},  # as an example
	)

	# Parameters with default values (for display purposes)
	PARAMETER_DEFAULTS: Dict[str, str] = {
		"max_steps": "no_limit",
		"phase": "random",
		"program": "gaussian16",
		"integration_algorithm": "verlet",
		"step_size": "1.00 fs",
		"temperature": "298.15 K",
		"energy_boost": "off",
		"oscillator_type": "quasiclassical",
		"geometry_displacement": "off",
		"rotational_energy": "off",
	}


def tokenize_input(input_lines: List[str]) -> List[List[str]]:
	"""Tokenize input lines efficiently.

	Args:
		input_lines: List of input file lines

	Returns:
		List of tokenized lines
	"""
	return [line.split(maxsplit=1) for line in (line.split("#", maxsplit=1)[0].strip() for line in input_lines) if line]


@lru_cache(maxsize=128)
def get_section_tokens(tokenized_lines: Tuple[Tuple[str, ...], ...], section: str) -> List[List[str]]:
	"""Extract tokens for a specific section.

	Args:
		tokenized_lines: Tuple of tokenized lines
		section: Section identifier

	Returns:
		List of tokens for the section
	"""
	tokens = []
	in_section = False

	for line in tokenized_lines:
		if not line:
			continue

		if line[0].casefold() == section:
			in_section = True
			continue
		elif line[0].casefold() == "$end":
			in_section = False
			continue

		if in_section:
			tokens.append(list(line))

	return tokens


def validate_sections(token_keys: List[str]) -> None:
	"""Validate section requirements and constraints.

	Args:
		token_keys: List of section identifiers

	Raises:
		InputError: If validation fails
	"""
	# Check required sections
	missing = InputRules.REQUIRED_SECTIONS - set(token_keys)
	if missing:
		raise exceptions.InputError(f"Could not find {missing.pop()} section.")

	# Check duplicate sections
	for section in InputRules.NO_DUPLICATE_SECTIONS:
		if token_keys.count(section) > 1:
			raise exceptions.InputError(f"Multiple {section} sections.")

	# Check mutually exclusive sections
	for m_e_set in InputRules.MUTUALLY_EXCLUSIVE_SECTIONS:
		if len(m_e_set.intersection(token_keys)) > 1:
			raise exceptions.InputError(f"{str(tuple(m_e_set))[1:-1]} are mutually exclusive.")


def validate_job_parameters(job_parameters: List[str]) -> None:
	"""Validate job parameter requirements and constraints.

	Args:
		job_parameters: List of job parameter names

	Raises:
		InputError: If validation fails
	"""
	# Check required parameters
	missing = InputRules.REQUIRED_JOB_PARAMETERS - set(job_parameters)
	if missing:
		raise exceptions.InputError(f"Could not find the required {missing.pop()} parameter in the $job section.")

	# Check mutually exclusive parameters
	for m_e_set in InputRules.MUTUALLY_EXCLUSIVE_JOB_PARAMETERS:
		if len(m_e_set.intersection(job_parameters)) > 1:
			raise exceptions.InputError(f"{str(tuple(m_e_set))[1:-1]} are mutually exclusive.")

	# Check duplicate parameters
	for param in set(job_parameters) - InputRules.ALLOWED_DUPLICATE_PARAMETERS:
		if job_parameters.count(param) > 1:
			raise exceptions.InputError(f"The '{param}' parameter can only be listed once.")


def parse_molecule_data(molecule_tokens: List[List[str]], program_state: ProgramState) -> None:
	"""Parse molecule section data.

	Args:
		molecule_tokens: List of molecule section tokens
		program_state: ProgramState to update

	Raises:
		InputError: If parsing fails
	"""
	try:
		charge_and_spin = molecule_tokens.pop(0)
		program_state.charge = int(charge_and_spin[0])
		program_state.spin = int(charge_and_spin[1])
	except (IndexError, ValueError):
		raise exceptions.InputError("Could not find charge and/or spin multiplicity in the $molecule section.")

	program_state.number_atoms = len(molecule_tokens)

	for atom_token in molecule_tokens:
		try:
			program_state.atoms.append(atom.Atom.from_symbol(atom_token[0]))
			x, y, z = map(float, atom_token[1].split())
			program_state.input_structure.append(x, y, z, enums.DistanceUnits.ANGSTROM)
		except (IndexError, KeyError, ValueError):
			raise exceptions.InputError(f"Could not interpret '{'  '.join(atom_token)}' in the $molecule section.")


def parse_input(input_iterable: Union[List[str], IO[str]], program_state: ProgramState) -> None:
	"""Parse input file and populate a ProgramState object.

	Args:
		input_iterable: Either a list of strings or a file-like object containing input
		program_state: ProgramState object to populate with parsed data

	Raises:
		InputError: If input format is invalid or required sections are missing
	"""
	# Convert input to lines
	input_lines = input_iterable.readlines() if isinstance(input_iterable, io.IOBase) else input_iterable
	if not isinstance(input_lines, list):
		raise exceptions.InputError("Unrecognized input iterable.")

	# Print input file
	print("### Input File ---------------------------------------------------")
	print("".join(input_lines))
	print()

	# Tokenize input
	tokenized_lines = tokenize_input(input_lines)
	token_keys = [tokens[0].casefold() for tokens in tokenized_lines]

	# Validate sections
	validate_sections(token_keys)

	# Extract section tokens
	job_tokens = get_section_tokens(tuple(tuple(line) for line in tokenized_lines), "$job")
	molecule_tokens = get_section_tokens(tuple(tuple(line) for line in tokenized_lines), "$molecule")
	isotope_tokens = get_section_tokens(tuple(tuple(line) for line in tokenized_lines), "$isotope")
	velocities_tokens = get_section_tokens(tuple(tuple(line) for line in tokenized_lines), "$velocities")
	frequency_data_tokens = get_section_tokens(tuple(tuple(line) for line in tokenized_lines), "$frequency_data")

	# Validate and process job parameters
	job_parameters = [tokens[0].casefold() for tokens in job_tokens]
	validate_job_parameters(job_parameters)

	# Parse molecule data
	parse_molecule_data(molecule_tokens, program_state)

	# Process isotope data
	for mass_token in isotope_tokens:
		try:
			index = int(mass_token[0]) - 1
			program_state.atoms[index].change_mass(mass_token[1])
		except (IndexError, KeyError):
			raise exceptions.InputError(f"Could not interpret '{'  '.join(mass_token)}' in the $isotope section.")

	program_state.structures.append(deepcopy(program_state.input_structure))

	# Process job parameters
	for tokens in job_tokens:
		parameter = tokens[0].casefold()
		if parameter in InputRules.PARAMETER_DEFAULTS:
			del InputRules.PARAMETER_DEFAULTS[parameter]
		try:
			job_function = getattr(JobSection, parameter)
		except AttributeError:
			raise exceptions.InputError(f"Invalid parameter '{tokens[0]}' in $job section.")
		options = tokens[1] if len(tokens) > 1 else ""
		job_function(options, program_state)

	# Process gaussian footer
	if "$gaussian_footer" in token_keys:
		in_section = False
		footer_lines = []
		for line in input_lines:
			if "$gaussian_footer" in line:
				in_section = True
			elif in_section and "$end" in line:
				break
			elif in_section:
				footer_lines.append(line)
		program_state.gaussian_footer = "".join(footer_lines)

	# Process frequency data
	try:
		for frequency_token in frequency_data_tokens:
			program_state.frequencies.append(float(frequency_token[0]), enums.FrequencyUnits.RECIP_CM)
			data = frequency_token[1].split()

			reduced_mass = float(data.pop(0))
			program_state.reduced_masses.append(reduced_mass, enums.MassUnits.AMU)

			force_constant = float(data.pop(0))
			program_state.force_constants.append(force_constant, enums.ForceConstantUnits.MILLIDYNE_PER_ANGSTROM)

			current_displacements = containers.Positions()
			for _ in range(program_state.number_atoms):
				x, y, z = map(float, (data.pop(0) for _ in range(3)))
				current_displacements.append(x, y, z, enums.DistanceUnits.ANGSTROM)
			program_state.mode_displacements.append(current_displacements)
	except (IndexError, ValueError):
		raise exceptions.InputError("Could not interpret $frequency_data section.")

	# Process velocity data
	if "$velocities" in token_keys:
		program_state.velocities.append(containers.Velocities())
		try:
			for velocities_token in velocities_tokens:
				x = float(velocities_token[0])
				y, z = map(float, velocities_token[1].split())
				program_state.velocities[0].append(x, y, z, enums.VelocityUnits.METER_PER_SEC)
		except (IndexError, ValueError):
			raise exceptions.InputError("Could not interpret $velocities section.")
		if len(velocities_tokens) != program_state.number_atoms:
			raise exceptions.InputError("Number of atoms in $velocities and $molecule sections does not match.")

	# Set job name
	try:
		name = os.readlink("/proc/self/fd/1").split("/")[-1].split(".")[0]
	except FileNotFoundError:
		name = "MiloJob"
	program_state.job_name = name

	# Print parsing results
	print("### Default Parameters Being Used --------------------------------")
	for parameter, value in InputRules.PARAMETER_DEFAULTS.items():
		print(f"  {parameter}: {value}")
	if not InputRules.PARAMETER_DEFAULTS:
		print("  (No defaults used.)")
	print()
	print("### Random Seed --------------------------------------------------")
	print(f"  {program_state.random.seed}")
	print()
	print("### Atomic Mass Data ---------------------------------------------")
	for i, atom_ in enumerate(program_state.atoms, 1):
		print(f"  {i:< 3d}  {atom_}")
	print()


class JobSection:
	"""Handle parsing and validation of job section parameters."""

	@staticmethod
	def current_step(options, program_state):
		"""Populate program_state.current_step from options."""
		err_msg = f"Could not interpret 'current_step {options}'. Expected 'current_step int'."
		try:
			program_state.current_step = int(options)
		except ValueError:
			raise exceptions.InputError(err_msg)

	@staticmethod
	def energy_boost(options, program_state):
		"""Populate program_state.energy_boost from options."""
		err_msg = (
			f"Could not interpret parameter 'energy_boost {options}'. "
			"Expected 'energy_boost on min max' or 'energy_boost off'."
		)
		if options.casefold() == "off":
			program_state.energy_boost = enums.EnergyBoost.OFF
		elif options.split()[0].casefold() == "on":
			try:
				program_state.energy_boost = enums.EnergyBoost.ON
				min, max = float(options.split()[1]), float(options.split()[2])
				if min > max:
					min, max = max, min
				program_state.energy_boost_min = min
				program_state.energy_boost_max = max
			except (IndexError, ValueError):
				raise exceptions.InputError(err_msg)
		else:
			raise exceptions.InputError(err_msg)

	@staticmethod
	def fixed_mode_direction(options: str, program_state: ProgramState) -> None:
		"""Set fixed mode direction.

		Args:
			options: String containing mode index and direction (1 or -1)
			program_state: Program state to update

		Raises:
			InputError: If options format is invalid
		"""
		err_msg = (
			"Could not interpret parameter 'fixed_mode_direction "
			f"{options}'. Expected 'fixed_mode_direction n 1', or "
			"'fixed_mode_direction n -1', where n is the mode index."
		)
		try:
			mode, direction = [int(x) for x in options.split()]
		except ValueError:
			raise exceptions.InputError(err_msg)
		if mode < 1 or (direction != -1 and direction != 1):
			raise exceptions.InputError(err_msg)
		program_state.fixed_mode_directions[mode] = direction

	@staticmethod
	def fixed_vibrational_quanta(options, program_state):
		"""Add vibrational quantum to fixed_vibrational_quanta."""
		err_msg = (
			"Could not interpret parameter 'fixed_vibrational_quanta "
			f"{options}'. Expected 'fixed_vibrational_quanta n m', "
			"where n is the mode index and m is the vibrational "
			"quantum number (integer >= 0)."
		)
		try:
			mode, quantum_number = [int(x) for x in options.split()]
		except ValueError:
			raise exceptions.InputError(err_msg)
		if mode < 1 or quantum_number < 0:
			raise exceptions.InputError(err_msg)
		program_state.fixed_vibrational_quanta[mode] = quantum_number

	@staticmethod
	def gaussian_header(options, program_state):
		"""Populate program_state.gaussian_header from options."""
		program_state.gaussian_header = options

	@staticmethod
	def gaussian_footer(options, program_state):
		"""Populate program_state.gaussian_header from options."""
		program_state.gaussian_footer = options.replace("\\n", "\n")

	@staticmethod
	def geometry_displacement(options, program_state):
		"""Populate program_state.geometry_displacement_type from options."""
		err_msg = (
			"Could not interpret parameter 'geometry_displacement "
			f"{options}'. Expected 'geometry_displacement edge_weighted"
			"', 'geometry_displacement gaussian', 'geometry_displacemen"
			"t uniform' or 'geometry_displacement off'."
		)
		if options.casefold() == "edge_weighted":
			program_state.geometry_displacement_type = enums.GeometryDisplacement.EDGE_WEIGHTED
		elif options.casefold() == "gaussian":
			program_state.geometry_displacement_type = enums.GeometryDisplacement.GAUSSIAN_DISTRIBUTION
		elif options.casefold() == "uniform":
			program_state.geometry_displacement_type = enums.GeometryDisplacement.UNIFORM
		elif options.casefold() == "off":
			program_state.geometry_displacement_type = enums.GeometryDisplacement.NONE
		else:
			raise exceptions.InputError(err_msg)

	@staticmethod
	def integration_algorithm(options, program_state):
		"""Populate program_state.propagation_algorithm from options."""
		err_msg = (
			f"Could not interpret parameter 'integration_algorithm {options}'. Expected 'verlet' or 'velocity_verlet'."
		)
		if options.casefold() == "verlet":
			program_state.propagation_algorithm = enums.PropagationAlgorithm.VERLET
		elif options.casefold() == "velocity_verlet":
			program_state.propagation_algorithm = enums.PropagationAlgorithm.VELOCITY_VERLET
		else:
			raise exceptions.InputError(err_msg)

	@staticmethod
	def max_steps(options, program_state):
		"""Populate program_state.max_steps from options."""
		err_msg = f"Could not interpret parameter 'max_steps {options}'. Expected 'max_steps integer' or 'no_limit'."
		if options.casefold() == "no_limit":
			program_state.max_steps = None
		else:
			try:
				program_state.max_steps = int(options)
			except ValueError:
				raise exceptions.InputError(err_msg)

	@staticmethod
	def memory(options, program_state):
		"""Populate program_state.memory_amount from options."""
		err_msg = f"Could not interpret parameter 'memory {options}'. Expected 'memory integer'."
		try:
			program_state.memory_amount = int(options)
		except ValueError:
			raise exceptions.InputError(err_msg)

	@staticmethod
	def oscillator_type(options, program_state):
		"""Populate program_state.oscillator_type from options."""
		err_msg = (
			f"Could not interpret parameter 'oscillator_type {options}'"
			". Expected 'oscillator_type classical' or 'oscillator_type"
			" quasiclassical'."
		)
		if options.casefold() == "classical":
			program_state.oscillator_type = enums.OscillatorType.CLASSICAL
		elif options.casefold() == "quasiclassical":
			program_state.oscillator_type = enums.OscillatorType.QUASICLASSICAL
		else:
			raise exceptions.InputError(err_msg)

	@staticmethod
	def phase(options, program_state):
		"""Populate program_state.phase_direction from options."""
		err_msg = (
			f"Could not interpret parameter 'phase {options}'. "
			"Expected 'phase bring_together index1 index2', 'phase "
			"push_apart index1 index2' or 'phase random'."
		)
		if options.casefold() == "random":
			program_state.phase_direction = enums.PhaseDirection.RANDOM
		elif options.split()[0].casefold() == "bring_together":
			program_state.phase_direction = enums.PhaseDirection.BRING_TOGETHER
			try:
				program_state.phase = (int(options.split()[1]), int(options.split()[2]))
			except (IndexError, ValueError):
				raise exceptions.InputError(err_msg)
		elif options.split()[0].casefold() == "push_apart":
			program_state.phase_direction = enums.PhaseDirection.PUSH_APART
			try:
				program_state.phase = (int(options.split()[1]), int(options.split()[2]))
			except (IndexError, ValueError):
				raise exceptions.InputError(err_msg)
		else:
			raise exceptions.InputError(err_msg)

	@staticmethod
	def processors(options, program_state):
		"""Populate program_state.processor_count from options."""
		err_msg = f"Could not interpret parameter 'processors {options}'. Expected 'processors integer'."
		try:
			program_state.processor_count = int(options)
		except ValueError:
			raise exceptions.InputError(err_msg)

	@staticmethod
	def program(options, program_state):
		"""Populate program_state.program_id from options."""
		err_msg = (
			f"Could not interpret parameter 'program {options}'. Expected 'program gaussian16' or 'program gaussian09'."
		)
		if options.casefold() == "gaussian16":
			program_state.program_id = enums.ProgramID.GAUSSIAN_16
		elif options.casefold() == "gaussian09":
			program_state.program_id = enums.ProgramID.GAUSSIAN_09
		else:
			raise exceptions.InputError(err_msg)

	@staticmethod
	def random_seed(options, program_state):
		"""Reset program_state.random seed from options."""
		err_msg = (
			f"Could not interpret parameter 'random_seed {options}'. "
			"Expected 'random_seed integer' or 'random_seed generate'."
		)
		if options.casefold() == "generate":
			program_state.random.reset_seed()
		else:
			try:
				program_state.random.reset_seed(int(options))
			except ValueError:
				raise exceptions.InputError(err_msg)

	@staticmethod
	def rotational_energy(options, program_state):
		"""Populate program_state.add_rotational_energy from options."""
		err_msg = (
			"Could not interpret parameter 'rotational_energy "
			f" {options}. Expected 'rotational_energy on' or "
			"'rotational_energy off'."
		)
		if options.casefold() == "on":
			program_state.add_rotational_energy = enums.RotationalEnergy.YES
		elif options.casefold() == "off":
			program_state.add_rotational_energy = enums.RotationalEnergy.NO
		else:
			raise exceptions.InputError(err_msg)

	@staticmethod
	def step_size(options, program_state):
		"""Populate program_state.step_size from options."""
		err_msg = f"Could not interpret parameter 'step_size {options}'. Expected 'step_size floating-point'."
		try:
			program_state.step_size = containers.Time(float(options), enums.TimeUnits.FEMTOSECOND)
		except ValueError:
			raise exceptions.InputError(err_msg)

	@staticmethod
	def temperature(options, program_state):
		"""Populate program_state.temperature from options."""
		err_msg = f"Could not interpret parameter 'temperature {options}'. Expected 'temperature floating-point'."
		try:
			program_state.temperature = float(options)
		except ValueError:
			raise exceptions.InputError(err_msg)


def main():
	"""Parse input from stdin to check input file validity."""
	import os
	import sys

	from milo_1_0_3 import program_state as ps

	stdout = sys.stdout
	null_output = open(os.devnull, "w")
	sys.stdout = null_output

	program_state = ps.ProgramState()

	try:
		parse_input(sys.stdin, program_state)
	except Exception as e:
		sys.stdout = stdout
		print("Input file is NOT valid.")
		print(e)
	else:
		sys.stdout = stdout
		print("Input file is valid.")

	null_output.close()

	return program_state


if __name__ == "__main__":
	main()
