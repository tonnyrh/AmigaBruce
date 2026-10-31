# OP0/OP5: rejected audio lookup experiments, 30 October 2026

Both experiments leave source SID drivers, extracted waveforms, envelope
rules, frequency mapping and DMA ownership unchanged. Their private source
files and baseline are under `reference/analysis/audio-lookup-2026-10-30`.
Neither is present in production.

The first variant replaces the 66-entry linear waveform lookup with an
exact sorted-key binary search. 200,238 host cases match the old renderer's
state, Paula parameters and faults. The second retains the old scan but
validates a per-voice last-wave index before reuse. 210,238 cases include
interleaved independent state instances and resets. Its three private
bytes occupy four extra BSS bytes in the native image. No source-C64 RAM
is used as a competing audio state.

| Continuous controlled 20-room route, 120 source steps/room | Baseline | Binary search | Validated hint |
| --- | ---: | ---: | ---: |
| HSYNC lines | 2837562 | 2836972 | 2808930 |
| Actual fields | 9062 | 9062 | 8970 |
| Audio misses within intervals | 148 | 167 | 176 |
| Room 12 fields | 418 | 414 | 419 |

Each native run passes its 710 contact/sprite controls, source/audio/DMA
fault checks, all 20 interval checks and the Chip reserve. COP1LC samples
stay inside the safe window. These controls do not make either candidate
an acceptable performance change: both increase missed audio service ticks;
the second also makes some individual room intervals worse. Both are
rejected. They are timing experiments, not natural playthroughs or source
raster certification. Separate runs carry source history across debug room
jumps; small per-room changes must not be attributed to a local routine
without a stronger comparison.

`decision.json` binds the raw reports and records that the current normal
binary and all production sources still match the baseline at the decision.
The R20 profile is only a priority measurement: it includes a first full
runtime paint and cold work, and its 32 empty profiler pairs cost 138 lines.
Room work averages 266 exclusive lines/call, versus 5.4 for the audio
renderer in this diagnostic. The audio-publish figure also includes test-only
hashing absent from normal play. These numbers must not be treated as a
clean normal-build budget or added to inclusive parent times.
