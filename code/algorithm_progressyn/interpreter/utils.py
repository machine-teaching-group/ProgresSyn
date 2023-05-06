import os
import errno
import signal
import numpy as np
from functools import wraps
from pyparsing import nestedExpr

class TimeoutError(Exception):
    pass

def str2bool(v):
    return v.lower() in ('true', '1')

class Tcolors:
    CYAN = '\033[1;30m'
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def cprint(string, color=Tcolors.OKBLUE):
    print(color + string + Tcolors.ENDC)


def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.setitimer(signal.ITIMER_REAL,seconds) #used timer instead of alarm
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result
        return wraps(func)(wrapper)
    return decorator

def beautify_fn(inputs, indent=1, tabspace=2):
    lines, queue = [], []
    space = tabspace * " "

    for item in inputs:
        if item == ";":
            lines.append(" ".join(queue))
            queue = []
        elif type(item) == str:
            queue.append(item)
        else:
            lines.append(" ".join(queue + ["{"]))
            queue = []

            inner_lines = beautify_fn(item, indent=indent+1, tabspace=tabspace)
            lines.extend([space + line for line in inner_lines[:-1]])
            lines.append(inner_lines[-1])

    if len(queue) > 0:
        lines.append(" ".join(queue))

    return lines + ["}"]

def pprint(code, *args, **kwargs):
    print(beautify(code, *args, **kwargs))

replace_dict = {
        'm(': '{',
        'm)': '}',
        'c(': '(',
        'c)': ')',
        'r(': '{',
        'r)': '}',
        'w(': '{',
        'w)': '}',
        'i(': '{',
        'i)': '}',
        'e(': '{',
        'e)': '}',
        'move': 'move ;',
        'turn_left': 'turn_left ;',
        'turn_right': 'turn_right ;',
        'pick_marker': 'pick_marker ;',
        'put_marker': 'put_marker ;',
        }



def beautify(code, tabspace=2):
    code = " ".join(replace_dict.get(token, token) for token in code.split())
    array = nestedExpr('{','}').parseString("{"+code+"}").asList()
    lines = beautify_fn(array[0])
    return "\n".join(lines[:-1]).replace(' ( ', '(').replace(' )', ')')

def makedirs(path):
    if not os.path.exists(path):
        print(" [*] Make directories : {}".format(path))
        os.makedirs(path)

def get_rng(rng, seed=123):
    if rng is None:
        rng = np.random.RandomState(seed)
    return rng


