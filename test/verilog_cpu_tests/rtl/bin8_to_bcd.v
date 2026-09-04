`timescale 1ns/1ps

// Converts an 8-bit binary value (0-255, though test_index_out only ever
// reaches 111) into 3 BCD digits, combinationally, via the standard
// double-dabble (shift-and-add-3) algorithm. Avoids relying on `/` or `%`
// with non-power-of-2 constants, which not every synthesis tool/version
// handles the same way -- double-dabble is simple shift/compare/add logic
// that's guaranteed to synthesize the same everywhere, including on the
// older Quartus 13.1 toolchain this project uses.
module bin8_to_bcd (
    input  wire [7:0] bin,
    output reg  [3:0] hundreds,
    output reg  [3:0] tens,
    output reg  [3:0] units
);
    integer i;
    reg [19:0] shift; // [19:16]=hundreds [15:12]=tens [11:8]=units [7:0]=binary

    always @(*) begin
        shift = 20'd0;
        shift[7:0] = bin;

        for (i = 0; i < 8; i = i + 1) begin
            if (shift[11:8] >= 5)
                shift[11:8] = shift[11:8] + 4'd3;
            if (shift[15:12] >= 5)
                shift[15:12] = shift[15:12] + 4'd3;
            if (shift[19:16] >= 5)
                shift[19:16] = shift[19:16] + 4'd3;

            shift = shift << 1;
        end

        units    = shift[11:8];
        tens     = shift[15:12];
        hundreds = shift[19:16];
    end
endmodule
