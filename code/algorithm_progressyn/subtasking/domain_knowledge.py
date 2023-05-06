import json

from code.algorithm_progressyn.interpreter.karel import Karel
from code.algorithm_progressyn.subtasking.code_tracker import current_ast
from code.algorithm_progressyn.interpreter.utils import beautify, cprint, Tcolors
from code.algorithm_progressyn.interpreter.ast_to_code_converter import convert_ast_to_code

def number_of_unique_substructures(csubs, rollout_param):
#     substructure_strings_param_1 = set()
    substructure_strings_param = set()
    print("Compute number of unique substructures per rollout param")
    for c in csubs:
        alive_code = current_ast(c, rollout_param=rollout_param)
        travel_string = _find_substructures_traversal(alive_code)
        substructure_strings_param.add(travel_string)
#         alive_code = current_ast(c, rollout_param=1)
#         print("Computing string for the code")
#         print(beautify(convert_ast_to_code(alive_code)))
#         travel_string = _find_substructures_traversal(alive_code)
#         print(travel_string)
#         substructure_strings_param_1.add(travel_string)
#     print(substructure_strings_param_1)
    print(substructure_strings_param)
    return len(substructure_strings_param)

def _find_substructures_traversal(node):
    traversal_string = ""
    for child in node["children"]:
        if "ifelse" in child["type"]:
            traversal_string += "IE"
            branches = [_find_substructures_traversal(branch) for branch in child["children"]]
            traversal_string += '{'+ branches[0] +'}' + '{' + branches[1] + '}'
        elif "if" in child["type"]:
            traversal_string += "I"
            branches = [_find_substructures_traversal(branch) for branch in child["children"]]
            assert len(branches) == 1
            traversal_string += '{'+ branches[0] +'}'

        elif "while" in child["type"]:
            traversal_string += "W{" + _find_substructures_traversal(child) + "}"

        elif "repeat" in child["type"]:
            traversal_string += "R{" + _find_substructures_traversal(child) + "}"

    return traversal_string

def _comp_depth_and_size(node):
    '''
    Computes the depth and size of the given code
    '''
    max_depth = 0
    size=0
    for child in node["children"]:
        if "if" in child["type"]: # Covers both if and ifelse
            branches = [_comp_depth_and_size(branch) for branch in child["children"]]
            size += sum([branch[1] for branch in branches]) + 1
            max_branch_depth = max([branch[0] for branch in branches])
            max_depth = max(max_branch_depth + 1, max_depth)
        elif "while" in child["type"] or "repeat" in child["type"]:
            node_depth, node_size = _comp_depth_and_size(child)
            size += node_size + 1
            max_depth = max(max_depth, node_depth + 1)
        else:
            size += 1

    return max_depth, size

def comp_depth_and_size(node, rollout_param):
    '''
    Scalarize the tuple
    '''
    alive_code = current_ast(node, rollout_param=rollout_param)
    depth, size = _comp_depth_and_size(alive_code)
    return 1000*depth + size


def taskDis(t1, t2):
#     assert (len(t1) > 1 and len(t2) > 1) or (len(t1) == len(t2) == 1)
    if len(t1) == len(t2) == 1:
        return abs(t1[0]["shortest_path"] - t2[0]["shortest_path"])
    else:
#         num_grid_diff = abs(len(t1) - len(t2))
        raise NotImplementedError()


def task_diff(t1, t2):
    karel1 = Karel(t1)
    karel2 = Karel(t2)

    loc_diff = (abs(karel1.hero.position[0] - karel2.hero.position[0]) +
                    abs(karel1.hero.position[0] - karel2.hero.position[0]))

    if karel1.hero.facing == karel2.hero.facing:
        dir_diff = 0
    elif karel1.hero.facing == (-karel2.hero.facing[0], -karel2.hero.facing[1]):
        dir_diff = 2
    else:
        dir_diff = 1

    marker_diff = 0
    for mark in karel1.markers:
        try:
            karel2.markers.remove(mark)
        except ValueError:
            marker_diff += 1
    marker_diff += len(karel2.markers)

    return 1/3*(loc_diff + dir_diff + marker_diff)


def is_equivalent_codes(c1, c2):
    if "repeat" in c1["type"]:
        if not "repeat" in c2["type"]:
            return False
        else:
            pass
    elif c1["type"] != c2["type"]:
        return False

    if len(c1.get("children", [])) != len(c2.get("children", [])):
        return False

    for child_c1, child_c2 in zip(c1.get("children", []), c2.get("children", [])):
        if not is_equivalent_codes(child_c1, child_c2):
            return False

    return True

