# OP0/OP4: long normal-build runs, 30 October 2026

These measurements use the unmodified normal EXE after the Copper commit
repair, SHA256
`9f4b2f7de024230282d8217ac7756ee5853db73a4209b4af31b5acade7ede0f8`.
They do not use BL_AUTOTEST, profiler counters/hashes or framebuffer capture.
Each run starts an independent owned WinUAE with the configured PAL A500
OCS/68000/KS1.3/512 KiB Chip+512 KiB slow target. This is not physical A500
evidence. Debug infinite lives/invincibility and room selection are enabled
through normal menu inputs; there are no direct source-RAM writes.

After warm-up, scalar counters are read with the emulator paused at both
boundaries. During the 140-second observation-free interval there are no
IPC reads, key events, recording or profiling. Wall time in the original
reports includes the final paused boundary read; actual PAL-field deltas
are the timing authority. Room and loader epoch remain unchanged.

| Controlled stationary scene | Actual fields | Source steps | Fields/step | Missed audio ticks |
| --- | ---: | ---: | ---: | ---: |
| Room 1 | 6877 | 1647 | 4.17547 | 235 |
| Room 12 | 6943 | 2088 | 3.32519 | 0 |

Both exceed 6000 fields. The room-12 audio condition passes, but neither
run establishes ordinary three-field cadence. The aggregate real-time gate
remains failed. Six fields of endpoint tolerance do not change either
result. No room reload occurred; source and DMA fault counters are zero.
In room 1, emitted audio ticks plus misses equal elapsed source-audio ticks.
The room-12 game/audio boundary counters differ by one field, as expected
from their different service points. Source room-age deltas match game-clock
deltas. These checks do not establish original C64 interrupt phase.

The first and last actor flags are retained in each report. Room 1 includes
source-driven enemies; room 12 has none active at the boundaries. These are
specific stationary scenes, not an active full-game route or proof that an
actor stayed active throughout the interval. Perceived scrolling smoothness
and natural play remain separate acceptance tasks.

Artifacts are under `reference/analysis/normal-runtime-2026-10-30`.
Initial raw reports and the original controller are preserved. Current
reports distinguish the audio condition from cadence so a zero audio-miss
count cannot be presented as full real-time acceptance.
