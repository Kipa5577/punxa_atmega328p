# Testing the transpiled Verilog ATmega328P CPU

This folder is a self-contained test kit for the **Verilog** version of the
multicycle ATmega328P CPU (transpiled from the Python/`py4hw` source via
`transcompilation/generate_verilog_for_processor_v2.py` in the main repo).
It does not require Python, `py4hw`, or any of the rest of the repo — only
a Verilog simulator.

It answers one question: *does the generated RTL actually execute the same
111-test AVR instruction-set suite correctly, at the gate level, in a real
event-driven Verilog simulator?* This is a materially stronger check than
the Python-level `py4hw` simulation, which caught real bugs the Python
simulator itself couldn't see (see "Why this matters" below).

## Layout

```
rtl/                          The CPU + test harness, as pure Verilog
  multicycleProcessor.v         The CPU itself (transpiled from Datapath.py +
                                 ControlBox.py + every SmallFSMS/*.py file)
  cpu_isa_test_harness.v        Self-checking test sequencer: ISP-flashes
                                 each test program into the CPU's program
                                 memory, runs it, and checks a pass/fail flag
  isp_master.v                  Bit-serial SPI-ISP protocol driver used by
                                 the harness to flash each test program
  prog_rom.hex                  All 111 ISA test programs, pre-assembled to
                                 a flat Verilog $readmemh hex image
  test_table.vh                 Index -> (offset, length) map into
                                 prog_rom.hex, one entry per test file name
                                 (auto-generated -- do not hand-edit)
  clk_divider.v, bin8_to_bcd.v,
  seven_seg_decoder.v           DE0 board support (see "Hardware-realistic
                                 path" below) -- not needed for plain sim

testbench/
  tb_iverilog.v                 Fast-path testbench: drives the harness
                                 directly at full clock speed. THIS IS WHAT
                                 YOU WANT for a normal regression run.
  tb_top.v                      DE0-realistic top level: same harness, but
                                 clocked through clk_divider (50MHz -> 10kHz)
                                 plus seven-segment/LED debug outputs, i.e.
                                 the actual FPGA top-level entity
  tb_main.cpp                   Verilator C++ driver for tb_top.v

fpga/
  Test_project.sdc              Quartus timing constraints for the DE0
                                 target. Only relevant if you're taking this
                                 into Quartus/synthesis -- ignore for
                                 simulation-only testing.

results/
  archived_reference_run_112of112.log
                                 A previously captured run against a
                                 modified (verify-only early-exit) version
                                 of the harness, reporting 112/112.
  freshly_verified_run_109of112.log
                                 A run captured in this environment just now
                                 against the harness exactly as shipped in
                                 this folder (unmodified). See "Current
                                 status" below -- the two logs disagree, and
                                 that disagreement is worth understanding
                                 before you trust either one.
```

## Prerequisites

Icarus Verilog (`iverilog`/`vvp`). On Debian/Ubuntu:

```bash
apt-get install -y iverilog
```

