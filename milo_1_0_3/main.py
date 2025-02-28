#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Serves as the main."""

import sys
import traceback
from functools import lru_cache

from milo_1_0_3 import electronic_structure_program_handler as esph
from milo_1_0_3 import force_propagation_handler as fph
from milo_1_0_3 import initial_energy_sampler, input_parser
from milo_1_0_3 import program_state as ps

# Cache frequently used string operations
STEP_FORMAT = "### Step {}: {} fs ".ljust(66, "-")
COORD_FORMAT = "    {:<2} {:15.6f} {:15.6f} {:15.6f}"
VECTOR_FORMAT = "    {:<2} {:15.6e} {:15.6e} {:15.6e}"


@lru_cache(maxsize=1)
def get_header() -> str:
	"""Return cached header string."""
	return """Thank you for using

               ___   ___   ___   ___       _______
              |   |_|   | |   | |   |     |       |
              |         | |   | |   |     |   _   |
              |         | |   | |   |     |  | |  |
              |  ||_||  | |   | |   |___  |  |_|  |
              |  |   |  | |   | |       | |       |
              |__|   |__| |___| |_______| |_______|

Milo is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Milo is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHNATABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Milo. If not, see <http://www.gnu.org/licenses/>.

Copyright 2021 Brigham Young University

You are using Milo 1.0.3 (18 November 2021 Update)

Authors:
Matthew S. Teynor, Nathan Wohlgemuth, Lily Carlson, Johnny Huang,
Samuel L. Pugh, Benjamin O. Grant, R. Spencer Hamilton, Ryan
Carlsen, Daniel H. Ess

Please cite Milo as:
Milo, Revision 1.0.3, M. S. Teynor, N. Wohlgemuth, L. Carlson,
J. Huang, S. L. Pugh, B. O. Grant, R. S. Hamilton, R. Carlsen,
D. H. Ess, Brigham Young University, Provo UT, 2021.
"""


def main():
	"""Run Milo."""
	try:
		print(get_header())

		program_state = ps.ProgramState()
		input_parser.parse_input(sys.stdin, program_state)

		program_handler = esph.get_program_handler(program_state)
		propagation_handler = fph.get_propagation_handler(program_state)

		if not program_state.velocities:
			initial_energy_sampler.generate(program_state)

		print_trajectory_units_header()

		current_time = round(program_state.current_step * program_state.step_size.as_femtosecond(), 10)
		print(STEP_FORMAT.format(program_state.current_step, current_time))

		print_structure(program_state)

		while not end_conditions_met(program_state):
			program_handler.generate_forces(program_state)
			propagation_handler.run_next_step(program_state)

			print_state_info(program_state)

			# Change to next time step
			print()
			program_state.current_step += 1
			current_time = round(program_state.current_step * program_state.step_size.as_femtosecond(), 10)
			print(STEP_FORMAT.format(program_state.current_step, current_time))

			print_structure(program_state)

		print_footer()

		if program_state.output_xyz_file:
			output_xyz_file(program_state)

	except Exception as e:
		print("\n\nOh no! It looks like there was an error! Error message:")
		print(e)
		print("\n\nPython error details:")
		print(traceback.format_exc())
		raise


def end_conditions_met(program_state: ps.ProgramState) -> bool:
	"""Check conditions to see if the program should abort."""
	return bool(program_state.max_steps is not None and program_state.current_step >= program_state.max_steps)


def output_xyz_file(program_state: ps.ProgramState) -> None:
	"""Write .xyz file efficiently using buffered I/O."""
	with open(f"{program_state.job_name}.xyz", "w", buffering=8192) as file:
		starting_step = program_state.current_step - len(program_state.structures) + 1
		for step, structure in enumerate(program_state.structures, start=starting_step):
			file.write(f"{program_state.number_atoms}\n")
			current_time = round(step * program_state.step_size.as_femtosecond(), 10)
			file.write(f"  Step {step}: {current_time} fs\n")
			for atom, (x, y, z) in zip(program_state.atoms, structure.as_angstrom()):
				file.write(f"{atom.symbol} {x:15.6f} {y:15.6f} {z:15.6f}\n")


def print_structure(program_state: ps.ProgramState) -> None:
	"""Print the last structure list in program_state."""
	print("  Coordinates:")
	for atom, position in zip(program_state.atoms, program_state.structures[-1].as_angstrom()):
		print(COORD_FORMAT.format(atom.symbol, *position))


def print_state_info(program_state: ps.ProgramState) -> None:
	"""Print all state information efficiently."""
	# Energy
	print("  SCF Energy:")
	print(f"    {program_state.energies[-1].as_hartree(0):.8f}")

	# Forces
	print("  Forces:")
	for atom, force in zip(program_state.atoms, program_state.forces[-1].as_newton()):
		print(VECTOR_FORMAT.format(atom.symbol, *force))

	# Accelerations
	print("  Accelerations:")
	for atom, acceleration in zip(program_state.atoms, program_state.accelerations[-1].as_meter_per_sec_sqrd()):
		print(VECTOR_FORMAT.format(atom.symbol, *acceleration))

	# Velocities
	print("  Velocities:")
	for atom, velocity in zip(program_state.atoms, program_state.velocities[-1].as_meter_per_sec()):
		print(VECTOR_FORMAT.format(atom.symbol, *velocity))


@lru_cache(maxsize=1)
def get_trajectory_units_header() -> str:
	"""Return cached trajectory units header."""
	return """### Starting Trajectory ----------------------------------------
  Units for trajectory output:
    Coordinates    angstrom
    SCF Energy     hartree
    Forces         newton
    Accelerations  meter/second^2
    Velocities     meter/second
"""


def print_trajectory_units_header() -> None:
	"""Print the units that the data from each trajectory step will use."""
	print(get_trajectory_units_header())


@lru_cache(maxsize=1)
def get_footer() -> str:
	"""Return cached footer string."""
	return "\n\nNormal termination.\nThank you for using Milo!"


def print_footer() -> None:
	"""Print the closing message to the output file."""
	print(get_footer())


if __name__ == "__main__":
	main()
