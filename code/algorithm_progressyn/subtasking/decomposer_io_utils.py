from matplotlib import patches
import matplotlib.pyplot as plt
import json
import os

from code.algorithm_progressyn.interpreter.ast_to_code_converter import convert_ast_to_code
from code.algorithm_progressyn.interpreter.utils import pprint as pretty_code
from code.algorithm_progressyn.interpreter.utils import beautify
from code.algorithm_progressyn.interpreter.karel import Karel
from code.algorithm_progressyn.subtasking.domain_knowledge import comp_depth_and_size
from code.algorithm_progressyn.subtasking.code_tracker import current_ast
# fcode = fcode_wang_sequencing
fcode_list = [comp_depth_and_size]

def identity(c):
    return c

current_ast = current_ast

def dump_pdf_multigrid(t_subs, c_subs, titles, path, taskID, rollout_param):

    assert len(t_subs) == len(c_subs), "Mismatch between subtasks and codes"

    nplots = len(t_subs)
    maxgrids = max([len(t) for t in t_subs])
    print(f"Maximum number of grids in the subtasks is {maxgrids}")
    fig, axs = plt.subplots(nplots, 2*maxgrids + 1, figsize=(7*maxgrids*2*4 + 1, 11*nplots),# sharex="all", sharey="all",
                            frameon=False, tight_layout=False, squeeze=False,
                            gridspec_kw={'width_ratios': [4]*(2*maxgrids) + [1]})
    for row in axs:
        for ax in row:
            ax.axis('off')

#     ax = axs[0][0]
#     ax.text(0,0.5,beautify(convert_ast_to_code(current_ast(c_subs[i]))),
#                        ha="left", va="center", fontsize=11, bbox={"alpha":0})

#     print(f"Total length of pregrid = {len(pregrid)}")
#     for i, col in enumerate(axs[0][:-1]):
#         print(f"Grid {i} is done")
#         ktemp = Karel(state=pregrid[i])
#         ax = col
#         ktemp.paint(ax, False)#"hoc" in taskID)
#         ax.set_title("Pregrid")

    for i in range(len(c_subs)):

        for j in range(len(t_subs[i])):
            ax = axs[i][2*j] #[int(titles[i][0])-1][2*int(titles[i][1]) - 0]
            ktemp = Karel(state=t_subs[i][j]['pre'])
#             ax = axs[int(titles[i][0])-1][2*int(titles[i][1]) - 1]
            ktemp.paint(ax, False)#"hoc" in taskID)
#             ax.set_title("-".join(map(str, titles[i])))#f"---- Subtask #{i+1}, Code Complexity: {fcode(c_subs[i])}----")
            ax = axs[i][2*j + 1]
            ktemp = Karel(state=t_subs[i][j]['post'])
            ktemp.paint(ax, False)#"hoc" in taskID)


        ax = axs[i][2*len(t_subs[i])]
        ax.text(0,0.5,beautify(convert_ast_to_code(current_ast(c_subs[i], rollout_param=rollout_param))),
                       ha="left", va="center", fontsize=15, bbox={"alpha":0})
#         axs[i//4][2*(i%4)].axis('off')



    plt.savefig(os.path.join(path, f"{taskID}_K__{len(c_subs)}.pdf"), format="pdf")

    

def _draw_grid(karel, label, io, remove_padding, desired_size):
    AGENTIDXS = {0:"north", 1: "south", 3:"east", 2: "west"}
    output = []
    gridline_counter = 1
    lines = karel.draw(no_print=True)
    lines, agentcol, agentrow = _get_to_desired_size(lines, desired_size[0], desired_size[1], karel.hero.position[0]+1, karel.hero.position[1]+1)
    header = '\t'.join([f'{label}_{io+1}'] + list(map(str, range(1, len(lines)+1))))

    output.append(header + '\n')
    for line in lines:
        print_line = '\t'.join([str(gridline_counter)] + list(line))
        gridline_counter += 1
        output.append(print_line + '\n')
    agentloc_line = f'agentloc_{io+1}' + '\t' + f'(col={agentcol},row={agentrow})'
    agentdir_line = f'agentdir_{io+1}' + '\t' + AGENTIDXS[karel.facing_idx]
    output.append(agentloc_line + '\n')
    output.append(agentdir_line)
    return output

