# USART0 test suite — catalogue, verification, and roadmap

This directory holds `tb_usart.py`'s test programs. It's organized in two
tiers:

- **`usart_tests/*.asm`** (this directory, flat) — the *active* suite.
  Anything here is wired up, passes, and is run by `runAllTests()`.
- **`usart_tests/pending/*.asm`** — tests received but not yet wired up.
  Not run by `runAllTests()` (the harness's file filter only looks at
  `usart_tests/*.asm` directly, so `pending/` is invisible to it by
  construction — no separate opt-out mechanism needed). Moved into the
  active directory one at a time as each is implemented and verified,
  per the person's "one test at a time" instruction.

Every test below was read against the real ATmega328P datasheet
behavior it claims to exercise before being accepted as useful. Two
real bugs were found and are called out explicitly rather than silently
worked around.

## Status table

| Test | Real-hardware behavior it targets | Verdict | What's needed |
|---|---|---|---|
| `test_usart_tx_rx_loopback.asm` | Basic TX/RX framing, TXC0 set/clear | **Active, passing.** Byte-identical to the already-verified baseline test. | Nothing. |
| `test_usart_9bit_mode.asm` | 9-bit character mode, TXB8/RXB8, read-before-UDR0 ordering | **Useful, hardware already correct.** | Harness: peer must be configured `nbBits=9` for this test only (see "Implemented" below — done). |
| `test_usart_char_size_mask.asm` | 5/6/7-bit character modes, hardware masks unused MSBs on both TX and RX | **Active, passing.** Hardware was already correct; the peer now tracks the DUT's live UCSZ config via `PeerUART(track_format=True)` (see below). | Done — `peer_uart.py` gained an optional `dut`/`track_format` mode; `tb_usart.py` opts this test into it. |
| `test_usart_dor0_overrun.asm` | 2-deep RX buffer, DOR0 set on 3rd unread byte, cleared on read | **Active, passing.** Worked against the default echo harness unmodified, as predicted. | Nothing. |
| `test_usart_u2x0_mode.asm` | U2X0 halves the baud divisor (16→8 ticks/bit) | **Active, passing.** Worked against the default harness unmodified, as predicted. | Nothing. |
| `test_usart_baud_sabotage.asm` | Real AVR has no double-buffering on the baud generator: writing UBRR mid-frame changes the *next* bit's timing immediately | **Active, passing** after fixing a real test-file calibration bug (see below). | Done — `tb_usart.py` gained a `TEST_POST_CHECKS` hook (`_check_baud_sabotage`) that inspects `peer.received` for any frame *without* corruption, since the DUT's own registers can't show this (it's the transmitter here, not the receiver). **Also required fixing the test's delay loop**: its `nop`/`dec`/`brne` timing comment (880 cycles ≈ 5 bits) assumed a real single-cycle AVR; empirically, in this multicycle CPU the same 220 iterations took ~9500+ simulator cycles — over 5× the entire 1760-cycle frame — so the sabotage write always landed thousands of cycles *after* the frame had already finished, and the peer always decoded a perfectly clean, uncorrupted `0x55`. Recalibrated to 20 iterations (verified empirically to land the write mid-frame and produce real corruption — confirmed both that the fixed version passes and that reverting to the original count makes the check correctly fail again). |
| `test_usart_baud_sweep.asm` | UBRR0 across its full range: 0 (fastest) and 4095/0x0FFF (slowest, 12-bit max) | **Active, passing** (1,346,261 cycles, ~7 minutes wall clock — genuinely slow, not a hang: the UBRR0=4095 sub-test alone needs ~655k cycles for one byte's round trip). | Done — `PeerUART(track_baud=True)` (mirrors the DUT's live UBRR0/ticks_per_bit every cycle) plus a per-test `TEST_STEP_LIMITS` override (3,000,000) in `tb_usart.py`. |
| `test_usart_dynamic_baud.asm` | Same UBRR-change-takes-effect-immediately behavior, simpler 2-rate case | **Active, passing.** | Done — same `track_baud=True` mechanism, default step limit was already enough. |
| `test_usart_break_condition.asm` | Holding RXD low ≥ a full frame reads as data=0x00 with FE0 set (AVR has no dedicated break-detect flag; this *is* how a break looks) | **Active, passing.** Hardware already produced exactly this once the wire was genuinely held low across a whole sampled frame. | Done — `PeerUART` gained a generic `on_frame_received(peer, entry)` hook (can suppress the default echo per-frame and queue a custom response) plus a `send_break()` helper; `tb_usart.py` wires a driver that reacts to the 0xBB sentinel. |
| `test_usart_parity.asm` | Even parity generation/checking, UPE0 on mismatch | **Active, passing.** Parity was already fully implemented on both sides. | Done — same `on_frame_received` hook, reacting to the 0xFF sentinel with `peer.send_bad_parity()` (already existed, just never had a driver wired to call it on cue); `parity='even'` added to `TEST_PEER_KWARGS` so the default-echo sub-test also comes back clean. |
| `test_usart_mpcm_filtering.asm` | MPCM0: silently discard 9-bit frames whose 9th bit (address marker) is 0 | **Useful and realistic concept, but a real hardware gap**: `MPCM0` is tracked as a raw bit (writable via UCSR0A) but **never consulted anywhere in `_finish_rx_frame`/`_refresh_rx_front_status`** — incoming frames are never filtered today regardless of MPCM0. This needs an actual USART0 fix, not just a harness/test change. | USART0: skip enqueueing (or immediately drop) a completed RX frame when `MPCM0==1` and its 9th bit is 0. Harness: needs `peer.send9()` with precise timing control for the two sub-frames. |
| `test_usart_tx_graceful_disable.asm` | Clearing TXEN0 mid-frame must not abort the in-flight frame; the pin stays under USART control until the shift register empties | **Active, passing.** Real `USART0` hardware bug fixed: `TX_logic` used to abort any in-flight frame the instant TXEN0 went to 0, contradicting the datasheet ("disabling... will not become effective until ongoing and pending transmissions are completed"). | Done — `TX_logic` no longer checks TXEN0 at all (an already-buffered or already-shifting frame always completes); `TXEN0` is now checked in `_write_udr` instead, gating whether a *new* byte is even accepted into the buffer in the first place. Also needed a harness fix: `tb_usart.py` had no GPIO peripheral wired up at all, so this test's `DDRD`/`PORTD` setup (PD1/TXD0 as a plain output before the USART takes the pin) hung forever — added `VirtualGPIO` (extended with Port D support, previously B/C-only) to the harness. |
| `test_usart_tx_reenable_glitch.asm` | Same graceful-disable requirement, plus toggling TXEN0 off/on quickly must not corrupt the frame or double-release the pin | **Active, passing.** Same fix as tx_graceful_disable covered this too — once frame completion is fully decoupled from TXEN0's instantaneous value, toggling it off and back on mid-frame has no effect on an already-accepted byte. | Same as above; no additional changes needed. |
| `test_usart_interrupt_driven.asm` | RXCIE0/UDRIE0-driven transfer entirely through ISRs | **Active, passing.** Interrupt wiring already existed. Two real, confirmed test-file bugs fixed: (1) ISR vectors were placed at the real chip's word addresses instead of this project's convention (see `INTERRUPT_IMPLEMENTATION_VS_AVR.md`); (2) after fixing (1) and re-running, a `brne fail` in `verify_data` turned out to exceed AVR's ±63-word conditional-branch range now that `fail:` sits past both ISRs — same class of bug as the ISA suite's own `test_branch_CP.asm` history. Fixed with a local `jmp` trampoline. | Nothing further — hardware already correct. |
| `test_usart_txc_vs_udre.asm` | UDRE fires when the buffer can accept a new byte; TXC fires only when the shift register *and* buffer are both empty — a real, easy-to-conflate timing distinction | **Active, passing.** This file's vector placement (`0x0026`/`0x0028`) was already correct against this project's convention (confirmed by the same empirical check above), and hardware already distinguishes UDRE vs TXC correctly. | Nothing. |
| `test_usart_sync_mode.asm` | UMSEL0=01 synchronous mode: XCK-clocked shifting, no start/stop bits, master drives XCK / slave has it driven externally | **Not supported at all.** `opp_mode` recognizes the `'Synchronous'` label and `ticks_per_bit` has a stubbed `2` for it, but nothing in `TX_logic`/`RX_logic` actually drives or consumes `USART_CLK` as a real XCK line, and framing is always built as async start/stop-bit frames regardless of `UMSEL`. This is a substantial new feature, not a bug fix. | New USART0 feature: real synchronous shift-register framing + XCK generation (master) / XCK-driven sampling (slave). Out of scope for "one test at a time" until explicitly prioritized. |
| `test_usart_mspim.asm` | UMSEL0=11 Master SPI mode: SPI-style full-duplex shift clocked by XCK, no UART framing at all | **Not supported at all**, same root gap as sync_mode (this mode reuses the same synchronous shift hardware on a real chip). | Same new-feature work as sync_mode, plus SPI mode/polarity (UCPOL0/UDORD0) semantics on top. Out of scope for now. |