Nothing else is required for the fast path. The hardware-realistic path
additionally needs [Verilator](https://www.veripool.org/verilator/).

## Quick start (recommended path)

From this folder:

```bash
cd rtl
iverilog -o /tmp/cpu_sim.vvp ../testbench/tb_iverilog.v \
    cpu_isa_test_harness.v multicycleProcessor.v isp_master.v
vvp /tmp/cpu_sim.vvp
```

`iverilog` picks up `prog_rom.hex` and `test_table.vh` automatically via
the harness's relative `$readmemh`/`` `include`` paths, which is why you
run it from inside `rtl/`.

**This takes a while.** The harness ISP-flashes every one of the 112 test
programs bit-serially before running each one (the same slow-but-realistic
protocol a real AVR programmer uses), so simulated time runs into the tens
of billions of nanoseconds. In this environment a full run took **just
under 10 minutes of wall-clock time**. `vvp`'s stdout is block-buffered
when not attached to a terminal, so if you redirect to a file (e.g. `vvp
/tmp/cpu_sim.vvp > run.log`) you may see **no output at all until the run
finishes or the buffer fills** -- that's normal, not a hang. If you want
to watch it live, run it directly in a terminal (unbuffered) instead of
piping/redirecting.

### Reading the output

The testbench prints one line per test as `test_index_out` advances:

```
T=<time> test_index=<N>
```

and finishes with:

```
ALL_TESTS_DONE all_tests_pass=<0 or 1> first_fail_index=<N>
TEST_PASS_BITS=<112-bit binary string>
```

`TEST_PASS_BITS` is `test_pass[111:0]` printed MSB-first, i.e. the
**leftmost** character is bit 111 and the **rightmost** is bit 0. A `0` at
bit position `N` means test index `N` failed. Cross-reference the index
against `rtl/test_table.vh`, which has the test file name in a trailing
comment on each `test_base[N] = ...` line, e.g.:

```verilog
test_base[ 83] = 14'd9399 ; test_len[ 83] = 9'd374 ; // test_data_ST.asm
```

Index 111 is special: unlike indices 0-110 (which are preloaded directly
into program memory for speed), index 111 re-flashes `test_arith_ADD`'s
program through the *real* bit-serial ISP protocol end-to-end, as a check
that the ISP path itself works, not just the CPU core.

## Current status (verified in this environment)

Running the harness exactly as shipped in this folder (unmodified),
Icarus Verilog 12.0 reports:

```
ALL_TESTS_DONE all_tests_pass=0 first_fail_index=83
```

with bits 83, 84, and 107 clear -- i.e. **109/112 pass**, and the three
failures are:

| Index | Test |
|---|---|
| 83 | `test_data_ST.asm` |
| 84 | `test_data_STD.asm` |
| 107 | `test_mcu_SEN.asm` |

This is worth flagging explicitly: the project's own prior notes
(`DE0_HARDWARE_SESSION_STATUS.md`) describe these exact same three tests
failing **only on real DE0 hardware** while claiming they **pass in Icarus
simulation**. The `archived_reference_run_112of112.log` in `results/`
backs that claim up -- but its own accompanying note says it was captured
against a **modified** copy of the harness with "a verify-only early-exit
in the test sequencer" patched in, described there as behavior-preserving.
The fresh run in this folder's `results/freshly_verified_run_109of112.log`
was captured against the plain, unmodified harness as it ships here, and
it does *not* reproduce the 112/112 result -- it fails the same three
tests that were previously reported as hardware-only failures.

Given there's no `$random` or other simulation-seed dependency anywhere in
this RTL (checked by grep), this isn't run-to-run noise -- the two logs
were produced by two different versions of the harness, and something
about that "verify-only" difference (or a difference in Icarus Verilog
version) is not actually behavior-preserving. **Treat tests 83/84/107 as a
live, unresolved discrepancy, not a settled "hardware-only" issue** --
the next step is a line-by-line diff between whatever harness produced the
archived log and the one in this folder, and/or re-running under the exact
Icarus version that produced the archived result, to pin down which
variable (harness patch vs. simulator version) actually explains the
difference.

## Hardware-realistic path (DE0 / Verilator)

`testbench/tb_top.v` is the actual FPGA top-level module: the same
`cpu_isa_test_harness` instance, but clocked through `clk_divider`
(50MHz board oscillator -> 10kHz internal clock, matching the real DE0
board bring-up configuration) and wired to seven-segment/LED debug
outputs. This is what you'd point Quartus at for real synthesis, and it's
also what `testbench/tb_main.cpp` (a Verilator C++ testbench) expects as
its top module.

Two things to know before using this path:

1. Because of the 50MHz->10kHz clock division, this path takes roughly
   **5000x more toggles of the top-level `clk` input** to advance the CPU
   by the same number of real cycles as the fast path above. It was not
   re-timed against this specific RTL snapshot in this session -- budget
   accordingly (likely well beyond what a quick regression check should
   cost you; use the fast `tb_iverilog.v` path for that instead).
2. `tb_main.cpp` caps itself at `MAX_CYCLES = 9,000,000` raw `clk` toggles
   before declaring a timeout -- given point 1, that's a low ceiling for
   this slow-clock configuration and may need raising if you use it.

To build with Verilator:

```bash
verilator --cc --exe --build -j 0 \
    --top-module tb_top \
    testbench/tb_main.cpp \
    rtl/multicycleProcessor.v rtl/cpu_isa_test_harness.v rtl/isp_master.v \
    rtl/clk_divider.v rtl/bin8_to_bcd.v rtl/seven_seg_decoder.v \
    testbench/tb_top.v
./obj_dir/Vtb_top
```

(Not run in this session -- treat the command above as a starting point,
not a verified recipe.)

## Why this matters (background)

The Python (`py4hw`) simulation of this CPU reports 111/111 on its own,
but that never caught three real bugs that only a true event-driven
Verilog simulation would: self-referencing nonblocking assignments that
silently pinned signals at reset values, a combinational decoder that
only worked because of a Python-simulator quirk (re-evaluating
`propagate()` regardless of whether inputs changed), and an uninitialized
synthetic Timer0 model in the test harness itself. All three are fixed in
the RTL in this folder -- see the main repo's `FIXES_THIS_SESSION.md` and
`HANDOFF.md` for the full history. This folder's whole point is to keep
that gate-level check independently runnable, without needing the rest of
the Python toolchain.
