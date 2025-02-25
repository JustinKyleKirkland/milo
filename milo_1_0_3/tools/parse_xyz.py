#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create .xyz files from Gaussian output files.

This script processes all .out files in the current directory and creates
corresponding .xyz files containing molecular coordinates from each geometry
optimization step.
"""

import os
from typing import List, TextIO


def extract_coordinates(out_file: TextIO) -> List[List[str]]:
	"""
	Extract coordinate blocks from Gaussian output file.

	Args:
		out_file: File handle for the Gaussian output file

	Returns:
		List of coordinate blocks, where each block is a list of coordinate lines
	"""
	coordinate_blocks: List[List[str]] = []
	current_block: List[str] = []
	in_coordinates = False
	skip_next = False

	for line in out_file:
		if "  Coordinates:" in line:
			in_coordinates = True
			skip_next = True  # Skip the next line (column headers)
			current_block = []
		elif "  SCF Energy:" in line or "Normal termination." in line:
			if current_block:
				coordinate_blocks.append(current_block)
				current_block = []
			in_coordinates = False
		elif in_coordinates:
			if skip_next:
				skip_next = False
				continue
			if line.strip():  # Only append non-empty lines
				current_block.append(line.strip())

	return coordinate_blocks


def write_xyz_file(xyz_path: str, coordinate_blocks: List[List[str]]) -> None:
	"""
	Write coordinate blocks to XYZ file.

	Args:
		xyz_path: Path to output XYZ file
		coordinate_blocks: List of coordinate blocks to write
	"""
	with open(xyz_path, mode="w") as xyz_file:
		num_atoms = len(coordinate_blocks[0]) if coordinate_blocks else 0

		for block in coordinate_blocks:
			xyz_file.write(f"{num_atoms}\n\n")
			for line in block:
				xyz_file.write(f"{line}\n")


def process_out_file(out_path: str) -> None:
	"""
	Process a single Gaussian output file and create corresponding XYZ file.

	Args:
		out_path: Path to Gaussian output file
	"""
	xyz_path = out_path[:-4] + ".xyz"  # Replace .out with .xyz

	with open(out_path, mode="r") as out_file:
		coordinate_blocks = extract_coordinates(out_file)
		write_xyz_file(xyz_path, coordinate_blocks)


def main() -> None:
	"""Convert all Gaussian output files in current directory to XYZ format."""
	out_files = [f for f in os.listdir(".") if os.path.isfile(f) and f.endswith(".out")]

	for out_file in out_files:
		process_out_file(out_file)


if __name__ == "__main__":
	main()
