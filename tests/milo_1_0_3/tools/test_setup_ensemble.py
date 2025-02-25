"""Tests for setup_ensemble module."""

import io
from textwrap import dedent

import pytest

from milo_1_0_3.tools import setup_ensemble


@pytest.fixture
def mock_template_file():
	"""Create a mock template file."""
	content = dedent("""
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
    """).lstrip()
	return io.StringIO(content)


def test_process_template_file(mock_template_file):
	"""Test template file processing."""
	template, memory, procs, gaussian = setup_ensemble.process_template_file(mock_template_file)

	assert memory == 5  # Original memory + 1
	assert procs == 8
	assert gaussian == "g16"
	assert any("random_seed" in line for line in template)


def test_make_input_file(tmp_path):
	"""Test input file creation."""
	template = ["line1\n", "    random_seed             random_seed_placeholder\n", "line3\n"]
	file_path = tmp_path / "test.in"

	setup_ensemble.make_input_file(str(file_path), template, 12345)

	with open(file_path) as f:
		content = f.readlines()
	assert content[0] == "line1\n"
	assert "random_seed             12345" in content[1]
	assert content[2] == "line3\n"


def test_make_submission_script(tmp_path):
	"""Test submission script creation."""
	file_path = tmp_path / "test.sh"

	setup_ensemble.make_submission_script(str(file_path), "01:00:00", 4, 8, "g16")

	with open(file_path) as f:
		content = f.readlines()

	# Check key lines in the submission script
	assert content[0] == "#!/bin/bash\n"
	assert content[1] == "#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8\n"
	assert content[2] == "#SBATCH --mem=4G\n"
	assert content[3] == "#SBATCH -t 01:00:00\n"
	assert "module load g16\n" in content


def test_gaussian09_detection(mock_template_file):
	"""Test detection of Gaussian 09 program."""
	mock_template_file = io.StringIO(
		dedent("""
        $job
            program gaussian09
        $end
    """)
	)

	_, _, _, gaussian = setup_ensemble.process_template_file(mock_template_file)
	assert gaussian == "g09"
