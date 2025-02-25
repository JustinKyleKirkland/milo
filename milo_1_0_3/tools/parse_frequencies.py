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
from datetime import datetime
from typing import IO, List, TextIO

from milo_1_0_3 import atom, containers, exceptions
from milo_1_0_3 import enumerations as enums
from milo_1_0_3 import program_state as ps


def parse_gaussian_header(input_file: TextIO, program_state: ps.ProgramState) -> None:
	"""
	Parse Gaussian header from frequency file.

	Args:
		input_file: File handle for the Gaussian output file
		program_state: Program state object to store parsed data

	Raises:
		InputError: If not a high-precision frequency calculation or parsing fails
	"""
	past_warning = False
	lines: List[str] = []

	for line in input_file:
		if "*****" in line:
			past_warning = True
		if past_warning and "-----" in line:
			for next_line in input_file:
				if "-----" in next_line:
					break
				lines.append(next_line[1:].strip("\n"))
			clean_line = "".join(lines).strip()

			if "hpmodes" not in clean_line.casefold():
				raise exceptions.InputError("Must be high-precision frequency calculation. Use 'freq=hpmodes'.")

			tokens = [
				x
				for x in clean_line.split()
				if "#" not in x and "opt" not in x.casefold() and "freq" not in x.casefold()
			]
			program_state.gaussian_header = " ".join(tokens)
			return

	raise exceptions.InputError("Error parsing gaussian_header.")


def parse_gaussian_charge_spin(input_file: TextIO, program_state: ps.ProgramState) -> None:
	"""
	Parse charge and spin multiplicity from frequency file.

	Args:
		input_file: File handle for the Gaussian output file
		program_state: Program state object to store parsed data

	Raises:
		InputError: If parsing fails
	"""
	for line in input_file:
		if "Charge =" in line:
			tokens = line.split()
			program_state.charge = int(tokens[2])
			program_state.spin = int(tokens[5])
			return

	raise exceptions.InputError("Error parsing charge and spin multiplicity.")


def parse_gaussian_molecule_data(input_file: TextIO, program_state: ps.ProgramState) -> None:
	"""
	Parse molecular geometry data from frequency file.

	Will use the last "Standard orientation:" in the log file, or the last
	"Input orientation:" if there is no "Standard orientation:" (e.g., when
	using the nosymm keyword).

	Args:
		input_file: File handle for the Gaussian output file
		program_state: Program state object to store parsed data

	Raises:
		InputError: If parsing fails
	"""
	for line in input_file:
		if "Harmonic frequencies (cm**-1)" in line:
			return

		if "Input orientation:" in line or "Standard orientation:" in line:
			positions = containers.Positions()

			for coord_line in input_file:
				if "Rotational constants" in coord_line or "Distance matrix" in coord_line:
					break

				coords = coord_line.split()
				if coords[0].isnumeric():
					x, y, z = map(float, coords[3:6])
					positions.append(x, y, z, enums.DistanceUnits.ANGSTROM)

			program_state.input_structure = positions

	raise exceptions.InputError("Error parsing molecule data.")


def parse_gaussian_frequency_data(input_file: TextIO, program_state: ps.ProgramState) -> None:
	"""
	Parse vibrational frequency data from frequency file.

	Extracts the first occurrence of high-precision frequency data.

	Args:
		input_file: File handle for the Gaussian output file
		program_state: Program state object to store parsed data

	Raises:
		InputError: If parsing fails
	"""
	has_started = False

	for line in input_file:
		if "Frequencies ---" in line:
			has_started = True
			for freq in line.split()[2:]:
				program_state.frequencies.append(float(freq), enums.FrequencyUnits.RECIP_CM)

		elif "Reduced masses ---" in line:
			for mass in line.split()[3:]:
				program_state.reduced_masses.append(float(mass), enums.MassUnits.AMU)

		elif "Force constants ---" in line:
			for force in line.split()[3:]:
				program_state.force_constants.append(float(force), enums.ForceConstantUnits.MILLIDYNE_PER_ANGSTROM)

		elif "Coord Atom Element:" in line:
			data_columns: List[List[str]] = []

			for coord_line in input_file:
				if "Harmonic frequencies (cm**-1)" in coord_line or "                    " in coord_line:
					break
				data_columns.append(coord_line.split()[3:])

			data_rows = list(zip(*data_columns))

			for frequency in data_rows:
				displacement = containers.Positions()
				coords = [float(x) for x in frequency]

				for x, y, z in zip(*[iter(coords)] * 3):
					displacement.append(x, y, z, enums.DistanceUnits.ANGSTROM)

				program_state.mode_displacements.append(displacement)

		elif has_started and "activities (A**4/AMU)" in line:
			return

	raise exceptions.InputError("Error parsing frequency data.")


