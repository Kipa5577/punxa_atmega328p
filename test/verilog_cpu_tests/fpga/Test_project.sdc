## Test_project.sdc
##
## Minimal timing constraints for the DE0 board's onboard 50MHz oscillator
## (CLOCK_50, PIN_G21). Every synthesis run of this project so far has been
## missing an .sdc file entirely (Critical Warning (332012) in every log),
## meaning Quartus's Fitter has been running as unconstrained "Auto Fit"
## the whole time -- optimizing for nothing in particular, with no timing
## closure guarantee at the board's actual clock rate. That's the kind of
## gap that lets marginal-timing paths (bit-serial protocol logic, unsafe
## inferred latches, deep combinational chains) synthesize "successfully"
## and pass zero-delay RTL simulation, yet misbehave on real silicon.
##
## Adjust the period below if this project's board or clock source differs
## from the DE0's 50MHz oscillator.

create_clock -name clk -period 20.000 [get_ports {clk}]

# clk_slow is the CPU's actual operating clock, derived from clk via
# clk_divider (DIVIDE_BY parameter there). Without this declaration
# TimeQuest doesn't know clk_slow is a clock at all -- it gets heuristically
# promoted to the global clock network for fanout reasons, but setup/hold
# analysis on the domain the CPU actually runs in is silently skipped
# ("Design is not fully constrained for setup/hold requirements" in the
# TimeQuest log). Keep this period in sync with clk_divider's DIVIDE_BY:
# period = 20.000 * DIVIDE_BY. Default DIVIDE_BY=5000 -> 100000.000ns (10kHz).
create_generated_clock -name clk_slow -source [get_ports {clk}] \
    -divide_by 5000 [get_pins {i_clkdiv|clk_out}]

# Reasonable default uncertainty since this design has no PLL (single
# free-running board oscillator, no jitter/skew analysis has been done).
derive_clock_uncertainty

# reset is asynchronous and only ever sampled well after any bounce/glitch
# settles (many clock cycles into S_GLOBAL_RESET) -- exclude it from setup/
# hold analysis so TimeQuest doesn't waste effort trying to meet timing on
# a signal that was never meant to be synchronous in the first place.
set_false_path -from [get_ports {reset}]

# None of these outputs feed anything timing-critical (LEDs/HEX displays/
# SignalTap probes only) -- false-path them instead of leaving them
# unconstrained.
set_false_path -to [get_ports {test_pass[*]}]
set_false_path -to [get_ports {all_tests_done}]
set_false_path -to [get_ports {all_tests_pass}]
set_false_path -to [get_ports {test_index_out[*]}]
set_false_path -to [get_ports {first_fail_index[*]}]
set_false_path -to [get_ports {heartbeat}]
set_false_path -to [get_ports {clk_alive_led}]
set_false_path -to [get_ports {test_progress_led[*]}]
set_false_path -to [get_ports {HEX0[*]}]
set_false_path -to [get_ports {HEX1[*]}]
set_false_path -to [get_ports {HEX2[*]}]
set_false_path -to [get_ports {HEX3[*]}]

