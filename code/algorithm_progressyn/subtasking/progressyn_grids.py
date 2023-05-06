import itertools
import json
import copy

from code.algorithm_progressyn.interpreter.parser_for_synthesis import KarelForSynthesisParser
from code.algorithm_progressyn.subtasking.code_tracker import ExecutionTracker, AST, current_ast
from code.algorithm_progressyn.subtasking.domain_knowledge import multiTaskDisGenerator
from code.algorithm_progressyn.interpreter.karel import Karel
from code.algorithm_progressyn.interpreter.utils import cprint, Tcolors


def progressyn_grids(tin, cin, completeness):
    ast = AST()
    remaining_idxs = list(range(len(tin)))
    t_subs = []
    c_subs = []
    ast, t, next_ind, remaining_idxs = choose_next_grid(tin, remaining_idxs,  cin, ast, completeness)
    t_subs.append(t_subs[-1] + [t] if len(t_subs) > 0 else [t])
    c_subs.append(ast.get_copy())

    if len(remaining_idxs) == 0:
        best_seq = (t_subs, c_subs)
    else:
        multiTaskDis = multiTaskDisGenerator(tin)
        def isBetter(score1, score2):
            return score1[0] < score2[0] or (score1[0] == score2[0] and score1[1] > score2[1])

        subtask_permutations = []
        best_perm = None
        best_score = None
        for perm in itertools.permutations(remaining_idxs):
            ast_temp = copy.deepcopy(ast)
            t_sequence = [[t]]
            c_sequence = [ast_temp.get_copy()]

            for i in perm:
                exec_tracker = ExecutionTracker()
                parser = KarelForSynthesisParser(exec_tracker, debug=False, max_func_call=1000)
                parser.new_game(state=tin[i]['pre'])
                exec_tracker.set_karel(parser.get_karel())
                parser.run(cin, tracking=True)
                cexec_trace = exec_tracker.get_ctoken_trace()
                num_basic_actions = sum([1 for cexec in cexec_trace if ("action" in cexec and cexec!="action-NOP")])
                ast_temp.parse_trace(cexec_trace)
                t_sequence.append(t_sequence[-1] + [tin[i]] if len(t_subs) > 0 else [tin[i]])
                c_sequence.append(ast_temp.get_copy())


            complexity_seq = [completeness(c, rollout_param=2) for c in c_sequence]
            complexity_score = max([min([complexity_seq[i] - complexity_seq[j] for j in range(i)]) for i in range(1,len(complexity_seq))])
            diversity_score = min([min([multiTaskDis(t_sequence[i], t_sequence[j]) for j in range(i)]) for i in range(1, len(t_sequence))])
            cprint(f"{perm}", Tcolors.CYAN)

            print(f"complexity_seq={complexity_seq}")
            print(f"complexity_score={complexity_score}")
            print(f"diversity_score={diversity_score}")
            score = (complexity_score, diversity_score)
            if (best_perm is None) or isBetter(score, best_score):
               print(f"{score} is found better than {best_score}")
               best_perm = perm
               best_score = score
               best_seq = (t_sequence, c_sequence)
        print(f"best_score={best_score}")
    return best_seq[0], best_seq[1]


def choose_next_grid(tin, remaining_idxs, c_in, ast_curr, completeness):
    '''
    remaining_tins:
    completeness: A function that compares an ast to a reference code and scores its completeness
    '''
    max_score = -1
    print(remaining_idxs)
#     print('\033[92m' + f" Current Code " + '\033[0m')
#     try:
#         print(ast_curr.readable_code())
#         print(json.dumps(ast_curr.root, indent=4))
#     except Exception as e:
#         print("Empty Code")

    for i in remaining_idxs:
        ast = copy.deepcopy(ast_curr)
        exec_tracker = ExecutionTracker()
        parser = KarelForSynthesisParser(exec_tracker, debug=False, max_func_call=1000)
        parser.new_game(state=tin[i]['pre'])
        exec_tracker.set_karel(parser.get_karel())
        parser.run(c_in, tracking=True)
        cexec_trace = exec_tracker.get_ctoken_trace()
        num_basic_actions = sum([1 for cexec in cexec_trace if ("action" in cexec and cexec!="action-NOP")])
#         grid_trace = exec_tracker.get_tvis_trace()
        ast.parse_trace(cexec_trace)
#         print('\033[92m' + f" Code after running example {i} " + '\033[0m')
#         print(ast.readable_code())
#         print(json.dumps(ast.root, indent=4))
        score = completeness(ast.get_copy(), rollout_param=2)#, c_in)
        if score > max_score:
            max_score = score
            best_num_basic_actions = num_basic_actions
            best_ind = i
            best_ast = ast
    best_t = tin[best_ind]
    best_t["shortest_path"] = best_num_basic_actions
    remaining_idxs.remove(best_ind)
    return best_ast, best_t, best_ind, remaining_idxs
