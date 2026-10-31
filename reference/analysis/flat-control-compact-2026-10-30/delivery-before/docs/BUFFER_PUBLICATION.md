# Buffer publication, 30 October 2026

User report: jerky scrolling in room 12 and corrupt pictures around death
and room changes. This is a presentation investigation; source gameplay
and the frozen Remember/T64 candidate remain unchanged. The candidate is
not certified as the untouched 1984 release.

The existing single-phase overlay passed a fresh 12-image paused room-12
check before this change. This establishes pixel coherence only. It does
not establish smooth real-time animation or exclude transient corruption.

A separate problem remained at Copper publication. `wait_frame()` services
audio while waiting and does not guarantee that it returns before line 309.
The main loop also performed timing/accounting work after waiting, before
writing COP1LC. The preceding native 20-room run recorded two out-of-window
publication samples (range 0..311). Such a late COP1LC update can miss the
automatic Copper restart: the software then assumes a buffer switch that
has not happened and may write into the bitmap still being displayed.
That mechanism is identified from the Amiga renderer; it is not a C64 rule.
The old late samples were taken before the old write and are evidence of
an unsafe window, not a complete raster trace of the Copper restart.

The new `present_frame()` completes outstanding Blitter DMA, waits, checks
the beam again, and accepts only lines 300..308 immediately before COP1LC.
An overrun waits for another safe window. All runtime menu/game switches
use it. Initial hardware takeover and OS restoration keep their own setup.
The main loop now commits before accounting work; its diagnostic raster
sample is taken by the commit helper. No source state, collision, animation
phase, input rule, sound composition, or memory allocation was changed.
The compiled normal helper contains the unsigned `(line-300)<=8` guard
followed by the COP1LC store, without intervening subroutine calls.

Before sources and binaries are preserved in
`reference/analysis/publication-2026-10-30/before`. The new scoped report is
`reference/analysis/publication-2026-10-30/report.json`; validation checks
`core/` identities against the previous source freeze. Native timing runs
and room-12/death captures are recorded separately. Controlled death and
debug room jumps are not a natural playthrough. Full real-time acceptance
and a new user test of perceived smoothness remain open.

Earlier aggregate delivery reports bind the earlier normal binary. They
must not be presented as acceptance of this new renderer without a fresh
aggregate run. Their historical measurements remain available.

Completed scoped controls: all 20 rooms, 120 source steps per room, 710
native contact/sprite controls (including 256 sprite-copy variants), no
source/audio/DMA/arithmetic/contact faults. Publication samples are now
300..301 with zero out-of-window samples. The normal room-12 check has
6 coherent images, followed by 6 more after room 12->13->12 and controlled
death; no mixed animation phases or static pixel mismatches were found.
Host painter checks pass all six contracts, including 60 full room paints
and 96 source-driven room-12 steps. Production BSS/data are unchanged;
normal EXE grows by 56 bytes. The new normal boot file has the same hash.

This is not a speed improvement. In the continuous 20-room timing route,
room 12 took 418 fields for 120 source steps (prior run: 409); the overall
route took 9062 fields (prior: 8996). These are separate controlled runs,
not certified original timing. Smooth animation under load remains open;
we retain the safe commit instead of claiming that all stutter is fixed.
