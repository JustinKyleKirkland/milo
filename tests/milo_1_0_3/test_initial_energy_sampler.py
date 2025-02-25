"""Tests for initial energy sampler module."""

import pytest

from milo_1_0_3 import containers, initial_energy_sampler
from milo_1_0_3 import enumerations as enums
from milo_1_0_3.program_state import ProgramState


@pytest.fixture
def mock_program_state():
	"""Create a mock program state for testing."""
	program_state = ProgramState()
	program_state.frequencies = containers.Frequencies()
	# Append frequencies one at a time
	program_state.frequencies.append(500, enums.FrequencyUnits.RECIP_CM)
	program_state.frequencies.append(1000, enums.FrequencyUnits.RECIP_CM)
	program_state.frequencies.append(1500, enums.FrequencyUnits.RECIP_CM)
	program_state.temperature = 300
	program_state.oscillator_type = enums.OscillatorType.QUASICLASSICAL
	return program_state


def test_calculate_zero_point_energies(mock_program_state):
	"""Test calculation of zero point energies."""
	zpe, total = initial_energy_sampler._calculate_zero_point_energies(mock_program_state)

	assert len(zpe) == 3  # Should match number of frequencies
	assert all(e > 0 for e in zpe.as_joules())  # All energies should be positive
	assert abs(total.as_joules(0) - sum(zpe.as_joules())) < 1e-10  # Total should match sum


def test_sample_zero_temperature(mock_program_state):
	"""Test sampling at zero temperature."""
	mock_program_state.temperature = 0
	zpe, _ = initial_energy_sampler._calculate_zero_point_energies(mock_program_state)
	quantum_numbers = initial_energy_sampler._sample(zpe, mock_program_state)

	assert all(n == 0 for n in quantum_numbers)  # All quantum numbers should be 0 at T=0


def test_energy_boost_bounds(mock_program_state):
	"""Test energy boost boundaries."""
	mock_program_state.energy_boost = enums.EnergyBoost.ON
	mock_program_state.energy_boost_min = 10
	mock_program_state.energy_boost_max = 20

	total_energy = containers.Energies()
	total_energy.append(5, enums.EnergyUnits.KCAL_PER_MOLE)

	# Energy below min should return True to indicate resampling needed
	assert initial_energy_sampler._energy_boost(total_energy, mock_program_state) is True
	assert mock_program_state.temperature > 300  # Temperature should increase
