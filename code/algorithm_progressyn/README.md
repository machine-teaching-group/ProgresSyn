## Our Subtasking Algorithm: progressyn

This folder contains the source code for our algorithm.

### Structure

- `interpreter/`: Files for running Karel code. These files are based on https://github.com/carpedm20/karel repo.
- `subtasking/`: Implementation files of our ProgresSyn algorithm
- `scripts/`: Scripts to run our algorithm


### Commands

#### Running ProgresSyn with Greedy Heuristic for Grid ordering

To run the our algorithm with "the grid with most code coverage first" heuristic: \
`python -m code.algorithm_progressyn.scripts.run_algorithm_progressyn`

Required/Important Arguments:
- `--input_task_id`: Task name to be searched under `input_program_path` which is `data/input_algorithm_progressyn_demo/` by default.
- `--num_subtasks`: Number of subtasks for single grid decomposition(K' from paper)
-  `--alg`: The algorithm to use: Options:
   - `grids`:  ProgresSyn^{grids} from our paper
   - `fine-grained`: ProgresSyn from our paper, ie. ProgresSyn^{grids} + ProgresSyn^{single}

 Example Command:
 `python -m code.algorithm_progressyn.scripts.run_algorithm_progressyn --input_task_id=hoc-8 --num_subtasks=3 --alg=fine-grained`

#### Running ProgresSyn with Exhaustive Enumeration


 To run it with exhaustive search as in the paper: (only for tasks with multiple grids, i.e. T_n > 1) For example, Stairway.

 `python -m code.algorithm_progressyn.scripts.run_algorithm_progressyn_exhaustive`

 - `--input_task_id`: Task name to be searched under `input_program_path` which is `data/input_algorithm_progressyn_demo/` by default.
 - `--num_subtasks`: Number of subtasks for single grid decomposition(K' from paper)

 Example Command:
 `python -m code.algorithm_progressyn.scripts.run_algorithm_progressyn_exhaustive --input_task_id=karel-stairway --num_subtasks=3`

#### Running Same-C Baseline from the Paper

To run the Same-C baseline in the paper:

`python -m code.algorithm_progressyn.scripts.run_algorithm_harddecomp`

- `--input_task_id`: Task name to be searched under `input_program_path` which is `data/input_algorithm_progressyn_demo/` by default.
- `--num_subtasks`: Number of subtasks for single grid decomposition(K' from paper)

Example Command:
`python -m code.algorithm_progressyn.scripts.run_algorithm_harddecomp --input_task_id=karel-stairway --num_subtasks=3`
