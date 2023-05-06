from code.algorithm_progressyn.interpreter.karel import Karel


def canHaveNMarkersInPre(N, pos, history):
    '''
    \not \exists i<=t where:
        (#Pick[0:i] - #Put[0:i] > N) or (#Pick[0:i] - #Put[0:i] = N and Bool_Marker[i])
                                            or  (#Pick[0:i] - #Put[0:i] <  N and Bool_No_Marker[i])
    '''
    print(f"Checking if {N} marker at {pos} in pre grid is possible")
    n_picks = 0
    n_puts = 0
    pos_history = history.get(pos, [])
    print("Marker history for this position: ", pos_history)
    for cexec in pos_history:
        if cexec == "pick_marker":
            n_picks += 1
            if n_picks - n_puts > N:
                return False
        elif cexec == "put_marker":
            n_puts += 1
        elif cexec == "bool_marker":
            if n_picks - n_puts == N:
                return False
        elif cexec == "bool_no_marker":
            if n_picks - n_puts < N:
                return False
    return True

def canHaveLMarkersinPost(L, pos, history):
    '''
    We can make the post grid have L \in {0,1} marker @pos at timestep t under C,T iff:
    We can generate a pre with L + #Pick[0:t] - #Put[0:t] for t steps of execution under C,T
    '''
    print(f"Checking if {L} marker at {pos} in post grid is possible")
    n_picks = history.get(pos, []).count("pick_marker")
    n_puts = history.get(pos, []).count("put_marker")
    print(f"n_picks={n_picks},n_puts={n_puts}. {L + n_picks - n_puts} marker at {pos} in pre grid needed")
    if L + n_picks - n_puts >= 0:
        success = canHaveNMarkersInPre(L + n_picks - n_puts, pos, history)
    else:
        success = False
    print("Possible" if success else "Impossible")
    return success, L + n_picks - n_puts


def symbolicExecution(block, pregrid, state, constraints, hoc=False):
    # print(f"Symbolic execution")
    karel = Karel(state=state)
#     karel.draw()
    known_cells = constraints['clear']
    known_walls = constraints['blocked']
    known_markers = {}
    new_cells = set()
    new_walls = set()

    if 'path' in block:
        if "path_ahead" in block:
            pos = karel._front()
        elif "path_left" in block:
            pos = karel._left()
        elif "path_right" in block:
            pos = karel._right()

        if ("no" in block):
#             print(pos)
#             print(known_walls)
            if pos in known_walls:
#                 print("This is known to be a wall")
                return None
            else:
                new_cells.add(pos)
        else:
            if pos in known_cells:
#                 print("This is known to be a cell")
                return None
            else:
                new_walls.add(pos)


    elif "goal" in block:
        pos = karel._position()
        known_markers[pos] = {'pre':1, 'post':1}

    elif "bool_marker" in block:
        pos = karel._position()
        canGenerate, n_pre_markers = canHaveLMarkersinPost(0, pos, constraints["marker-history"])
        if canGenerate:
            known_markers[pos] = {'pre':n_pre_markers, 'post':0}
        else:
            return None
    elif "bool_no_marker" in block:
        pos = karel._position()
        canGenerate, n_pre_markers = canHaveLMarkersinPost(1, pos, constraints["marker-history"])
        if canGenerate:
            known_markers[pos] = {'pre':n_pre_markers, 'post':1}
        else:
            return None

    elif block == "no_change":
        pass

    else:
        raise Exception("Unknown block type: ", block)

#     print(f"New walls {new_walls}")
#     print(f"New cells {new_cells}")

    T = state.copy()
    Tin = pregrid.copy()
    ## If HOC, remove the original goal and put one to the new position
    if hoc:
        pos = karel._position()
        known_markers[pos] = {'pre':1, 'post':1}
        for i in range(len(T)):
            for j in range(len(T[0])):
                T[i, j, 6] = 0
                T[i, j, 5] = 1
                Tin[i, j, 6] = 0
                Tin[i, j, 5] = 1
#         for pos in known_markers:
#             T[pos[1], pos[0], 6] = 1
#             T[pos[1], pos[0], 5] = 0
#             Tin[pos[1], pos[0], 6] = 1
#             Tin[pos[1], pos[0], 5] = 0


    for pos in new_walls:
        T[pos[1], pos[0], 4] = 1
        Tin[pos[1], pos[0], 4] = 1
    for pos in new_cells:
        T[pos[1], pos[0], 4] = 0
        Tin[pos[1], pos[0], 4] = 0
#         Karel(state=T).draw()

    for pos, marker_count in known_markers.items():

        # print(f"Make {pos} have {marker_count} markers")
        T[pos[1], pos[0], 5:16] = 0
        T[pos[1], pos[0], 5+marker_count['post']] = 1
        Tin[pos[1], pos[0], 5:16] = 0
        Tin[pos[1], pos[0], 5+marker_count['pre']] = 1
    return (Tin, T)
