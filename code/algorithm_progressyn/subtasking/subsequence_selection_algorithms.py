import bisect

from code.algorithm_progressyn.subtasking.domain_knowledge import taskDis
from code.algorithm_progressyn.interpreter.utils import beautify, cprint, Tcolors
from code.algorithm_progressyn.interpreter.ast_to_code_converter import convert_ast_to_code
from code.algorithm_progressyn.subtasking.code_tracker import current_ast

def subtask_selection_dp_multi_candidate(c_subs, t_subs, K, fcode, rollout_param):
#     print(f"Choose K={K} subtasks")
#     for i, (c,t) in enumerate(zip(c_subs, t_subs)):
#         cprint(f"Snapshot {i} with complexity {fcode(c, rollout_param)}, and shortest path {t[0]['shortest_path']}", Tcolors.CYAN)
#         print(beautify(convert_ast_to_code(current_ast(c, rollout_param=rollout_param))))


    def notWorse(tuple1, tuple2):
        return (tuple1[0] < tuple2[0]) or (tuple1[0] == tuple2[0] and tuple1[1] >= tuple2[1])

    def deltafcode(c1, c2):
        return fcode(c2, rollout_param) - fcode(c1, rollout_param)


    N = len(c_subs)
    c_subs.insert(0, {"type":"run", "alive":True, "children":[]})
    t_subs.insert(0, [{"shortest_path":0}])

    tableM = [[(1e5, 0) for i in range(N+1)] for j in range(K+1)]
    tableM[0] = [(deltafcode(c_subs[0], c_subs[j]), taskDis(t_subs[j], t_subs[0])) for j in range(N+1)]

    tableU = [[None for i in range(N+1)] for j in range(K+1)]#[[None]*N]*(K+1)
    tableU[0] = [[[0, i]] for i in range(N+1)]
    # N + 1 because we will add empty subtask, K + 1 because empty subtask should always be a part of this

    for j in range(0, N+1):
        for i in range(1, K+1, 1):
            combined_tuple = (max(tableM[i-1][0][0], min([deltafcode(c_subs[ind], c_subs[j]) for ind in tableU[i-1][0][0]])),
                              min(tableM[i-1][0][1], taskDis(t_subs[j], t_subs[0])))
            tableM[i][j] = combined_tuple
            tableU[i][j] = [tableU[i-1][0][0] + [j]]
            for k in range(1, j):
                for candidate_list in tableU[i-1][k]:
                    combined_tuple = (max(tableM[i-1][k][0], min([deltafcode(c_subs[ind], c_subs[j]) for ind in candidate_list])),
                                      min(tableM[i-1][k][1], taskDis(t_subs[j], t_subs[k])))
                    if notWorse(combined_tuple, tableM[i][j]):
                        if notWorse(tableM[i][j],combined_tuple):
                            tableM[i][j] = combined_tuple
                            tableU[i][j] += [candidate_list + [j]]
                        else:
                            tableM[i][j] = combined_tuple
                            tableU[i][j] = [candidate_list + [j]]
#     print("tableM")
#     for row in tableM:
#         print(row)

#     print("tableU")
#     for row in tableU:
#         print(row)


    list_of_candidate_lists = tableU[K][-1]
    best_differences = None
    best_candidate_list = None
    for candidate_list in list_of_candidate_lists:
        differences = [taskDis(t_subs[candidate_list[i+1]], t_subs[candidate_list[i]]) for i in range(len(candidate_list)-1)]
        sorted_differences = sorted(differences)
        if best_differences is None or best_differences <= sorted_differences:
            print(f"Previous best differences: {best_differences}")
            print(f"New best differences: {sorted_differences}")
            best_differences=sorted_differences
            best_candidate_list = candidate_list

    indices = best_candidate_list[1:-1]
    for ind in indices:
        print(f"ind={ind}")
        print(fcode(c_subs[ind], rollout_param), t_subs[ind][0]["shortest_path"])
    return indices #t_subs_k, c_subs_k

