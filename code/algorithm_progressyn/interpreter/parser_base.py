from __future__ import print_function

import random
import ply.lex as lex
from functools import wraps
from collections import defaultdict

from . import yacc
from .karel import Karel
from .utils import pprint, timeout, get_rng, str2bool, TimeoutError


class Parser(object):
    """
    Base class for a lexer/parser that has the rules defined as methods.
    """
    tokens = ()
    precedence = ()

    def __init__(self, rng=None, min_int=0, max_int=19,
                 max_func_call=100, debug=False, **kwargs):

        self.names = {}
        self.debug = kwargs.get('debug', 0)

        # Build the lexer and parser
        modname = self.__class__.__name__

        self.lexer = lex.lex(module=self, debug=self.debug)

        self.yacc, self.grammar = yacc.yacc(
                module=self,
                debug=self.debug,
                tabmodule="_parsetab",
                with_grammar=True)

        self.prodnames = self.grammar.Prodnames

        #########
        # main
        #########

        self.debug = debug
        self.min_int = min_int
        self.max_int = max_int
        self.max_func_call = max_func_call
        self.int_range = list(range(min_int, max_int+1))

        int_tokens = ['INT{}'.format(num) for num in self.int_range]
        self.tokens_details = list(set(self.tokens) - set(['INT'])) + int_tokens

        #self.idx_to_token = { idx: token for idx, token in enumerate(tokens) }
        #self.token_to_idx = { token:idx for idx, token in idx_to_token.items() }

        self.tokens_details.sort()
        self.tokens_details = ['END'] + self.tokens_details

        self.idx_to_token_details = {
                idx: token for idx, token in enumerate(self.tokens_details) }
        self.token_to_idx_details = {
                token:idx for idx, token in self.idx_to_token_details.items() }

        self.rng = get_rng(rng)
        self.flush_hit_info()
        self.call_counter = [0]

        def callout(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                if self.call_counter[0] > self.max_func_call:
                    raise TimeoutError
                r = f(*args, **kwargs)
                self.call_counter[0] += 1
                return r
            return wrapped

        self.callout = callout

    def lex_to_idx(self, code, details=False):
        tokens = []
        self.lexer.input(code)
        while True:
            tok = self.lexer.token()
            if not tok:
                break

            if details:
                if tok.type == 'INT':
                    idx = self.token_to_idx_details["INT{}".format(tok.value)]
                else:
                    idx = self.token_to_idx_details[tok.type]
            else:
                idx = self.token_to_idx[tok.type]
            tokens.append(idx)
        return tokens


    #########
    # Karel
    #########

    def get_state(self):
        return self.karel.state

    def run(self, code, with_timeout=False, **kwargs):
        code_hash = hash(code)
        self.call_counter = [0]

        if code_hash in self.funct_table:
            def fn():
                return self.funct_table[code_hash]()
        else:
            yacc = self.yacc
            def fn():
                return yacc.parse(code, **kwargs)()
            self.funct_table[code_hash] = fn

        out = fn()
        return out

    def new_game(self, **kwargs):
        self.karel = Karel(debug=self.debug, rng=self.rng, **kwargs)

    def draw(self, *args, **kwargs):
        return self.karel.draw(*args, **kwargs)

    def draw_for_tensorboard(self):
        return "\t" + "\n\t".join(self.draw(no_print=True))

    def random_code(self, create_hit_info=False, *args, **kwargs):
        code = " ".join(self.random_tokens(*args, **kwargs))

        # check minimum # of move()
        min_move = getattr(kwargs, 'min_move', 0)
        count_diff = min_move - code.count(self.t_MOVE)

        if count_diff > 0:
            action_candidates = []
            tokens = code.split()

            for idx, token in enumerate(tokens):
                if token in self.action_functions and token != self.t_MOVE:
                    action_candidates.append(idx)

            idxes = self.rng.choice(
                    action_candidates, min(len(action_candidates), count_diff))
            for idx in idxes:
                tokens[idx] = self.t_MOVE
            code = " ".join(tokens)

        if create_hit_info:
            self.hit_info = defaultdict(int)
        else:
            self.hit_info = None

        return code

    def random_tokens(self, start_token="prog", depth=0, stmt_min_depth=2, stmt_max_depth=5, **kwargs):
        #print(depth, start_token)
        if start_token == 'stmt':
            if depth > stmt_max_depth:
                start_token = "action"
            #if depth < 2:
            #    start_token = self.rng.choice(
            #            ['action'] * 1
            #            + ['while'] * 4
            #            + ['repeat'] * 4
            #            + ['stmt_stmt'] * 16
            #            + ['if', 'ifelse'] * 4, 1)[0]

        codes = []
        candidates = self.prodnames[start_token]

        prod = candidates[self.rng.randint(len(candidates))]

        for term in prod.prod:
            if term in self.prodnames: # need digging
                codes.extend(self.random_tokens(term, depth + 1, stmt_max_depth))
            else:
                token = getattr(self, 't_{}'.format(term))
                if callable(token):
                    if token == self.t_INT:
                        token = self.random_INT()
                    else:
                        raise Exception(" [!] Undefined token `{}`".format(token))

                codes.append(str(token).replace('\\', ''))

        return codes

    def flush_hit_info(self):
        self.hit_info = None
        self.funct_table = {} # save parsed function


def dummy():
    pass

def get_hash():
    return random.getrandbits(128)

def parser_prompt(parser):
    import argparse
    from prompt_toolkit import prompt
    from prompt_toolkit.token import Token

    def continuation_tokens(cli, width):
        return [(Token, ' ' * (width - 5) + '.' * 3 + ':')]

    def is_multi_line(line):
        return line.strip()

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--debug', type=str2bool, default=False)
    arg_parser.add_argument('--world', type=str, default=None, help='Path to world text file')
    arg_parser.add_argument('--world_height', type=int, default=8, help='Height of square grid world')
    arg_parser.add_argument('--world_width', type=int, default=8, help='Width of square grid world')
    args = arg_parser.parse_args()

    line_no = 1
    parser.debug = args.debug

    print('Press [Meta+Enter] or [Esc] followed by [Enter] to accept input.')
    while True:
        code = prompt(u'In [{}]: '.format(line_no), multiline=True,
                      get_continuation_tokens=continuation_tokens)

        if args.world is not None:
            parser.new_game(world_path=args.world)
        else:
            parser.new_game(world_size=(args.world_width, args.world_height))

        parser.draw("Input:  ", with_color=True)
        parser.run(code, debug=False)
        parser.draw("Output: ")
        line_no += 1
