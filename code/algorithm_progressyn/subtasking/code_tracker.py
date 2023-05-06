import json
import os
import copy

from code.algorithm_progressyn.interpreter.ast_to_code_converter import convert_ast_to_code
from code.algorithm_progressyn.interpreter.utils import pprint as pretty_code
from code.algorithm_progressyn.interpreter.utils import beautify          


class ExecutionTracker(object):
    def __init__(self, karel=None):
        self.ctoken_trace = []
        self.tvis_trace = []
        self.karel = karel
#         self.ast = AST()

    def token_snapshot(self, cexec):
        self.ctoken_trace.append(cexec)
        self.tvis_trace.append(self.karel.state)
#         self.update_ast()

#     def update_ast(self):
#         self.ast.parse_trace([cexec])
        
    def set_karel(self, karel):
        self.karel = karel
        
    def get_ctoken_trace(self):
        return self.ctoken_trace
    
    def get_tvis_trace(self):
        return self.tvis_trace    
        
class AST(object):
    def __init__(self, rollout_param=2):
        self.current = None
        self.root = self.current
        self.open_structures = []
        self.child_ind_stack = []   
        self.child_ind = 0
        self.block_id_counter = 0
        self.last_block = None
        self.rollout_param=rollout_param
             
    def _enter_structure(self, block):
        self.open_structures.append(self.current)
        self.current = block
        self.child_ind_stack.append(self.child_ind)
        self.child_ind = 0
        
    def _exit_structure(self):
        self.current = self.open_structures.pop()
        self.child_ind = self.child_ind_stack.pop()
        
    def _add_child(self, new_child):
        self.current["children"] += [new_child]
#         self.child_ind += 1      
        
    def _parsed_block(self):
        self.child_ind += 1
            
    def mark_branch(self, start, branch):
        info = start["info"]
        
        if_visited = info["visited-branches"].count("if")
        else_visited = len(info["visited-branches"]) - if_visited
        
        if branch == "if" and not if_visited and else_visited:
            # Make whole thing alive
            start.update({"alive":True})
            for child in start["children"]:
                child.update({"alive":True})
            
        elif branch == "else" and not else_visited and if_visited:
            # Make whole thing alive
            start.update({"alive":True})
            for child in start["children"]:
                child.update({"alive":True})
        
        info["visited-branches"].append(branch)
        self._update_all_open_structures()        
        
    def _update_all_open_structures(self):
#         print("printing all open structures")
#         for obj in self.open_structures:
#             print(obj)
        for i in range(len(self.open_structures)-1, -1, -1):
            block = self.open_structures[i]
            if block:
                if "repeat" in block["type"] or "while" in block["type"]:
                    block.update({"alive":_loop_aliveness(block, self.rollout_param)})
            
            


                
    def parse_trace(self, cexec_trace):
        
        for token in cexec_trace:
#             print(json.dumps(self.current, indent=3))
#             print(token)
            ## n
            if token == "run":
                if self.root is None:
#                     print("First grid")
                    new_block = {"type":"run", "alive":True, "children":[], "iden":self.block_id_counter}
                    self.block_id_counter += 1
                    self.root = new_block
                else:
#                     print("New grid")                    
                    assert self.code_over
                    self.code_over = False
                self._enter_structure(self.root)
                    
            elif token == "EOL":
                self.code_over = True
                self.current = None
                
            ## While Loop
            elif token == "while":                
                if self.child_ind < len(self.current["children"]):
                    assert token in self.current["children"][self.child_ind]["type"]
                    block = self.current["children"][self.child_ind]
                    block["info"]["nIterations"] = 0
                else:
                    assert self.child_ind == len(self.current["children"])
                    info = {"condition-entered":False, "past-n-iters":[], "while-body-seen":False, "nIterations": 0}#   
                    block = {"type": "while", "alive":False, "children":[], "info":info, "iden":self.block_id_counter}
                    self.block_id_counter += 1
                    self._add_child(block)
                self._parsed_block()
                self._enter_structure(block)
                
            elif token == "start-while-body":
                self.current["info"]["nIterations"] += 1
                self.current["alive"] = _loop_aliveness(self.current, self.rollout_param)
#                 if self.current["info"]["loop-skipped"] or self.current["info"]["nIterations"] == 2:
#                     self.current["alive"] = True
                    
            elif token == "end-while-body":