## Regrouping (by feature area, for planning purposes only — files stay flat)

1. **Core framing** — `tx_rx_loopback` (done), `9bit_mode`, `char_size_mask`
2. **Baud rate generator** — `u2x0_mode`, `baud_sabotage`, `baud_sweep`, `dynamic_baud`
3. **Error detection** — `break_condition`, `parity`, `dor0_overrun`
4. **Multi-processor mode** — `mpcm_filtering` (blocked on a real hardware gap)
5. **Transmitter enable/disable edge cases** — `tx_graceful_disable`, `tx_reenable_glitch` (both fixed and active)
6. **Interrupts** — `interrupt_driven` (test bug, fixed), `txc_vs_udre`
7. **Alternate clocking modes** — `sync_mode`, `mspim` (both blocked on a missing major feature)

## Implementation order (one at a time)

Roughly easiest/most-ready to hardest, since readiness (hardware already
correct vs. needing a real fix) matters more here than the grouping above:

1. ~~`tx_rx_loopback`~~ — already active, no work needed.
2. ~~`9bit_mode`~~ — hardware already correct; only needed a harness
   wiring change (per-test peer config). **Implemented.**
3. ~~`char_size_mask`~~ — same shape as #2 (per-test peer config, this
   time tracking a config change across sub-tests within one run, via
   a new general-purpose `PeerUART(dut=..., track_format=True)` mode).
   **Implemented.**
