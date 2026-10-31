# Sprite publication and register-layout experiments, 30 October 2026

These are isolated OP1/OP5 experiments. The production core, main, EXE and
boot command are unchanged. No timing, memory or source-equality gate is
relaxed. The reference is the frozen Remember/T64 candidate with SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`;
its identity as an untouched 1984 release remains unverified.

## Native publisher

Original `$25E2-$269F` publishes actor positions, high-X bits, colors and
sprite pointers. The private helper preserves the `$277E` guard, every
source RAM/stack store, flags and return semantics. Decimal entries retain
the earlier instruction translation. The whole-RAM/register/return control
covers 21,504 binary cases against 1,464,315 actual original instructions,
plus 256 before/after decimal fallbacks. Those fallbacks are not a claim of
original decimal-mode parity. The private native fixture run completes
53 fixtures/1,200 loops with 52,632 bytes in the largest Chip block.

Two original-layout twenty-room attempts could not allocate before the
first gameplay step. They are retained as failures. Packing the test-only
statistics reduced BSS by 320 bytes but added 502 code bytes and also failed;
that diagnostic packing is rejected.

The successful pair instead uses exactly the same controller with all
11 statistics per room retained as 32-bit values. Its 880-byte record array
is explicitly allocated in Chip RAM and freed during cleanup, removing
876 static BSS bytes. Both runs report memory type 3, address 102496 and a
68,136-byte largest Chip block, above the unchanged 49,152-byte gate.
This is a diagnostic layout, not a change to production allocations.

| Twenty-room route | PAL fields | HSYNC lines | Missed audio service ticks |
| --- | ---: | ---: | ---: |
| Current core | 8,980 | 2,810,128 | 131 |
| Private publisher V1 | 8,973 | 2,809,420 | 123 |

Each room includes exactly 120 source steps. Both runs pass 710 native
contact/sprite controls, including 256 sprite-copy variants. All source,
audio, DMA, arithmetic and contact fault counters are zero; all measured
publications occur on lines 300..301. Room 12 takes 410 versus 415 fields:
this pair does not demonstrate smoother room-12 animation or a general
speed improvement. V1 is not promoted on this small result.

## Direct leaf call

The actual bytes contain a JSR to `$25E2` at `$15BA`. A separate variant
calls the binary-mode helper directly from that site. It retains the two
guest stack writes, stack-decoded return and every continuation guard;
D=1 still calls the previous actor translation. The original reference
entry remains available. No call graph is pruned on an assumed invariant.

`test-source-sprite-direct.ps1` reproduces this private variant and tests
the entire `$15B8-$169D` prefix against actual original instructions.
640 binary cases across twenty rooms/two controller modes match all RAM
and registers after 81,112 instructions. Another 640 D=1 cases match the
previous implementation. The room seeds come from the current loader;
this test is not a natural C64 IRQ schedule.

The first native room-1 run passes 710 controls and 360 source steps in
1,420 fields with four audio-service misses and a 69,016-byte Chip block.
Earlier current-core trials used 1,430/1,431 fields and V1 used 1,424.
These include startup/music time and are not pure per-step game intervals.
The first full-room run completes 2,400 source steps in 8,905 fields,
2,788,266 HSYNC lines and 121 missed audio-service ticks (reference:
8,980 / 2,810,128 / 131). Room 12 uses 407 fields (reference 410). All
710 native controls and the 68,136-byte Chip reserve pass. A fresh repeated pair gives 9,044 -> 8,981 fields, 2,831,345 ->
2,811,349 HSYNC lines and 131 -> 131 audio-service misses. This repeats
a small time improvement (about 0.7%); it is not a real-time pass. The
variant is retained without production integration while the larger native
call-control change is evaluated.

## Adjacent private CPU bytes

A separate compiler probe replaces private scalar CPU accesses with
`CPU_R(field)` into a nine-byte struct, preserving member fields and the
`PLANAR_WORD` macro's local `c` parameter. No C64 RAM layout changes.
The isolated 68000 object text is 176,640 -> 175,274 bytes (-1,366), with
unchanged data (3), BSS (195,424) and rodata (42,185). These are unlinked
object sections, not a normal executable footprint. The private host build passes all 3,034 existing actor-chain controls
against actual original bytes, and five integrated modes against 7,055,873
original instructions, comparing all RAM at the field/main boundaries.
The original auditors are retained with only explicit library/output paths
and production-enabled metadata changed. The native build passes 53 fixtures/1,200 loops with an unchanged
52,632-byte Chip reserve. Its fresh R01 pilot gives 1,433 -> 1,423 fields
but eight -> ten audio-service misses, with 710 controls passing. It is
not selected for integration after this pilot: the small time improvement
does not establish acceptable audio service. No repeatable audio regression
is claimed from this one pair. The compact native call-control candidate
is being evaluated instead.

Machine-readable identities and results are under
`reference/analysis/sprite-publish-2026-10-30/experiment.json` and
`reference/analysis/cpu-register-layout-2026-10-30/probe.json`.
Full PAL cadence, correct IRQ/input phase, native stack headroom, natural
playthrough and physical A500 acceptance remain open.
