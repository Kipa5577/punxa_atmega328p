`timescale 1ns/1ps

module tb_iverilog;
    reg clk = 0;
    reg reset = 1;
    wire [111:0] test_pass;
    wire all_tests_done;
    wire all_tests_pass;
    wire [7:0] test_index_out;
    wire [7:0] first_fail_index;
    wire heartbeat;

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

    always #5 clk = ~clk;

    integer last_index;

    initial begin
        last_index = -1;
        #20;
        reset = 0;
        $display("T=%0t reset released", $time);
    end

    always @(posedge clk) begin
        if (test_index_out !== last_index) begin
            $display("T=%0t test_index=%0d", $time, test_index_out);
            last_index = test_index_out;
        end
    end

    // Periodic heartbeat every 5,000,000,000 time units (500ms sim time)
    // so we can tell whether the simulation is progressing at all vs
    // genuinely stuck, without spamming the log given how long a full
    // 112-test run actually takes (each test observed taking ~65M
    // cycles, not the harness comment's estimated ~32k).
    initial begin
        forever begin
            #5_000_000_000;
            $display("T=%0t HEARTBEAT test_index=%0d state=%0d", $time, dut.test_index_out, dut.state);
        end
    end

    initial begin
        wait (all_tests_done);
        #20;
        $display("ALL_TESTS_DONE all_tests_pass=%b first_fail_index=%0d", all_tests_pass, first_fail_index);
        $display("TEST_PASS_BITS=%b", test_pass);
        $finish;
    end

    // safety timeout -- generous margin over the ~72.8B ns (112 tests x
    // ~65M cycles/test x 10ns, observed empirically) a full run actually
    // takes, well beyond the harness comment's ~32k-cycles-per-test estimate
    initial begin
        #150_000_000_000;
        $display("TIMEOUT waiting for all_tests_done. test_index=%0d test_pass=%b", test_index_out, test_pass);
        $finish;
    end
endmodule
