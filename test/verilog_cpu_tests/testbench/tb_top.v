`timescale 1ns/1ps

module tb_top (
    input clk,          // still the raw 50MHz board oscillator pin -- no
                         // .qsf / pin-assignment changes needed
    input reset,
    output [111:0] test_pass,
    output all_tests_done,
    output all_tests_pass,
    output [7:0] test_index_out,
    output [7:0] first_fail_index,
    output heartbeat,

    // DIAGNOSTIC (10kHz run): liveness LEDs, see previous message.
    output clk_alive_led,
    output [3:0] test_progress_led,

    // Current test index on DE0's 4 seven-segment displays, decimal,
    // e.g. test 84 shows "0 0 8 4". test_index_out only ever reaches
    // 111, so 3 digits cover it -- HEX3 (thousands) is always blank.
    // Each HEXn is {g,f,e,d,c,b,a}, active low (Terasic DE0 convention).
    output [6:0] HEX0,   // units
    output [6:0] HEX1,   // tens
    output [6:0] HEX2,   // hundreds
    output [6:0] HEX3    // unused, blanked off
);

    wire clk_slow;

    clk_divider #(.DIVIDE_BY(5000)) i_clkdiv (
        .clk_in (clk),
        .clk_out(clk_slow)
    );

    cpu_isa_test_harness dut (
        .clk(clk_slow),
        .reset(reset),
        .test_pass(test_pass),
        .all_tests_done(all_tests_done),
        .all_tests_pass(all_tests_pass),
        .test_index_out(test_index_out),
        .first_fail_index(first_fail_index),
        .heartbeat(heartbeat)
    );

    // ~1.2Hz blink at clk_slow = 10kHz (toggle every 2^12 = 4096 cycles).
    reg [12:0] alive_cnt;
    always @(posedge clk_slow or posedge reset)
        if (reset) alive_cnt <= 13'd0;
        else       alive_cnt <= alive_cnt + 13'd1;
    assign clk_alive_led = alive_cnt[12];

    assign test_progress_led = test_index_out[3:0];

    // --- Seven-segment test index display ---
    wire [3:0] idx_hundreds, idx_tens, idx_units;

    bin8_to_bcd i_bcd (
        .bin      (test_index_out),
        .hundreds (idx_hundreds),
        .tens     (idx_tens),
        .units    (idx_units)
    );

    seven_seg_decoder i_hex0 (.digit(idx_units),    .blank(1'b0), .seg(HEX0));
    seven_seg_decoder i_hex1 (.digit(idx_tens),     .blank(1'b0), .seg(HEX1));
    seven_seg_decoder i_hex2 (.digit(idx_hundreds), .blank(1'b0), .seg(HEX2));
    seven_seg_decoder i_hex3 (.digit(4'd0),         .blank(1'b1), .seg(HEX3)); // always blank

endmodule