#                 self.current["info"]["nIterations"] += 1            
                self.current["info"]["while-body-seen"] = True
                self.current["alive"] = _loop_aliveness(self.current, self.rollout_param)    
                self.child_ind = 0
                
            elif token == "end-while":
                assert "while" in self.current["type"]
                self.current["info"]["past-n-iters"].append(self.current["info"]["nIterations"])
#                 if not self.current["info"]["while-body-seen"]:
#                     self.current["info"]["loop-skipped"] = True
#                 self.current["info"]["loop-over"] = True
                self._exit_structure()
            
            ## Repeat
            elif token == "repeat":
                if self.child_ind < len(self.current["children"]):
                    assert token in self.current["children"][self.child_ind]["type"]
                    block = self.current["children"][self.child_ind]
                    block["info"]["nIterations"] = 0
                else:
                    assert self.child_ind == len(self.current["children"])
                    block = {"type":"repeat", "alive":False, "children":[], "iden":self.block_id_counter, "info":{"nIterations":0}}
                    self.block_id_counter += 1
                    self._add_child(block)
                self._parsed_block()                    
                self._enter_structure(block)
                
            elif token == "start-repeat-body":
                self.current["alive"] = _loop_aliveness(self.current, self.rollout_param)
#                 if self.current["info"]["nIterations"] == 2:
#                     self.current["alive"] = True
                self.current["type"] = "repeat" + "(" + str(self.current["info"]["nIterations"]) + ")"
                
            elif token == "end-repeat-body":
                self.child_ind = 0
                self.current["info"]["nIterations"] += 1
                self.current["type"] = "repeat" + "(" + str(self.current["info"]["nIterations"]) + ")"
                
        
            elif token == "end-repeat":
                assert "repeat" in self.current["type"]
                self._exit_structure()
                
            # IF
            
            elif token == "if" or token == "ifelse":
                if self.child_ind < len(self.current["children"]):
                    assert token in self.current["children"][self.child_ind]["type"]
                    block = self.current["children"][self.child_ind]
                else:
                    assert self.child_ind == len(self.current["children"])
                    info = {"visited-branches":[], "condition-entered":False}
                    nb_if = {"type":"do", "alive":False, "children":[], "iden": self.block_id_counter}

                    if token == "ifelse":
                        nb_else = {"type":"else", "alive":False, "children":[], "iden": self.block_id_counter + 1}
#                         block = {"type": token, "alive":False, "children":[nb_if, nb_else],
#                                  "iden": self.block_id_counter + 2, "info":info}
                    else:
                        nb_else = {"type":"else", "alive":False, "iden": self.block_id_counter + 1,
                                   "internal": True}
#                         block = {"type": token, "alive":False, "children":[nb_if],
#                                  "iden": self.block_id_counter + 2, "info":info}
                    block = {"type": token, "alive":False, "children":[nb_if, nb_else],
                             "iden": self.block_id_counter + 2, "info":info}
                
                    self.block_id_counter += 3
                    self._add_child(block)
                self._parsed_block()
                self._enter_structure(block)
#                 print("If/Ifelse - Post : " + str(self.current))
                
            elif token == "do":
                assert "if" in self.current["type"] or "ifelse" in self.current["type"]
                self.mark_branch(self.current, "if")
                self._enter_structure(self.current["children"][0])
                
            elif token == "else":
#                 print("Else - Pre: " + self.current["type"])
                self.mark_branch(self.current, "else")
   
                if "ifelse" in self.current["type"]:
                    self._enter_structure(self.current["children"][1])
                elif "if" in self.current["type"]:                    
#                     self._enter_structure({"type":"dummy", "iden":-1})
                    self._enter_structure(self.current["children"][1])
                    self.last_block = self.current["iden"]
                        
            elif token == "end-if" or token == "end-ifelse":
                self._exit_structure()
                self._exit_structure()                
                
            elif "action" in token and not "NOP" in token:
                if self.child_ind < len(self.current["children"]):
                    self.last_block = self.current["children"][self.child_ind]["iden"]
                else:
                    l_name = token.lower()
                    block = {"type":l_name.split("action-")[1], "alive":True, "iden":self.block_id_counter}
                    self.last_block = self.block_id_counter
                    self.block_id_counter += 1   
                    self._add_child(block)
                self._parsed_block()
            
            elif "condition" in token:
                condition = token.lower()
                assert "if" in self.current["type"] or "while" in self.current["type"], f"Condition not preceded by conditional block, current_block: " + self.current["type"]
                if not self.current["info"]["condition-entered"]:
                    self.current["type"] += "(" + condition.split("condition-")[1] + ")"
                    self.current["info"]["condition-entered"] = True           
                
                
                        
    def pprint(self, ast, human_readable=False):
        return json.dumps(ast, indent=4)
    
    def readable_code(self):
        return beautify(convert_ast_to_code(self.current_ast()))
    
    def current_ast(self):
        if self.root:
            root = _remove_dead_replace_loops(self.root, rollout_param=self.rollout_param)[0]
            _remove_internal(root)            
            return root
        else:
            return None

    def valid_snapshot(self, cexec):
        if self.root is None:
            return False
        else:
#             root = _remove_dead(self.root, keep_iden=True)[0]
            root = self.root
            return self._rightmost_child_no_loop(root, cexec)
        
    def _rightmost_child_no_loop(self, block, iden):
        if block.get("children", None) is None:
            return block["iden"] == iden
        else:
            if not (any([elem in block["type"] for elem in ["run", "repeat", "while", "do"]]) or block["type"] == "else"):
                ## If the node is not any of [run, repeat(int), while(cond), do, else]. 
                # Else is written as a separate check because `"else" in block["type"]` is true for both `else` and `ifelse`.
                return any([self._rightmost_child_no_loop(child, iden) for child in block["children"]])
            elif "while" in block["type"] or "repeat" in block["type"]:
                return block["iden"] == iden
            else:
                return self._rightmost_child_no_loop(block["children"][-1], iden) if len(block["children"]) != 0 else True        
        
#     def _rightmost_child(self, block, iden):
#         if block.get("children", None) is None:
#             return block["iden"] == iden
#         else:
#             if not (any([elem in block["type"] for elem in ["run", "repeat", "while", "do"]]) or block["type"] == "else"):
#                 return any([self._rightmost_child(child, iden) for child in block["children"]])
#             else:
#                 return self._rightmost_child(block["children"][-1], iden)# if len(block["children"]) == 0 else True


    def get_copy(self):
        return copy.deepcopy(self.root)
    
    def get_nodes(self):
        return dfs(self.root)

        
    def dfs(block):
        nodes = []
        for child in self.block.get("children", []):
            nodes += dfs(child)
        return nodes
   
    def __str__(self):
        return self.pprint(self.current_ast())
    
    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, copy.deepcopy(v, memo))
        return result
    
def current_ast(root, hoc=False, rollout_param=2):
    root = _remove_dead_replace_loops(root, rollout_param=rollout_param)[0]
    _remove_internal(root)
    if hoc:
        _remove_turn_suffix(root)
    return root

def _remove_turn_suffix(block):
    pass
#     if block["children"]:
#         child = block["children"][-1]
#         while "turn" in child["type"]:
#             block["children"].pop()
#             if block["children"]:
#                 child = block["children"][-1]
#             else:
#                 break
    
def _remove_internal(block):
    if not block.get("internal", False) and block.get("children", None) is None:
        return block

    elif not block.get("children", None) is None:
        block["children"] = [_remove_internal(child) for child in block["children"] if not child.get("internal", False)]
        return block
                    
def _remove_dead(block, keep_iden=False):       
    if not block["alive"]:
        children_to_adopt = []
        for child in [_remove_dead(c, keep_iden=keep_iden) for c in block.get("children", [])]:
            for grandchild in child:
                children_to_adopt.append(grandchild)
        return children_to_adopt
    else:
        new_block = {"type":block["type"], "internal":True} if block.get("internal", False) else {"type":block["type"]}
        if keep_iden:
            new_block["iden"] = block["iden"]

        if block.get("children", None) is None:
            pass
        else:
            children_to_adopt = []
            for child in [_remove_dead(c, keep_iden=keep_iden) for c in block.get("children", [])]:
                for grandchild in child:
                    children_to_adopt.append(grandchild)                
            new_block["children"] = children_to_adopt
        return [new_block] 
    
def _remove_dead_replace_loops(block, iteration=0, alive_parents=True, keep_iden=False, rollout_param=2):
#     print()
#     print(block)
    if "while" in block["type"] or "repeat" in block["type"]:
