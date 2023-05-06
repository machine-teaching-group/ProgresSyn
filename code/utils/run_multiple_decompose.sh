nsamples=1000
offset=0
for run in {0..9}
do
    let start_sample=nsamples*run+offset end_sample=nsamples+start_sample
    screen -A -m -d -S decompose$end_sample python -m code.agents_neural.scripts.decompose_dataset --input_dataset=cleaned10k.json --start_sample=$start_sample --end_sample=$end_sample --alg=C --num_subtasks=4
    echo $end_sample
done
