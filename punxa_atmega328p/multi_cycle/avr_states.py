"""
avr_states.py
=============
The full list of FSM states, grouped by *phase of execution* rather than
dumped in one flat list. Each phase has a one-line description of what
it accomplishes and roughly when control flow enters/exits it.

High-level flow (every instruction goes through ENTRY; everything else
is opcode-dependent):

    ENTRY
      FETCH_INSTRUION -> DECODE_INSTRUCTION
                              |
                              v
              (branches out into exactly ONE of the phases below,
               based on what kind of instruction was decoded)
                              |
                              v
                 FINISED_INSTRUCTION_EXECUTION
                              |
                              v
                       FETCH_INSTRUION   (loop back to top)

Phases reachable from DECODE_INSTRUCTION:

    FETCH_RD / FETCH_RR      -> read operand register(s) into ALU buffers
    EXECUTE                  -> ALU op, branch test, or skip test
    LOAD_FROM_MEMORY         -> LD / LDS / LPM
    STORE_TO_MEMORY          -> ST / STS / SPM
    WRITE_RESULT             -> commit ALU/memory result back to a register
    MOVW                     -> dedicated register-pair copy (bypasses ALU)
    JUMP_CALL_RETURN         -> RJMP/IJMP/JMP/CALL family/RET/RETI
    PUSH_POP                 -> stack push/pop
    IO                       -> IN / OUT
    INTERRUPT                -> save context + jump to interrupt vector

Every phase below funnels into FINISED_INSTRUCTION_EXECUTION when done.
"""

STATES = [
    # ── Entry / main loop ───────────────────────────────────────────────
    'FETCH_INSTRUION',                  # ask RomHandler to fetch next instruction
    'DECODE_INSTRUCTION',                # wait for decoder, then route by opcode
    'EXECUTE_INSTRUCTION',               # (reserved / unused marker state)
    'FINISED_INSTRUCTION_EXECUTION',     # signal done, loop back to fetch

    # ── Fetch Rd (8-bit) ────────────────────────────────────────────────
    'FETCH_RD_INIT',                     # drive Rd address, request read
    'FETCH_RD_WAIT',                     # wait for MemoryInterface resp
    'FETCH_RD_LOADBUFFER',               # latch Rd value into ALU buffer
    # Fetch Rd high byte (ADIW / SBIW need Rd+1; MOVW has its own path)
    'FETCH_RD_INIT_B2',
    'FETCH_RD_WAIT_B2',
    'FETCH_RD_LOADBUFFER_B2',

    # ── Fetch Rr (8-bit) ────────────────────────────────────────────────
    'FETCH_RR_INIT',
    'FETCH_RR_WAIT',
    'FETCH_RR_LOADBUFFER',
    # Fetch Rr high byte (currently unused — no opcode routes here, since
    # MOVW has its own dedicated path — but kept for future 16-bit two-reg ops)
    'FETCH_RR_INIT_B2',
    'FETCH_RR_WAIT_B2',
    'FETCH_RR_LOADBUFFER_B2',

    # ── Execute ─────────────────────────────────────────────────────────
    'EXECUTE_ALU_OPP',                   # ALU computes; routes to write-back or done
    'EXECUTE_BRANCH',                    # evaluate branch condition, jump if taken
    'EXECUTE_SKIP',                      # CPSE/SBRC/SBRS/SBIC/SBIS: maybe skip next
    'SKIP',                              # swallow (NotExecute) the skipped instruction

    # ── Load from memory (LD / LDS / LPM) ──────────────────────────────
    # Before entering this phase, the control box has already arranged
    # for X/Y/Z to hold the right pointer value:
    #   R26:R27 -> X register of MemoryInterfaceHandler
    #   R28:R29 -> Y register of MemoryInterfaceHandler
    #   R30:R31 -> Z register of MemoryInterfaceHandler
    'FETCH_MEMORY_VALL_INIT',
    'FETCH_MEMORY_VALL_WAIT',

    # ── Store to memory (ST / STS / SPM) ───────────────────────────────
    # STS needs an extra step before the write: its address lives in the
    # instruction's SECOND word, so the RomHandler must fetch it
    # (Fetch_Address) and hand it to the MemoryInterfaceHandler before the
    # write can happen. ST(X/Y/Z) skip this step entirely — their address
    # already comes from the X/Y/Z pointer.
    'WRITE_MEMORY_FETCH_ADDR_INIT',
    'WRITE_MEMORY_FETCH_ADDR_WAIT',
    'WRITE_MEMORY_VALL_INIT',
    'WRITE_MEMORY_VALL_WAIT',

    # ── Write result back to register file (8-bit) ─────────────────────
    'WRITE_RES_INIT',
    'WRITE_RES_WAIT',
    'WRITE_RES_FINISHED',
    # High byte for 16-bit results (ADIW / SBIW / MUL family)
    'WRITE_RES_INIT_B2',
    'WRITE_RES_WAIT_B2',
    'WRITE_RES_FINISHED_B2',

    # ── MOVW — dedicated register-pair copy path ───────────────────────
    # MOVW is a pure Rr -> Rd copy (and Rr+1 -> Rd+1). It never touches
    # the ALU operand buffers or the ALU write-result sequence: each byte
    # is just read from Rr and written straight back out to Rd.
    'MOVW_FETCH_RR_INIT',
    'MOVW_FETCH_RR_WAIT',
    'MOVW_WRITE_RD_INIT',
    'MOVW_WRITE_RD_WAIT',
    'MOVW_FETCH_RR_INIT_B2',
    'MOVW_FETCH_RR_WAIT_B2',
    'MOVW_WRITE_RD_INIT_B2',
    'MOVW_WRITE_RD_WAIT_B2',

    # ── Jump / Call / Return ────────────────────────────────────────────
    'JUMP_LOAD_PC',                       # load new PC from instr / Z / K
    'CALL_PUSH_PCL_INIT', 'CALL_PUSH_PCL_WAIT',   # push return addr (low)
    'CALL_PUSH_PCH_INIT', 'CALL_PUSH_PCH_WAIT',   # push return addr (high)
    'RET_POP_PCH_INIT',  'RET_POP_PCH_WAIT',      # pop return addr (high)
    'RET_POP_PCL_INIT',  'RET_POP_PCL_WAIT',      # pop return addr (low)
    'RET_LOAD_PC',                                # write restored PC

    # ── PUSH / POP ──────────────────────────────────────────────────────
    'PUSH_INIT', 'PUSH_WAIT',
    'POP_INIT',  'POP_WAIT',
    # (No POP_LOADBUFFER state: after a pop we write straight to the
    # destination register, no intermediate buffer needed.)

    # ── IN / OUT ────────────────────────────────────────────────────────
    'IO_READ_INIT',  'IO_READ_WAIT',  'IO_READ_LOADBUFFER',
    'IO_WRITE_INIT', 'IO_WRITE_WAIT',

    # ── Long-jump upper-bits helper (JMP / CALL absolute) ──────────────
    'LONG_JUMP_LOAD_UPPER6_BITS_IN_TO_REGISTER',

    # ── Interrupt handling ──────────────────────────────────────────────
    'INTERRUPT_INIT', 'INTERRUPT_JUMP',
    # No separate 'INTERRUPT' state is needed: once we've jumped to the
    # vector, we just wait for the eventual RETI to come back through
    # the normal RET path.
    'RETURN_FROM_INTERRUPT',
]