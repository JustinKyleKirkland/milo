#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate initial velocities based on frequency data."""

import math
from functools import lru_cache
from typing import Dict, List, Tuple

import numpy as np

from milo_1_0_3 import containers, exceptions
from milo_1_0_3 import enumerations as enums
from milo_1_0_3 import scientific_constants as sc
from milo_1_0_3.program_state import ProgramState


@lru_cache(maxsize=128)
def _get_conversion_factors() -> Dict[str, float]:
	"""Cache commonly used conversion factors."""
	return {
		"units_ke": sc.AMU_TO_KG * math.pow(sc.ANGSTROM_TO_METER, 2) * sc.JOULE_TO_KCAL_PER_MOLE,
		"classical_energy": 0.5 * sc.h * sc.c * sc.CLASSICAL_SPACING,
		"meter_conversion": sc.ANGSTROM_TO_METER,
	}


def _calculate_zero_point_energies(program_state: ProgramState) -> Tuple[containers.Energies, containers.Energies]:
	"""
	Calculate the zero point energy for each mode.

	Args:
		program_state: The program state containing frequencies and oscillator type

	Returns:
		Tuple containing:
		- zero_point_energies: Energy for each mode
		- total_zpe: Sum of all zero point energies

	Notes:
		When oscillator_type is set to CLASSICAL, it isn't technically ZPE, but it
		is treated the same, so for simplicity the variable is still named ZPE
	"""
	zero_point_energies = containers.Energies()
	zpe_sum = 0
	classical_energy = _get_conversion_factors()["classical_energy"]

	for frequency in program_state.frequencies.as_recip_cm():
		frequency = max(frequency, 2)  # Replace frequency < 0 with 2
		energy = (
			classical_energy
			if program_state.oscillator_type == enums.OscillatorType.CLASSICAL
			else 0.5 * sc.h * sc.c * frequency
		)
		zero_point_energies.append(energy, enums.EnergyUnits.JOULE)
		zpe_sum += energy

	total_zpe = containers.Energies()
	total_zpe.append(zpe_sum, enums.EnergyUnits.JOULE)
	return zero_point_energies, total_zpe


def _sample(zero_point_energies: containers.Energies, program_state: ProgramState) -> List[int]:
	"""
	Determine the vibrational excitation quanta numbers.

	Args:
		zero_point_energies: The zero point energies for each mode
		program_state: The program state containing temperature and random generator

	Returns:
		List of vibrational quantum numbers for each mode
	"""
	if program_state.temperature == 0:
		return [0] * len(program_state.frequencies)

	vibrational_quantum_numbers = []
	rt_factor = sc.GAS_CONSTANT_KCAL * program_state.temperature

	for f in range(len(program_state.frequencies)):
		zpe_ratio = math.exp(-2 * zero_point_energies.as_kcal_per_mole(f) / rt_factor)
		zpe_ratio = min(zpe_ratio, 0.99999999999)

		c_e_fraction = 1 - zpe_ratio
		random_number = program_state.random.uniform()

		i = 1
		max_iter = int(4000 * zpe_ratio + 2)
		while i <= max_iter and random_number > c_e_fraction:
			c_e_fraction += math.pow(zpe_ratio, i) * (1 - zpe_ratio)
			i += 1
		vibrational_quantum_numbers.append(i - 1)

	# Apply fixed vibrational quanta
	for mode, quanta in program_state.fixed_vibrational_quanta.items():
		vibrational_quantum_numbers[mode - 1] = quanta

	return vibrational_quantum_numbers


