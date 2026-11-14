# OP4 input-slot candidate, 30 October 2026

The candidate below was isolated in October. The November production
implementation passes the full RAM/register comparison and samples the
Amiga joystick ports at the active field slot. [November results](FIELD_WORK.md).

The production field seam still has the two gaps recorded in
[the IRQ/input audit](IRQ_INPUT_AUDIT.md). This candidate does not replace it.
It is a small native C implementation of the frozen `$169D-$1702` slot.
There is no 6502 interpreter in the candidate; py65 executes the original
bytes only in the offline comparison.

Source SHA256:
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
The Remember/T64 candidate remains unverified as the untouched 1984 edition.

## Amiga Fire 1 jump shortcut, 4 November 2026

During play, Fire 1 supplies Up to the same input slot as the stick.
It takes precedence over Down and preserves Left, Right and Fire 0.
With the standard stick selector this produces direction `$0E` alone,
`$0A` with Left and `$06` with Right in `$98`. Fire 0 independently
drives `$9B`. The original grounded movement branches, including
`$1DEC–$1E10` for climbing or a vertical jump, consume those inputs.
Menus and the room picker continue to confirm with Fire 0.

Paula reads the second button on pin 9 through POTINP bit 10 or 14,
depending on the port. Both pin 9 lines are driven high to sense the
active-low switches during hardware takeover. The game returns control of
POTGO to the OS on exit. [Commodore Amiga Hardware Reference Manual, chapter 8](https://www.ikod.se/wp-content/uploads/2020/08/Amiga_Hardware_Reference_Manual_3rd_Edition.pdf)

The `--buttons` WinUAE check exercises punch, straight and diagonal jumps,
the original stick-Up input, simultaneous attack and jump inputs, and
room confirmation on the PAL A500 build.

## October input-slot comparison

The helper retains `$0104`'s sampling gate, player-dependent pin selection,
the `$1383+X` flag and `$4A85` conversion table, `$42CA`'s second-controller
gate, and the original input-buffer, PHA and PHP writes. The native flags,
A/X/Y and restored SP match the source at `$1703`. Indexed fire reads are
retained even for deliberately nonstandard player bytes. Fixed CIA pin
values are supplied explicitly; this does not define a physical sampling
window or add an input latch.

`test-source-input-slot.ps1` passes 99,072 complete 64-KiB RAM/register
comparisons against 3,803,993 executed frozen instructions:

- 32,768 gate/player/mode/selector/32-by-32 pin combinations;
- 65,536 stack-position/status-byte combinations, including page-1 aliases;
- 768 nonstandard-player cases with full eight-bit pin values.

The candidate and report are in
`reference/analysis/irq-input-2026-10-30/candidate/input_slot.h` and
`input-slot-candidate.json`. Production sources and normal EXE/ADF are
unchanged by this experiment.

The original menu writes selectors at `$0974/$0983` (zero) and
`$0993/$09A3` (one). `controller-select.txt` disassembles those actual bytes;
its comments from the upstream partial disassembly are not used as proof
of device semantics.

Before integration, the helper must be reconciled with the complete IRQ's
caller context, stack writes, raster/palette prologue and source-field
execution order. Existing integrated world controls inject decoded inputs
and skip this slot; they cannot independently establish its correctness.
No full IRQ, physical input, real-time or natural-play acceptance is claimed.


Further controlled context reconstruction now passes3,352 complete IRQ
comparisons, including game raster handlers, announcement and a Game Over
tail. See [the context candidate](IRQ_CONTEXT_CANDIDATE.md). Native execution
and physical scheduling/phase remain unverified; the production seam is
still unchanged.