def _get_to_desired_size(tout, nrows, ncols, agentcol, agentrow):
    tout, agentcol, agentrow = _remove_padding(tout, agentcol, agentrow)

    assert len(tout[0]) <= ncols, "The grid is too wide"
    new_col = agentcol
    if len(tout[0]) != ncols:
        diff = ncols - len(tout[0])
        if diff % 2 == 0:
            tout = [["#"]*(diff//2) + list(line) + ["#"]*(diff//2) for line in tout]
            new_col = agentcol + (diff//2)
        else:
            tout = [["#"]*(diff//2 + 1) + list(line) + ["#"]*(diff//2) for line in tout]
            new_col = agentcol + (diff//2 + 1)

    new_row = agentrow
    if len(tout) != nrows:
        diff = nrows - len(tout)
        if diff % 2 == 0:
            tout = [["#"]*ncols]*(diff//2) + tout + [["#"]*ncols]*(diff//2)
            new_row = agentrow + (diff//2)

        else:
            tout = [["#"]*ncols]*(diff//2 + 1) + tout + [["#"]*ncols]*(diff//2)
            new_row = agentrow + (diff//2 + 1)

#     print(f"Agent location after padding to desired size: {new_col}, {new_row}")
    return tout, new_col, new_row

def _remove_padding(tout, agentcol, agentrow):
#     print(f"Initial agent location: {agentcol}, {agentrow}")
    lines = tout
    pad_free = []
    lpadding = 1000
    rpadding = 1000
    initial_skipped_rows = 0
    non_padding_line_seen = False
    for line in lines:
        if not line == "#"*len(line):
            rpadding = min(rpadding, len(line) - len(line.rstrip("#")))
            lpadding = min(lpadding, len(line) - len(line.lstrip("#")))
            pad_free.append(line)
            non_padding_line_seen = True
        elif not non_padding_line_seen:
            initial_skipped_rows += 1

    pad_free = ["#"*len(pad_free[0])] + pad_free + ["#"*len(pad_free[0])]
    if rpadding > 1:
        pad_free = [line[max(lpadding-1,0):-rpadding+1] for line in pad_free]
    else:
        pad_free = [line[max(lpadding-1,0):] for line in pad_free]

#     print(f"Agent location after removing padding: {agentcol - max(lpadding-1,0)}, {agentrow - initial_skipped_rows + 1}")
    return pad_free, agentcol - max(lpadding-1,0), agentrow - initial_skipped_rows + 1

def dump_output(t_subs, c_subs, path, taskID, rollout_param, remove_padding=True, desired_size=(12,12)):
    assert len(t_subs) == len(c_subs), "Mismatch between subtasks and codes"
    for i in range(len(t_subs)):
        with open(os.path.join(path,taskID, f"ours-k{len(t_subs)}-{taskID}-1_subtask-{chr(97+i)}_task.txt"), "w") as f:

            header = f'type' + '\t' + ('karel' if 'karel' in taskID else 'hoc') + '\n'
            header += 'gridsz' + '\t' + f'(ncol={desired_size[1]},nrow={desired_size[0]})' + '\n'
            header += 'number_of_grids' + '\t' + str(len(t_subs[i]))
            f.write(header)
            for io in range(len(t_subs[i])):
                output = ['\n \n']
                ktemp = Karel(state=t_subs[i][io]['pre'])
                output += _draw_grid(ktemp, 'pregrid', io, remove_padding, desired_size)
                output += ['\n \n']
                ktemp = Karel(state=t_subs[i][io]['post'])
                output += _draw_grid(ktemp, 'postgrid', io, remove_padding, desired_size)
                for line in output:
                    f.write(line)

        with open(os.path.join(path,taskID, f"ours-k{len(t_subs)}-{taskID}-1_subtask-{chr(97+i)}_code.json"), "w") as f:
            f.write(json.dumps(current_ast(c_subs[i], rollout_param=rollout_param), indent=4))
