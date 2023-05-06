nsamples=1000
offset=0
alg="algCK4"
for run in {0..9};
do
    let start_sample=nsamples*run+offset end_sample=nsamples+start_sample
    cat data/output/agents_neural_generated_dataset/subtasks_from_${start_sample}_to_${end_sample}.json >> data/input_agents_neural/datasets/subtasks_dataset_${alg}.json
    rm data/output/agents_neural_generated_dataset/subtasks_from_${start_sample}_to_${end_sample}.json

    cat data/output/agents_neural_generated_dataset/samples_with_unactivated_branchesfrom_${start_sample}_to_${end_sample}.csv >> data/output/agents_neural_generated_dataset/all_failed_samples_${alg}.csv
    cat data/output/agents_neural_generated_dataset/failed_samplesfrom_${start_sample}_to_${end_sample}.csv >> data/output/agents_neural_generated_dataset/all_other_failed_samples_${alg}.csv
    rm data/output/agents_neural_generated_dataset/samples_with_unactivated_branchesfrom_${start_sample}_to_${end_sample}.csv
    rm data/output/agents_neural_generated_dataset/failed_samplesfrom_${start_sample}_to_${end_sample}.csv
    echo "," >> data/output/agents_neural_generated_dataset/all_failed_samples_${alg}.csv
    echo "," >> data/output/agents_neural_generated_dataset/all_other_failed_samples_${alg}.csv


    cat data/output/agents_neural_generated_dataset/nsubtasksfrom_${start_sample}_to_${end_sample}.csv >> data/output/agents_neural_generated_dataset/nsubtasks_${alg}.csv
    rm data/output/agents_neural_generated_dataset/nsubtasksfrom_${start_sample}_to_${end_sample}.csv
    echo "," >> data/output/agents_neural_generated_dataset/nsubtasks_${alg}.csv

    echo $end_sample
done
