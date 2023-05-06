from __future__ import print_function

from .parser_base import dummy, get_hash, parser_prompt, Parser
from code.algorithm_progressyn.subtasking.code_tracker import ExecutionTracker
# from .output_tracker import OutputTracker
from code.algorithm_progressyn.interpreter.utils import beautify

class KarelForSynthesisParser(Parser):


    tokens = [
            'DEF', 'RUN',
            'M_LBRACE', 'M_RBRACE', 'C_LBRACE', 'C_RBRACE', 'R_LBRACE', 'R_RBRACE',
            'W_LBRACE', 'W_RBRACE', 'I_LBRACE', 'I_RBRACE', 'E_LBRACE', 'E_RBRACE',
            'INT', #'NEWLINE', 'SEMI',
            'WHILE', 'REPEAT',
            'IF', 'IFELSE', 'ELSE',
#             'FRONT_IS_CLEAR', 'LEFT_IS_CLEAR', 'RIGHT_IS_CLEAR',
#             'MARKERS_PRESENT', 'NO_MARKERS_PRESENT', 'NOT',
            'FRONT_IS_CLEAR', 'NO_FRONT_IS_CLEAR', 'LEFT_IS_CLEAR', 'NO_LEFT_IS_CLEAR',
            'RIGHT_IS_CLEAR', 'NO_RIGHT_IS_CLEAR', 'MARKERS_PRESENT', 'NO_MARKERS_PRESENT',
            'NO_GOAL_PRESENT',
            'MOVE', 'TURN_RIGHT', 'TURN_LEFT',
            'PICK_MARKER', 'PUT_MARKER',
    ]

    t_ignore =' \t\n'

    t_M_LBRACE = 'm\('
    t_M_RBRACE = 'm\)'

    t_C_LBRACE = 'c\('
    t_C_RBRACE = 'c\)'

    t_R_LBRACE = 'r\('
    t_R_RBRACE = 'r\)'

    t_W_LBRACE = 'w\('
    t_W_RBRACE = 'w\)'

    t_I_LBRACE = 'i\('
    t_I_RBRACE = 'i\)'

    t_E_LBRACE = 'e\('
    t_E_RBRACE = 'e\)'

    t_DEF = 'DEF'
    t_RUN = 'run'
    t_WHILE = 'WHILE'
    t_REPEAT = 'REPEAT'
    t_IF = 'IF'
    t_IFELSE = 'IFELSE'
    t_ELSE = 'ELSE'
#     t_NOT = 'not'

    t_FRONT_IS_CLEAR = 'bool_path_ahead'
    t_NO_FRONT_IS_CLEAR = 'bool_no_path_ahead'
    t_LEFT_IS_CLEAR = 'bool_path_left'
    t_NO_LEFT_IS_CLEAR = 'bool_no_path_left'
    t_RIGHT_IS_CLEAR = 'bool_path_right'
    t_NO_RIGHT_IS_CLEAR = 'bool_no_path_right'
    t_MARKERS_PRESENT = 'bool_marker'
    t_NO_MARKERS_PRESENT = 'bool_no_marker'
    t_NO_GOAL_PRESENT = 'bool_no_goal'

    conditional_functions = [
            t_FRONT_IS_CLEAR, t_NO_FRONT_IS_CLEAR,
            t_LEFT_IS_CLEAR, t_NO_LEFT_IS_CLEAR,
            t_RIGHT_IS_CLEAR, t_NO_RIGHT_IS_CLEAR,
            t_MARKERS_PRESENT, t_NO_MARKERS_PRESENT,
            t_NO_GOAL_PRESENT
    ]


    t_MOVE = 'move'
    t_TURN_RIGHT = 'turn_right'
    t_TURN_LEFT = 'turn_left'
    t_PICK_MARKER = 'pick_marker'
    t_PUT_MARKER = 'put_marker'

    action_functions = [
            t_MOVE,
            t_TURN_RIGHT, t_TURN_LEFT,
            t_PICK_MARKER, t_PUT_MARKER,
    ]


    def __init__(self, exec_tracker, *args, **kwargs):
        super().__init__(*args,**kwargs)
        self.tracker = exec_tracker

    def new_game(self, **kwargs):
        super().new_game(**kwargs)
