"""Tests for setup_ensemble module."""

import io
from pathlib import Path
from textwrap import dedent
from typing import TextIO

import pytest

from milo_1_0_3.tools import setup_ensemble

# Test constants
TEST_TEMPLATE = """
$comment
    Test input
$end

$job
    memory 4
    processors 8
    program gaussian16
$end

$molecule
    0 1
    H 0 0 0
    H 1 0 0
$end
"""

TEST_INPUT_TEMPLATE = ["line1\n", "    random_seed             random_seed_placeholder\n", "line3\n"]


@pytest.fixture
def mock_template_file() -> TextIO:
	"""Create a mock template file with Gaussian 16 configuration.

	Returns:
		TextIO: A StringIO object containing the template content.
	"""
	return io.StringIO(dedent(TEST_TEMPLATE).lstrip())


@pytest.fixture
def mock_gaussian09_template() -> TextIO:
	"""Create a mock template file with Gaussian 09 configuration.

	Returns:
		TextIO: A StringIO object containing the Gaussian 09 template.
	"""
	content = dedent("""
        $job
            program gaussian09
        $end
    """)
	return io.StringIO(content)


def test_process_template_file(mock_template_file: TextIO) -> None:
	"""Test template file processing with Gaussian 16 configuration."""
	template, memory, procs, gaussian = setup_ensemble.process_template_file(mock_template_file)

	assert memory == 5  # Original memory + 1
	assert procs == 8
	assert gaussian == "g16"
	assert any("random_seed" in line for line in template)


@pytest.mark.parametrize(
	"seed,expected",
	[
		(12345, "random_seed             12345"),
		(0, "random_seed             0"),
		(999999, "random_seed             999999"),
	],
)
def test_make_input_file(tmp_path: Path, seed: int, expected: str) -> None:
	"""Test input file creation with different random seeds."""
	file_path = tmp_path / "test.in"

	setup_ensemble.make_input_file(str(file_path), TEST_INPUT_TEMPLATE, seed)

	with open(file_path) as f:
		content = f.readlines()

	assert content[0] == "line1\n"
	assert expected in content[1]
	assert content[2] == "line3\n"


@pytest.mark.parametrize(
	"time,mem,cpus,gaussian",
	[
		("01:00:00", 4, 8, "g16"),
		("02:00:00", 8, 16, "g09"),
	],
)
def test_make_submission_script(tmp_path: Path, time: str, mem: int, cpus: int, gaussian: str) -> None:
	"""Test submission script creation with different configurations."""
	file_path = tmp_path / "test.sh"

	setup_ensemble.make_submission_script(str(file_path), time, mem, cpus, gaussian)

	with open(file_path) as f:
		content = f.read().splitlines()

	# Test required headers
	expected_headers = [
		"#!/bin/bash",
		f"#SBATCH --nodes=1 --ntasks=1 --cpus-per-task={cpus}",
		f"#SBATCH --mem={mem}G",
		f"#SBATCH -t {time}",
		"#SBATCH -C 'avx2'",
	]

	for i, expected in enumerate(expected_headers):
		assert content[i] == expected, f"Header mismatch at line {i + 1}"

	# Test module loads
	assert "module load python/3.8" in content
	assert f"module load {gaussian}" in content

	# Test key script components
	script_content = "\n".join(content)
	assert "export TEMPORARY_DIR=/tmp/$SLURM_JOB_ID" in script_content
	assert 'export JOB_SOURCE_DIR="$SLURM_SUBMIT_DIR"' in script_content
	assert "function cleanup" in script_content
	assert "python -m milo_1_0_3" in script_content


def test_gaussian09_detection(mock_gaussian09_template: TextIO) -> None:
	"""Test detection of Gaussian 09 program."""
	_, _, _, gaussian = setup_ensemble.process_template_file(mock_gaussian09_template)
	assert gaussian == "g09"