def parse_gaussian_isotope_data(input_file: TextIO, program_state: ps.ProgramState) -> None:
	"""
	Parse isotope and atomic number data from frequency file.

	Args:
		input_file: File handle for the Gaussian output file
		program_state: Program state object to store parsed data

	Raises:
		InputError: If parsing fails
	"""
	for line in input_file:
		if "Thermochemistry" in line:
			atoms: List[atom.Atom] = []

			for mass_line in input_file:
				if "Molecular mass" in mass_line:
					break

				tokens = mass_line.split()
				if tokens[0] == "Atom":
					atomic_number = int(tokens[5])
					new_atom = atom.Atom.from_atomic_number(atomic_number)
					new_atom.change_mass(tokens[8])
					atoms.append(new_atom)

			program_state.atoms = atoms
			return

	raise exceptions.InputError("Error parsing isotope data.")


def print_section(output_file: TextIO, section_name: str, content: str) -> None:
	"""
	Print a formatted section to the output file.

	Args:
		output_file: File handle for output
		section_name: Name of the section
		content: Content to write in the section
	"""
	print(f"${section_name}", file=output_file)
	print(content, file=output_file)
	print("$end\n", file=output_file)


def print_job_section(output_file: TextIO, program_state: ps.ProgramState, verbose: int) -> None:
	"""
	Print the $job section with Gaussian header and optional parameters.

	Args:
		output_file: File handle for output
		program_state: Program state containing parsed data
		verbose: Verbosity level (0=minimal, 1=common params, 2=all params)
	"""
	lines = [f"    gaussian_header         {program_state.gaussian_header}"]

	if verbose >= 1:
		lines.extend(
			[
				"    # step_size               1.00  # in femtoseconds",
				"    # max_steps               100  # or no_limit",
				"    # temperature             298.15  # in kelvin",
				"    # phase                   bring_together n m  #  or  push_apart n m",
				"    # memory                  24  # in GB",
				"    # processors              24",
				"    # random_seed             generate  # or an integer",
			]
		)

	if verbose >= 2:
		lines.extend(
			[
				"    # oscillator_type         quasiclassical",
				"    # geometry_displacement   off",
				"    # rotational_energy       off",
				"    # energy_boost            off",
				"    # integration_algorithm   verlet",
				"    # program                 gaussian16",
				"    # fixed_mode_direction    n 1  # or n -1",
			]
		)

	print_section(output_file, "job", "\n".join(lines))


def print_molecule_section(output_file: TextIO, program_state: ps.ProgramState) -> None:
	"""
	Print the $molecule and $isotope sections.

	Args:
		output_file: File handle for output
		program_state: Program state containing parsed data
	"""
	# Molecule section
	lines = [f"    {program_state.charge} {program_state.spin}"]

	for atom_obj, (x, y, z) in zip(program_state.atoms, program_state.input_structure.as_angstrom()):
		lines.append(f"    {atom_obj.symbol} {x:12.6f} {y:12.6f} {z:12.6f}")

	print_section(output_file, "molecule", "\n".join(lines))

	# Isotope section
	lines = [f"    {i:< 3d} {atom_obj.mass:10.5f}" for i, atom_obj in enumerate(program_state.atoms, 1)]
	print_section(output_file, "isotope", "\n".join(lines))


def print_frequency_data_section(output_file: TextIO, program_state: ps.ProgramState) -> None:
	"""
	Print the $frequency_data section.

	Args:
		output_file: File handle for output
		program_state: Program state containing parsed data
	"""
	lines = []

	for freq, mass, force, mode in zip(
		program_state.frequencies.as_recip_cm(),
		program_state.reduced_masses.as_amu(),
		program_state.force_constants.as_millidyne_per_angstrom(),
		program_state.mode_displacements,
	):
		lines.append(f"   {freq:10.4f} {mass:7.4f} {force:7.4f}")

		for x, y, z in mode.as_angstrom():
			lines.append(f"  {x:8.5f} {y:8.5f} {z:8.5f}")

		lines.append("\n")

	lines.pop()  # Remove last newline
	print_section(output_file, "frequency_data", "".join(lines))


def print_output_comment(input_file: IO, output_file: TextIO) -> None:
	"""
	Print a comment section with input file name and parsing timestamp.

	Args:
		input_file: Input file handle
		output_file: Output file handle
	"""
	comment = ["    Frequency and molecule data parsed "]

	if input_file != sys.stdin:
		comment.extend(["from ", os.path.basename(input_file.name), " "])
	else:
		try:
			name = os.readlink("/proc/self/fd/0").split("/")[-1].split(".")[0]
			comment.extend(["from ", name, " "])
		except FileNotFoundError:
			comment.append("from <stdin> ")

	comment.append(datetime.now().strftime("on %d-%b-%Y at %X"))
	print_section(output_file, "comment", "".join(comment))


def main() -> None:
	"""Parse frequency file and create Milo input."""
	parser = argparse.ArgumentParser(
		description=("Make a Milo input file from a high-precision Gaussian frequency calculation.\n")
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
		print("Oh no! It looks like there was an error!")
		print("Error message:", e)
		print("\nPython error details:")
		raise


if __name__ == "__main__":
	main()
