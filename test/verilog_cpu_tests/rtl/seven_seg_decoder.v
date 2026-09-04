`timescale 1ns/1ps

// Standard Terasic DE0 seven-segment convention: each HEXn is 7 bits
// [6:0] = {g,f,e,d,c,b,a}, ACTIVE LOW (0 = segment lit). `blank` forces
// all segments off, useful for suppressing leading zeros if you want
// that later.
module seven_seg_decoder (
    input  wire [3:0] digit,   // 0-9 only; other values shown as blank
    input  wire       blank,
    output reg  [6:0] seg      // {g,f,e,d,c,b,a}, active low
);
    always @(*) begin
        if (blank) begin
            seg = 7'b1111111; // all off
        end else begin
            case (digit)
                4'd0: seg = 7'b1000000;
                4'd1: seg = 7'b1111001;
                4'd2: seg = 7'b0100100;
                4'd3: seg = 7'b0110000;
                4'd4: seg = 7'b0011001;
                4'd5: seg = 7'b0010010;
                4'd6: seg = 7'b0000010;
                4'd7: seg = 7'b1111000;
                4'd8: seg = 7'b0000000;
                4'd9: seg = 7'b0010000;
                default: seg = 7'b1111111; // off for anything unexpected
            endcase
        end
    end
endmodule
