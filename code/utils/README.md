## Commands for Augmenting a Neural Program Synthesis Dataset with Subtasks

Example command:

`python -m code.utils.decompose_dataset --input_dataset=cleaned10k.json --start_sample=0 --end_sample=1000 --num_subtasks=4 --alg=fine-grained `

- `--input_dataset` is the name of the file that will be searched under `data/input_agents_neural/datasets/`
- `--start_sample` and `--end_sample` determines which part of the dataset to create subtasks of. These two are useful to divide the dataset into parts to augment them in parallel.
- `--alg` and `--num_subtasks` are parameters for subtasking algorithm. See `code/algorithm_progressyn/README` for more information.
- **Note:** `--baseline=harddecomp --alg=fine-grained` should be used for **Same-C** baseline from the paper. `--baseline=progressyn` should be used for all others.


This command will crate a new dataset that consists of the generated subtasks under `data/output/agents_neural_generated_dataset/`. This file can be copied into `data/input_agents_neural/datasets/` to be used in the training of `agents_neural`.


## Scripts to Parallelize the Augmenting

While it is not the prettiest way, we used multiple calls to `decompose_dataset.py` to parallelize the subtask generation process. We provide an example of our bash scripts that can be used for reference.


`run_multiple_decompose.sh` shows an example of scripts that we used for this. It creates a separate screen process for each 1000 tasks in the dataset.  

`combine_subtasks.sh` should be run after all processes are done to combine all of the generated sub-datasets. It also copies the generated dataset from `output/agents_neural_generated_dataset/` to `data/input_agents_neural/datasets/`.
