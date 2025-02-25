"""Tests for setup_restart module."""

import io
from dataclasses import dataclass
from datetime import datetime

import pytest

from milo_1_0_3.program_state import ProgramState
from milo_1_0_3.tools import setup_restart


@dataclass
class MockAtom:
	"""Mock atom class for testing."""

	symbol: str
	mass: float


@pytest.fixture
def mock_program_state():
	"""Create a mock program state for testing."""
	program_state = ProgramState()
	program_state.number_atoms = 2
	program_state.atoms = [MockAtom("H", 1.008), MockAtom("O", 15.999)]
	return program_state


def test_get_isotope_section(mock_program_state):
	"""Test isotope section generation."""
	result = setup_restart.get_isotope_section(mock_program_state)

	# Check formatting
	lines = result.split("\n")
	assert len(lines) >= 2  # At least 2 atoms
	assert "     1     1.00800" in lines[0]  # Check first atom
	assert "     2    15.99900" in lines[1]  # Check second atom


def test_get_job_section():
	"""Test job section generation."""
	old_input = ["$job\n", "    random_seed 12345\n", "    current_step 100\n", "    temperature 300\n", "$end\n"]
	result = setup_restart.get_job_section(old_input, 200, "54321")

	assert "current_step            200" in result
	assert "random_seed             54321" in result
	assert "temperature 300" in result
	assert "random_seed 12345" not in result
	assert "current_step 100" not in result


def test_get_output_comment():
	"""Test output comment generation."""
	test_file = io.StringIO()
	test_file.name = "test_output.txt"

	result = setup_restart.get_output_comment(test_file, 100)

	assert "step 100" in result
	assert "test_output.txt" in result
	assert datetime.now().strftime("%d-%b-%Y") in result


def test_print_section():
	"""Test section printing."""
	output = io.StringIO()
	setup_restart.print_section(output, "test", "content")

	result = output.getvalue()
	assert "$test\n" in result
	assert "content\n" in result
	assert "$end\n" in result