def _calculate_displacement(
	zero_point_energies: containers.Energies, vibrational_quantum_numbers: List[int], program_state: ProgramState
) -> Tuple[containers.Energies, List[float], containers.Energies]:
	"""
	Calculate the displacements (shifts) and vibrational energy per mode.

	Args:
		zero_point_energies: The zero point energies for each mode
		vibrational_quantum_numbers: The quantum numbers for each mode
		program_state: The program state containing frequencies and force constants

	Returns:
		Tuple containing:
		- total_mode_energy: Sum of all mode energies
		- shifts: List of displacement values for each mode
		- mode_energies: Energy for each mode
	"""
	mode_energies = containers.Energies()
	mode_energies_sum = 0

	shifts = []
	freq_array = np.array(program_state.frequencies.as_recip_cm())

	for f in range(len(freq_array)):
		# Calculate mode energy
		if program_state.oscillator_type is enums.OscillatorType.QUASICLASSICAL and freq_array[f] > 10:
			energy = zero_point_energies.as_joules(f) * (2 * vibrational_quantum_numbers[f] + 1)
		else:
			energy = zero_point_energies.as_joules(f) * (2 * vibrational_quantum_numbers[f])

		mode_energies.append(energy, enums.EnergyUnits.JOULE)
		mode_energies_sum += energy

		# Calculate shift
		max_shift = math.sqrt(
			2 * mode_energies.as_millidyne_angstrom(f) / program_state.force_constants.as_millidyne_per_angstrom(f)
		)

		random_weight = 0
		if freq_array[f] > 10:
			if program_state.geometry_displacement_type is enums.GeometryDisplacement.EDGE_WEIGHTED:
				random_weight = program_state.random.edge_weighted()
			elif program_state.geometry_displacement_type is enums.GeometryDisplacement.GAUSSIAN_DISTRIBUTION:
				random_weight = program_state.random.gaussian()
			elif program_state.geometry_displacement_type is enums.GeometryDisplacement.UNIFORM:
				random_weight = 2 * (program_state.random.uniform() - 0.5)

		shifts.append(max_shift * random_weight)

	total_mode_energy = containers.Energies()
	total_mode_energy.append(mode_energies_sum, enums.EnergyUnits.JOULE)
	return total_mode_energy, shifts, mode_energies


def _energy_boost(total_mode_energy: containers.Energies, program_state: ProgramState) -> bool:
	"""
	Boost/drop the energy of the system by changing temperature.

	Returns true if the strucutre needs to be resampled (because the
	temperature changed). Returns false if sampling does not need to be done
	again.

	Reference: C++ - line 138.
	"""
	energy = total_mode_energy.as_kcal_per_mole(0)
	if energy <= program_state.energy_boost_min:
		program_state.temperature += 5.0
		return True
	elif energy >= program_state.energy_boost_max:
		program_state.temperature -= 2.0
		return True
	return False


def _geometry_displacement(shifts: List[float], program_state: ProgramState) -> None:
	"""
	Apply the displacements (shifts) to the coordinates in program_state.

	Referece: C++ - line 167.
	"""
	structures = program_state.structures[0]
	mode_displacements = program_state.mode_displacements

	for f, shift in enumerate(shifts):
		for j in range(program_state.number_atoms):
			current_pos = structures.as_angstrom(j)
			mode_pos = mode_displacements[f].as_angstrom(j)
			new_pos = tuple(c + (m * shift) for c, m in zip(current_pos, mode_pos))
			structures.alter_position(j, *new_pos, enums.DistanceUnits.ANGSTROM)
	return


def _check_if_mode_pushes_apart(program_state: ProgramState) -> bool:
	"""
	Check if the first mode increases the distance between the phase atoms.

	Reference: C++ line 185.
	"""
	# Go from 1-based index to 0-based index
	atom1_id, atom2_id = program_state.phase[0] - 1, program_state.phase[1] - 1

	atom1_modes = np.array(program_state.mode_displacements[0].as_angstrom(atom1_id))
	atom2_modes = np.array(program_state.mode_displacements[0].as_angstrom(atom2_id))
	atom1_pos = np.array(program_state.structures[0].as_angstrom(atom1_id))
	atom2_pos = np.array(program_state.structures[0].as_angstrom(atom2_id))

	before_distance = np.sum(np.square(atom1_pos - atom2_pos))
	atom1_new_pos = atom1_pos + atom1_modes
	atom2_new_pos = atom2_pos + atom2_modes
	after_distance = np.sum(np.square(atom1_new_pos - atom2_new_pos))

	return after_distance > before_distance


