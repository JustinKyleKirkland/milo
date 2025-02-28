#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create .xyz files from Gaussian output files.

This script processes all .out files in the current directory and creates
corresponding .xyz files containing molecular coordinates from each geometry
optimization step.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, TextIO


@dataclass
class CoordinateBlock:
	"""Container for coordinate block data."""

	lines: List[str]


def extract_coordinates(out_file: TextIO) -> Iterator[CoordinateBlock]:
	"""
	Extract coordinate blocks from Gaussian output file using generator pattern.

	Args:
		out_file: File handle for the Gaussian output file

	Yields:
		CoordinateBlock objects containing coordinate data
	"""
	current_block: List[str] = []
	in_coordinates = False
	skip_next = False

	for line in out_file:
		if "  Coordinates:" in line:
			in_coordinates = True
			skip_next = True
			current_block = []
		elif "  SCF Energy:" in line or "Normal termination." in line:
			if current_block:
				yield CoordinateBlock(current_block)
				current_block = []
			in_coordinates = False
		elif in_coordinates:
			if skip_next:
				skip_next = False
				continue
			if line := line.strip():  # Walrus operator for efficiency
				current_block.append(line)


def write_xyz_file(xyz_path: str, coordinate_blocks: Iterator[CoordinateBlock]) -> None:
	"""
	Write coordinate blocks to XYZ file efficiently using context manager.

	Args:
		xyz_path: Path to output XYZ file
		coordinate_blocks: Iterator of coordinate blocks to write
	"""
	first_block = next(coordinate_blocks, None)
	if not first_block:
		return

	num_atoms = len(first_block.lines)
	with open(xyz_path, mode="w", buffering=8192) as xyz_file:  # Use buffered I/O
		# Write first block
		xyz_file.write(f"{num_atoms}\n\n")
		xyz_file.writelines(f"{line}\n" for line in first_block.lines)

		# Write remaining blocks
		for block in coordinate_blocks:
			xyz_file.write(f"{num_atoms}\n\n")
			xyz_file.writelines(f"{line}\n" for line in block.lines)


def process_out_file(out_path: str) -> None:
	"""
	Process a single Gaussian output file and create corresponding XYZ file.

	Args:
		out_path: Path to Gaussian output file
	"""
	xyz_path = Path(out_path).with_suffix(".xyz")

	with open(out_path, mode="r", buffering=8192) as out_file:  # Use buffered I/O
		coordinate_blocks = extract_coordinates(out_file)
		write_xyz_file(str(xyz_path), coordinate_blocks)


def main() -> None:
	"""Convert all Gaussian output files in current directory to XYZ format."""
	out_files = [f for f in Path(".").glob("*.out") if f.is_file()]

	for out_file in out_files:
		process_out_file(str(out_file))


if __name__ == "__main__":
	main()
