# OP0/OP1/OP4 follow-up, 30 October 2026

Production C sources, the normal EXE/ELF/ADF and CLI boot copy are unchanged
by these experiments. The remaining OP0-OP6 requirements stay open.

## Current room-1 profile

The standard diagnostic profile failed allocation before any source steps.
Its failure report and binaries are preserved as `observer-r01-profile-native`.
A separate `observer-r01-profile-bounded` build omits the unused diagnostic
framebuffer-capture allocation and its matching allocation guard. Actual
compiled main/build files and their overrides are archived. No production
allocation or memory requirement was changed. The run passes 454 native
controls, 360 source steps and the 49,152-byte Chip reserve gate (69,016
bytes measured); profiler nesting errors are zero.

Selected exclusive costs, in PAL raster lines per call:

| Component | Calls | Mean |
| --- | ---: | ---: |
| Contact driver excluding nested helpers | 360 | 123.283 |
| Contact row processing | 2,882 | 15.282 |
| Sprite publishing | 360 | 84.028 |
| VIC latch/cache | 1,565 | 24.863 |
| Field work excluding VIC/audio children | 1,565 | 17.739 |
| View projection | 360 | 48.419 |

Multiply by call counts before comparing components. Wait time is not CPU
work. The 32 empty profiler pairs cost 135 lines; instrumentation affects
these results. Diagnostic audio publication includes test hashing absent
from the normal build. This profile chooses work to investigate and does
not establish normal real-time acceptance.

## Contact-call fusion experiment: rejected

The only C-source changes force inlining of the existing pointer wrapper,
body wrapper and row-inner function. Function bodies, source service points,
RAM writes and gameplay rules are unchanged. This tests native call-boundary
cost, not new collision behavior. The isolated normal-object probe grows
text by 888 bytes. Actual linked diagnostic footprints are recorded separately.

Two matched pairs run the same archived native binaries, 360 source steps
and 710 contact/sprite controls per run. Both retain the Chip reserve and
have zero source/audio/DMA/arithmetic/contact faults. All eight assembly
contact primitives are compared byte-for-byte with resolved relocations.

| Pair | Before elapsed fields | Candidate | Before missed audio ticks | Candidate |
| --- | ---: | ---: | ---: | ---: |
| 1 | 1,433 | 1,425 | 8 | 11 |
| 2 | 1,430 | 1,425 | 8 | 11 |

These are the existing diagnostic elapsed counters, which include startup
service, not pure game-only intervals. The small reduction is accompanied
by repeated audio-service regression and code growth. The candidate is
rejected before full 53-fixture/all-room delivery testing. No production
promotion or overall game-speed gain is claimed.

## Input candidate

[The native input-slot candidate](INPUT_SLOT_CANDIDATE.md) passes 99,072
whole-RAM/register comparisons against the actual frozen instructions.
It remains isolated until the complete IRQ/stack/palette context is
reconciled. The existing production seam's gaps remain explicitly open.

`tools/verify_op_followup.py` binds the scope, original-byte controls,
compiled overrides, raw native reports and current unchanged normal build.
The frozen Remember/T64 candidate is still not certified as the untouched
1984 release. Natural play, original raster/input phase, whole-call-chain
stack margin, strict normal PAL cadence and physical A500 remain unverified.
