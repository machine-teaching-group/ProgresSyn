import argparse
import os
from pathlib import Path
import json

from code.algorithm_progressyn.interpreter.parser_for_synthesis import KarelForSynthesisParser
from code.algorithm_progressyn.interpreter.utils import beautify, cprint, Tcolors, tin_converter, hoc2karel, grid2state
from code.algorithm_progressyn.interpreter.ast_to_code_converter import convert_files, AstToCodeConverter
from code.algorithm_progressyn.subtasking.progressyn import progressyn
from code.algorithm_progressyn.subtasking.harddecomp import harddecomp
from code.algorithm_progressyn.subtasking.domain_knowledge import (task_diff, comp_depth_and_size, code_quality)

from code.algorithm_progressyn.interpreter.karel import Karel
from code.algorithm_progressyn.subtasking.code_tracker import current_ast

# from code.agents_neural.karel.world import
from code.utils.progressyn_neural_converters import iclr2carpedm_task, iclr2carpedm_code, to_iclr_dataset, to_iclr_dataset_dict
# from code.agents_neural.karel.ast
# fcode = fcode_wang_sequencing

if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--data_out_path', type=str, default="data/output/agents_neural_generated_dataset/", help='output folder path for new tasks')
    arg_parser.add_argument('--input_dataset', type=str, required=True, help='task_id in correct format: in-hoc-A / in-karel-E / etc')
    arg_parser.add_argument('--input_program_path', type=str, default="data/input_agents_neural/datasets/", help='path to program as AST in json format')
#     arg_parser.add_argument('--grid_order', type=int, nargs='+', default=-1, help='the sequence of grids to be processed')
    arg_parser.add_argument('--num_subtasks', type=int, default=5, help='the number of subtasks to generate')
    arg_parser.add_argument('--alg', choices=['grids', 'fine-grained', 'with-backprop'], default='fine-grained', help='the algorithm to be used')
    arg_parser.add_argument('--baseline', choices=['progressyn', 'harddecomp'], default='fine-grained', help='the baseline to be generated') 
    arg_parser.add_argument('--end_sample', type=int, default=10, help='the number of samples to generate subtasks for in this dataset')
    arg_parser.add_argument('--start_sample', type=int, default=0, help='the number of samples to generate subtasks for in this dataset')
    arg_parser.add_argument('--keep_progression', action='store_true', help='Setting this saves the subtasks of a task in a dict')
    # arg_parser.add_argument('--throw_in_rest', action="store_true", help='throw-in remaining grids if the whole code is covered')
    # arg_parser.add_argument('--snapshots', action="store_true", help='subtask elimination active')
    # arg_parser.add_argument('--num_diverse_tasks', type=int, default=10, help='number of diverse new tasks to generate for input task')
    args = arg_parser.parse_args()
#     Path("../_temp_input/").mkdir(parents=True, exist_ok=True)
#     convert_files(os.path.join(args.input_program_path, f"{args.input_task_id}_code.json"), "../_temp_input/")
#     with open(f'../_temp_input/{args.input_task_id}_code.txt') as fp:
#         code = fp.read()

    if args.baseline == "progressyn":
        decompose = progressyn
    elif args.baseline == "harddecomp":
        decompose = harddecomp
    else:
        raise Exception("Unknown baseline")

    ast_conv = AstToCodeConverter()
    failed_samples = []
    samples_with_unactivated_branches = []
    nsubtasks = []
    run_name = "from_" + str(args.start_sample) + "_to_" + str(args.end_sample)
    Path(args.data_out_path).mkdir(parents=True, exist_ok=True)
    dataset_save_func = to_iclr_dataset_dict if args.keep_progression else to_iclr_dataset
    with open(os.path.join(args.input_program_path, args.input_dataset)) as file:
        i = -1
        for line in file.readlines():
            i += 1
            if i >= args.start_sample:
                try:
                    cprint(f"Start decomposing sample {i}", Tcolors.FAIL)
                    d = json.loads(line)
#                     print(d['program_tokens'])
                    code = iclr2carpedm_code(d['program_tokens'])
#                     print(code)
                    iostates = iclr2carpedm_task(d['examples'])
        #             for state in iostates:
        #                 Karel(state=state[0]).draw()
        #             print(iostates[0][0])
#                     subtask_elimination = False if args.snapshots else True
#                     (t_subs, c_subs), k, best_order, actions_dict = decompose_task(iostates, code, args.num_subtasks, fcode,
#                                                          subtask_elimination =  subtask_elimination, hoc=False)#"hoc" in args.input_task_id)


                    (t_subs, c_subs), k, actions_dict, rollout_param = decompose(iostates, code, K=args.num_subtasks, N=10,
                                                                  completeness=comp_depth_and_size,
                                                                  code_quality=lambda x: 1,
                                                                  alg=args.alg,
                                                                  # throw_in_rest=args.throw_in_rest,
                                                                  hoc=False)
                    nsubtasks.append(len(c_subs))
                    c_subs_ast = c_subs
                    c_subs = []
                    for c in c_subs_ast:
    #                     print(json.dumps(c, indent=4))
                        c = current_ast(c)
                        c_subs.append(ast_conv.to_tokens(c))
    #                     print(c_subs[-1])

                    with open(os.path.join(args.data_out_path, "nsubtasks" + run_name + ".csv"), 'w') as file:
                        file.write(",".join(map(str,nsubtasks)))
                    dataset_save_func("subtasks" + "_" + run_name, args.data_out_path, c_subs, t_subs, actions_dict)
                    if i > args.end_sample:
                        break

                except UnboundLocalError as e:
                    print(f"ERROR IN DECOMPOSING SAMPLE {i}")
                    print(e)
                    samples_with_unactivated_branches.append(i)
                    with open(os.path.join(args.data_out_path, "samples_with_unactivated_branches" + run_name + ".csv"), 'w') as file:
                        file.write(",".join(map(str,samples_with_unactivated_branches)))
#                     if input("exit? (y/n)") != "y":
#                         pass
#                     else:
#                         exit()


                except Exception as e:
                    print(f"ERROR IN DECOMPOSING SAMPLE {i}")
                    print(e)
                    failed_samples.append(i)
                    with open(os.path.join(args.data_out_path, "failed_samples" + run_name + ".csv"), 'w') as file:
                        file.write(",".join(map(str,failed_samples)))

    with open(os.path.join(args.data_out_path, "samples_with_unactivated_branches" + run_name + ".csv"), 'w') as file:
        file.write(",".join(map(str,samples_with_unactivated_branches)))
    with open(os.path.join(args.data_out_path, "failed_samples" + run_name + ".csv"), 'w') as file:
        file.write(",".join(map(str,failed_samples)))



    #             os.makedirs(os.path.join(args.data_out_path, str(c)), exist_ok=True)
    #             dump_pdf(t_subs, c_subs, k, os.path.join(args.data_out_path, str(c)), str(c), fcode,
    #                      subtask_elimination = subtask_elimination)
