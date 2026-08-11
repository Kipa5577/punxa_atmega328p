`timescale 1ns/1ps

module tb_top (
    input clk,
    input reset,
    output [111:0] test_pass,
    output all_tests_done,
    output all_tests_pass,
    output [7:0] test_index_out,
    output [7:0] first_fail_index,
    output heartbeat
);

    cpu_isa_test_harness dut (
        .clk(clk),
        .reset(reset),
        .test_pass(test_pass),
        .all_tests_done(all_tests_done),
        .all_tests_pass(all_tests_pass),
        .test_index_out(test_index_out),
        .first_fail_index(first_fail_index),
        .heartbeat(heartbeat)
    );

endmodule
