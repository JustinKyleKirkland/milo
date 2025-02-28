#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create multiple input files with different seeds to form an ensemble.

This script can setup input files in two ways:
 - from a single input file, corresponding to only one direction, or
 - from two input files, one forward and one backward.

The script will also create SLURM submission scripts, unless turned off with
the --no_script flag.
"""

import argparse
from functools import lru_cache
from random import randrange
from typing import List, TextIO, Union

_SUBMISSION_SCRIPT_TEMPLATE = """#!/bin/bash
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task={procs}
#SBATCH --mem={memory}G
#SBATCH -t {time_string}
#SBATCH -C 'avx2'

export JOB_NAME={job_name}

export TEMPORARY_DIR=/tmp/$SLURM_JOB_ID
export JOB_SOURCE_DIR="$SLURM_SUBMIT_DIR"

function cleanup
{{
  echo "---"
  echo "Starting clean up"

  for file in "$TEMPORARY_DIR"/*.{{out,xyz,txt}}; do
    [ -e $file ] || continue
    cp -vp $file "$JOB_SOURCE_DIR"
  done

mkdir -p "$JOB_SOURCE_DIR/com_log_files/"
echo "Archiving .com and .log files"
tar -cf ${{JOB_NAME}}_${{SLURM_JOB_ID}}_com_log_files.tar *.{{com,log}}
cp -v ${{JOB_NAME}}_${{SLURM_JOB_ID}}_com_log_files.tar "$JOB_SOURCE_DIR/com_log_files/"

  cd "$JOB_SOURCE_DIR"
  rm -fr "$TEMPORARY_DIR"

  echo "Clean up finished at `date`"
}}

echo "---"
echo "Milo SLURM Diagnostic Information"
echo "---"
echo "Start date and time: `date`"
echo "---"
echo "Nodes assigned:"
cat `/fslapps/fslutils/generate_pbs_nodefile`
echo "---"
echo "Job Source Directory: $JOB_SOURCE_DIR"
echo "Temporary Directory: $TEMPORARY_DIR"
mkdir $TEMPORARY_DIR
cp -v "$JOB_SOURCE_DIR/$JOB_NAME.in" "$TEMPORARY_DIR"
cd "$TEMPORARY_DIR"
echo "---"
echo "Starting Milo run"

module load python/3.8
module load {gaussian_string}
python -m milo_1_0_3 < "$JOB_NAME.in" > "$JOB_NAME.out" &
pid=$!
# Associate the function "cleanup" with the TERM signal, which is usually
# how jobs get killed
trap "kill $pid; cleanup; exit 1" TERM SIGTERM KILL SIGKILL
wait $pid

cleanup
"""


def make_submission_script(
	file_name: str, time_string: str, memory: Union[int, str], procs: Union[int, str], gaussian_string: str
) -> None:
	"""Create a SLURM submission script.

	Args:
		file_name: Name of script file to create
		time_string: Wall time request in HH:MM:SS format
		memory: Memory request in GB
		procs: Number of processors to request
		gaussian_string: Gaussian version to load (g09/g16)
	"""
	job_name = file_name.split(".")[0]
	script_content = _SUBMISSION_SCRIPT_TEMPLATE.format(
		procs=procs, memory=memory, time_string=time_string, job_name=job_name, gaussian_string=gaussian_string
	)

	with open(file_name, "w") as file:
		file.write(script_content)


def make_input_file(file_name: str, template: List[str], random_seed: int) -> None:
	"""Create an input file from template with specified random seed.

	Args:
		file_name: Name of output file to create
		template: List of template lines to write
		random_seed: Random seed to insert into template
	"""
	# Join all lines and replace placeholder in one operation
	content = "".join(template).replace("random_seed_placeholder", str(random_seed))

	with open(file_name, "w") as file:
		file.write(content)


@lru_cache(maxsize=32)
def _process_job_section(
	line: str,
	in_job_section: bool,
	random_seed_set: bool,
	memory: Union[int, str],
	procs: Union[int, str],
	gaussian_string: str,
) -> tuple[bool, bool, Union[int, str], Union[int, str], str, str]:
	"""Process a line in the job section and return updated values.

	Args:
	    line: The current line being processed
	    in_job_section: Whether currently in job section
	    random_seed_set: Whether random seed has been set
	    memory: Current memory value
	    procs: Current processors value
	    gaussian_string: Current gaussian string value

	Returns:
	    Tuple containing updated values for in_job_section, random_seed_set, memory, procs, gaussian_string, and processed line
	"""
	line_lower = line.casefold()
	if "$job" in line_lower:
		in_job_section = True
	elif in_job_section and "$end" in line_lower:
		in_job_section = False
	elif in_job_section:
		if "random_seed" in line_lower:
			line = "    random_seed             random_seed_placeholder\n"
			random_seed_set = True
		elif "memory" in line_lower:
			memory = int(line.split()[1]) + 1
		elif "processors" in line_lower:
			procs = int(line.split()[1])
		elif "program" in line_lower and "gaussian09" in line_lower:
			gaussian_string = "g09"

	return in_job_section, random_seed_set, memory, procs, gaussian_string, line


def process_template_file(template_file: TextIO) -> tuple[List[str], Union[int, str], Union[int, str], str]:
	"""Process a template input file to extract parameters.

	Args:
	    template_file: Input file to process

	Returns:
	    Tuple containing:
	    - List of template lines with random_seed placeholder
	    - Memory requirement in GB
	    - Number of processors
	    - Gaussian version string
	"""
	template = []
	in_job_section = False
	random_seed_set = False
	memory = "memory_placeholder"
	procs = "processors_placeholder"
	gaussian_string = "g16"

	for line in template_file:
		in_job_section, random_seed_set, memory, procs, gaussian_string, processed_line = _process_job_section(
			line, in_job_section, random_seed_set, memory, procs, gaussian_string
		)
		template.append(processed_line)

		if not in_job_section and not random_seed_set:
			template.append("    random_seed             random_seed_placeholder\n")
			random_seed_set = True

	return template, memory, procs, gaussian_string


def main() -> None:
	"""Create ensemble of input files with different random seeds."""
	parser = argparse.ArgumentParser(description="Make Milo input files for an ensemble of trajectories.")

	parser.add_argument(
		"-n",
		"--number_trajectories",
		type=int,
		required=True,
		help="The number of trajectories to make input files for.",
	)

	parser.add_argument(
		"-f",
		"--forward",
		type=argparse.FileType("r"),
		required=True,
		help="A template input file for the forward direction.",
	)
	parser.add_argument(
		"-b",
		"--backward",
		type=argparse.FileType("r"),
		default=None,
		help="A template input file for the backward direction.",
	)

	parser.add_argument(
		"-t",
		"--time",
		default="time_placeholder",
		help="Amount of time the submission script should request for forward trajectories, formatted as HH:MM:SS.",
	)
	parser.add_argument(
		"--time_backward",
		default=None,
		help="Amount of time the submission script should request for backward trajectories, formatted as HH:MM:SS.",
	)

	parser.add_argument("--no_script", action="store_true", help="Stops submission scripts from being output.")

	args = parser.parse_args()

	# Process forward template
	forward_template, forward_memory, forward_procs, gaussian_string = process_template_file(args.forward)
	input_file_basename = args.forward.name.split(".")[0]

	# Process backward template if provided
	backward_data = None
	if args.backward is not None:
		backward_template, backward_memory, backward_procs, _ = process_template_file(args.backward)
		backward_data = (backward_template, backward_memory, backward_procs)

	# Print warnings for missing parameters
	if not args.no_script:
		if forward_memory == "memory_placeholder":
			print(
				"Warning: Could not find memory specification in forward "
				"template file. Replace 'memory_placeholder' in submission "
				"script before submitting jobs."
			)
		if forward_procs == "processors_placeholder":
			print(
				"Warning: Could not find processors specification in forward "
				"template file. Replace 'processors_placeholder' in submission "
				"script before submitting jobs."
			)
		if args.time == "time_placeholder":
			print(
				"Warning: Time not specified. Replace 'time_placeholder' in submission script before submitting jobs."
			)

	# Generate files for each trajectory
	for _ in range(args.number_trajectories):
		random_seed = randrange(10000000000, 99999999999)

		if backward_data:
			# Generate forward direction files
			forward_name = f"{input_file_basename}_{random_seed}_fwd.in"
			make_input_file(forward_name, forward_template, random_seed)
			if not args.no_script:
				make_submission_script(
					forward_name.replace(".in", ".sh"), args.time, forward_memory, forward_procs, gaussian_string
				)

			# Generate backward direction files
			backward_name = f"{input_file_basename}_{random_seed}_bwd.in"
			make_input_file(backward_name, backward_data[0], random_seed)
			if not args.no_script:
				make_submission_script(
					backward_name.replace(".in", ".sh"),
					args.time_backward if args.time_backward is not None else args.time,
					backward_data[1],
					backward_data[2],
					gaussian_string,
				)
		else:
			# Generate single direction files
			name = f"{input_file_basename}_{random_seed}.in"
			make_input_file(name, forward_template, random_seed)
			if not args.no_script:
				make_submission_script(
					name.replace(".in", ".sh"), args.time, forward_memory, forward_procs, gaussian_string
				)


if __name__ == "__main__":
	main()
