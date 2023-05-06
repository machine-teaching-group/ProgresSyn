# Evaluate a trained model on the test set
eval_cmd.py --model_weights data/output/agents_neural_exps/finetune_original_dataset/Weights/best.model \
            \
            --vocabulary data/input_agents_neural/datasets/new_vocab.vocab \
            --dataset data/input_agents_neural/datasets/test.json \
            --eval_nb_ios 5 \
            --eval_batch_size 8 \
            --output_path data/output/agents_neural_exps/finetune_original_datasetResults/TestSet_ \
            \
            --beam_size 64 \
            --top_k 10 \
            --use_grammar \
            \
            --use_cuda