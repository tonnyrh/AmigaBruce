# OP4: native IRQ context candidate, 30 October 2026

The isolated candidate now covers source handlers `$48C1`, `$491E`, `$4982`,
player announcement `$14A4`, and the `$1574` half of the Game Over chain.
It is native C, with no opcode interpreter in its runtime path. The frozen
source is executed by py65 only in the offline comparison.

Source SHA256:
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
This Remember/T64 candidate is not certified as the untouched 1984 release.

The game IRQ is not equivalent to writing joystick buffers and decrementing
timers. `$1103` saves registers after the hardware frame; `$48EA-$4913` writes
palette pointers `$0A-$0D`, palette bytes `$0153-$015E` and the band schedule
`$47F5-$47F8`. `$4915` calls `$15A8`, which clears decimal mode, runs all three
SID drivers, publishes sprites and performs input/field work. The candidate
retains the original nested JSR/PHA/PHP stores, including the sound-command
subroutine frames, before restoring registers and the IRQ's returned PC.

The `$491E/$4982` raster chain updates source palette registers and the next
handler/line. The announcement candidate retains ordered color/JSR-frame
writes and the guarded `$48` decrement. Physical beam and CPU delay loops
are excluded from native work; their timing is not claimed equivalent.
These bytes matter to later source execution: `$1159/$1163` increments `$16`
and reads `($16),Y`, which can reach the stack/palette page.

`test-source-irq-context.ps1` passes 3,352 complete 64-KiB RAM, register,
returned-PC and SID rising-gate comparisons against 479,308 executed source
instructions. Tests include source-selected raster-handler sequences from
20 room states, active/pause/controller gates, all eight source sound-command
branches for all three voices, actual effect streams, both terminating
branches in `$4991-$499E`, announcement wait boundaries and masked IRQs.
Room states, caller registers and entry points are explicit controlled
fixtures; this is not a natural playthrough or a hardware raster model.

The m68000 compile probe also records code/data/BSS and compiler-reported
local stack frames in `irq-context-binding.json`. It uses `-m68000 -mshort`
and the existing per-function O2 attributes. Unlinked object totals include
public test wrappers; they are not the production HUNK footprint. Its two
extra BSS bytes are the test wrapper's returned-PC field. Local frame values
do not establish a complete call-chain or runtime stack margin.

The candidate is not integrated. Production source files, normal EXE/ELF/ADF
and the CLI start copy remain unchanged. Integration still needs native
Amiga execution, measured whole-field cost, source-PC mapping at existing
service points and coordination of field/input/SID work. Original interrupt
phase, general stack aliases, physical input timing and `$152C`/title-music
state remain open. The test does not validate generated VIC collisions.

Run `python tools/audit_irq_context_candidate.py` to verify the recorded
bindings. The frozen disassembly and candidate are kept separately under
`reference/analysis/irq-input-2026-10-30`; original source material is untouched.
