`timescale 1ns/1ps
//
// cpu_isa_test_harness.v
//
// Self-contained, synthesizable test harness for the punxa_atmega328p
// multicycle CPU core (Datapath+ControlBox, exported to Verilog as
// `multicycleProcessor` -- see multicycleProcessor.v). Meant to be dropped
// straight into a Quartus project and flashed to an FPGA: it needs only
// `clk`/`reset` from the board, and reports one pass/fail bit per test as
// an output bus (plus a few convenience status signals -- see the bottom
// of this file for why that's a better fit for Quartus/SignalTap than 110
// individual top-level pins).
//
// What it tests, and how "pass" is decided
// -----------------------------------------
// The project's own isa_tests/isa/*.asm files are each a small self-checking
// AVR program: they loop forever once done, having written a pass/fail byte
// (1 = pass, 0xFF = fail) to a fixed SRAM location (`final_result`, address
// 0x0101). There's no OS/console on the FPGA to poll that byte, so this
// harness does it itself in hardware: load a program into instruction
// memory, hold a fixed cycle budget for it to run, then sample
// `final_result` and latch the corresponding output bit.
//
//   - Tests 0..110 (NUM_ISA_TESTS-1): the 111 isa_tests/isa/*.asm files,
//     assembled offline (punxa_atmega328p/assembly.py) and embedded as a
//     flat ROM (see prog_rom below / test_table.vh) -- loaded by directly
//     writing instruction memory, the same "preload" approach the
//     project's own Python ISA harness uses.
//   - Test 111 (ISP_TEST_INDEX): the *same* small program (test_arith_ADD),
//     but flashed the way real hardware is actually programmed -- bit-
//     banging the real Programming-Enable / Load-Program-Memory-Page /
//     Write-Program-Memory-Page / Poll-RDY-BSY sequence through the CPU's
//     own PROG_MOSI/PROG_SCK/PROG_MISO pins (see isp_master.v and
//     ROM_FLASHING_DESIGN.md) -- proving the whole flash-then-run path,
//     not just direct execution.
//
// `reset` (the harness's own input, distinct from the DUT's internal
// `cpu_reset`) restarts the entire sequence from test 0 with every result
// bit cleared. Tests run strictly sequentially (one CPU, one shared
// memory) -- a full pass takes on the order of NUM_TESTS * ~32k cycles.
//
module cpu_isa_test_harness (
    input  wire clk,
    input  wire reset,

    // one bit per test, latched 1 the moment that test is confirmed
    // passing, held until the next `reset`
    output wire [111:0] test_pass,

    // convenience status (see bottom of file)
    output wire        all_tests_done,
    output wire        all_tests_pass,
    output wire [7:0]  test_index_out,
    output wire [7:0]  first_fail_index,
    output wire        heartbeat
);

    `include "test_table.vh"

    // =========================================================================
    // Flat instruction ROM: every test program's machine code, back to back.
    // Assembled offline from the project's own isa_tests/isa/*.asm files via
    // punxa_atmega328p/assembly.py -- see gen_test_table.py. Combinational
    // read (simple lookup table); if a synthesis run prefers a registered
    // ROM read, add one pipeline stage here and to the FSM below together.
    // =========================================================================
    reg [15:0] prog_rom [0:12032];
    initial $readmemh("prog_rom.hex", prog_rom);

    wire [13:0] isa_rom_addr = test_base[test_index] + load_i[13:0];
    wire [13:0] isp_rom_addr = test_base[ISP_TEST_INDEX] + {8'd0, word_i};
    wire [13:0] cur_rom_addr = (state == S_LOAD) ? isa_rom_addr : isp_rom_addr;
    wire [15:0] rom_data = prog_rom[cur_rom_addr];

    // =========================================================================
    // DUT: the multicycle CPU core
    // =========================================================================
    wire        Interrupt_Enable;
    wire        ins_mem_read, ins_mem_write;
    wire [15:0] ins_mem_writedata;
    wire [13:0] ins_mem_address;
    wire        ins_mem_instype;
    reg  [15:0] ins_mem_readdata;
    reg         ins_mem_resp;

    wire        memory_read, memory_write;
    wire [7:0]  memory_writedata;
    wire [15:0] memory_address;
    wire        memory_instype;
    reg  [7:0]  memory_readdata;
    reg         memory_resp;

    wire        isp_mosi, isp_sck;
    wire        PROG_MISO;

    reg         cpu_reset;

    multicycleProcessor dut (
        .clk(clk),
        .reset(cpu_reset),
        .Interrupt(cpu_interrupt),
        .ins_mem_readdata(ins_mem_readdata),
        .ins_mem_resp(ins_mem_resp),
        .memory_readdata(memory_readdata),
        .memory_resp(memory_resp),
        .PROG_MOSI(isp_mosi),
        .PROG_SCK(isp_sck),
        .Interrupt_Enable(Interrupt_Enable),
        .ins_mem_read(ins_mem_read),
        .ins_mem_write(ins_mem_write),
        .ins_mem_writedata(ins_mem_writedata),
        .ins_mem_address(ins_mem_address),
        .ins_mem_instype(ins_mem_instype),
        .memory_read(memory_read),
        .memory_write(memory_write),
        .memory_writedata(memory_writedata),
        .memory_address(memory_address),
        .memory_instype(memory_instype),
        .PROG_MISO(PROG_MISO)
    );

    // =========================================================================
    // Instruction memory: 16K x 16, read/write. Two write sources, muxed:
    //  - the loader (direct-preload path, tests 0..NUM_ISA_TESTS-1)
    //  - the CPU itself (normal fetch reads; also RomHandler's own writes
    //    during the ISP test, and SPM self-programming -- both already
    //    arrive on ins_mem_write/writedata/address, no extra plumbing
    //    needed for those)
    // =========================================================================
    reg         loading;
    reg  [13:0] loader_addr;
    reg  [15:0] loader_wdata;

    reg [15:0] ins_mem [0:16383];

    always @(posedge clk) begin
        if (loading) begin
            ins_mem[loader_addr] <= loader_wdata;
            ins_mem_resp <= 1'b0;
        end else if (ins_mem_write) begin
            ins_mem[ins_mem_address] <= ins_mem_writedata;
            ins_mem_resp <= 1'b1;
        end else if (ins_mem_read) begin
            ins_mem_readdata <= ins_mem[ins_mem_address];
            ins_mem_resp <= 1'b1;
        end else begin
            ins_mem_resp <= 1'b0;
        end
    end

    // =========================================================================
    // Data memory: 64K x 8, plain passthrough for everything except a
    // handful of I/O addresses that need real (not RAM) behavior -- see
    // below. (No external loader needed here: every test program
    // initializes its own `final_result`/`test_case` variables at the
    // start of its own run.)
    // =========================================================================
    reg [7:0] data_mem [0:65535];

    // ---- Minimal Timer0 + interrupt-vector peripheral ----
    // Needed for exactly one test (test_mcu_SLEEP.asm): `sleep` halts the
    // CPU until a real interrupt arrives, so a CPU-core-only harness with
    // no interrupt source at all can never wake it back up. This mirrors
    // the project's own reference Python peripherals (Timers.py's
    // SimpleTimer, Interrupt_Unit.py's SimpleInterruptUnit) just enough to
    // drive one Timer0-overflow interrupt: real TCCR0B/TCNT0/TIMSK0/TIFR0
    // registers with free-running counting, an `Interrupt` line gated by
    // the CPU's own Interrupt_Enable (SREG I) output, and the interrupt
    // vector low/high bytes the CPU's own interrupt-entrance logic reads
    // back from addresses 0xFE/0xFF (same convention SimpleInterruptUnit
    // uses -- confirmed empirically, this harness's DUT was generated
    // against that same external-vector-fetch memory map). Every other
    // ISA test leaves TCCR0B at its power-up 0, so the prescaler never
    // runs and none of this affects them.
    reg [7:0]  tccr0b, tcnt0, timsk0, tifr0;
    reg [15:0] t0_prescaler;

    wire [15:0] t0_prescaler_limit =
        (tccr0b[2:0] == 3'd1) ? 16'd1    :
        (tccr0b[2:0] == 3'd2) ? 16'd8    :
        (tccr0b[2:0] == 3'd3) ? 16'd64   :
        (tccr0b[2:0] == 3'd4) ? 16'd256  :
        (tccr0b[2:0] == 3'd5) ? 16'd1024 : 16'd0;

    localparam [15:0] TIMER0_OVF_VECTOR = 16'h0020;

    wire cpu_interrupt = Interrupt_Enable && timsk0[0] && tifr0[0];

    always @(posedge clk) begin
        reg [7:0]  n_tccr0b, n_tcnt0, n_timsk0, n_tifr0;
        reg [15:0] n_presc;

        n_tccr0b = tccr0b;
        n_tcnt0  = tcnt0;
        n_timsk0 = timsk0;
        n_tifr0  = tifr0;
        n_presc  = t0_prescaler;

        if (memory_write) begin
            case (memory_address)
                16'h0045: n_tccr0b = memory_writedata;
                16'h0046: n_tcnt0  = memory_writedata;
                16'h0047: if (memory_writedata[0]) n_tifr0[0] = 1'b0; // write-1-to-clear
                16'h006E: n_timsk0 = memory_writedata;
                default:  ; // handled by the plain-RAM block below
            endcase
        end

        // free-running counter/prescaler, independent of bus activity
        if (t0_prescaler_limit != 16'd0) begin
            if (n_presc + 16'd1 >= t0_prescaler_limit) begin
                n_presc = 16'd0;
                if (n_tcnt0 == 8'hFF) begin
                    n_tcnt0    = 8'h00;
                    n_tifr0[0] = 1'b1; // overflow flag latched
                end else begin
                    n_tcnt0 = n_tcnt0 + 8'd1;
                end
            end else begin
                n_presc = n_presc + 16'd1;
            end
        end

        tccr0b       <= n_tccr0b;
        tcnt0        <= n_tcnt0;
        timsk0       <= n_timsk0;
        tifr0        <= n_tifr0;
        t0_prescaler <= n_presc;
    end

    always @(posedge clk) begin
        if (memory_write) begin
            case (memory_address)
                16'h0045, 16'h0046, 16'h0047, 16'h006E: ; // handled above
                16'h00FE, 16'h00FF:                      ; // read-only vector bytes
                default: data_mem[memory_address] <= memory_writedata;
            endcase
            memory_resp <= 1'b1;
        end else if (memory_read) begin
            case (memory_address)
                16'h0045: memory_readdata <= tccr0b;
                16'h0046: memory_readdata <= tcnt0;
                16'h0047: memory_readdata <= tifr0;
                16'h006E: memory_readdata <= timsk0;
                16'h00FE: memory_readdata <= TIMER0_OVF_VECTOR[7:0];
                16'h00FF: memory_readdata <= TIMER0_OVF_VECTOR[15:8];
                default:  memory_readdata <= data_mem[memory_address];
            endcase
            memory_resp <= 1'b1;
        end else begin
            memory_resp <= 1'b0;
        end
    end

    // Shadow copy of `final_result` (SRAM 0x0101), refreshed whenever the
    // CPU writes it -- avoids needing a second read port into data_mem for
    // the checker below. Cleared at the start of every test so a test that
    // (due to a real bug) never gets around to writing final_result can't
    // inherit a stale "pass" from whatever ran before it.
    reg [7:0] test_case_shadow;
    always @(posedge clk) begin
        if (clear_final_result)
            test_case_shadow <= 8'h00;
        else if (memory_write && (memory_address == 16'h0100))
            test_case_shadow <= memory_writedata;
    end

    reg [7:0] final_result_shadow;
    reg       clear_final_result;

    always @(posedge clk) begin
        if (clear_final_result)
            final_result_shadow <= 8'h00;
        else if (memory_write && (memory_address == 16'h0101))
            final_result_shadow <= memory_writedata;
    end

    // =========================================================================
    // ISP master (bit-serial AVR ISP protocol -- see isp_master.v)
    // =========================================================================
    reg        isp_start;
    reg  [7:0] isp_b0, isp_b1, isp_b2, isp_b3;
    wire       isp_busy, isp_done;
    wire [7:0] isp_reply2, isp_reply3;

    isp_master u_isp_master (
        .clk(clk),
        .start(isp_start),
        .b0(isp_b0), .b1(isp_b1), .b2(isp_b2), .b3(isp_b3),
        .busy(isp_busy),
        .done(isp_done),
        .reply2(isp_reply2),
        .reply3(isp_reply3),
        .PROG_MOSI(isp_mosi),
        .PROG_SCK(isp_sck),
        .PROG_MISO(PROG_MISO)
    );

    // =========================================================================
    // Test sequencer FSM
    // =========================================================================
    reg [31:0] dbg_fetch_count;
    always @(posedge clk) begin
        if (state == S_RUN_START)
            dbg_fetch_count <= 32'd0;
        else if (state == S_RUNNING && ins_mem_read)
            dbg_fetch_count <= dbg_fetch_count + 32'd1;
    end
    localparam S_GLOBAL_RESET      = 5'd0;
    localparam S_LOAD              = 5'd1;
    localparam S_RUN_START         = 5'd2;
    localparam S_RUNNING           = 5'd3;
    localparam S_CHECK             = 5'd4;
    localparam S_NEXT              = 5'd5;
    // ISP-only path (kept as a contiguous range -- cpu_reset decode below
    // relies on it): reset must stay asserted for all of these.
    localparam S_ISP_RESET_HOLD    = 5'd6;
    localparam S_ISP_PROGEN_SEND   = 5'd7;
    localparam S_ISP_PROGEN_WAIT   = 5'd8;
    localparam S_ISP_LOAD_LOW_SEND = 5'd9;
    localparam S_ISP_LOAD_LOW_WAIT = 5'd10;
    localparam S_ISP_LOAD_HIGH_SEND= 5'd11;
    localparam S_ISP_LOAD_HIGH_WAIT= 5'd12;
    localparam S_ISP_WRITEPAGE_SEND= 5'd13;
    localparam S_ISP_WRITEPAGE_WAIT= 5'd14;
    localparam S_ISP_POLL_SEND     = 5'd15;
    localparam S_ISP_POLL_WAIT     = 5'd16;
    localparam S_ISP_RELEASE       = 5'd17;
    localparam S_DONE              = 5'd18;

    localparam [15:0] TIMEOUT_CYCLES   = 16'd65000; // >> worst-case ISA test (~25000 cyc, HANDOFF.md)
    localparam [7:0]  GLOBAL_HOLD      = 8'd8;       // cpu_reset hold before test 0
    localparam [7:0]  ISP_RESET_HOLD_N = 8'd16;      // cpu_reset hold before Programming Enable
    localparam [7:0]  ISP_POLL_MAX     = 8'd200;     // Poll RDY/BSY give-up guard

    reg [4:0]  state;
    reg [7:0]  test_index;
    reg [15:0] load_i;
    reg [15:0] timeout_cnt;
    reg [7:0]  hold_cnt;
    reg [5:0]  word_i;          // word-in-page index for the ISP load loop
    reg        isp_failed;
    reg [7:0]  isp_poll_cnt;

    reg [111:0] test_pass_r;
    reg         all_tests_done_r;
    reg [7:0]   first_fail_index_r;
    reg         first_fail_latched;

    always @(posedge clk) begin
        if (reset) begin
            state               <= S_GLOBAL_RESET;
            test_index          <= 8'd0;
            hold_cnt            <= 8'd0;
            test_pass_r         <= {112{1'b0}};
            all_tests_done_r    <= 1'b0;
            first_fail_index_r  <= 8'd0;
            first_fail_latched  <= 1'b0;
            isp_failed          <= 1'b0;
            cpu_reset           <= 1'b1;
            loading             <= 1'b0;
            clear_final_result  <= 1'b0;
            isp_start           <= 1'b0;
        end else begin
            // defaults each cycle; explicit states override below
            loading            <= 1'b0;
            clear_final_result <= 1'b0;
            isp_start          <= 1'b0;

            case (state)

                S_GLOBAL_RESET: begin
                    cpu_reset <= 1'b1;
                    if (hold_cnt == GLOBAL_HOLD) begin
                        hold_cnt           <= 8'd0;
                        load_i             <= 16'd0;
                        clear_final_result <= 1'b1;
                        state              <= S_LOAD;
                    end else begin
                        hold_cnt <= hold_cnt + 8'd1;
                    end
                end

                // ---- direct-preload path (tests 0..NUM_ISA_TESTS-1) ----
                S_LOAD: begin
                    cpu_reset <= 1'b1;
                    if (load_i < test_len[test_index]) begin
                        loading      <= 1'b1;
                        loader_addr  <= load_i[13:0];
                        loader_wdata <= rom_data;
                        load_i       <= load_i + 16'd1;
                    end else begin
                        state <= S_RUN_START;
                    end
                end

                S_RUN_START: begin
                    cpu_reset   <= 1'b0;
                    timeout_cnt <= TIMEOUT_CYCLES;
                    state       <= S_RUNNING;
                end

                S_RUNNING: begin
                    if (timeout_cnt == 16'd0)
                        state <= S_CHECK;
                    else
                        timeout_cnt <= timeout_cnt - 16'd1;
                end

                S_CHECK: begin
                    if (!isp_failed && (final_result_shadow == 8'h01)) begin
                        test_pass_r[test_index] <= 1'b1;
                    end else begin
                        if (!first_fail_latched) begin
                            first_fail_index_r <= test_index;
                            first_fail_latched <= 1'b1;
                        end
                    end
                    state <= S_NEXT;
                end

                S_NEXT: begin
                    if (test_index == NUM_TESTS - 1) begin
                        state            <= S_DONE;
                        all_tests_done_r <= 1'b1;
                    end else begin
                        test_index         <= test_index + 8'd1;
                        isp_failed         <= 1'b0;
                        clear_final_result <= 1'b1;
                        if ((test_index + 8'd1) == ISP_TEST_INDEX) begin
                            hold_cnt <= 8'd0;
                            state    <= S_ISP_RESET_HOLD;
                        end else begin
                            load_i <= 16'd0;
                            state  <= S_LOAD;
                        end
                    end
                end

                // ---- ISP flash-and-run path (test ISP_TEST_INDEX) ----
                S_ISP_RESET_HOLD: begin
                    cpu_reset <= 1'b1;
                    if (hold_cnt == ISP_RESET_HOLD_N) begin
                        hold_cnt <= 8'd0;
                        state    <= S_ISP_PROGEN_SEND;
                    end else begin
                        hold_cnt <= hold_cnt + 8'd1;
                    end
                end

                S_ISP_PROGEN_SEND: begin
                    cpu_reset <= 1'b1;
                    isp_b0 <= 8'hAC; isp_b1 <= 8'h53; isp_b2 <= 8'h00; isp_b3 <= 8'h00;
                    isp_start <= 1'b1;
                    state <= S_ISP_PROGEN_WAIT;
                end
                S_ISP_PROGEN_WAIT: begin
                    cpu_reset <= 1'b1;
                    if (isp_done) begin
                        if (isp_reply2 != 8'h53)
                            isp_failed <= 1'b1;
                        word_i <= 6'd0;
                        state  <= S_ISP_LOAD_LOW_SEND;
                    end
                end

                S_ISP_LOAD_LOW_SEND: begin
                    cpu_reset <= 1'b1;
                    if (word_i == test_len[ISP_TEST_INDEX][5:0]) begin
                        state <= S_ISP_WRITEPAGE_SEND;
                    end else begin
                        state    <= S_ISP_LOAD_LOW_WAIT;
                    end
                end
                S_ISP_LOAD_LOW_WAIT: begin
                    // rom_data already reflects word_i combinationally
                    cpu_reset <= 1'b1;
                    isp_b0 <= 8'h40; isp_b1 <= 8'h00;
                    isp_b2 <= {2'b00, word_i};
                    isp_b3 <= rom_data[7:0];
                    isp_start <= 1'b1;
                    state <= S_ISP_LOAD_HIGH_SEND;
                end
                S_ISP_LOAD_HIGH_SEND: begin
                    // wait for the low-byte send (issued above) to finish
                    cpu_reset <= 1'b1;
                    if (isp_done) begin
                        isp_b0 <= 8'h48; isp_b1 <= 8'h00;
                        isp_b2 <= {2'b00, word_i};
                        isp_b3 <= rom_data[15:8];
                        isp_start <= 1'b1;
                        state <= S_ISP_LOAD_HIGH_WAIT;
                    end
                end
                S_ISP_LOAD_HIGH_WAIT: begin
                    cpu_reset <= 1'b1;
                    if (isp_done) begin
                        word_i <= word_i + 6'd1;
                        state  <= S_ISP_LOAD_LOW_SEND;
                    end
                end

                S_ISP_WRITEPAGE_SEND: begin
                    cpu_reset <= 1'b1;
                    isp_b0 <= 8'h4C; isp_b1 <= 8'h00; isp_b2 <= 8'h00; isp_b3 <= 8'h00; // page 0
                    isp_start <= 1'b1;
                    state <= S_ISP_WRITEPAGE_WAIT;
                end
                S_ISP_WRITEPAGE_WAIT: begin
                    cpu_reset <= 1'b1;
                    if (isp_done) begin
                        isp_poll_cnt <= 8'd0;
                        state <= S_ISP_POLL_SEND;
                    end
                end

                S_ISP_POLL_SEND: begin
                    cpu_reset <= 1'b1;
                    isp_b0 <= 8'hF0; isp_b1 <= 8'h00; isp_b2 <= 8'h00; isp_b3 <= 8'h00;
                    isp_start <= 1'b1;
                    state <= S_ISP_POLL_WAIT;
                end
                S_ISP_POLL_WAIT: begin
                    cpu_reset <= 1'b1;
                    if (isp_done) begin
                        if (isp_reply3[0] == 1'b0) begin
                            state <= S_ISP_RELEASE;
                        end else if (isp_poll_cnt == ISP_POLL_MAX) begin
                            isp_failed <= 1'b1;
                            state <= S_ISP_RELEASE;
                        end else begin
                            isp_poll_cnt <= isp_poll_cnt + 8'd1;
                            state <= S_ISP_POLL_SEND;
                        end
                    end
                end

                S_ISP_RELEASE: begin
                    cpu_reset <= 1'b0;
                    state     <= S_RUN_START;
                end

                S_DONE: begin
                    cpu_reset <= 1'b1; // park the (finished) CPU in reset
                end

                default: state <= S_GLOBAL_RESET;
            endcase
        end
    end

    assign test_pass         = test_pass_r;
    assign all_tests_done    = all_tests_done_r;
    assign all_tests_pass    = &test_pass_r;
    assign test_index_out    = test_index;
    assign first_fail_index  = first_fail_index_r;

    // Free-running heartbeat, independent of the sequencer -- proves the
    // design is alive on real hardware even before the first test finishes.
    reg [23:0] hb_cnt;
    always @(posedge clk) hb_cnt <= hb_cnt + 24'd1;
    assign heartbeat = hb_cnt[23];

endmodule