def subtask_selection_dp_single_candidate_list_compare(c_subs, t_subs, K, fcode, rollout_param):
#     print(f"Choose K={K} subtasks")
#     for i, (c,t) in enumerate(zip(c_subs, t_subs)):
#         cprint(f"Snapshot {i} with complexity {fcode(c, rollout_param)}, and shortest path {t[0]['shortest_path']}", Tcolors.CYAN)
#         print(beautify(convert_ast_to_code(current_ast(c, rollout_param=rollout_param))))


    def notWorse(tuple1, tuple2):
        return (tuple1[0] < tuple2[0]) or (tuple1[0] == tuple2[0] and tuple1[1] >= tuple2[1])

    def deltafcode(c1, c2):
        return fcode(c2, rollout_param) - fcode(c1, rollout_param)


    N = len(c_subs)
    c_subs.insert(0, {"type":"run", "alive":True, "children":[]})
    t_subs.insert(0, [{"shortest_path":0}])

    tableM = [[(1e5, 0) for i in range(N+1)] for j in range(K+1)]
    tableM[0] = [(deltafcode(c_subs[0], c_subs[j]), [taskDis(t_subs[j], t_subs[0])]) for j in range(N+1)]

    tableU = [[None for i in range(N+1)] for j in range(K+1)]#[[None]*N]*(K+1)
    tableU[0] = [[0, i] for i in range(N+1)]
    # N + 1 because we will add empty subtask, K + 1 because empty subtask should always be a part of this

    for j in range(0, N+1):
        for i in range(1, K+1, 1):
            subseq = tableM[i-1][0][1].copy()
            bisect.insort(subseq, taskDis(t_subs[j], t_subs[0]))
            combined_tuple = (max(tableM[i-1][j][0], min([deltafcode(c_subs[ind], c_subs[j]) for ind in tableU[i-1][0]])),
                              subseq)
            tableM[i][j] = combined_tuple
            tableU[i][j] = tableU[i-1][0] + [j]
            for k in range(1, j):
                subseq = tableM[i-1][k][1].copy()
                bisect.insort(subseq, taskDis(t_subs[j], t_subs[k]))
                combined_tuple = (max(tableM[i-1][k][0], min([deltafcode(c_subs[ind], c_subs[j]) for ind in tableU[i-1][k]])),
                                  subseq)
                if notWorse(combined_tuple, tableM[i][j]):
                    tableM[i][j] = combined_tuple
                    tableU[i][j] = tableU[i-1][k] + [j]

    print("tableM")
    for row in tableM:
        print(row)

    print("tableU")
    for row in tableU:
        print(row)


    indices = tableU[K][-1][1:-1]

    for ind in indices:
        print(f"ind={ind}")
        print(fcode(c_subs[ind], rollout_param), t_subs[ind][0]["shortest_path"])
    return indices #t_subs_k, c_subs_k