def _calculate_mode_velocities(
	mode_energy: containers.Energies, shift: List[float], program_state: ProgramState
) -> Tuple[List[float], List[int]]:
	"""
	Calculate the modal velocity, in a random direction, for each frequency.

	Reference: C++ line 181.
	"""
	units = sc.FROM_MILLI * sc.FROM_CENTI * sc.METER_TO_ANGSTROM
	mode_velocities = []
	mode_directions = []

	for f in range(len(program_state.frequencies)):
		# kinetic energy units: gram angstrom**2 / s**2
		kinetic_energy = units * (
			mode_energy.as_millidyne_angstrom(f)
			- (0.5 * program_state.force_constants.as_millidyne_per_angstrom(f) * math.pow(shift[f], 2))
		)
		if f == 0 and program_state.frequencies.as_recip_cm(f) < 0:
			if program_state.phase_direction is enums.PhaseDirection.RANDOM:
				direction = program_state.random.one_or_neg_one()
			else:
				if _check_if_mode_pushes_apart(program_state):
					direction = 1
				else:
					direction = -1
		else:
			direction = program_state.random.one_or_neg_one()
		if program_state.phase_direction is enums.PhaseDirection.BRING_TOGETHER:
			direction *= -1
		if f + 1 in program_state.fixed_mode_directions:
			# This needs to rewrite the random call from above so the random
			# number generator will give the same results for everything else.
			direction = program_state.fixed_mode_directions[f + 1]
		mode_directions.append(direction)
		velocity = direction * math.sqrt(
			2 * kinetic_energy / (program_state.reduced_masses.as_amu(f) / sc.AVOGADROS_NUMBER)
		)
		mode_velocities.append(velocity)
	return mode_velocities, mode_directions


def _calculate_atomic_velocities(mode_velocities: List[float], program_state: ProgramState) -> List[List[float]]:
	"""
	Calculate atomic velocities from modal velocities.

	Referece: C++ line 230.
	"""
	atomic_velocities = np.zeros((program_state.number_atoms, 3))

	for f, velocity in enumerate(mode_velocities):
		for j in range(program_state.number_atoms):
			atomic_velocities[j] += np.array(program_state.mode_displacements[f].as_angstrom(j)) * velocity

	return atomic_velocities.tolist()


def _calculate_kinetic_energy(atomic_velocities: List[List[float]], program_state: ProgramState) -> containers.Energies:
	"""
	Calculate the total kinetic energy of the system.

	Referece: C++ line - 308
	"""
	units = _get_conversion_factors()["units_ke"]
	velocities = np.array(atomic_velocities)
	masses = np.array([atom.mass for atom in program_state.atoms])

	kinetic_energy_sum = 0.5 * np.sum(masses[:, np.newaxis] * np.sum(velocities**2, axis=1)) * units

	kinetic_energy = containers.Energies()
	kinetic_energy.append(kinetic_energy_sum, enums.EnergyUnits.KCAL_PER_MOLE)
	return kinetic_energy


