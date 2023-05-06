import json
import copy
import torch
import os
from code.agents_neural.karel.world import World
from code.agents_neural.karel.ast_converter import AstParser
from code.algorithm_progressyn.interpreter.karel import Karel

REPLACE_DICT_TO_CARPEDM = {
     ## Actions
    'turnLeft' : 'turn_left',
    'turnRight': 'turn_right',
    'pickMarker': 'pick_marker',
    'putMarker': 'put_marker',
    'markersPresent': 'bool_marker',
    'noMarkersPresent': 'bool_no_marker',
    'leftIsClear': 'bool_path_left',
    'rightIsClear': 'bool_path_right',
    'frontIsClear': 'bool_path_ahead'
}

COMBINE_DICT_NOT = {
        'frontIsClear': 'bool_no_path_ahead',
        'leftIsClear': 'bool_no_path_left',
        'rightIsClear': 'bool_no_path_right',
}

IMG_FEAT = 5184
IMG_DIM = 18
IMG_SIZE = torch.Size((16, IMG_DIM, IMG_DIM))


def karel2nips(filename):
    samples = []
    with open(filename) as file:
        for line in file.readlines():
            d = json.loads(line)

            samples.append(d)

def iclr2carpedm_code(tokens):
    replace_dict = REPLACE_DICT_TO_CARPEDM

    combine_dict_not = COMBINE_DICT_NOT

    new_tokens = []
    ind = 0
    while ind < len(tokens):
        token = tokens[ind]
        if token == 'not':
            assert tokens[ind + 1] == 'c(' and tokens[ind + 2] in combine_dict_not.keys() and tokens[ind + 3] == 'c)'
            new_tokens.append(combine_dict_not[tokens[ind+2]])
            ind = ind + 4
        elif token in replace_dict:
            new_tokens.append(replace_dict[token])
            ind += 1
        else:
            new_tokens.append(token)
            ind += 1

    return " ".join(new_tokens)


def iclr_data(c_subs, t_subs, actions_dict):
    astparser = AstParser()
    samples = []
    for c,t in zip(c_subs, t_subs):
        print("New Subtask")
        tokens = carpedm2iclr_tokens(c)
        ast = astparser.parse(tokens)
        d = {}
        d['program_json'] = ast
        d['program_tokens'] = tokens
        d['examples'] = prepare_examples(t, actions_dict)
        samples.append(d)
    return samples


def to_iclr_dataset(dataset_name, dataset_path, c_subs, t_subs, actions_dict):
    dataset_name += ".json"
    filename = os.path.join(dataset_path, dataset_name)
    samples = iclr_data(c_subs, t_subs, actions_dict)
    with open(filename, 'a') as file:
        for d in samples:
            d_str = json.dumps(d)
            d_str += '\n'
            file.write(d_str)


def prepare_examples(task, actions_dict):
    ex_counter = 0
    examples = []
    for grid in task:
#         print("New Grid")
        example = {}
        example['actions'] = actions_dict[grid['ind']]
        example['example_index'] = ex_counter
        ## Input Grid (pregrid)
        inp_grid = Karel(grid['pre'])
        example['inpgrid_json'] = inp_grid.toJson()
        inp_world = World.parseJson(example['inpgrid_json'])
        inp_tensor = inp_world.toPytorchTensor(IMG_DIM)
        inp_idx = inp_tensor.reshape(IMG_FEAT).nonzero()
        example['inpgrid_tensor'] = " ".join([f"{int(i)}:1.0" for i in inp_idx])
        ### Output Grid (postgrid)
        out_grid = Karel(grid['post'])
        example['outgrid_json'] = out_grid.toJson()
#         print(example['outgrid_json'])
        out_world = World.parseJson(example['outgrid_json'])
#         print(out_world.toString())
        out_tensor = out_world.toPytorchTensor(IMG_DIM)
        out_idx = out_tensor.reshape(IMG_FEAT).nonzero()
        example['outgrid_tensor'] = " ".join([f"{int(i)}:1.0" for i in out_idx])
        examples.append(example)
        ex_counter += 1
    if ex_counter < 6:
        examples_to_create = 6-ex_counter
        for i in range(examples_to_create):
            examples.append(copy.deepcopy(examples[-1]))
    return examples



def carpedm2iclr_tokens(tokens):
    replace_dict = dict((v,k) for k,v in REPLACE_DICT_TO_CARPEDM.items())
    combine_dict_not = dict((v,k) for k,v in COMBINE_DICT_NOT.items())
    new_tokens = []
    ind = 0
    while ind < len(tokens):
        token = tokens[ind]
        if 'no' in token and not 'marker' in token:
            new_tokens.append('not')
            new_tokens.append('c(')
            new_tokens.append(combine_dict_not[token])
            new_tokens.append('c)')
            ind += 1
        elif token in replace_dict:
            new_tokens.append(replace_dict[token])
            ind += 1
        else:
            new_tokens.append(token)
            ind += 1

    return new_tokens

def iclr2carpedm_task(examples):
    io_states = []
    for i in range(6):
        state_pair = []
        pregrid = World.parseJson(examples[i]['inpgrid_json'])
#         print(examples[i]['inpgrid_json'])
#         print(pregrid.toString())
        state_pair.append(pregrid.toCarpedm())
        postgrid = World.parseJson(examples[i]['outgrid_json'])
        state_pair.append(postgrid.toCarpedm())
        io_states.append(state_pair)
    return io_states


def writeKarelJsonAsNipsTask(tasks, filename):
    alltasks = ''
    alltasks += 'type' + '\t' + 'karel' + '\n'
    alltasks += 'gridsz' + '\t' + '(ncol=16,nrow=16)' + '\n'
    alltasks += 'number_of_grids' + '\t' + len(tasks)
    for i, task in enumerate(tasks):
        task = '\n'
        pre = world.World.parseJson(task['inpgrid_json'])
        pregrid = pre.toTSVString('pregrid', i+1)
        task += pregrid + '\n'
        post = world.World.parseJson(task['outgrid_json'])
        postgrid = post.toTSVString('postgrid', i+1)
        task += postgrid
        alltasks += task

    with open(filename, 'w') as file:
        file.write(alltasks)
