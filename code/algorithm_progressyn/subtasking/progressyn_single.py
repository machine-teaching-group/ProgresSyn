from itertools import compress
import itertools
import json
import copy
import torch

from code.algorithm_progressyn.interpreter.parser_for_synthesis import KarelForSynthesisParser
from code.algorithm_progressyn.subtasking.code_tracker import ExecutionTracker, AST, current_ast
from code.algorithm_progressyn.subtasking.domain_knowledge import is_equivalent_codes, task_diff, comp_depth_and_size, taskDis, number_of_unique_substructures
from code.algorithm_progressyn.subtasking.symbolic_exec import symbolicExecution
from code.algorithm_progressyn.interpreter.karel import Karel
from code.algorithm_progressyn.interpreter.utils import beautify, cprint, Tcolors
from code.algorithm_progressyn.interpreter.ast_to_code_converter import convert_ast_to_code



def progressyn_single(tvis, cin, hoc, rollout_param):
    '''
    Inputs: T^in, C^in
    '''
    ### Required Objects: ExecutionTracker

    # print("Running the code to obtain the execution trace")
    exec_tracker = ExecutionTracker()
    parser = KarelForSynthesisParser(exec_tracker, debug=False, max_func_call=1000)
    parser.new_game(state=tvis)
    exec_tracker.set_karel(parser.get_karel())
    parser.run(cin, tracking=True)
    cexec_trace = exec_tracker.get_ctoken_trace()
    grid_trace = exec_tracker.get_tvis_trace()
    # print("Execution trace is obtained")
    ## Preconditions_1: Grid_Trace, Cexec_Trace
    ## Required Function:
    #  GetValidSnapshots: From Grid_Trace and Cexec_Trace, generate ((T^1,C^1), (T^2, C^2), ..., (T^n, C^n))
    # print("Filtering execution trace")
    t_subs, c_subs, ast = get_valid_snapshots(tvis, grid_trace, cexec_trace, hoc=hoc, rollout_param=rollout_param)
#     t_subs = [[(tvis, t)] for t in t_subs]
    ## Post-condition: (T^1,C^1), (T^2, C^2), ..., (T^n, C^n)
#     for i,c in enumerate(c_subs):
#         print(c)
#         print(t_subs[i])

    return t_subs, c_subs

def _tvis_compute(cexec, tin, tout, ast, constraints, hoc):
#     print(f"Check if {cexec} is alright for {ast}")
    if cexec == "end-while-body":
#         print("End while body seen, let's check if it is valid")
#         print(beautify(convert_ast_to_code(ast.current_ast())))
        if ast.valid_snapshot(ast.current["iden"]):
#             print("Yes, it is.")
            if ast.current["alive"]:
#                 print("Loop alive, so symbolic execution will be done")
        #         print(ast.current)
                if "path" in ast.current["type"]:# and ast.current["alive"]:
                    typename = ast.current["type"]
        #             print(f"Symbolic execution for {typename}")
                    output = symbolicExecution(ast.current["type"], tin, tout, constraints, hoc=hoc)
                elif "goal" in ast.current["type"]:# and ast.current["alive"]:
        #             print("Goal Enters Symbolic")
                    output = symbolicExecution(ast.current["type"], tin, tout, constraints, hoc=hoc)
                elif "marker" in ast.current["type"]:# and ast.current["alive"]:
#                     cprint(f"Symbolic execution for {ast.current['type']}",Tcolors.CYAN)
                    output = symbolicExecution(ast.current["type"], tin, tout, constraints, hoc=hoc)
                else:
                    output =  None
            else:
#                 print("Loop isn't alive, so passing tout directly")
                output = symbolicExecution("no_change", tin, tout, constraints, hoc=hoc)
        else:
            output = None
        if not output is None:
            pass
#             print("There is a valid tout too")
    elif cexec == "end-while":
        if ast.valid_snapshot(ast.current["iden"]):
            if "path" not in ast.current["type"] and "goal" not in ast.current["type"] :
                output = symbolicExecution("no_change", tin, tout, constraints, hoc=hoc)
            else:
                output =  None
        else:
            output = None
    elif cexec == "end-repeat-body":
#         print("End repeat body seen, let's check if it is valid")
#         print(beautify(convert_ast_to_code(ast.current_ast())))
#         print(ast.root)
        if ast.valid_snapshot(ast.current["iden"]):#ast.current["alive"]:
#             print("Yes, it is.")
            output = symbolicExecution("no_change", tin, tout, constraints, hoc=hoc)
        else:
            output = None

    elif cexec == "EOL":
        output = symbolicExecution("no_change", tin, tout, constraints, hoc=hoc)

    else:
#         print(f"checking for action: {cexec}")
        ast.parse_trace([cexec])
        if ast.valid_snapshot(ast.last_block):# and not (hoc and "Turn" in cexec):
            return symbolicExecution("no_change", tin, tout, constraints, hoc=hoc)
        else:
