# -*- coding: utf-8 -*-
"""
Created on Thu Jul 17 07:45:32 2025

@author: 2016570
"""
from .transpilation.hls_timed import *
from .transpilation.astutils import *
from .base import Logic
import astunparse

class Py4hwGenerator:
    
    def generateSequentialCode(self, obj):
        tree = self.generateSequentialAST(self, obj)
        ast.fix_missing_locations(tree)
        return astunparse.unparse(tree)


    def generateSequentialAST(self, obj, useIfElseTree=False):
        
        if isinstance(obj, type):
            if issubclass(obj, Logic):
                return self.generateSequentialASTFromClass(obj, useIfElseTree)
            else:
                raise Exception(f'{type(obj)} not supported')
                
        elif isinstance(obj, Logic):
            return self.generateSequentialASTFromClass(obj.__class__, useIfElseTree)
        else:
            raise Exception(f'{type(obj)} not supported')

    def generateSequentialASTFromClass(self, clz, useIfElseTree):
        tree = get_class_ast(clz)

        tree = replaceConstants(tree, clz)

        tree = ScopedSelfAliasRewriter().visit(tree)
        tree = ReplacePrintByPass().visit(tree)
        tree = RemoveIrrelevantConditions().visit(tree)
        tree = SSARewriter().visit(tree)
        tree = removeUnusedAssignments(tree)

        tree = inline_yield_from(tree)
        
        #tree = transform_generator_to_fsm(tree)
        #tree  = yield_to_state(tree)
        
        run_node = getASTFromClassMethod(tree, 'run')
        
        build = CFGBuilder()
        build.build(run_node)
        
        removePassFromCFG(build)
        removeEmptyNodesFromCFG(build)
        removeIrrelevantConditionsFromCFG(build)
        removeUnusedTargetsInCFG(build)
        removeConstantControlFlowFromCFG(build)
        removeEmptyNodesFromCFG(build)
        yields = selectYieldingNodes(build)
        state = extractStates(build, yields)
        if (useIfElseTree):
            topif = createStateSelectionIfElseTree(state, yields)
        else:
            topif = createStateSelectionMatchCase(state, yields)
            topif = ReplaceIfElseTreeByMatchCase().visit(topif)
        tr = ClockMethodReplacer(topif)
        tree = tr.visit(tree)
        tr = KeepInitAndClockTransformer()
        tree = tr.visit(tree)
        return tree
    
        
    