import sys, io, contextlib, os 
current_dir = os.path.dirname(os.path.abspath(__file__))

asm_path = os.path.join(current_dir,'..','isa_tests','isa','test_arith_ADD.asm')
testbench_path = os.path.join(current_dir,'..','isa_tests','tb_ISA_tests_Multicycle_rewrite.py')
sys.path.insert(0, '.')
exec(open(testbench_path).read().split("if __name__")[0])

import py4hw
from py4hw.rtl_generation import VerilogGenerator

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    hw, cpu, ins_mem, mem, symbols = prepareTest(asm_path)
    silence_debug(cpu._cpu)

actual = cpu._cpu

def walk(node, path=""):
    yield (path, node)
    for name, child in node.children.items():
        yield from walk(child, path + "/" + name)

targets = []
for path, node in walk(actual):
    targets.append((path, node))

print(f"total nodes: {len(targets)}")

results = {}
for path, node in targets:
    cls = type(node).__name__
    key = f"{cls}"
    if key in results:
        continue  # only test each class once
    vg = VerilogGenerator(hw)
    try:
        v = vg.getVerilog(node)
        results[key] = ("OK", path)
    except Exception as e:
        results[key] = (f"FAIL: {type(e).__name__}: {e}", path)

for k, v in results.items():
    print(k, '->', v)