#             print("None")
            return None
    ast.parse_trace([cexec])
    return output


def get_snapshot_indices(cexec_trace):
    '''
    From the sequence Cexec_Trace, get the indices where Cexec is an action block
    '''
#     for cexec in cexec_trace:
#         print(cexec)
    block_types = ["action", "end-while-body", "end-while", "end-repeat-body", "EOL"]
    return list(compress(range(len(cexec_trace)), map(lambda x: any([block in x for block in block_types]), cexec_trace)))


def add_constraint_from_conditional(tstate, conditional, value, constraints):
#     print(f"Adding constraint for {conditional} evaluated {value}")
    karel = Karel(state=tstate)
    cond = conditional.split('-')[1].lower()
    position_functions = {'ahead': karel._front, 'right': karel._right, 'left':karel._left}
    if 'bool_path' in cond:
        direction = cond.split('bool_path_')[1]
        pos = position_functions[direction]()
        if value:
            to_add = constraints['clear']
            to_check = constraints['blocked']
        else:
            to_add = constraints['blocked']
            to_check = constraints['clear']


    elif 'bool_no_path' in cond:
        direction = cond.split('bool_no_path_')[1]
        pos = position_functions[direction]()
        if not value:
            to_add = constraints['clear']
            to_check = constraints['blocked']
        else:
            to_add = constraints['blocked']
            to_check = constraints['clear']

    elif 'marker' in cond:
        pos = karel._position()
        if not pos in constraints['marker-history'].keys():
            constraints['marker-history'][pos] = []
        if ('bool_marker' in cond and value) or ('bool_no_marker' in cond and not value):
            constraints['marker-history'][pos].append('bool_marker')
        else:
            constraints['marker-history'][pos].append('bool_no_marker')
        return True
    elif "goal" in cond:
        return True
    else:
        raise Exception(f"Unknown Conditional {cond}")


    if pos in to_check:
        return False
    else:
        to_add.add(pos)
        return True

def add_constraint_from_agent_position(tstate, constraints):
    karel = Karel(state=tstate)
    pos = karel._position()
    if pos in constraints['blocked']:
        return False
    else:
        constraints['clear'].add(pos)
#         constraints['no_goal'].add(pos)
        return True

def marker_action_add_to_history(tstate, cexec, constraints):
    karel = Karel(state=tstate)
    pos = karel._position()
    if not pos in constraints['marker-history'].keys():
        constraints['marker-history'][pos] = []
    if "Put" in cexec:
        constraints['marker-history'][pos].append('put_marker')
    elif "Pick" in cexec:
        constraints['marker-history'][pos].append('pick_marker')
    else:
        raise Exception()



def get_valid_snapshots(tin, touts, cexecs, hoc, rollout_param):
    '''
    From the sequence Cexec_Trace, build the Code snapshots
    '''
    ast = AST(rollout_param)
    indices = get_snapshot_indices(cexecs)
    t_subs = []
    c_subs = []
    constraints = {}
    constraints['blocked'] = set()
    constraints['clear'] = set()
    constraints['marker-history'] = {}
#     constraints['no_marker'] = set()

    num_basic_actions = 0
#     constraints['no_goal'] = set()
#     print([cexecs[i] for i in indices])
#     print(cexecs)

    for i in range(len(cexecs)):
        # To be able to access the while loop that "end-while" closes,
        # parsing is done inside _tvis_compute
#         ast.parse_trace(cexecs[i:i+1])
        if i in indices:
            if "action" in cexecs[i] and cexecs[i] != 'action-NOP':
                num_basic_actions += 1
            success = add_constraint_from_agent_position(touts[i], constraints)
            if "action" in cexecs[i] and "Marker" in cexecs[i]:
                marker_action_add_to_history(touts[i], cexecs[i], constraints)
            assert success, "Conflict in constraints"
            tout = _tvis_compute(cexecs[i], tin, touts[i], ast, constraints, hoc=hoc)
            if not tout is None:
#                 print(f"Valid Snapshot Found for {cexecs[i]} and shortest path is: {num_basic_actions}")
#                 print(ast.get_copy())
                t_subs.append({"tout": tout, "shortest_path": num_basic_actions})
                c_subs.append(ast.get_copy())#current_ast())
        else:

            if 'condition' in cexecs[i]:
                if cexecs[i+1] in ['do', 'start-while-body']:
                    # Condition evaluated to True
                    value = True
                else:
                    # Condition evaluated to False
                    assert cexecs[i+1] in ['else', 'end-while'], "Unexpected next token"
                    value = False
                success = add_constraint_from_conditional(touts[i], cexecs[i], value, constraints)
                assert success, "Conflict in constraints"


            ast.parse_trace(cexecs[i:i+1])
#     print(constraints['marker-history'])
    return t_subs, c_subs, ast
