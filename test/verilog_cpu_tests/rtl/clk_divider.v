`timescale 1ns/1ps

// Divides an input clock down to a much slower output clock, ~50% duty
// cycle.
//
// IMPORTANT: this is deliberately free-running and NOT gated by reset.
// An earlier version gated clk_out to a fixed 0 while reset was
// asserted -- which meant clk_out could never produce a single edge
// while reset was high. Since cpu_isa_test_harness's own reset
// initialization only runs on a posedge of its clk input (this
// divider's output), that meant its `if (reset) ...` branch could
// NEVER execute at all: reset would always have already gone low
// before clk_slow ever ticked for the first time, so test_index,
// test_pass, etc. stayed permanently undefined ('X' in simulation --
// on real hardware, effectively "stuck at whatever the FPGA happens to
// power up with", almost certainly non-functional). This would have
// made the CPU look completely dead on real hardware regardless of how
// long the reset button was held. Real clock dividers should always be
// free-running for exactly this reason -- only the downstream logic
// should be reset, never the clock that carries the reset signal to it.
module clk_divider #(
    parameter integer DIVIDE_BY = 5000   // 50_000_000 / 5000 = 10_000 Hz
)(
    input  wire clk_in,
    output reg  clk_out = 1'b0
);
    localparam integer HALF = DIVIDE_BY / 2; // toggle every HALF input clocks

    reg [31:0] count = 32'd0;

    always @(posedge clk_in) begin
        if (count == HALF - 1) begin
            count   <= 32'd0;
            clk_out <= ~clk_out;
        end else begin
            count <= count + 32'd1;
        end
    end
endmodule
