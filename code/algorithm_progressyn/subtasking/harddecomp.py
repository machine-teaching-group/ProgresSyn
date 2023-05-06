import itertools
import json
import copy

from code.algorithm_progressyn.interpreter.parser_for_synthesis import KarelForSynthesisParser
from code.algorithm_progressyn.interpreter.karel import Karel
from code.algorithm_progressyn.interpreter.utils import beautify, cprint, Tcolors
from code.algorithm_progressyn.interpreter.ast_to_code_converter import AstToCodeConverter,convert_ast_to_code

from code.algorithm_progressyn.subtasking.code_tracker import ExecutionTracker, AST, current_ast
from code.algorithm_progressyn.subtasking.domain_knowledge import number_of_unique_substructures, is_equivalent_codes
from code.algorithm_progressyn.subtasking.subsequence_selection_algorithms import subtask_selection_dp_single_candidate_list_compare as subtask_selection_dp
from code.algorithm_progressyn.subtasking.progressyn_single import progressyn_single
from code.algorithm_progressyn.subtasking.progressyn_grids import progressyn_grids
from code.algorithm_progressyn.subtasking.backprop_grids import backpropagation_grids

def harddecomp(tin, cin,
              K, # 0,
              N, # 0
              completeness, # comp_depth_and_size,
              code_quality, # lambda x,y: 1,
              alg, # 'B',
              hoc): #  False):

    '''
    Algorithms:
    grids : Task level decomposition only
    fine-grained : Single-grid decomposition + Task level decomposition
    with-backprop : Alg fine-grained + Backpropagation of
                          grids to enhance single grid subtasks
    '''
    assert alg in ['grids', 'fine-grained', 'with-backprop'], "Unknown alg name, must be one of ['grids', 'fine-grained', 'with-backprop']"
    rollout_param=None

    ## Index input grids and put in a dict
    tin = [{'ind':i, 'pre':t[0], 'post':t[1]} for i, t in enumerate(tin)]

    cprint(f"Running ProgresSyn-Grids", Tcolors.OKBLUE)
    ## Decompose full grids, ie. find the grid order
    t_subs_multi, c_subs_multi = progressyn_grids(tin, cin, completeness) # t_subs = List[List[dict{}]]

    if len(t_subs_multi) > N:
        ## Choose N subtasks from task level decomposition
        t_subs_multi, c_subs_multi = choose_subtasks(t_subs_multi, c_subs_multi, N,
                                                     code_quality,
                                                     completeness,
                                                     rollout_param=rollout_param)

    ## Logging
    cprint(f"ProgresSyn-Grids is done, number of subtasks: {len(t_subs_multi)}", Tcolors.OKBLUE)
    cprint(f" The obtained snapshots are: ", Tcolors.OKGREEN)
    for i, c in enumerate(c_subs_multi):
        cprint(f"Snapshot {i} with complexity {completeness(c,rollout_param=2)}", Tcolors.CYAN)
        print(beautify(convert_ast_to_code(current_ast(c))))

    assert len(t_subs_multi) == len(c_subs_multi)

    t_subs_single, c_subs_single = [], []
    ## If single grid decomposition will be used
    if alg in ['fine-grained', 'with-backprop']:
        cprint(f"Running ProgresSyn-Single", Tcolors.OKBLUE)        
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
        cprint(f"By ProgresSyn-Single, we found {len(t_subs_single)} new subtasks from decomping the first grid")
        cprint(f" The obtained snapshots are: ", Tcolors.OKGREEN)
        for i, (c,t) in enumerate(zip(c_subs_single, t_subs_single)):
            cprint(f"Snapshot {i} with complexity {completeness(c,rollout_param)}, and shortest path {t[0]['shortest_path']}", Tcolors.CYAN)
            print(beautify(convert_ast_to_code(current_ast(c, rollout_param=rollout_param))))

        ## Choose K subtasks for single grid decomposition
        if K > 0:
            cprint("Choosing subtasks")
            t_subs_single, c_subs_single = choose_subtasks(t_subs_single, c_subs_single, K, code_quality,
                                                           completeness,
                                                           rollout_param=rollout_param)

            cprint(f"After trying to choose {K} subtasks from the single grid snapshots, we've chosen {len(t_subs_single)} subtasks")

        assert len(t_subs_multi[0]) == 1 and t_subs_single[0][0]['ind'] == t_subs_multi[0][0]['ind']
        t_subs_multi, c_subs_multi = t_subs_multi[1:], c_subs_multi[1:]

    t_subs, c_subs = t_subs_single + t_subs_multi, c_subs_single + c_subs_multi
    assert len(t_subs) == len(c_subs)

    if alg in ['with-backprop']:
        t_subs, c_subs = backpropagation_grids(tin, t_subs, c_subs, cin,  hoc, rollout_param)
        cprint(f"After backpropagation there are {len(t_subs)} subtasks")
        assert len(t_subs) == len(c_subs)

#     print("Number of grids per subtask")
#     for t in t_subs:
#         print(t[0]["post"].shape)


    return (t_subs, c_subs), len(c_subs), get_actions_dict(tin, cin), rollout_param if rollout_param else 2



def choose_subtasks(t_subs, c_subs, K, code_quality, code_complexity, rollout_param):
    ## Binary Elimination
    good_snapshots_idxs = [i for i, c in enumerate(c_subs) if code_quality(c) > 0]
    print(f"Out of {len(c_subs)} code snapshots, {len(good_snapshots_idxs)} are good")
    good_codes = [c_subs[i] for i in good_snapshots_idxs]
    good_tasks = [t_subs[i] for i in good_snapshots_idxs]    
    
    inds_same_code_with_last_subtask = []    
    for i, c in enumerate(good_codes):
        if is_equivalent_codes(current_ast(c, rollout_param=rollout_param), current_ast(good_codes[-1], rollout_param=rollout_param)):
            print(i)
            inds_same_code_with_last_subtask.append(i)
    assert len(inds_same_code_with_last_subtask) > 0
    print("Snapshots with the same code as last subtask: ", inds_same_code_with_last_subtask)
    subtask_indices = [inds_same_code_with_last_subtask[i*(len(inds_same_code_with_last_subtask)//(K-1))] for i in range(K-1)]
    print("Chosen snapshots: ", subtask_indices)    
    return [good_tasks[i] for i in subtask_indices] + [good_tasks[-1]], [good_codes[i] for i in subtask_indices] + [good_codes[-1]]
    

def get_actions_dict(tin, cin):
    actions_dict = {}
    for t in tin:
        exec_tracker = ExecutionTracker()
        parser = KarelForSynthesisParser(exec_tracker, debug=False, max_func_call=1000)
        parser.new_game(state=t['pre'])
        exec_tracker.set_karel(parser.get_karel())
        parser.run(cin, tracking=True)
        cexec_trace = exec_tracker.get_ctoken_trace()
        actions = [token for token in cexec_trace if "action" in token]
        actions_dict[t['ind']] = actions

    return actions_dict
