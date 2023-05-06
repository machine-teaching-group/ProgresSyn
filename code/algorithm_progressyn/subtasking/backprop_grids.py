from code.agents_neural.karel.fast_emulator import FastEmulator
from code.agents_neural.karel.ast_converter import AstParser
from code.agents_neural.karel.ast import Ast as iclrAST
from code.agents_neural.karel.world import World
from code.algorithm_progressyn.interpreter.ast_to_code_converter import AstToCodeConverter,convert_ast_to_code
from code.algorithm_progressyn.interpreter.karel import Karel
from code.algorithm_progressyn.subtasking.progressyn_single import progressyn_single
from code.algorithm_progressyn.subtasking.code_tracker import current_ast
from code.utils.progressyn_neural_converters import carpedm2iclr_tokens



class CarpedmEmulator():
    def __init__(self, max_ticks=None, max_actions=None):
        self.iclr_emulator = FastEmulator(max_ticks, max_actions)
        self.ast_conv = AstToCodeConverter()
        self.ast_parser = AstParser()

    def emulate(self, c, pregrid):
        # Grid
        inp_grid = Karel(pregrid)
        inpgrid_json = inp_grid.toJson()
        inp_world = World.parseJson(inpgrid_json)
#         print("Input Grid")
#         print(inp_world.toString())
        # Code
        carpedm_json = current_ast(c)
        carpedm_tokens = self.ast_conv.to_tokens(carpedm_json)
        iclr_tokens = carpedm2iclr_tokens(carpedm_tokens)
        iclr_json = self.ast_parser.parse(iclr_tokens)
        ast = iclrAST(iclr_json)
        result = self.iclr_emulator.emulate(ast, inp_world)
        return result.outgrid, result.crashed

def backpropagation_grids(tin, t_subs, c_subs, cin, hoc, rollout_param):
    print(f"\n\n {'*'*15} \n Backpropagation_grids \n {'*'*15} \n\n")
    emulator = CarpedmEmulator()
    grid_starting_idxs = {}
    curr_n_grids = 0
    for i, t in enumerate(t_subs):
        for grid in t:
            if grid['ind'] not in grid_starting_idxs:
                grid_starting_idxs[grid['ind']] = i

    grid_order = sorted(list(grid_starting_idxs.items()), key=lambda x: x[1])
    print(grid_order)

    for grid_idx, _ in grid_order[1:]:
        t_candidates, c_candidates = progressyn_single(tin[grid_idx]['pre'], cin, hoc, rollout_param)
        t_candidates = [[{'ind':tin[grid_idx]['ind'], 'pre':t["tout"][0], 'post':t["tout"][1]}] for t in t_candidates]
#         print(f"Length of candidate sequence for grid {grid_idx} is {len(t_candidates)}")
        grid_start_ind = grid_starting_idxs[grid_idx]
        search_start_ind = len(t_candidates) -1
#         print(f"Backwards Looping from subtask {grid_start_ind}")
        for j in range(grid_start_ind-1, -1, -1):
            P = c_subs[j]
            ind = -1
#             print(f"For subtask {j}, going to try {beautify(convert_ast_to_code(current_ast(P)))} on {search_start_ind}th candidate snapshots")
            for k in range(search_start_ind,-1, -1):
#                 print(f"Candidate {k}")
                assert len(t_candidates[k]) == 1, "Too many grids for single grid decomposition"
                result_grid, crashed = emulator.emulate(P, t_candidates[k][0]['pre'])
                assert len(t_candidates[k]) == 1, "Too many grids for single grid decomposition"
                out_grid = Karel(t_candidates[k][0]['post'])
                outgrid_json = out_grid.toJson()
                out_world = World.parseJson(outgrid_json)
#                 print("Result Grid")
#                 print(result_grid.toString())

#                 print("Expected Output Grid")
#                 print(out_world.toString())


#                 print(f"Emulated candidate {k}, crashed: {crashed}")
                if not crashed and result_grid == out_world:
                    ind= k
                    break
            if ind != -1:
                t_subs[j] += t_candidates[ind]
                search_start_ind = ind - 1
            else:
#                 print(f"Unsuccesful code was {beautify(convert_ast_to_code(current_ast(P)))}")
                break
    return t_subs, c_subs
