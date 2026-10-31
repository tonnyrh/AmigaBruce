# OP4: original CIA input slot, 30 October 2026

Frozen candidate SHA256:
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Remember/T64 remains unverified as the untouched 1984 edition.

The earlier integrated world oracle stops before `$169D`, supplies decoded
input buffers directly and resumes at `$1703`. It does not establish that
the native input seam follows all original conditions.

The new audit executes the actual `$169D-$1702` bytes, checks that the
executed slot still matches the frozen source and checks table `$4A85`.
It covers 32,768 fixed-input cases: both active flags, active players,
human-Yamo modes and both values of each controller flag, with all 32x32
five-bit CIA port combinations. Native comparison is restricted to the
four input buffers. The controlled native field includes its normal prefix;
the original comparison deliberately isolates the input slot. It does not
claim complete IRQ equivalence, stack-prefix parity or natural timing.

Code-derived rules:

- `$169D/$16A0`: `$0104=0` bypasses sampling and retains all four buffers.
- `$16A5/$16BF`: `$03` selects the active controller and fire source.
- `$16CF/$16D2`: `$42CA=0` retains the other controller's buffers.
- `$16AE/$16E5`: a zero `$1383+X` selects the `$4A85` direction conversion.
  Its device meaning has not been inferred from a generic joystick model.
- `$16B3/$16D9/$16EA`: PHA/PHP leave stack writes; these cannot be omitted
  when later establishing complete IRQ/memory equivalence.

All active/default-controller configurations match the native buffers.
25,304 cases differ when the active gate or non-default conversion matters.
The current seam writes active inputs unconditionally and bypasses the
conversion. These are open implementation gaps, not passing parity. Whether
the non-default flags are reachable through the present Amiga menu is a
separate question. No new input window or OR latch was added.

Artifacts: `reference/analysis/irq-input-2026-10-30/report.json` and
`cia-slot.txt`. Run `test-source-irq-audit.ps1` to reproduce. Full hardware
IRQ stack/caller-PC/raster-prologue analysis and physical input timing remain
open; this isolated audit must not be used to close those requirements.

A second controlled check now injects one real py65 `MPU.irq()` at source
PC `$1C32`, through the original `$1103` vector and `$48C1` handler to RTI.
It includes the original three SID calls and compares all 64 KiB against
current native audio+field work in 16 active/default-controller cases.
Caller registers/SP/status are restored (py65's representational B bit is
excluded; physical status bits are compared). Differences are recorded,
not accepted: palette pointer scratch `$0A-$0D`, 12 source palette-buffer
bytes, stack-page writes, raster scheduling bytes and hardware-register
state. These cold controlled cases have no uncategorized RAM differences.
Stack/palette differences must not be dismissed as harmless: later source
reads, including `$1159`, require a separate dependency analysis.
`full-irq.json` keeps every differing byte and the executed PC trace.
This still does not model the remaining raster handlers or establish
naturally occurring interrupt PCs/input phases.


The isolated [native input-slot candidate](INPUT_SLOT_CANDIDATE.md) now
passes99,072 complete RAM/register controls, including all65,536 SP/status
combinations. It is not integrated. Its preserved PHA/PHP bytes belong to
that controlled slot entry; they do not resolve the full IRQ's caller PC,
hardware push frame, raster chain or palette scratch differences above.
The current production audit has been rerun against core hash2d3692711dfd;
its25,304 input-buffer mismatches remain open.


The [parameterized native IRQ-context candidate](IRQ_CONTEXT_CANDIDATE.md)
now matches3,352 actual-source cases/479,308 instructions over all64KiB,
physical register bits, returned PC and all three SID rising-gate edges.
The candidate includes the three game raster handlers, $14A4 announcement
and $1574 tail, with original JSR/PHA/PHP stack writes. These explicit
contexts are not a native Amiga run or a natural interrupt distribution.
$152C/title-music state, source-PC mapping and actual pending/masked IRQ
scheduling remain open. Normal source and EXE/ELF/ADF are unchanged.
