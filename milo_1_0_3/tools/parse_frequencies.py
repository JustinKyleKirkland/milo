#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create a Milo input file from a Gaussian frequency calculation.

This script parses Gaussian 09/16 high-precision frequency calculation output files
and converts them to Milo input format. The input must be generated with the
'freq=(hpmodes)' option in Gaussian.
"""

import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime
from functools import wraps
from typing import IO, Any, Callable, Dict, List, TextIO

from milo_1_0_3 import atom, containers, exceptions
from milo_1_0_3 import enumerations as enums
from milo_1_0_3 import program_state as ps


def error_handler(func: Callable) -> Callable:
	"""Decorator to handle parsing errors consistently.

	Args:
		func: Function to wrap with error handling

	Returns:
		Wrapped function with error handling
	"""

	@wraps(func)
	def wrapper(*args, **kwargs) -> Any:
		try:
			return func(*args, **kwargs)
		except Exception as e:
			raise exceptions.InputError(f"Error in {func.__name__}: {str(e)}")

	return wrapper


@error_handler
def parse_gaussian_header(input_file: TextIO, program_state: ps.ProgramState) -> None:
	"""Parse Gaussian header from frequency file."""
	past_warning = False
	lines: List[str] = []

	for line in input_file:
		if "*****" in line:
			past_warning = True
		if past_warning and "-----" in line:
			for next_line in input_file:
				if "-----" in next_line:
					break
				lines.append(next_line[1:].strip())
			clean_line = "".join(lines).strip()

			if "hpmodes" not in clean_line.casefold():
				raise exceptions.InputError("Must be high-precision frequency calculation. Use 'freq=hpmodes'.")

			tokens = [x for x in clean_line.split() if not any(kw in x.casefold() for kw in ("#", "opt", "freq"))]
			program_state.gaussian_header = " ".join(tokens)
			return

	raise exceptions.InputError("Error parsing gaussian_header.")


@error_handler
def parse_gaussian_charge_spin(input_file: TextIO, program_state: ps.ProgramState) -> None:
	"""Parse charge and spin multiplicity from frequency file."""
	for line in input_file:
		if "Charge =" in line:
			tokens = line.split()
			program_state.charge = int(tokens[2])
			program_state.spin = int(tokens[5])
			return

	raise exceptions.InputError("Error parsing charge and spin multiplicity.")


@error_handler
def parse_gaussian_molecule_data(input_file: TextIO, program_state: ps.ProgramState) -> None:
	"""Parse molecular geometry data from frequency file."""
	for line in input_file:
		if "Harmonic frequencies (cm**-1)" in line:
			return

		if "Input orientation:" in line or "Standard orientation:" in line:
			positions = containers.Positions()

			for coord_line in input_file:
				if any(x in coord_line for x in ("Rotational constants", "Distance matrix")):
					break

				coords = coord_line.split()
				if coords and coords[0].isnumeric():
					x, y, z = map(float, coords[3:6])
					positions.append(x, y, z, enums.DistanceUnits.ANGSTROM)

			program_state.input_structure = positions

	raise exceptions.InputError("Error parsing molecule data.")


@error_handler
def parse_gaussian_frequency_data(input_file: TextIO, program_state: ps.ProgramState) -> None:
	"""Parse vibrational frequency data from frequency file."""
	data_map: Dict[str, List[float]] = defaultdict(list)
	has_started = False

	for line in input_file:
		if "Frequencies ---" in line:
			has_started = True
			data_map["frequencies"].extend(map(float, line.split()[2:]))
		elif "Reduced masses ---" in line:
			data_map["masses"].extend(map(float, line.split()[3:]))
		elif "Force constants ---" in line:
			data_map["forces"].extend(map(float, line.split()[3:]))
		elif "Coord Atom Element:" in line:
			data_columns: List[List[str]] = []

			for coord_line in input_file:
				if "Harmonic frequencies (cm**-1)" in coord_line or coord_line.isspace():
					break
				data_columns.append(coord_line.split()[3:])

			for frequency in zip(*data_columns):
				displacement = containers.Positions()
				coords = [float(x) for x in frequency]

				for x, y, z in zip(*[iter(coords)] * 3):
					displacement.append(x, y, z, enums.DistanceUnits.ANGSTROM)

				program_state.mode_displacements.append(displacement)

		elif has_started and "activities (A**4/AMU)" in line:
			# Add parsed data to program state
			for freq in data_map["frequencies"]:
				program_state.frequencies.append(freq, enums.FrequencyUnits.RECIP_CM)
			for mass in data_map["masses"]:
				program_state.reduced_masses.append(mass, enums.MassUnits.AMU)
			for force in data_map["forces"]:
				program_state.force_constants.append(force, enums.ForceConstantUnits.MILLIDYNE_PER_ANGSTROM)
			return

	raise exceptions.InputError("Error parsing frequency data.")


@error_handler
def parse_gaussian_isotope_data(input_file: TextIO, program_state: ps.ProgramState) -> None:
	"""Parse isotope and atomic number data from frequency file."""
	for line in input_file:
		if "Thermochemistry" in line:
			atoms: List[atom.Atom] = []

			for mass_line in input_file:
				if "Molecular mass" in mass_line:
					break

				tokens = mass_line.split()
				if tokens and tokens[0] == "Atom":
					atomic_number = int(tokens[5])
					new_atom = atom.Atom.from_atomic_number(atomic_number)
					new_atom.change_mass(tokens[8])
					atoms.append(new_atom)

			program_state.atoms = atoms
			return

	raise exceptions.InputError("Error parsing isotope data.")


def print_section(output_file: TextIO, section_name: str, content: str) -> None:
	"""Print a formatted section to the output file."""
	print(f"${section_name}", file=output_file)
	print(content, file=output_file)
	print("$end\n", file=output_file)


def print_job_section(output_file: TextIO, program_state: ps.ProgramState, verbose: int) -> None:
	"""Print the $job section with Gaussian header and optional parameters."""
	lines = [f"    gaussian_header         {program_state.gaussian_header}"]

	parameter_groups = {
		1: [
			"    # step_size               1.00  # in femtoseconds",
			"    # max_steps               100  # or no_limit",
			"    # temperature             298.15  # in kelvin",
			"    # phase                   bring_together n m  #  or  push_apart n m",
			"    # memory                  24  # in GB",
			"    # processors              24",
			"    # random_seed             generate  # or an integer",
		],
		2: [
			"    # oscillator_type         quasiclassical",
			"    # geometry_displacement   off",
			"    # rotational_energy       off",
			"    # energy_boost            off",
			"    # integration_algorithm   verlet",
			"    # program                 gaussian16",
			"    # fixed_mode_direction    n 1  # or n -1",
		],
	}

	for level in range(1, verbose + 1):
		if level in parameter_groups:
			lines.extend(parameter_groups[level])

	print_section(output_file, "job", "\n".join(lines))


def print_molecule_section(output_file: TextIO, program_state: ps.ProgramState) -> None:
	"""Print the $molecule and $isotope sections."""
	# Molecule section
	lines = [f"    {program_state.charge} {program_state.spin}"]
	lines.extend(
		f"    {atom_obj.symbol} {x:12.6f} {y:12.6f} {z:12.6f}"
		for atom_obj, (x, y, z) in zip(program_state.atoms, program_state.input_structure.as_angstrom())
	)
	print_section(output_file, "molecule", "\n".join(lines))

	# Isotope section
	lines = [f"    {i:< 3d} {atom_obj.mass:10.5f}" for i, atom_obj in enumerate(program_state.atoms, 1)]
	print_section(output_file, "isotope", "\n".join(lines))


def print_frequency_data_section(output_file: TextIO, program_state: ps.ProgramState) -> None:
	"""Print the $frequency_data section."""
	lines = []
	for freq, mass, force, mode in zip(
		program_state.frequencies.as_recip_cm(),
		program_state.reduced_masses.as_amu(),
		program_state.force_constants.as_millidyne_per_angstrom(),
		program_state.mode_displacements,
	):
		lines.append(f"   {freq:10.4f} {mass:7.4f} {force:7.4f}")
		lines.extend(f"  {x:8.5f} {y:8.5f} {z:8.5f}" for x, y, z in mode.as_angstrom())
		lines.append("")

	if lines:
		lines.pop()  # Remove last empty line
	print_section(output_file, "frequency_data", "\n".join(lines))


def print_output_comment(input_file: IO, output_file: TextIO) -> None:
	"""Print a comment section with input file name and parsing timestamp."""
	comment = ["    Frequency and molecule data parsed "]

	if input_file != sys.stdin:
		comment.append(f"from {os.path.basename(input_file.name)} ")
	else:
		try:
			name = os.readlink("/proc/self/fd/0").split("/")[-1].split(".")[0]
			comment.append(f"from {name} ")
		except FileNotFoundError:
			comment.append("from <stdin> ")

	comment.append(datetime.now().strftime("on %d-%b-%Y at %X"))
	print_section(output_file, "comment", "".join(comment))


def main() -> None:
	"""Parse frequency file and create Milo input."""
	parser = argparse.ArgumentParser(
		description="Make a Milo input file from a high-precision Gaussian frequency calculation."
	)
	parser.add_argument(
		"infile",
		nargs="?",
		type=argparse.FileType("r"),
		default=sys.stdin,
		help="Frequency calculation file. <stdin> by default.",
	)
	parser.add_argument(
		"outfile",
		nargs="?",
		type=argparse.FileType("w"),
		default=sys.stdout,
		help="New Milo input file. <stdout> by default.",
	)
	parser.add_argument(
		"-v",
		"--verbose",
		action="count",
		default=0,
		help="Print other parameters in $job section. -v for common parameters, -vv for all parameters",
	)

	args = parser.parse_args()
	program_state = ps.ProgramState()

	try:
		parse_gaussian_header(args.infile, program_state)
		parse_gaussian_charge_spin(args.infile, program_state)
		parse_gaussian_molecule_data(args.infile, program_state)
		parse_gaussian_frequency_data(args.infile, program_state)
		parse_gaussian_isotope_data(args.infile, program_state)

		print_job_section(args.outfile, program_state, args.verbose)
		print_output_comment(args.infile, args.outfile)
		print_molecule_section(args.outfile, program_state)
		print_frequency_data_section(args.outfile, program_state)

	except Exception as e:
		print(f"Error: {str(e)}", file=sys.stderr)
		print("\nPython error details:", file=sys.stderr)
		raise


if __name__ == "__main__":
	main()