def code_quality(c, cref):
    '''
    assings a quality score to c w.r.t cref.
    '''
#     print("Trying to compute the quality score for")
#     print(beautify(convert_ast_to_code(current_ast(c))))
    score = 1
    assert c['type'] == 'run'
    for child, refchild in zip(c['children'], cref['children']):
#         print(child)
#         print()
#         print(refchild)
        assert child['type'] == refchild['type'] or ("repeat" in child['type'] and "repeat" in refchild["type"])
        if 'while' in child['type'] or 'repeat' in child['type']:
            if len(child["children"]) != len(refchild["children"]):
#             if not is_equivalent_codes(child, refchild):
                score = -1
                break
#     print(score, "\n")

    return score

def alignGridsBottomLeft(listOfGrids):
    new_grids = []
    ## Strip padding
    for grid in listOfGrids:
        k = Karel(state=grid)
        grid = k.draw(no_print=True, include_agent=True)
#         print("Before alignment")
#         k.draw()
        lpadding = 100
        for row in grid[::-1]:
            lpadding = min(lpadding, len(row) - len(row.lstrip('#')))
        new_grid = []
        padding_rows = True
        bpadding = 0
        for row in grid[::-1]:
            if len(row.lstrip('#')) != 0:
                padding_rows = False
            if not padding_rows:
                new_grid.append(row[lpadding:])
        new_grids.append(new_grid)
    ## Padding
    maxw, maxh = 0,0
    new_grids_as_karel = []
    for new_grid in new_grids:
        maxw = max(maxw, len(new_grid[0]))
        maxh = max(maxh, len(new_grid))
    for new_grid in new_grids:
        w = len(new_grid[0])
        padded_grid = []
        if  w < maxw:
            for row in new_grid:
                padded_grid.append(row + "#"*(maxw-w))
        else:
            padded_grid = new_grid
        h = len(new_grid)
        if h < maxh:
            padded_grid += ["#"*maxw]*(maxh-h)
        k = Karel(world_str=padded_grid[::-1])
#         print("Grid")
#         k.draw()
        new_grids_as_karel.append(k)

    return new_grids_as_karel

def hammingDistance(grid1, grid2):
    '''
    Expects the grids to be bottom left aligned already and be karel objects
    '''
    k1 = grid1 # Karel(state=grid1)
    k2 = grid2 # Karel(state=grid2)
    descr1 = k1.toJson()
    descr2 = k2.toJson()
    assert descr1['rows'] == descr2['rows'] and descr1['cols'] == descr2['cols']

    # Hero
    agentrow1, agentcol1, agentdir1 = descr1['hero'].split(':')
    agentrow2, agentcol2, agentdir2 = descr1['hero'].split(':')

    agentPosDiff = 0 if agentrow1==agentrow2 and agentcol1==agentcol2 else 1
    agentDirDiff = 0 if agentdir1==agentdir2 else 1

    ## Cells
    walls1 = set(descr1['blocked'].split())
    walls2 = set(descr2['blocked'].split())

    wallDif = walls1.symmetric_difference(walls2)
    hammingDistance = len(wallDif)

    markers1 = set(descr1['markers'].split())
    markers2 = set(descr2['markers'].split())

    hammingDistance += len(markers1.symmetric_difference(markers2))


#     print(agentPosDiff, agentDirDiff, hammingDistance)

    return 1/3*(agentPosDiff + agentDirDiff) + hammingDistance/(descr1['rows']*descr1['cols'])

def compute_pairwise_hamming_distances(listOfGrids):
    '''
    Expects a list of grids marked with grid ind
    '''
    listOfPreGrids = [grid["pre"] for grid in listOfGrids]
    inds = [grid["ind"] for grid in listOfGrids]
    alignedGrids = alignGridsBottomLeft(listOfPreGrids)
    markedGrids = {i:grid for i,grid in zip(inds,alignedGrids)}
    distances = {(i,j):hammingDistance(markedGrids[i],markedGrids[j]) if i!=j else 0 for i in inds for j in inds}
    print(distances)
    return distances

def multiTaskDisGenerator(listOfGrids):
    distances = compute_pairwise_hamming_distances(listOfGrids)
    def multiTaskDis(t1, t2):
#         print(f"Grids for distance: {[g['ind'] for g in t1]} and {[g['ind'] for g in t2]}")
#         print(sum([min([distances[(g['ind'], gp['ind'])] for gp in t2]) for g in t1]))
        return 1/len(t1) * sum([min([distances[(g['ind'], gp['ind'])] for gp in t2]) for g in t1])
    return multiTaskDis
