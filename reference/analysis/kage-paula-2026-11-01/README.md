# Reproduce the R01 fall-hit controls

The timing reference is the tested build at `5ed53f6`. The private builds
use its normal-scheduler OP0 sources and shared objects in
`.tmp/op-pipeline/candidate`. These are produced by the 31 October
`build_pipeline.py candidate` recipe at that commit. The ROM, VICE
snapshots, C64 RAM and Amiga combat captures stay in the local reference
tree. The recorded delivery identifies the ordinary game and the probes
separately.

* Run `vice_run.ps1` with modes `play`, `match168` and `match207` on free
  localhost ports. Each process restores the hash-checked starting snapshot.
  The two matched runs apply the listed fixture writes. The joystick-only
  run searches the live program. The fork at the hit repeats right, left
  and right under VICE's own raster interrupts.
* Run `build.py fold` and `proof.py`. The host test compares all 65,536 RAM
  bytes and ten register/flag values with the original instruction path.
  Its private cases include binary score rollover, extra-life threshold
  crossings, unusual stack positions and two complete combat calls.
* Run `build.py hud`, `native.py` and the shared `run.ps1 proof` with
  `-StageName kage-paula` and a fresh output label. The 68000 checks the
  same 124 cases, then compares the entire 40 KiB display for 128 score
  drawings before setting the success word in its report.
* `build.py polled-hud` builds the selected OP0 route. Pass its mode, a
  fresh label, room 1, enemy mask 3, route 2 and `-StageName kage-paula`
  to the 31 October score `run.ps1`. Its eight route bytes specify a
  240-step warmup and 240 measured steps. The long mode stops after at least
  6,000 physical fields. The output timestamp is taken immediately before
  the writes of the three Paula voices.
* `response-old`, `response-old-full`, `response`, `response-full` and
  `response-polled-hud` are separate instrumented forks. The route's probe
  byte selects step 168 or 207 and the held direction. Values 1/2 select
  left/right for the first hit and 5/6 select left/right for the second.
  `compare.py` reduces their raw reports along with the VICE forks.
* Build the ordinary game with `amiga-build.ps1`. The CLI and disk checks
  exercise the complete menu image, pause, room crossing or the next player
  after death. Run `python tools/verify_op_finish.py` from the repository
  root to verify the recorded identities and scoped acceptance results.