#         ## ToDo Unify nIterations field for repeat and while
#         if block["info"]["nIterations"] > 3 or len(block["children"]) > 5:
#             ## Loop alive - branching is not overwritten
#             loop_alive = True
#         elif block["info"]["nIterations"] <= 3:
#             if all([max(child["info"]["visited-branches"].count("if"), child["info"]["visited-branches"].count("else")) < 3 for child in block["children"] if "if" in child["type"]]):
#                 ### Loop alive - branching is not overwritten
#                 loop_alive = False
#             else:
#                 ### Loop dead - overwrite branching
#                 print
#                 loop_alive = True

#         print(f"Observed that loop_alive={loop_alive} and block[alive]={block.get('alive', None)}")
        if not _loop_aliveness(block,rollout_param=rollout_param):#["alive"]:# and not block["alive"]:
            children_to_adopt = []
            for i in range(block["info"]["nIterations"]):
                for child in block.get("children", []):
                    if "if" in child["type"]:
#                         print(f"Childs of child: {child['children']}, visited branches {child['info']['visited-branches']}")
                        if len(child["info"]["visited-branches"]) > i:
                            branch_for_this_iter = child["children"][child["info"]["visited-branches"][i] == "else"]
                            grandchild_list = _remove_dead_replace_loops(branch_for_this_iter, iteration=i, alive_parents = False, keep_iden=keep_iden, rollout_param=rollout_param)
                        else:
                            grandchild_list = []
                    else:
                        grandchild_list = _remove_dead_replace_loops(child, iteration=i, alive_parents = False, keep_iden=keep_iden, rollout_param=rollout_param)

                    for grandchild in grandchild_list:
                        children_to_adopt.append(grandchild)
#                 for child in [_remove_dead_replace_loops(c, iteration=i, alive_parents = False, keep_iden=keep_iden, rollout_param=rollout_param) for c in block.get("children", [])]:
#                     for grandchild in child:
#                         children_to_adopt.append(grandchild)
            return children_to_adopt          
        else:
            ## What to do when loop is alive? --> The regular thing
            new_block = {"type":block["type"], "internal":True} if block.get("internal", False) else {"type":block["type"]}
            if keep_iden:
                new_block["iden"] = block["iden"]

            if block.get("children", None) is None:
                pass
            else:
                children_to_adopt = []
                for child in [_remove_dead_replace_loops(c, keep_iden=keep_iden, rollout_param=rollout_param) for c in block.get("children", [])]:
                    for grandchild in child:
                        children_to_adopt.append(grandchild)                
                new_block["children"] = children_to_adopt
            return [new_block]                     


    else:
        ## What to do when the block is not loop?
        if not block["alive"] or (not alive_parents and any([elem in block["type"] for elem in ["if", "do", "else"]])):
            children_to_adopt = []
            for child in [_remove_dead_replace_loops(c, keep_iden=keep_iden, rollout_param=rollout_param) for c in block.get("children", [])]:
                for grandchild in child:
                    children_to_adopt.append(grandchild)
            return children_to_adopt
        else:
            new_block = {"type":block["type"], "internal":True} if block.get("internal", False) else {"type":block["type"]}
            if keep_iden:
                new_block["iden"] = block["iden"]

            if block.get("children", None) is None:
                pass
            else:
                children_to_adopt = []
                for child in [_remove_dead_replace_loops(c, keep_iden=keep_iden,rollout_param=rollout_param) for c in block.get("children", [])]:
                    for grandchild in child:
                        children_to_adopt.append(grandchild)                
                new_block["children"] = children_to_adopt
            return [new_block]         

def _loop_aliveness(block, rollout_param=2): 
#     print(block)
#     print()
    loop_alive = False
    if not ("while" in block["type"] or "repeat" in block["type"]):
        return loop_alive    
    if "while" in block["type"]:
        if len(set(block["info"]["past-n-iters"])) > 1:
            loop_alive = True                
        elif len(block["info"]["past-n-iters"]) > 0:
            if block["info"]["past-n-iters"][0] < block["info"]["nIterations"]:
                loop_alive = True
    if len(block["children"]) > 50 and block["info"]["nIterations"] > 1:
        ## Loop alive - branching is not overwritten
        loop_alive = True
    elif block["info"]["nIterations"] > rollout_param:
        branching_liveness = [max(child["info"]["visited-branches"].count("if"), child["info"]["visited-branches"].count("else")) > rollout_param for child in block["children"] if "if" in child["type"]]
        if len(branching_liveness) == 0 or any(branching_liveness):
            ### Loop alive - branching is not overwritten
#                 pass
            loop_alive = True
        else:
            ### Loop dead - overwrite branching
            pass
#                 loop_alive = False
    return loop_alive