#         if self.output_tracker is None:
#             self.output_tracker = OutputTracker(self.decomposer, self.karel)
#             self.output_tracker.new_grid(self.karel, first=True)
#         else:
#             self.output_tracker.new_grid(self.karel)
#             print(self.decomposer.readable_code())

    def get_karel(self):
        return self.karel
    #########
    # lexer
    #########

    INT_PREFIX = 'R='
    def t_INT(self, t):
        r'R=\d+'

        value = int(t.value.replace(self.INT_PREFIX, ''))
        if not (self.min_int <= value <= self.max_int):
            raise Exception(" [!] Out of range ({} ~ {}): `{}`". \
                    format(self.min_int, self.max_int, value))

        t.value = value
        return t

    def random_INT(self):
        return "{}{}".format(
                self.INT_PREFIX,
                self.rng.randint(self.min_int, self.max_int + 1))

    def t_error(self, t):
        print("Illegal character %s" % repr(t.value[0]))
        t.lexer.skip(1)

    #########
    # parser
    #########

    def p_prog(self, p):
        '''prog : DEF RUN M_LBRACE stmt M_RBRACE'''
        stmt = p[4]

        @self.callout
        def fn():
            self.tracker.token_snapshot("run")
            res = stmt()
            self.tracker.token_snapshot("EOL")
#             self.output_tracker.take_snapshot(prog_end=True)
            return res
        p[0] = fn

    def p_stmt(self, p):
        '''stmt : while
                | repeat
                | stmt_stmt
                | action
                | if
                | ifelse
        '''
        function = p[1]

        @self.callout
        def fn():
            return function()
        p[0] = fn

    def p_stmt_stmt(self, p):
        '''stmt_stmt : stmt stmt
        '''
        stmt1, stmt2 = p[1], p[2]

        @self.callout
        def fn():
            stmt1(); stmt2();
        p[0] = fn

    def p_if(self, p):
        '''if : IF C_LBRACE cond C_RBRACE I_LBRACE stmt I_RBRACE
        '''
        cond, stmt = p[3], p[6]
#         iden = get_hash()
        iden = p.lexpos(3)

        hit_info = self.hit_info
        if hit_info is not None:

            num = get_hash()
            hit_info[num] += 1

            @self.callout
            def fn():
                if cond():
                    hit_info[num] -= 1
                    out = stmt()
                else:
                    out = dummy()
                return out
        else:
            @self.callout
            def fn():
#                 start = self.decomposer.add_conditional_block(iden, block_type = "if")
                self.tracker.token_snapshot("if")
                if cond():
#                     self.decomposer.jump_to_if()
#                     self.decomposer.mark_branch(start, "if")
                    self.tracker.token_snapshot("do")
                    out = stmt()
                else:
                    self.tracker.token_snapshot("else")
                    self.tracker.token_snapshot("action-NOP")
                    out = dummy()
                self.tracker.token_snapshot("end-if")
#                 self.decomposer.end_conditional_block(start)
#                 self.output_tracker.take_snapshot()
                return out

        p[0] = fn

    def p_ifelse(self, p):
        '''ifelse : IFELSE C_LBRACE cond C_RBRACE I_LBRACE stmt I_RBRACE ELSE E_LBRACE stmt E_RBRACE
        '''
        cond, stmt1, stmt2 = p[3], p[6], p[10]
#         iden = get_hash()
#         iden = p.lexpos(3)

        hit_info = self.hit_info
        if hit_info is not None:
            num1, num2 = get_hash(), get_hash()
            hit_info[num1] += 1
            hit_info[num2] += 1

            @self.callout
            def fn():
                if cond():
                    hit_info[num1] -= 1
                    out = stmt1()
                else:
                    hit_info[num2] -= 1
                    out = stmt2()
                return out
        else:
            @self.callout
            def fn():
#                 start = self.decomposer.add_conditional_block(iden, block_type = "ifelse")
                self.tracker.token_snapshot("ifelse")
                if cond():
#                     self.decomposer.jump_to_if()
#                     self.decomposer.mark_branch(start, "if")
                    self.tracker.token_snapshot("do")
                    out = stmt1()
                else:
