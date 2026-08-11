import sys, io, contextlib , os
current_dir = os.path.dirname(os.path.abspath(__file__))

testbench_path = os.path.join(current_dir,'..','isa_tests','tb_ISA_tests_Multicycle_rewrite.py')
asm_path = os.path.join(current_dir,'..','isa_tests','isa','test_arith_ADD.asm')
sys.path.insert(0, os.path.join(current_dir, '..'))
exec(open(testbench_path).read().split("if __name__")[0])

import py4hw
from py4hw.rtl_generation import VerilogGenerator

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    hw, cpu, ins_mem, mem, symbols = prepareTest(asm_path)
    silence_debug(cpu._cpu)


from py4hw.rtl_generation import clearWireNamesCache
from py4hw.transpilation.python2verilog_transpilation import ExtractInitializers

shared_created_structures = []


def gen_hierarchy(hw, obj, noInstanceNumberInTopEntity=True):
    probe = VerilogGenerator(hw)
    clearWireNamesCache()
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

out_path = os.path.join(current_dir, 'multicycleProcessor.v')
with open(out_path, 'w') as f:
    f.write(verilog)

print("Verilog generated:", len(verilog), "chars,", verilog.count('\n'), "lines")
print("modules found:", verilog.count('module '))
