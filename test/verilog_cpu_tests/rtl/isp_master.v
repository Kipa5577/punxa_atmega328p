`timescale 1ns/1ps
//
// isp_master.v -- synthesizable AVR ISP ("in-system programming") bit-serial
// protocol master.
//
// Sends one 4-byte ISP instruction per `start` pulse, MSB-first per byte,
// mirroring TB_of_Top/isp_driver.py's isp_send_bit()/isp_send_byte(): each
// bit takes *two* clk cycles -- MOSI+SCK driven high (chip samples MOSI on
// this rising edge), then SCK dropped low (chip drives MISO on this falling
// edge, sampled here).
//
// IMPORTANT TIMING NOTE (found by tracing this exact RTL under Verilator,
// not assumed): RomHandler's reply byte is only fully shifted onto MISO one
// bit-time *after* the byte that triggered it nominally ends -- e.g. the
// Programming Enable echo (0x53), armed while byte index 2 (the 3rd byte)
// is being received, only finishes shifting out one bit into byte index 3.
// For the 4th byte's own reply (Poll RDY/BSY's busy bit, Read Program
// Memory's data byte), that means the true value only lands one bit *past*
// the nominal 32-bit instruction -- so this module clocks one extra
// "phantom" bit (MOSI don't-care) after the 4 real bytes specifically to
// let that last reply byte fully land before `done` fires. Confirmed by
// direct bit-level trace against RomHandler's internal `_prog_bit_count`/
// `_prog_shift_reg`/`_prog_reply_armed` state: the echo is bit-correct only
// when captured with this one-bit-late alignment.
//
// reply2 = the 8-bit value that was being shifted out while byte index 2
//          (the 3rd byte) was nominally being sent -- Programming Enable's
//          0x53 echo shows up here.
// reply3 = the 8-bit value for byte index 3 (the 4th byte) -- Poll RDY/BSY's
//          busy bit and Read Program Memory's data byte show up here.
//
module isp_master (
    input        clk,
    input        start,          // pulse 1 cycle to send {b0,b1,b2,b3}
    input  [7:0] b0,
    input  [7:0] b1,
    input  [7:0] b2,
    input  [7:0] b3,
    output reg   busy,
    output reg   done,           // pulses 1 for exactly one cycle when finished
    output reg [7:0] reply2,
    output reg [7:0] reply3,
    output reg   PROG_MOSI,
    output reg   PROG_SCK,
    input        PROG_MISO
);

    localparam S_IDLE = 1'b0;
    localparam S_SEND = 1'b1;

    reg        state;
    reg [7:0]  bytes [0:3];
    reg [5:0]  bit_counter;  // 0..32: bits 0..31 = the 4 real bytes, 32 = phantom bit
    reg        phase;        // 0 = about to raise SCK (drive MOSI); 1 = about to drop SCK (capture MISO)
    reg [7:0]  cur_reply;

    wire [1:0] cur_byte_idx = bit_counter[4:3];
    wire [2:0] cur_bit_idx  = 3'd7 - bit_counter[2:0];
    wire       cur_mosi_bit = bytes[cur_byte_idx][cur_bit_idx];

    always @(posedge clk) begin
        done <= 1'b0;

        case (state)
            S_IDLE: begin
                PROG_SCK <= 1'b0;
                if (start) begin
                    bytes[0] <= b0;
                    bytes[1] <= b1;
                    bytes[2] <= b2;
                    bytes[3] <= b3;
                    bit_counter <= 6'd0;
                    phase       <= 1'b0;
                    busy        <= 1'b1;
                    state       <= S_SEND;
                end else begin
                    busy <= 1'b0;
                end
            end

            S_SEND: begin
                if (phase == 1'b0) begin
                    // rising edge phase: present MOSI (don't-care on the
                    // phantom 33rd bit), raise SCK
                    PROG_MOSI <= (bit_counter < 6'd32) ? cur_mosi_bit : 1'b0;
                    PROG_SCK  <= 1'b1;
                    phase     <= 1'b1;
                end else begin
                    // falling edge phase: drop SCK, capture MISO
                    PROG_SCK  <= 1'b0;
                    cur_reply <= {cur_reply[6:0], PROG_MISO};

                    // one-bit-late reply capture (see module header):
                    // bit_counter==24 is the first bit of byte index 3 --
                    // that's when byte index 2's true reply value has just
                    // finished landing. bit_counter==32 is the phantom bit
                    // past the end of byte index 3 -- likewise for its reply.
                    if (bit_counter == 6'd24)
                        reply2 <= {cur_reply[6:0], PROG_MISO};
                    if (bit_counter == 6'd32)
                        reply3 <= {cur_reply[6:0], PROG_MISO};

                    if (bit_counter == 6'd32) begin
                        busy  <= 1'b0;
                        done  <= 1'b1;
                        state <= S_IDLE;
                    end else begin
                        bit_counter <= bit_counter + 6'd1;
                        phase       <= 1'b0;
                    end
                end
            end
        endcase
    end

    initial begin
        state       = S_IDLE;
        busy        = 1'b0;
        done        = 1'b0;
        PROG_MOSI   = 1'b0;
        PROG_SCK    = 1'b0;
        bit_counter = 6'd0;
        phase       = 1'b0;
        cur_reply   = 8'd0;
        reply2      = 8'd0;
        reply3      = 8'd0;
    end

endmodule
