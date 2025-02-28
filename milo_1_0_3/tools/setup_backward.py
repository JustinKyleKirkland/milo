#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create an input file with opposite phase for each output file in the directory.

This script creates input files (.in) and SLURM submission scripts (.sh) for each
.out file in the current directory. The input files will have opposite phase
(push_apart ↔ bring_together). This is useful for trajectories initiated from a
transition state. Note: Only works with explicitly specified phases (push_apart
or bring_together), not with random phase.

You can use command line options to determine max_steps for the input file and
memory, number of CPUs, and time limit for the submission script.
"""

import argparse
from pathlib import Path
from typing import List, Optional


def parse_arguments() -> argparse.Namespace:
	"""Parse and validate command line arguments."""
	parser = argparse.ArgumentParser(description="Make Milo input files with opposite phase from .out files.")

	parser.add_argument(
		"-t",
		"--time",
		required=True,
		help="Time request for submission script (HH:MM:SS)",
	)
	parser.add_argument(
		"-m",
		"--memory",
		type=int,
		required=True,
		help="Memory request in GB (submission script gets this value, input file gets this-1)",
	)
	parser.add_argument(
		"-p",
		"--processors",
		type=int,
		required=True,
		help="Number of processors to request (used in both scripts)",
	)
	parser.add_argument(
		"-s",
		"--max_steps",
		default=None,
		help="Maximum trajectory steps (integer or 'no_limit'). Default: same as .out file",
	)
	parser.add_argument(
		"--no_script",
		action="store_true",
		help="Skip generating submission scripts",
	)
	parser.add_argument(
		"--gaussian09",
		action="store_true",
		help="Use 'module load g09' instead of 'module load g16'",
	)

	return parser.parse_args()


def parse_out_file(out_file: Path) -> tuple[List[str], Optional[str]]:
	"""Parse the output file to extract input section and random seed."""
	input_lines = []
	random_seed = None

	try:
		with out_file.open("r") as f:
			in_input_section = False
			in_random_seed_section = False

			for line in f:
				if "### Input File ----------------------------------" in line:
					in_input_section = True
				elif "### Default Parameters Being Used -------------" in line:
					in_input_section = False
				elif in_input_section:
					input_lines.append(line)
				elif "### Random Seed -------------------------------" in line:
					in_random_seed_section = True
				elif in_random_seed_section:
					random_seed = line.strip()
					break

	except IOError as e:
		print(f"Error reading {out_file}: {e}")
		return [], None

	return input_lines, random_seed


def make_input_file(
	job_name: str, old_input: List[str], random_seed: str, max_steps: Optional[str], memory: int, procs: int
) -> None:
	"""Generate input file with switched phase."""
	new_input = []
	in_job_section = False
	random_seed_set = False

	phase_map = {"bring_together": "push_apart", "push_apart": "bring_together"}

	for line in old_input:
		line_lower = line.casefold()
		if "$job" in line_lower:
			in_job_section = True
		elif in_job_section and "$end" in line_lower:
			if not random_seed_set:
				new_input.append(f"    random_seed             {random_seed}\n")
			in_job_section = False
		elif in_job_section:
			if "random_seed" in line_lower:
				line = f"    random_seed             {random_seed}\n"
				random_seed_set = True
			elif max_steps is not None and "max_steps" in line_lower:
				line = f"    max_steps               {max_steps}\n"
			elif "phase" in line_lower:
				for old_phase, new_phase in phase_map.items():
					if old_phase in line_lower:
						line = line.replace(old_phase, new_phase)
						break
				else:
					print(
						f"Warning: {job_name[:-4]}.out - Script requires explicit"
						" 'push_apart' or 'bring_together' phase specification."
					)
			elif "memory" in line_lower:
				line = f"    memory                  {memory - 1}\n"
			elif "processors" in line_lower:
				line = f"    processors              {procs}\n"
		new_input.append(line)

	try:
		with open(f"{job_name}.in", "w") as f:
			f.writelines(new_input)
	except IOError as e:
		print(f"Error writing input file {job_name}.in: {e}")


def make_submission_script(job_name: str, time_string: str, memory: int, procs: int, use_g09: bool) -> None:
	"""Generate SLURM submission script."""
	script_content = f"""#!/bin/bash
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task={procs}
#SBATCH --mem={memory}G
#SBATCH -t {time_string}
#SBATCH -C 'avx2'

export JOB_NAME={job_name}
export TEMPORARY_DIR=/tmp/$SLURM_JOB_ID
export JOB_SOURCE_DIR="$SLURM_SUBMIT_DIR"

function cleanup {{
    echo "---"
    echo "Starting clean up"

    for file in "$TEMPORARY_DIR"/*.{{out,xyz,txt}}; do
        [ -e "$file" ] || continue
        cp -vp "$file" "$JOB_SOURCE_DIR"
    done

    mkdir -p "$JOB_SOURCE_DIR/com_log_files/"
    echo "Archiving .com and .log files"
    tar -cf "${{JOB_NAME}}_${{SLURM_JOB_ID}}_com_log_files.tar" *.{{com,log}}
    cp -v "${{JOB_NAME}}_${{SLURM_JOB_ID}}_com_log_files.tar" "${{JOB_SOURCE_DIR}}/com_log_files/"

    cd "$JOB_SOURCE_DIR"
    rm -fr "$TEMPORARY_DIR"

    echo "Clean up finished at $(date)"
}}

echo "---"
echo "Milo SLURM Diagnostic Information"
echo "---"
echo "Start date and time: $(date)"
echo "---"
echo "Nodes assigned:"
cat $(/fslapps/fslutils/generate_pbs_nodefile)
echo "---"
echo "Job Source Directory: $JOB_SOURCE_DIR"
echo "Temporary Directory: $TEMPORARY_DIR"

mkdir "$TEMPORARY_DIR"
cp -v "$JOB_SOURCE_DIR/$JOB_NAME.in" "$TEMPORARY_DIR"
cd "$TEMPORARY_DIR"

echo "---"
echo "Starting Milo run"

module load python/3.8
module load {("g09" if use_g09 else "g16")}

python -m milo_1_0_3 < "$JOB_NAME.in" > "$JOB_NAME.out" &
pid=$!

trap "kill $pid; cleanup; exit 1" TERM SIGTERM KILL SIGKILL
wait $pid

cleanup
"""

	try:
		with open(f"{job_name}.sh", "w") as f:
			f.write(script_content)
	except IOError as e:
		print(f"Error writing submission script {job_name}.sh: {e}")


def main():
	"""Main execution function."""
	args = parse_arguments()

	# Process all .out files in current directory
	out_files = list(Path(".").glob("*.out"))
	if not out_files:
		print("No .out files found in current directory")
		return

	for out_file in out_files:
		job_name = f"{out_file.stem}_rev"
		input_lines, random_seed = parse_out_file(out_file)

		if not input_lines or random_seed is None:
			print(f"Failed to process {out_file}")
			continue

		make_input_file(job_name, input_lines, random_seed, args.max_steps, args.memory, args.processors)

		if not args.no_script:
			make_submission_script(job_name, args.time, args.memory, args.processors, args.gaussian09)


if __name__ == "__main__":
	main()
