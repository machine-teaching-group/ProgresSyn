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


# fcode = fcode_wang_sequencing

if __name__ == '__main__':

    data_out_path = os.path.join("data","output", "out_algorithm_progressyn_demo")
    input_task_id = "karel-stairway"
    input_program_path = os.path.join("data","input_algorithm_progressyn_demo")
    tempdir = os.path.join("data", "_temp_input")
    num_subtasks = 3


    Path(tempdir).mkdir(parents=True, exist_ok=True)
    convert_files(os.path.join(input_program_path, f"{input_task_id}_code.json"), tempdir)
    with open(os.path.join(input_program_path,f"{input_task_id}_code.json")) as file:
        codejson=json.load(file)
#         codejson = json.loads(file.readline())

    with open(os.path.join(tempdir, f'{input_task_id}_code.txt')) as fp:
        code = fp.read()

    if "hoc" in input_task_id:
        codejson = hoc2kareljson(codejson)

    grids = tin_converter(os.path.join(input_program_path, f"{input_task_id}_task.txt"), verbose=True)
    iostates = grid2state(grids)

    def compare_to_reference(c):
        return code_quality(c, codejson)


    if len(iostates) == 1:
        print("This is a single grid task, the output will be same with greedy heuristic")
        (t_subs, c_subs), k, _, rollout_param = progressyn(iostates, code, K=num_subtasks, N=10,
                                                          completeness=comp_depth_and_size,
                                                          code_quality=compare_to_reference,
                                                          alg='fine-grained', hoc='hoc' in input_task_id)

    else:
        print("Running exhaustive enumeration of all grid orders")
        (t_subs, c_subs), k, rollout_param = progressyn_exhaustive(iostates, code, K=num_subtasks, N=10,
                                                                    completeness=comp_depth_and_size,
                                                                    code_quality_func=compare_to_reference,
                                                                    hoc='hoc' in input_task_id)

    os.makedirs(os.path.join(data_out_path,input_task_id), exist_ok=True)
    dump_pdf_multigrid(t_subs, c_subs, None, os.path.join(data_out_path,input_task_id), input_task_id, rollout_param)
    dump_output(t_subs, c_subs, data_out_path, input_task_id, rollout_param)
