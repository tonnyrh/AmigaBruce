# OP1/OP5 candidate: skip empty color observers, 30 October 2026

This candidate is isolated under
`reference/analysis/color-observer-2026-10-30/candidate/c64_rooms.c`.
It is not yet production. The source stores remain the frozen candidate's
`$42A1-$42BA`, reached through the room-20 loop at `$4272`.
Source SHA256:
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
The candidate's original-edition identity remains unverified.

The existing active animation observer first marks fallback dirty when the
cell's glyph is `$61-$63` (after masking bit 7), then returns immediately
if the cell has no cached animation membership. Consequently, when neither
condition holds the call performs no writes. The private color observer
can omit exactly those calls. All eligible calls still execute the original
active body. The general source writer, color write order, virtual flags,
registers, stack, IRQ/service points and C64 RAM are unchanged. No new cache
or memory allocation is introduced.

The four exhaustive predicate cases are: no animation cache (no observer);
animated glyph with no membership (fallback update preserved); membership
with any glyph (full observer preserved); and neither (a no-op omitted).
The code never skips an observer solely because a rectangle was already
marked dirty, or because a cell's current glyph differs from its cached one.

Controls passed so far:

- 7,424 original-byte color-loop cases, 1,113,600 source instructions,
  comparing all virtual RAM and CPU registers.
- 192 old/new renderer-state and bitmap cases.
- 4,096 glyph/membership/fallback/mismatch combinations, comparing complete
  source RAM and recorded renderer/cache metadata against the old observer.
- Original generic writer: 810 native bytes and 41 resolved relocations
  unchanged; active observer: 200 bytes and 8 relocations unchanged in the
  current normal image, baseline tour and candidate tour.
- One 20-room native route, 120 source steps per room, 710 contact/sprite
  controls, zero source/audio/DMA faults and safe publication samples.

The first route changed total work from 2,837,562 to 2,819,874 HSYNC lines,
and room 20 from 188,320 to 179,889 (4.48% less work). Interval audio misses
fell 148->132. Some other room samples vary and some audio-miss counts rise;
this route carries source history across debug jumps. It is not a clean
isolated per-room causal test or natural playthrough. Room 12 changes must
not be attributed to this room-20-only helper. A second before/after pair
is required before choosing the candidate.

Raw host controls, linked-image bindings and the candidate source are kept
in the analysis folder. Before promotion, complete repeated timing and the
required current-build source/native acceptance. Neither these partial
controls nor a lower total closes the OP0-OP6 real-time/IRQ/input/stack and
physical-machine requirements.

Second pair completed: total work 2,839,196->2,815,830 lines and interval
audio misses 156->127. Room 20 changes 192,076->179,575 lines (6.51%).
Both paired runs retain the reserve and native reference controls. The
isolated 53-fixture image also passes all controls and 1200 loops, with
52,632 bytes largest Chip block. Its actual core override is explicit in
`native-fixture.json`; it must not be mislabeled as a current-production
fixture run. Production integration, current normal image/UI checks and
aggregate delivery binding are still pending. `decision.json` records that
status and the unchanged production baseline.


Production integration completed, 30 October: the current core is byte-identical
to the measured observer candidate. Fresh standard runs pass 53 fixtures/1200
loops and the separate 710 contact/sprite controls; linked instructions and
relocations are checked in six images. EXE 343388 bytes; BSS unchanged. New
CLI/ADF boot, menu transitions, room12 and controlled death/room roundtrip
captures bind the same normal ELF. The preliminary decision above describes
its earlier, isolated stage; current delivery is recorded separately in
reference/validation/color-observer-optimization.json.

Uninstrumented normal runs still fail the three-field cadence target: room1
4.174 fields/step with 241 missed audio services; room12 3.328 fields/step
with zero missed audio services. No room12 speed gain is attributed to the
room20 observer guard. Input/IRQ phase, full stack high-water, natural play
and physical A500 acceptance remain open.
