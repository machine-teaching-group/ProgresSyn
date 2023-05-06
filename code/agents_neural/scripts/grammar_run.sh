train_cmd.py --kernel_size 3 \
             --conv_stack "64,64,64" \
             --fc_stack "512" \
             --tgt_embedding_size 256 \
             --lstm_hidden_size 256 \
             --nb_lstm_layers 2 \
             \
             --signal supervised \
             --nb_ios 5 \
             --nb_epochs 150 \
             --optim_alg Adam \
             --batch_size 128 \
             --learning_rate 1e-4 \
             --seed 1 \
             \
             --nb_samples 0 \
             --train_file data/input_agents_neural/datasets/subtasks_dataset_algCK4Mult.json \
             --val_file data/input_agents_neural/datasets/val.json \
             --vocab data/input_agents_neural/datasets/new_vocab.vocab \
             --result_folder data/output/agents_neural_exps/supervised_original_dataset \
             \
             --use_grammar \
             \
             --use_cuda
