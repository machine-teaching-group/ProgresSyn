# Use a pretrained model, to fine-tune it using simple Reinforce
# Change the --environment flag if you want to use a reward including performance.
train_cmd.py  --signal rl \
              --environment BlackBoxGeneralization \
              --nb_rollouts 100 \
              \
              --init_weights data/input_agents_neural/models/pretrained.model \
              --nb_epochs 50 \
              --optim_alg Adam \
              --learning_rate 1e-5 \
              --batch_size 16 \
              --seed 1 \
              \
             --nb_samples 0 \
             --train_file data/input_agents_neural/datasets/cleaned10k.json \
             --val_file data/input_agents_neural/datasets/val.json \
             --vocab data/input_agents_neural/datasets/new_vocab.vocab \
             --result_folder data/output/agents_neural_exps/finetune_original_dataset \
              \
              --use_grammar \
              \
              --use_cuda