#                     self.decomposer.jump_to_else()
#                     self.decomposer.mark_branch(start, "else")
                    self.tracker.token_snapshot("else")
                    out = stmt2()
                ## Create Snapshot if this is the first time we see this --> Add Body
                ## or both branches are visited for the first time. --> Add Construct
                self.tracker.token_snapshot("end-ifelse")

#                 self.decomposer.end_conditional_block(start)
#                 self.output_tracker.take_snapshot()
                return out

        p[0] = fn

    def p_while(self, p):
        '''while : WHILE C_LBRACE cond C_RBRACE W_LBRACE stmt W_RBRACE
        '''
        cond, stmt = p[3], p[6]
#         iden = get_hash()
        iden = p.lexpos(3)

        hit_info = self.hit_info
        if hit_info is not None:
            num = get_hash()
            hit_info[num] += 1

            @self.callout
            def fn():
                while(cond()):
                    hit_info[num] -= 1
                    stmt()
        else:
            @self.callout
            def fn():
                self.tracker.token_snapshot("while")
                while(cond()):
                    self.tracker.token_snapshot("start-while-body")
                    stmt()
                    self.tracker.token_snapshot("end-while-body")
                self.tracker.token_snapshot("end-while")
        p[0] = fn

    def p_repeat(self, p):
        '''repeat : REPEAT cste R_LBRACE stmt R_RBRACE
        '''
        cste, stmt = p[2], p[4]
#         iden = get_hash()
        iden = p.lexpos(2)

        hit_info = self.hit_info
        if hit_info is not None:
            num = get_hash()
            hit_info[num] += 1

            @self.callout
            def fn():
                for _ in range(cste()):
                    hit_info[num] -= 1
                    stmt()
        else:
            @self.callout
            def fn():
#                 self.decomposer.add_repeat_node(iden, times=1)
                self.tracker.token_snapshot("repeat")
                for i in range(cste()):
                    self.tracker.token_snapshot("start-repeat-body")
#                     if i == 1:
#                         self.decomposer.make_alive(iden)
#                     if i >= 1:
#                         self.decomposer.change_repeat_number(i+1, iden)
                    stmt()
                    self.tracker.token_snapshot("end-repeat-body")
                self.tracker.token_snapshot("end-repeat")
#                     self.output_tracker.take_snapshot()
#                 self.decomposer.end_repeat(iden)
        p[0] = fn


    def p_cond(self, p):
        '''cond : FRONT_IS_CLEAR
                | NO_FRONT_IS_CLEAR
                | LEFT_IS_CLEAR
                | NO_LEFT_IS_CLEAR
                | RIGHT_IS_CLEAR
                | NO_RIGHT_IS_CLEAR
                | MARKERS_PRESENT
                | NO_MARKERS_PRESENT
                | NO_GOAL_PRESENT
        '''
        cond = p[1]
        def fn():
#             self.decomposer.add_condition(condition=cond.title())
            self.tracker.token_snapshot(f"condition-{cond.title()}")

#             print("------------------------------------------------------------------------------")
#             print(self.decomposer)
            evaluation = getattr(self.karel, cond)()

            return evaluation

        p[0] = fn


    def p_action(self, p):
        '''action : MOVE
                  | TURN_RIGHT
                  | TURN_LEFT
                  | PICK_MARKER
                  | PUT_MARKER
        '''
        action = p[1]
#         iden = get_hash()
        iden = p.lexpos(1)
        karel = self.karel
        def fn():
#             self.decomposer.add_action(iden, name=action.title())

            res = getattr(karel, action)()
            self.tracker.token_snapshot(f"action-{action.title()}")
#             self.output_tracker.take_freq_snapshot(cexec=iden)
            ## Add snapshot here but not for output
#             print("------------------------------------------------------------------------------")
#             print(self.decomposer)#.make_json())
            return res
        p[0] = fn

    def p_cste(self, p):
        '''cste : INT
        '''
        value = p[1]
        p[0] = lambda: int(value)

    def p_error(self, p):
        if p:
            print("Syntax error at '%s'" % p.value)
        else:
            print("Syntax error at EOF")


if __name__ == '__main__':
    parser = KarelForSynthesisParser()
    parser_prompt(parser)
