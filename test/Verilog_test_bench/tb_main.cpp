#include "Vtb_top.h"
#include "verilated.h"
#include <cstdio>
#include <bitset>

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    Vtb_top* top = new Vtb_top;

    top->clk = 0;
    top->reset = 1;

    auto tick = [&]() {
        top->clk = 0; top->eval();
        top->clk = 1; top->eval();
    };

    for (int i = 0; i < 10; i++) tick();
    top->reset = 0;

    unsigned last_index = 255;
    unsigned long long cycles = 0;
    const unsigned long long MAX_CYCLES = 9000000ULL;

    while (!top->all_tests_done && cycles < MAX_CYCLES) {
        tick();
        cycles++;

        unsigned idx = top->test_index_out;
        if (idx != last_index) {
            printf("[cyc %llu] now running test_index=%u\n", cycles, idx);
            last_index = idx;
        }
    }

    if (cycles >= MAX_CYCLES) {
        printf("TIMEOUT: never reached all_tests_done after %llu cycles (stuck at test_index=%u)\n",
               cycles, (unsigned)top->test_index_out);
    } else {
        printf("all_tests_done after %llu cycles\n", cycles);
    }

    // Print the 112-bit test_pass vector (4 x 32-bit words from Verilator's packed array)
    printf("all_tests_pass = %u\n", (unsigned)top->all_tests_pass);
    printf("first_fail_index = %u\n", (unsigned)top->first_fail_index);

    printf("test_pass words: %08x %08x %08x %08x\n",
           top->test_pass[3], top->test_pass[2], top->test_pass[1], top->test_pass[0]);

    int fail_count = 0;
    for (int i = 0; i < 112; i++) {
        unsigned word = top->test_pass[i / 32];
        bool bit = (word >> (i % 32)) & 1;
        if (!bit) {
            printf("FAIL/NOT-PASSED: test_index %d\n", i);
            fail_count++;
        }
    }
    printf("total not-passed: %d / 112\n", fail_count);

    top->final();
    delete top;
    return 0;
}
