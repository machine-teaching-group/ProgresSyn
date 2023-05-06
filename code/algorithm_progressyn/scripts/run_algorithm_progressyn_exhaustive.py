import argparse
import os
from pathlib import Path
import json


from code.algorithm_progressyn.interpreter.utils import tin_converter, hoc2karel, grid2state, hoc2kareljson
from code.algorithm_progressyn.interpreter.utils import beautify, cprint, Tcolors
from code.algorithm_progressyn.interpreter.ast_to_code_converter import convert_files, convert_ast_to_code
from code.algorithm_progressyn.subtasking.progressyn import progressyn
from code.algorithm_progressyn.subtasking.progressyn_exhaustive import progressyn_exhaustive
from code.algorithm_progressyn.subtasking.decomposer_io_utils import dump_pdf_multigrid, dump_output
from code.algorithm_progressyn.subtasking.domain_knowledge import (comp_depth_and_size, code_quality)


if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--data_out_path', type=str, default="data/output/subtasks/", help='output folder path for generated subtasks tasks')
    arg_parser.add_argument('--input_task_id', type=str, required=True, help='task_id, expected code/task file names: {input_task_id}_code.json/{input_task_id}_task.txt')
    arg_parser.add_argument('--input_program_path', type=str, default="data/input_algorithm_progressyn_demo/", help='path to reference code and task')
    arg_parser.add_argument('--num_subtasks', type=int, default=3, help='the number of subtasks to generate for progressyn_single')

    args = arg_parser.parse_args()
    Path("data/output/_temp_input/").mkdir(parents=True, exist_ok=True)
    convert_files(os.path.join(args.input_program_path, f"{args.input_task_id}_code.json"), "data/output/_temp_input/")
    with open(os.path.join(args.input_program_path,f"{args.input_task_id}_code.json")) as file:
        codejson=json.load(file)

    with open(f'data/output/_temp_input/{args.input_task_id}_code.txt') as fp:
        code = fp.read()

    if "hoc" in args.input_task_id:
        codejson = hoc2kareljson(codejson)

    grids = tin_converter(os.path.join(args.input_program_path, f"{args.input_task_id}_task.txt"), verbose=True)
    iostates = grid2state(grids)

    def compare_to_reference(c):
        return code_quality(c, codejson)

    if len(iostates) == 1:
        print("This is a single grid task, the output will be same with greedy heuristic")
        (t_subs, c_subs), k, _, rollout_param = progressyn(iostates, code, K=args.num_subtasks, N=10,
                                                          completeness=comp_depth_and_size,
                                                          code_quality=compare_to_reference,
                                                          alg='fine-grained', hoc='hoc' in args.input_task_id)

    else:
        print("Running exhaustive enumeration of all grid orders")
        (t_subs, c_subs), k, rollout_param = progressyn_exhaustive(iostates, code, K=args.num_subtasks, N=10,
                                                                    completeness=comp_depth_and_size,
                                                                    code_quality_func=compare_to_reference,
                                                                    hoc='hoc' in args.input_task_id)



    os.makedirs(os.path.join(args.data_out_path,args.input_task_id), exist_ok=True)
    dump_pdf_multigrid(t_subs, c_subs, None, os.path.join(args.data_out_path,args.input_task_id), args.input_task_id, rollout_param)
    dump_output(t_subs, c_subs, args.data_out_path, args.input_task_id, rollout_param)
