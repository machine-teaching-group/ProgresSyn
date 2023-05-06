import itertools
import copy

from code.algorithm_progressyn.interpreter.parser_for_synthesis import KarelForSynthesisParser
from code.algorithm_progressyn.interpreter.utils import beautify, cprint, Tcolors
from code.algorithm_progressyn.interpreter.ast_to_code_converter import convert_files, convert_ast_to_code
from code.algorithm_progressyn.subtasking.progressyn import choose_subtasks
from code.algorithm_progressyn.subtasking.progressyn_single import progressyn_single
from code.algorithm_progressyn.subtasking.domain_knowledge import (taskDis, multiTaskDisGenerator, number_of_unique_substructures)
from code.algorithm_progressyn.subtasking.code_tracker import ExecutionTracker, AST, current_ast


def progressyn_exhaustive(tin, cin, K, N, completeness, code_quality_func, hoc):

    def isBetterAllSeq(score1, score2):
        return (score1[0] < score2[0] or
                (score1[0] == score2[0] and score1[1] > score2[1]) or
                (score1[0] == score2[0] and score1[1] == score2[1] and score1[2] > score2[2]))
    best_first_grid = None
    best_score_allseq = None
    ## Index input grids and put in a dict
    tin = [{'ind':i, 'pre':t[0], 'post':t[1]} for i, t in enumerate(tin)]

    for first_grid_ind in range(len(tin)):
        cprint(f"Trying {first_grid_ind} as the first grid", Tcolors.OKBLUE)

        rollout_param=None


        ## Fix the first grid
        t_subs = [[tin[first_grid_ind]]]
        # Compute AST
        ast = AST()
        exec_tracker = ExecutionTracker()
        parser = KarelForSynthesisParser(exec_tracker, debug=False, max_func_call=1000)
        parser.new_game(state=tin[first_grid_ind]['pre'])
        exec_tracker.set_karel(parser.get_karel())
        parser.run(cin, tracking=True)
        cexec_trace = exec_tracker.get_ctoken_trace()
        num_basic_actions = sum([1 for cexec in cexec_trace if ("action" in cexec and cexec!="action-NOP")])
        ast.parse_trace(cexec_trace)
        c_subs = [ast.get_copy()]


        ## Find the order for remaining grids
        remaining_idxs = list(range(len(tin)))
        remaining_idxs.remove(first_grid_ind)
        multiTaskDis = multiTaskDisGenerator(tin)
        def isBetter(score1, score2):
            return score1[0] < score2[0] or (score1[0] == score2[0] and score1[1] > score2[1])

        subtask_permutations = []
        best_perm = None
        best_score = None
        for perm in itertools.permutations(remaining_idxs):
            ast_temp = copy.deepcopy(ast)
            t_sequence = [t_subs[-1]]
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

        t_subs_multi, c_subs_multi = best_seq[0], best_seq[1]

        ## Logging
        cprint(f"Task-level decomposition done, number of subtasks: {len(t_subs_multi)}", Tcolors.OKBLUE)
        cprint(f" The obtained snapshots are: ", Tcolors.OKGREEN)
        for i, c in enumerate(c_subs_multi):
            cprint(f"Snapshot {i} with complexity {completeness(c,rollout_param=2)}", Tcolors.CYAN)
            print(beautify(convert_ast_to_code(current_ast(c))))

        assert len(t_subs_multi) == len(c_subs_multi)

        t_subs_single, c_subs_single = [], []
        ## Decompose the first grid
        # Find the first grid
        first_grid = tin[t_subs_multi[0][0]['ind']]
        pregrid = first_grid['pre']
        # Decompose the grid with rollout_param=1 and rollout_param=2
        t1_subs_rollout1, c1_subs_rollout1 = progressyn_single(pregrid, cin, hoc, 1)
        t1_subs_rollout2, c1_subs_rollout2 = progressyn_single(pregrid, cin, hoc, 2)
        # Count the number of unique substructures in snapshots
        n_substructure_param1 = number_of_unique_substructures(c1_subs_rollout1, 1)
        n_substructure_param2= number_of_unique_substructures(c1_subs_rollout2, 2)
        # rollout_param should be 2 if rollout_param=1 doesn't give anything extra
        rollout_param = 1 if n_substructure_param1 > n_substructure_param2 else 2
        print(f"Number of unique structures per rollout param { n_substructure_param1, n_substructure_param2 }")
        t_subs_single = t1_subs_rollout1 if rollout_param == 1 else t1_subs_rollout2
        c_subs_single = c1_subs_rollout1 if rollout_param == 1 else c1_subs_rollout2

        ## progressyn_single returns List[List[dict{"tout":, "shortest_path"}]. Expand "tout" item.
        t_subs_single = [[{'ind':t_subs_multi[0][0]['ind'],
                           'pre':t["tout"][0],
                           'post':t["tout"][1],
                           "shortest_path":t["shortest_path"]}] for t in t_subs_single]
        assert len(t_subs_single) == len(c_subs_single)

    #         ## Logging
        cprint(f"By action level decomposition, we found {len(t_subs_single)} new subtasks from decomping the first grid")
        cprint(f" The obtained snapshots are: ", Tcolors.OKGREEN)
        for i, (c,t) in enumerate(zip(c_subs_single, t_subs_single)):
            cprint(f"Snapshot {i} with complexity {completeness(c,rollout_param)}, and shortest path {t[0]['shortest_path']}", Tcolors.CYAN)
            print(beautify(convert_ast_to_code(current_ast(c, rollout_param=rollout_param))))

        ## Choose K subtasks for single grid decomposition
        if K > 0:
            cprint("Choosing subtasks")
            t_subs_single, c_subs_single = choose_subtasks(t_subs_single, c_subs_single, K, code_quality_func,
                                                           completeness,
                                                           rollout_param=rollout_param)

            cprint(f"After trying to choose {K} subtasks from the single grid snapshots, we've chosen {len(t_subs_single)} subtasks")

        assert len(t_subs_multi[0]) == 1 and t_subs_single[0][0]['ind'] == t_subs_multi[0][0]['ind']