def _add_rotational_energy(atomic_velocities: List[List[float]], program_state: ProgramState) -> containers.Energies:
	"""
	Calculate and add the rotational energy.

	Reference: C++ line - 251
	"""
	positions = np.array([program_state.structures[0].as_angstrom(i) for i in range(program_state.number_atoms)])

	# Create rotation matrices
	rotateX = np.zeros((len(positions), 3))
	rotateY = np.zeros((len(positions), 3))
	rotateZ = np.zeros((len(positions), 3))

	rotateX[:, 1] = -positions[:, 2]
	rotateX[:, 2] = positions[:, 1]
	rotateY[:, 0] = positions[:, 2]
	rotateY[:, 2] = -positions[:, 0]
	rotateZ[:, 0] = -positions[:, 1]
	rotateZ[:, 1] = positions[:, 0]

	step_size = program_state.step_size.as_second()
	units = _get_conversion_factors()["units_ke"]
	masses = np.array([atom.mass for atom in program_state.atoms])

	# Calculate rotational energies
	eRot = np.zeros(3)
	for axis, rotate in enumerate([rotateX, rotateY, rotateZ]):
		eRot[axis] = np.sum(0.5 * masses[:, np.newaxis] * rotate**2) / step_size**2 * units

	# Calculate kinetic rotational energies
	kRot = np.zeros(3)
	for i, e in enumerate(eRot):
		if e >= 1:
			kRot[i] = (
				math.log(1 - program_state.random.uniform()) * -0.5 * sc.GAS_CONSTANT_KCAL * program_state.temperature
			)

	signs = np.array([program_state.random.one_or_neg_one() for _ in range(3)])
	scales = np.sqrt(kRot / np.where(eRot == 0, 1, eRot))

	# Update atomic velocities
	rotations = [rotateX, rotateY, rotateZ]
	for i in range(len(atomic_velocities)):
		for axis in range(3):
			if eRot[axis] > 0:
				for k in range(3):
					atomic_velocities[i][k] += rotations[axis][i][k] * scales[axis] * signs[axis] / step_size

	rotational_kinetic_energy = containers.Energies()
	rotational_kinetic_energy.append(np.sum(kRot), enums.EnergyUnits.KCAL_PER_MOLE)
	return rotational_kinetic_energy


def _add_velocities_to_program_state(atomic_velocities: List[List[float]], program_state: ProgramState) -> None:
	"""
	Append initial velocities to program_state.

	Referece: C++ line - 318.
	"""
	velocities = containers.Velocities()
	for vel in atomic_velocities:
		velocities.append(*vel, enums.VelocityUnits.ANGSTROM_PER_SEC)
	program_state.velocities.append(velocities)


