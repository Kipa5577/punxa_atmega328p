`timescale 1ns / 1ps

module tb_processor;

    // ----------------------------------------------------
    // 1. Declare signals to connect to the processor
    // ----------------------------------------------------
    // Inputs to UUT (Registers)
    reg clk;
    reg reset;
    reg Interrupt;
    reg [15:0] ins_mem_readdata;
    reg ins_mem_resp;
    reg [7:0] memory_readdata;
    reg memory_resp;
    reg PROG_MOSI;
    reg PROG_SCK;

    // Outputs from UUT (Wires)
    wire Interrupt_Enable;
    wire ins_mem_read;
    wire ins_mem_write;
    wire [15:0] ins_mem_writedata;
    wire [13:0] ins_mem_address;
    wire ins_mem_instype;
    wire memory_read;
    wire memory_write;
    wire [7:0] memory_writedata;
    wire [15:0] memory_address;
    wire memory_instype;
    wire PROG_MISO;

    // ----------------------------------------------------
    // 2. Instantiate the Unit Under Test (UUT)
    // ----------------------------------------------------
    multicycleProcessor uut (
        .clk(clk),
        .reset(reset),
        .Interrupt(Interrupt),
        .ins_mem_readdata(ins_mem_readdata),
        .ins_mem_resp(ins_mem_resp),
        .memory_readdata(memory_readdata),
        .memory_resp(memory_resp),
        .PROG_MOSI(PROG_MOSI),
        .PROG_SCK(PROG_SCK),
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

    // ----------------------------------------------------
    // 3. Clock Generation
    // ----------------------------------------------------
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 10ns period (100 MHz clock)
    end

    // ----------------------------------------------------
    // 4. Main Stimulus & Simulation Control
    // ----------------------------------------------------
    initial begin
        // Setup GTKWave dumping
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_processor);

        // Initialize all inputs to known states
        reset = 1;
        Interrupt = 0;
        PROG_MOSI = 0;
        PROG_SCK = 0;
        
        // Initial memory bus states
        ins_mem_readdata = 16'h0000;
        ins_mem_resp = 0;
        memory_readdata = 8'h00;
        memory_resp = 0;

        // Hold reset for a few clock cycles
        #20;
        reset = 0;

        // Let the simulation run for a set amount of time
        // Increase this number if you need a longer simulation
        #1000; 
        
        $display("Simulation Finished.");
        $finish;
    end

    // ----------------------------------------------------
    // 5. Dummy Memory Responders
    // ----------------------------------------------------
    // This block mimics simple asynchronous ROM/RAM so the 
    // processor doesn't hang waiting for responses.
    always @(posedge clk) begin
        // --- Instruction Memory Response ---
        if (ins_mem_read) begin
            ins_mem_resp <= 1;
            // Provide a dummy instruction here (e.g., NOP).
            // To run real code, you'd map a memory array here using `ins_mem_address`.
            ins_mem_readdata <= 16'h0000; 
        end else begin
            ins_mem_resp <= 0;
        end

        // --- Data Memory Response ---
        if (memory_read) begin
            memory_resp <= 1;
            // Dummy data payload
            memory_readdata <= 8'hAA; 
        end else if (memory_write) begin
            // Acknowledge the write
            memory_resp <= 1;
            $display("Time %0t: Processor wrote %h to address %h", $time, memory_writedata, memory_address);
        end else begin
            memory_resp <= 0;
        end
    end

endmodule