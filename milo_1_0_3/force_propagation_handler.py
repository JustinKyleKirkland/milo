#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Calculate the next position using force data from previous step."""

from typing import Dict, Tuple, Type

import numpy as np

from milo_1_0_3 import containers
from milo_1_0_3 import enumerations as enums
from milo_1_0_3.program_state import ProgramState


def get_propagation_handler(program_state: ProgramState) -> Type["ForcePropagationHandler"]:
	"""Return the correct propagation handler class based on program state.

	Args:
		program_state: The program state containing propagation configuration

	Returns:
		The appropriate propagation handler class

	Raises:
		ValueError: If the propagation algorithm is not recognized
	"""
	handlers: Dict[enums.PropagationAlgorithm, Type["ForcePropagationHandler"]] = {
		enums.PropagationAlgorithm.VERLET: Verlet,
		enums.PropagationAlgorithm.VELOCITY_VERLET: VelocityVerlet,
	}

	if program_state.propagation_algorithm not in handlers:
		raise ValueError(f"Unknown force propagation algorithm: {program_state.propagation_algorithm}")

	return handlers[program_state.propagation_algorithm]


class ForcePropagationHandler:
	"""Template class for force propagation handlers."""

	_acceleration_cache: Dict[Tuple[int, int], np.ndarray] = {}
	_velocity_cache: Dict[Tuple[int, int], np.ndarray] = {}

	@classmethod
	def _calculate_acceleration(cls, program_state: ProgramState) -> None:
		"""Calculate acceleration with F = m*a.

		Args:
			program_state: The program state to update with calculated acceleration
		"""
		cache_key = (id(program_state), len(program_state.forces))
		if cache_key in cls._acceleration_cache:
			acceleration = containers.Accelerations.from_numpy(cls._acceleration_cache[cache_key])
		else:
			acceleration = containers.Accelerations.from_forces(program_state.forces[-1], program_state.atoms)
			cls._acceleration_cache[cache_key] = acceleration.to_numpy()

			# Cache cleanup - remove old entries
			if len(cls._acceleration_cache) > 1000:
				cls._acceleration_cache.clear()

		program_state.accelerations.append(acceleration)

	@classmethod
	def _calculate_velocity(cls, program_state: ProgramState) -> None:
		"""Calculate velocity with v(n) = v(n-1) + 1/2*(a(n-1) + a(n))*dt.

		Args:
			program_state: The program state to update with calculated velocity
		"""
		cache_key = (id(program_state), len(program_state.accelerations))
		if cache_key in cls._velocity_cache:
			velocity = containers.Velocities.from_numpy(cls._velocity_cache[cache_key])
		else:
			accel_sum = program_state.accelerations[-1] + program_state.accelerations[-2]
			velocity = program_state.velocities[-1] + (
				containers.Velocities.from_acceleration(accel_sum, program_state.step_size) * 0.5
			)
			cls._velocity_cache[cache_key] = velocity.to_numpy()

			# Cache cleanup
			if len(cls._velocity_cache) > 1000:
				cls._velocity_cache.clear()

		program_state.velocities.append(velocity)

	@staticmethod
	def _validate_program_state(program_state: ProgramState) -> None:
		"""Validate program state before calculations.

		Args:
			program_state: The program state to validate

		Raises:
			ValueError: If program state is invalid
		"""
		if not program_state.forces:
			raise ValueError("No forces available in program state")
		if not program_state.atoms:
			raise ValueError("No atoms defined in program state")
		if program_state.step_size <= 0:
			raise ValueError("Step size must be positive")


class Verlet(ForcePropagationHandler):
	"""Calculate the next structure using the Verlet algorithm.

	Each pass calculates the acceleration and velocity of the previous time
	step, then calculates the new positions for the current time step.

	Velocities are calculated in this algorithm only to be output. They are
	not used in the actual force propagation algorithm.

	Verlet algorithm equations:
		a(n-1) = F*m
		x(n) = x(n-1) + v(n-1)*dt + 1/2*a(n-1)*(dt^2);    when n == 1
			 = 2*x(n-1) - x(n-2) + a(n-1)*(dt^2);         when n >= 2

		v(n-1) = v(n-2) + 1/2*(a(n-2) + a(n-1))*dt;       only used for output
	"""

	@classmethod
	def run_next_step(cls, program_state: ProgramState) -> None:
		"""Calculate the next structure using the Verlet algorithm.

		Args:
			program_state: The program state to update with next step calculations
		"""
		cls._validate_program_state(program_state)

		# Calculate a(n-1) from forces
		cls._calculate_acceleration(program_state)

		# Calculate v(n-1) using equation above (only used for output)
		if len(program_state.structures) > 1:
			cls._calculate_velocity(program_state)

		# Calculate x(n) using vectorized operations
		if len(program_state.structures) == 1:
			structure = (
				program_state.structures[-1]
				+ containers.Positions.from_velocity(program_state.velocities[-1], program_state.step_size)
				+ (
					containers.Positions.from_acceleration(program_state.accelerations[-1], program_state.step_size)
					* 0.5
				)
			)
		else:
			structure = (
				(program_state.structures[-1] * 2)
				- program_state.structures[-2]
				+ containers.Positions.from_acceleration(program_state.accelerations[-1], program_state.step_size)
			)
		program_state.structures.append(structure)


class VelocityVerlet(ForcePropagationHandler):
	"""Calculate the next structure using the Velocity Verlet algorithm.

	Each pass calculates the acceleration and velocity of the previous time
	step, then calculates the new positions for the current time step.

	On the first pass, the velocities are not calculated and instead come from
	initial_energy_sampler or the input file.

	Velocity Verlet algorithm equations:
		a(n-1) = F*m
		v(n-1) = v(n-2) + 1/2*(a(n-2) + a(n-1))*dt
		x(n) = x(n-1) + v(n-1)*dt + 1/2*a(n-1)*dt^2
	"""

	@classmethod
	def run_next_step(cls, program_state: ProgramState) -> None:
		"""Calculate the next structure using the Velocity Verlet algorithm.

		Args:
			program_state: The program state to update with next step calculations
		"""
		cls._validate_program_state(program_state)

		# Calculate a(n-1) from forces
		cls._calculate_acceleration(program_state)

		# Calculate v(n-1) using equation above
		if len(program_state.structures) > 1:
			cls._calculate_velocity(program_state)

		# Calculate x(n) using vectorized operations
		structure = (
			program_state.structures[-1]
			+ containers.Positions.from_velocity(program_state.velocities[-1], program_state.step_size)
			+ (containers.Positions.from_acceleration(program_state.accelerations[-1], program_state.step_size) * 0.5)
		)
		program_state.structures.append(structure)
