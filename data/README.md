## Structure

#### `input_algorithm_progressyn_demo/`
This is where the reference code and task files are located for demo. \
They should come with this repo.

#### `input_agents_neural/`
This is where the datasets to be used in Neural Program Synthesizer experiments should be located. \
Expected format and files is below:
 - `datasets/{training_dataset_name}.json`
 - `datasets/val.json`
 - `datasets/test.json`
 - `datasets/target.vocab`
 - `datasets/new_vocab.vocab`

The original training dataset and the other named files should be taken from the Karel Dataset. See `code/agents_neural/README` for more information on where to get it.

Datasets with subtasks can be generated and put here for experiments. See `code/utils/README` for more information on how to generate them.

#### `output/`

This is where the outputs of most scripts will be located, with the exception of graph generation and dataset generation scripts, which will be copied to the respective input folders explained above.
