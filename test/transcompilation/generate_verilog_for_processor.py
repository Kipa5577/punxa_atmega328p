import sys, io, contextlib , os 
current_dir = os.path.dirname(os.path.abspath(__file__))

testbench_path = os.path.join(current_dir,'..','isa_tests','tb_ISA_tests_Multicycle_rewrite.py')
asm_path = os.path.join(current_dir,'..','isa_tests','isa','test_arith_ADD.asm')
sys.path.insert(0, '.')
exec(open(testbench_path).read().split("if __name__")[0])

import py4hw
from py4hw.rtl_generation import VerilogGenerator

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    hw, cpu, ins_mem, mem, symbols = prepareTest(asm_path)
    silence_debug(cpu._cpu)


from py4hw.rtl_generation import clearWireNamesCache
from py4hw.transpilation.python2verilog_transpilation import (
    ExtractInitializers, Python2VerilogTranspiler, createVerilogBody,
    RemovePrints, RemoveAssert, ReplaceIf, ReplaceParameterCalls,
    ReplaceWireCalls, ReplaceExpr, ReplaceOperators, ReplaceWiresAndVariables,
    ReplaceConstant, ReplaceAssign,
)
import ast


def _fixed_transpileCombinational(self):
    """Drop-in replacement for Python2VerilogTranspiler.transpileCombinational,
    monkey-patched in at runtime (this process's memory only -- nothing on
    disk is modified). The stock method is missing the one line that
    transpileSequential has (`node.wires.variables =
    wiresAndVars.variables.values()`), so every propagate()-based
    (combinational) module's local-variable declaration section comes out
    empty regardless of how many locals its propagate() body actually
    uses -- confirmed by direct comparison against transpileSequential in
    site-packages/py4hw/transpilation/python2verilog_transpilation.py.
    Every other line below is copied verbatim from the stock method."""
    module = self.getMethodAST('__init__')
    node = createVerilogBody(module.body)

    initExtracter = ExtractInitializers(self.obj)
    init = initExtracter.visit(node)

    module = self.getMethodAST('propagate')
    node = createVerilogBody(module.body, '*')

    assert isinstance(node, ast.AST)

    node = RemovePrints().visit(node)
    node = RemoveAssert().visit(node)

    node = ReplaceIf().visit(node)
    node = ReplaceParameterCalls().visit(node)
    node = ReplaceWireCalls().visit(node)
    node = ReplaceExpr().visit(node)
    node = ReplaceOperators().visit(node)
    node = ReplaceOperators().visit(node)

    wiresAndVars = ReplaceWiresAndVariables(initExtracter.ports, initExtracter.variables, initExtracter.arguments)
    node = wiresAndVars.visit(node)
    node = ReplaceConstant().visit(node)
    node = ReplaceAssign().visit(node)

    node.wires.variables = wiresAndVars.variables.values()  # the missing line

    return node


Python2VerilogTranspiler.transpileCombinational = _fixed_transpileCombinational

shared_created_structures = []


def gen_hierarchy(hw, obj, noInstanceNumberInTopEntity=True):
    """Re-implementation of VerilogGenerator._getVerilogForHierarchy that
    creates a brand-new VerilogGenerator for every single module's own
    variable-declaration extraction, instead of reusing one
    VerilogGenerator instance (and therefore one shared variable-name
    namespace) across the whole hierarchy -- see module docstring below
    for why. `shared_created_structures` is intentionally the one piece
    of state still shared across every fresh generator (matching what
    getVerilogForHierarchy itself does across its own recursive calls),
    since that's what dedupes generic/primitive modules (Add8, Reg8RE,
    ...) that are legitimately instantiated many times -- losing that
    dedup produces duplicate `module Foo` definitions instead.

    Two confirmed root causes are worked around here, both purely by
    resetting shared state between modules (nothing in the transpiler
    itself is modified):

    1. getWireNames() caches its result keyed by `obj ==
       wire_names_cache_obj` (equality, not identity) in two module-level
       globals -- clearWireNamesCache() resets them.
    2. ExtractInitializers (python2verilog_transpilation.py) declares
       `ports`, `variables` and `arguments` as CLASS-level dicts
       (`class ExtractInitializers: ports = {}; variables = {}
       ; arguments = {}`) and its __init__ never shadows them with
       instance attributes (`self.variables = {}`, etc.) -- so every
       instance across the whole process shares and *accumulates into*
       the same three dicts for the process's entire lifetime. This is
       the actual cause of the "module X declares module Y's local
       variables" corruption (confirmed by direct inspection of
       site-packages/py4hw/transpilation/python2verilog_transpilation.py):
       whichever modules were transpiled earlier in the hierarchy walk
       leak their every local variable into every module transpiled
       after them. Clearing the three class-level dicts before each
       module fixes it.
    """
    probe = VerilogGenerator(hw)
    clearWireNamesCache()
    ExtractInitializers.ports.clear()
    ExtractInitializers.variables.clear()
    ExtractInitializers.arguments.clear()
    vg = VerilogGenerator(hw)
    vg.created_structures = shared_created_structures
    text = vg._getVerilog(obj, noInstanceNumber=noInstanceNumberInTopEntity)

    for child in obj.children.values():
        if probe.isInlinable(child):
            continue
        part = gen_hierarchy(hw, child, noInstanceNumberInTopEntity=False)
        if len(part) > 0:
            text += "\n" + part

    return text


verilog = gen_hierarchy(hw, cpu._cpu)

with open('multicycleProcessor.v', 'w') as f:
    f.write(verilog)

print("Verilog generated:", len(verilog), "chars,", verilog.count('\n'), "lines")
print("modules found:", verilog.count('module '))