#         if alg in ['D']:
#             t_subs, c_subs = backpropagation_grids(tin, t_subs, c_subs, cin,  hoc, rollout_param)
#             cprint(f"After backpropagation there are {len(t_subs)} subtasks")
#             assert len(t_subs) == len(c_subs)

        c_sequence = c_subs_single + c_subs_multi[1:]
        c_sequence.insert(0, {"type":"run", "alive":True, "children":[]})
        complexity_seq = [completeness(c, rollout_param=rollout_param) for c in c_sequence]
        complexity_score = max([min([complexity_seq[i] - complexity_seq[j] for j in range(i)]) for i in range(1,len(complexity_seq))])


        t_subs_single.insert(0, [{"shortest_path":0}])

        diversity_score_single = min([min([taskDis(t_subs_single[i], t_subs_single[j]) for j in range(i)]) for i in range(1, len(t_subs_single))])

        diversity_score_multi = min([min([multiTaskDis(t_subs_multi[i], t_subs_multi[j]) for j in range(i)]) for i in range(1, len(t_subs_multi))])

        cprint(f"{first_grid_ind}", Tcolors.CYAN)
        print(f"complexity_seq={complexity_seq}")
        print(f"complexity_score={complexity_score}")
        print(f"diversity_score_single={diversity_score_single}")
        print(f"diversity_score_multi={diversity_score_multi}")

        score_allseq = (complexity_score, diversity_score_single, diversity_score_multi)


        t_subs_multi, c_subs_multi = t_subs_multi[1:], c_subs_multi[1:]
        t_subs, c_subs = t_subs_single[1:] + t_subs_multi, c_subs_single + c_subs_multi
        assert len(t_subs) == len(c_subs)

        if (best_first_grid is None) or isBetterAllSeq(score_allseq, best_score_allseq):
           print(f"{score_allseq} is found better than {best_score_allseq}")
           best_first_grid = first_grid_ind
           best_score_allseq = score_allseq
           best_subtasking = (t_subs, c_subs)
           best_rollout_param = rollout_param


    return (best_subtasking[0], best_subtasking[1]), len(best_subtasking[0]), best_rollout_param if best_rollout_param else 2