def generate(program_state: ProgramState) -> None:
	"""Sample initial energy (kinetic and potential).

	Args:
		program_state: The program state to sample energies for

	Raises:
		exceptions.InputError: If energy boost maximum is less than zero point energy
		exceptions.InputError: If frequencies are not set
		exceptions.InputError: If temperature is negative
	"""
	if not program_state.frequencies:
		raise exceptions.InputError("No frequencies set in program state")

	if program_state.temperature < 0:
		raise exceptions.InputError("Temperature cannot be negative")

	# Calculate energies and quantum numbers
	zero_point_energies, total_zpe = _calculate_zero_point_energies(program_state)
	vibrational_quantum_numbers = _sample(zero_point_energies, program_state)
	total_mode_energy, shifts, mode_energies = _calculate_displacement(
		zero_point_energies, vibrational_quantum_numbers, program_state
	)

	# Energy boost handling
	print("### Energy Boost -------------------------------------------------")
	if program_state.energy_boost is enums.EnergyBoost.ON:
		print("  Energy boost on")
		print("  Changing temperature and resampling until the vibrational ")
		print(f"  energy is between {program_state.energy_boost_min} and {program_state.energy_boost_max} kcal/mol.")
		print()

		if program_state.energy_boost_max < total_zpe.as_kcal_per_mole(0):
			raise exceptions.InputError("Energy Boost max energy is less than ZPE.")

		print("  Attempt   Vibrational Energy (kcal/mol)   Temperature (K)")
		print("  ---------------------------------------------------------")

		i = 1
		print(
			f"  {i:>7}   {total_mode_energy.as_kcal_per_mole(0):18.6f}              {program_state.temperature:11.2f}"
		)

		while _energy_boost(total_mode_energy, program_state):
			i += 1
			vibrational_quantum_numbers = _sample(zero_point_energies, program_state)
			total_mode_energy, shifts, mode_energies = _calculate_displacement(
				zero_point_energies, vibrational_quantum_numbers, program_state
			)
			print(
				f"  {i:>7}   {total_mode_energy.as_kcal_per_mole(0):18.6f}              {program_state.temperature:11.2f}"
			)
		print("  Energy boost criteria met")
	else:
		print("  Energy boost off")
	print()

	# Stretch coordinates
	print("### Initial Geometry Displacement --------------------------------")
	if program_state.geometry_displacement_type is not enums.GeometryDisplacement.NONE:
		_geometry_displacement(shifts, program_state)
		print("  Modified initial structure")
		for atom, position in zip(program_state.atoms, program_state.structures[0].as_angstrom()):
			print(f"    {atom.symbol.ljust(2)} {position[0]:10.6f} {position[1]:10.6f} {position[2]:10.6f}")
	else:
		print("  Geometry displacement turned off. Using input structure for")
		print("  starting geometry.")
	print()

	# Calculate velocities and energies
	mode_velocities, mode_directions = _calculate_mode_velocities(mode_energies, shifts, program_state)

	print("### Vibrational Quantum Numbers ----------------------------------")
	print("  Mode  Wavenumber  Quantum No.  Energy (kcal/mol)  Mode Direction")
	print("  ----------------------------------------------------------------")
	for i, (mode_energy, quantum_n, frequency, direction) in enumerate(
		zip(
			mode_energies.as_kcal_per_mole(),
			vibrational_quantum_numbers,
			program_state.frequencies.as_recip_cm(),
			mode_directions,
		),
		1,
	):
		print(f"  {i:>4}  {frequency:10.3f}  {quantum_n:>11}  {mode_energy:17.6f}  {direction:>14}")
	print()

	print("### Mode Velocities (meters/second) ------------------------------")
	meter_conversion = _get_conversion_factors()["meter_conversion"]
	for mode_velocity in mode_velocities:
		print(f"  {mode_velocity * meter_conversion:15.6e}")
	print()

	atomic_velocities = _calculate_atomic_velocities(mode_velocities, program_state)
	vibrational_kinetic_energy = _calculate_kinetic_energy(atomic_velocities, program_state)

	print("### Rotational Energy --------------------------------------------")
	if program_state.add_rotational_energy is enums.RotationalEnergy.YES:
		rotational_kinetic_energy = _add_rotational_energy(atomic_velocities, program_state)
		print(f"  {rotational_kinetic_energy.as_kcal_per_mole(0):.6f} kcal/mol rotational energy added.")
		total_kinetic_energy = _calculate_kinetic_energy(atomic_velocities, program_state)
	else:
		print("  Rotational energy turned off.")
		rotational_kinetic_energy = containers.Energies()
		rotational_kinetic_energy.append(0, enums.EnergyUnits.KCAL_PER_MOLE)
		total_kinetic_energy = vibrational_kinetic_energy
	print()

	_add_velocities_to_program_state(atomic_velocities, program_state)

	print("### Initial Velocities (meters/second) ---------------------------")
	for atom, velocity in zip(program_state.atoms, program_state.velocities[-1].as_meter_per_sec()):
		print(f"  {atom.symbol.ljust(2)} {velocity[0]:15.6e} {velocity[1]:15.6e} {velocity[2]:15.6e}")
	print()

	# Calculate and print energy summary
	excitation_energy = containers.Energies()
	excitation_energy.append(
		total_mode_energy.as_kcal_per_mole(0) - total_zpe.as_kcal_per_mole(0), enums.EnergyUnits.KCAL_PER_MOLE
	)

	print("### Initial Energy Sampling Summary (kcal/mol) -------------------")
	print("  Zero point energy:")
	print(f"  {total_zpe.as_kcal_per_mole(0):11.6f}")
	print("  Excitation energy:")
	print(f"  {excitation_energy.as_kcal_per_mole(0):11.6f}")
	print("  Quantum vibrational energy (zpe + excitation):")
	print(f"  {total_mode_energy.as_kcal_per_mole(0):11.6f}")
	print("  Vibrational component of kinetic energy:")
	print(f"  {vibrational_kinetic_energy.as_kcal_per_mole(0):11.6f}")
	print("  Rotation component of kinetic energy:")
	print(f"  {rotational_kinetic_energy.as_kcal_per_mole(0):11.6f}")
	print("  Total kinetic energy:")
	print(f"  {total_kinetic_energy.as_kcal_per_mole(0):11.6f}")
	print()