def subtask_selection_dp_single_candidate(c_subs, t_subs, K, fcode, rollout_param):
    print(f"Choose K={K} subtasks")
    for i, (c,t) in enumerate(zip(c_subs, t_subs)):
        cprint(f"Snapshot {i} with complexity {fcode(c, rollout_param)}, and shortest path {t[0]['shortest_path']}", Tcolors.CYAN)
        print(beautify(convert_ast_to_code(current_ast(c, rollout_param=rollout_param))))


    def notWorse(tuple1, tuple2):
        return (tuple1[0] < tuple2[0]) or (tuple1[0] == tuple2[0] and tuple1[1] >= tuple2[1])

    def deltafcode(c1, c2):
        return fcode(c2, rollout_param) - fcode(c1, rollout_param)


    N = len(c_subs)
    c_subs.insert(0, {"type":"run", "alive":True, "children":[]})
    t_subs.insert(0, [{"shortest_path":0}])

    tableM = [[(1e5, 0) for i in range(N+1)] for j in range(K+1)]
    tableM[0] = [(deltafcode(c_subs[0], c_subs[j]), taskDis(t_subs[j], t_subs[0])) for j in range(N+1)]

    tableU = [[None for i in range(N+1)] for j in range(K+1)]#[[None]*N]*(K+1)
    tableU[0] = [[0, i] for i in range(N+1)]
    # N + 1 because we will add empty subtask, K + 1 because empty subtask should always be a part of this

    for j in range(0, N+1):
        for i in range(1, K+1, 1):
            combined_tuple = (max(tableM[i-1][0][0], min([deltafcode(c_subs[ind], c_subs[j]) for ind in tableU[i-1][0]])),
                              min(tableM[i-1][0][1], taskDis(t_subs[j], t_subs[0])))
            tableM[i][j] = combined_tuple
            tableU[i][j] = tableU[i-1][0] + [j]
            for k in range(1, j):
                combined_tuple = (max(tableM[i-1][k][0], min([deltafcode(c_subs[ind], c_subs[j]) for ind in tableU[i-1][k]])),
                                  min(tableM[i-1][k][1], taskDis(t_subs[j], t_subs[k])))
                if notWorse(combined_tuple, tableM[i][j]):
                    tableM[i][j] = combined_tuple
                    tableU[i][j] = tableU[i-1][k] + [j]

    print("tableM")
    for row in tableM:
        print(row)

    print("tableU")
    for row in tableU:
        print(row)


    indices = tableU[K][-1][1:-1]

    for ind in indices:
        print(f"ind={ind}")
        print(fcode(c_subs[ind], rollout_param), t_subs[ind][0]["shortest_path"])
    return indices #t_subs_k, c_subs_k

def subtask_selection_dp_monotonous(c_subs, t_subs, K, fcode, rollout_param):
    print(f"Choose K={K} subtasks")
    for i, (c,t) in enumerate(zip(c_subs, t_subs)):
        cprint(f"Snapshot {i} with complexity {fcode(c, rollout_param)}, and shortest path {t[0]['shortest_path']}", Tcolors.CYAN)
        print(beautify(convert_ast_to_code(current_ast(c, rollout_param=rollout_param))))

    def notWorse(tuple1, tuple2):
        return (tuple1[0] < tuple2[0]) or (tuple1[0] == tuple2[0] and tuple1[1] >= tuple2[1])

    def deltafcode(c1, c2):
        return fcode(c2, rollout_param) - fcode(c1, rollout_param)

    N = len(c_subs)
    c_subs.insert(0, {"type":"run", "alive":True, "children":[]})
    t_subs.insert(0, [{"shortest_path":0}])

    tableM = [[(1e5, 0) for i in range(N+1)] for j in range(K+1)]
    tableM[0] = [(deltafcode(c_subs[j], c_subs[-1]), taskDis(t_subs[j], t_subs[-1])) for j in range(N+1)]
    tableU = [[None for i in range(N+1)] for j in range(K+1)]#[[None]*N]*(K+1)
    # N + 1 because we will add empty subtask, K + 1 because empty subtask should always be a part of this

    for j in range(N, -1, -1):
        for i in range(1, K+1, 1):
            combined_tuple = (max(tableM[i-1][j][0], deltafcode(c_subs[j], c_subs[j])),
                              min(tableM[i-1][j][1], taskDis(t_subs[j], t_subs[j])))
            tableM[i][j] = combined_tuple
            tableU[i][j] = j
            for k in range(2, N-j+1):
                combined_tuple = (max(tableM[i-1][j+k-1][0], deltafcode(c_subs[j], c_subs[j+k-1])),
                                  min(tableM[i-1][j+k-1][1], taskDis(t_subs[j], t_subs[j+k-1])))
                if notWorse(combined_tuple, tableM[i][j]):
                    tableM[i][j] = combined_tuple
                    tableU[i][j] = j + k - 1

    print("tableM")
    for row in tableM:
        print(row)

    print("tableU")
    for row in tableU:
        print(row)

    indices = []
    ind = 0
    for i in range(K):
        ind = tableU[K-i][ind]
        print(f"ind={ind}")
        print(fcode(c_subs[ind], rollout_param), t_subs[ind][0]["shortest_path"])
        indices.append(ind)

    return indices