def tin_converter(world_path, include_walls=False, verbose=False):
    '''
    This reads from a txt file that is organized in NIPS format and converts to carpedm format.
    '''
    with open(world_path) as fp:
        contents = fp.readlines()

    AGENTSYMBS = {"north":'^', "south":'v', "east":'>', "west":'<', "any":'o'}

    assert "type" in contents[0], "Wrong format - type is not found"
    assert "gridsz" in contents[1], "Wrong format - grid size is not found"
    assert "number_of_grids" in contents[2], "Wrong format -number of grids is not found"

    taskType = contents[0].split()[1]
    gridsz = contents[1].split()[1][1:-1].split(",")
    assert "ncol" in gridsz[0] and "nrow" in gridsz[1], f"Expected format for gridsz (ncols=,nrows=), Found ({gridsz[0],gridsz[1]})"
    ncols,nrows = [int(dim.split("=")[1]) for dim in gridsz]
    nGrids = contents[2].split()[1]

    if verbose:
        print(f"Task type: {taskType}, grid size: (ncols={ncols},nrows={nrows}), Number of grids: {nGrids}")


    ## ToDo: Check whether the encountered grid have the right number.
    ## Done: They are checked when extracted from the grids list.
    grids = []
    current_grid_info = {}
    current_grid = []
    for line in contents[4:]:
        if line[0].isdigit():
            current_grid.append(line.split()[1:])
        elif "grid" in line:
            current_grid_info.update(name=line.split()[0])
        elif "agentloc" in line:
            agentloc = line.split()[1][1:-1].split(",")
            assert "col" in agentloc[0] and "row" in agentloc[1], "Expected format for agentloc (col=,row=)"
            col, row = [int(dim.split("=")[1]) for dim in agentloc]
            current_grid_info.update(agentloc=(col,row))
        elif "agentdir" in line:
            agentdir = line.split()[1]
            assert agentdir in AGENTSYMBS.keys()

            ## FIX THIS
            if agentdir == "any":
                agentdir = "north"

            ##
            current_grid_info.update(agentdir=agentdir)
            ### Padding to fit to the gridsz.
            assert len(current_grid[0]) <= ncols, "The grid is too wide"
            new_col = col
            if len(current_grid[0]) != ncols:
                diff = ncols - len(current_grid[0])
                if diff % 2 == 0:
                    current_grid = [["#"]*(diff//2) + line + ["#"]*(diff//2) for line in current_grid]
                    new_col = col + (diff//2)
                else:
                    current_grid = [["#"]*(diff//2 + 1) + line + ["#"]*(diff//2) for line in current_grid]
                    new_col = col + (diff//2 + 1)

            assert len(current_grid) <= nrows, "The grid is too wide"
            new_row = row
            if len(current_grid) != nrows:
                diff = nrows - len(current_grid)
                if diff % 2 == 0:
                    current_grid = [["#"]*ncols]*(diff//2) + current_grid + [["#"]*ncols]*(diff//2)
                    new_row = row + (diff//2)

                else:
                    current_grid = [["#"]*ncols]*(diff//2 + 1) + current_grid + [["#"]*ncols]*(diff//2)
                    new_row = row + (diff//2 + 1)

            current_grid_info.update(agentloc=[new_col,new_row])
            ### Padding over

            current_grid_info.update(grid=current_grid)
            grids.append(current_grid_info)
            current_grid_info = {}
            current_grid = []
        else:
            pass
    return grids

def grid2txt(grids):
    AGENTSYMBS = {"north":'^', "south":'v', "east":'>', "west":'<', "any":'o'}
    tins = []
    for i in range(len(grids)//2):
        pregrid = grids[2*i]
        postgrid = grids[2*i + 1]
        assert pregrid["name"] == f"pregrid_{i+1}", f"Unexpected grid! Expected: pregrid_{i+1}, Found: {pregrid['name']}"
        assert postgrid["name"] == f"postgrid_{i+1}", f"Unexpected grid! Expected: postgrid_{i+1}, Found: {postgrid['name']}"

        offset = not include_walls

        tin_wo_agent_pre = [line[offset:-offset] for line in pregrid["grid"][offset:-offset]]
        tin_wo_agent_post = [line[offset:-offset] for line in postgrid["grid"][offset:-offset]]

        c,r = pregrid["agentloc"]
        tin_wo_agent_pre[r-1-offset][c-1-offset] = AGENTSYMBS[pregrid["agentdir"]]
        c,r = postgrid["agentloc"]
        tin_wo_agent_post[r-1-offset][c-1-offset] = AGENTSYMBS[postgrid["agentdir"]]

        tin_pre = "\n".join(map("".join, tin_wo_agent_pre))
        tin_post = "\n".join(map("".join, tin_wo_agent_post))

        tins.append((tin_pre, tin_post))

    return tins

def grid2state(grids):
    WALL_CHAR = '#'
    AGENTIDXS = {"north":0, "south":1, "east":3, "west":2}
    max_marker = 10
    hero_direction = 4

    io_states = []
    for i in range(len(grids)//2):
        state = np.zeros_like(grids[2*i]["grid"], dtype=np.int8)

        zero_state = np.tile(
                np.expand_dims(state, -1),
                    [1, 1, hero_direction + 1 + (max_marker + 1)])

        state_pair = []

        for j in range(2):
            state = zero_state.copy()
            state[:,:,5] = 1

            x,y = grids[2*i+j]["agentloc"]
            agentdir = grids[2*i+j]["agentdir"]

            # 0 ~ 3: Hero facing North, South, West, East
            if agentdir in AGENTIDXS.keys():
                state[y-1, x-1, AGENTIDXS[agentdir]] = 1

            # 4: wall or not
            for jdx, row in enumerate(grids[2*i+j]["grid"]):
                for idx, char in enumerate(row):
                    if char == WALL_CHAR:
                        state[jdx][idx][4] = 1
                    elif char[0].isdigit():
                        ## I guess this would accept maximum of 9
                        state[jdx][idx][int(char) + 5] = 1
#                     elif char == self.WALL_CHAR or char in self.HERO_CHARS:
#                         state[:,:,5] = 1

#             # 5 ~ 15: marker counter
#             for (x, y), count in Counter(self.markers).items():
#                 state[y][x][5] = 0
#                 state[y][x][5 + count] = 1
                #state[y][x][min(5 + count, self.max_marker)] = 1
            state_pair.append(state)
        io_states.append(state_pair)
        # draw2d(state[:,:,5])
    return io_states

def hoc2karel(code):
    code = code.replace("repeat_until_goal(bool_goal)","while(bool_no_goal)")
    return code

def hoc2kareljson(codejson):
    for child in codejson["children"]:
        if child["type"] == "repeat_until_goal(bool_goal)":
            child["type"] = "while(bool_no_goal)"
    return codejson
