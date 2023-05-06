# Notes

This is the source code for supplementary material part of our "Synthesizing a Progression of Subtasks for Block-Based Visual Programming Tasks" submission.

- `agents_neural/` has the source code for training of Neural Program Synthesizers based on the paper "Leveraging Grammar and Reinforcement Learning for Neural Program Synthesis".
- `algorithm_progressyn/` has the source code for our subtasking algorithm [ProgresSyn].
- `algorithm_progressyn_demo/` contains scripts to run the decomposition algorithm on sample tasks from the paper.
- `utils` has some functions and scripts that connects different subpackages through converters and wrappers. Particularly, scripts to be used for dataset generation for `agents_neural/` are located here.

The directories have their own `README` file which can be referred to for further information on commands associated with each module.