4. ~~`u2x0_mode`~~, ~~`dor0_overrun`~~, ~~`txc_vs_udre`~~ — all three worked
   against the existing harness completely unmodified, as predicted.
   **Implemented.**
5. ~~`interrupt_driven`~~ — vector-address bug fixed (see
   `INTERRUPT_IMPLEMENTATION_VS_AVR.md`); a second, unrelated bug
   surfaced after that fix (a `brne` exceeding AVR's branch-range limit
   once the corrected vector table pushed `fail:` further away — same
   class as the ISA suite's `test_branch_CP.asm` history), fixed with a
   local `jmp` trampoline. **Implemented.**
6. ~~`dynamic_baud`~~, ~~`baud_sweep`~~ — needed the harness-side
   baud-tracking mechanism described above (and, for baud_sweep, a
   raised step limit). **Implemented.** ~~`baud_sabotage`~~
   deliberately does *not* use this mechanism (see its own entry
   above) and needed a new `TEST_POST_CHECKS` hook plus a real
   test-file timing fix instead. **Implemented.**
7. ~~`break_condition`~~, ~~`parity`~~ — needed the new generic
   `on_frame_received` trigger-byte-driven driver mechanism in
   `PeerUART`/`tb_usart.py`. **Implemented.** `mpcm_filtering` uses the
   same class of harness mechanism but additionally needs a real
   USART0 fix (MPCM0 is currently a dead bit) — still pending.
8. ~~`tx_graceful_disable`~~, ~~`tx_reenable_glitch`~~ — needed a real
   `USART0` fix (TXEN0 used to abort in-flight frames instead of
   finishing them) plus a harness fix (no GPIO peripheral was wired up
   in `tb_usart.py` at all, so these tests' `DDRD`/`PORTD` setup hung).
   **Implemented.**
9. `sync_mode`, `mspim` — need a genuinely new USART0 feature (real
   synchronous/XCK-clocked framing). Substantial; should be scoped as
   its own piece of work rather than folded into "one test at a time."

## Gotcha: software delay loops can't assume real single-cycle AVR timing

Found while implementing `baud_sabotage` (see its entry above): a
`nop`/`dec`/`brne` software delay loop calibrated against the real
ATmega328P's documented single-cycle cost per instruction (`nop`=1,
`dec`=1, `brne`=2-taken, so N iterations ≈ 4N cycles) will run for far
more than 4N *simulator* cycles here, since this project's CPU is
multicycle — every instruction, delay loop or not, costs many more
simulator cycles than its real single-cycle equivalent. Concretely: a
220-iteration loop meant to model 880 real-AVR cycles (5 bit periods at
UBRR0=10) actually took **~9500+ simulator cycles** — more than 5× an
entire 1760-cycle USART frame — confirmed by direct instrumentation
(logging the exact simulator step of the loop's exit against the
USART's own frame-start/frame-end steps). Any new test whose
correctness depends on a software delay landing at a *specific point*
relative to some other real-time event (a UART frame, a timer period,
etc.) needs its iteration count calibrated against this simulator's
actual per-instruction cost, not the datasheet's, and that calibration
is worth doing empirically (instrument the actual event timing) rather
than computing it from AVR's per-instruction cycle table.

## Wishlist — tests that should exist but haven't been written yet

Gaps noticed while reviewing the above against the datasheet, not written
as `.asm` yet per instruction:

- **2 stop bits (USBS0=1)** — framing/timing with `nbStopBits=2`; nothing
  in the current suite exercises this at all (every test above uses 8N1).
- **RXEN0 disabled mid-reception** — real hardware's receiver shift
  register keeps running even if RXEN0 is cleared mid-frame (only gates
  whether a *completed* frame is transferred to the buffer); worth a
  test analogous to tx_graceful_disable but for the RX side.
  Cross-check needed once tx_graceful_disable's fix lands, since a
  parallel gap likely exists on the RX side.
- **Simultaneous interrupt priority** — RXC, UDRE, and TXC all pending
  at once: confirm `SimpleInterruptUnit`'s dict-iteration priority
  matches the real chip's fixed priority order (RXC > UDRE > TXC among
  these three) rather than incidental dict ordering.
- **Reset-default register readback** — confirm UCSR0A/B/C, UBRR0L/H
  read back their documented power-on-reset values before any
  configuration write (currently only exercised implicitly).
- **9-bit mode + parity combined** — the two features are only ever
  tested independently; a combined test would catch the "8 vs 9 data
  bits" mask-width edge case in the parity calculation (`ones` counting
  loop already branches on `nb == 9`, but nothing exercises it with
  parity enabled).
- **MPCM0 in normal (non-filtering) transmit-side use** — real firmware
  toggles TXB80 to *mark* address bytes when using MPCM, independent of
  whatever the receiver-side filtering is doing; worth a test once
  mpcm_filtering's hardware gap is fixed.
- **DOR0 exact boundary** — back-to-back arrival timed so the 3rd byte's
  start bit arrives in the exact same tick the 2nd byte's stop bit is
  still being sampled, to pin down the FIFO-full edge case rather than
  the comfortably-late timing baud_sabotage/dor0_overrun currently use.
