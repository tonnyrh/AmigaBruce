# Reproducing the three field tests

The reference game is the preceding local `kage-paula-2026-11-01`
delivery, including its unmetered game, normal OP0 probe and 6,000-field
probe. Its README describes the private reference and toolchain inputs.
The new experiments build in `.tmp/field-work`. The release record binds
the timed binary and ordinary executable separately.

* Run `build_field.py release` and `build_field.py long-release` to
  build the selected probes. Use `measure.ps1` for all eight routes.
  For an individual trial use the shared score `run.ps1` with
  `-StageName field-work`. Room 1, mask 3, routes 0 and 2 select Bruce
  standing still or moving with both enemies. Use a fresh directory label
  for each repetition. The cadence report counts physical Paula writes.
* `vice_run.ps1` restores the frozen baseline in a dedicated PAL VICE
  process, reaches the two player states using joystick input and forks
  before and after the source slot. It does not patch the C64 program.
  `proof_field.py input candidate` compares the four buffers through the
  integrated field routine, including stale input from a prior display
  iteration. `test-source-input-slot.ps1` checks all RAM and registers.
* `native_ports.py candidate` and `run_ports.py <fresh-label>` exercise
  the game's Amiga port reader with actual WinUAE joystick events at the
  agreed test boundaries. The handshakes deliberately exclude host event
  latency from the comparison.
* `proof_field.py dma` builds a 68000 proof of all nine supported image
  lengths, repeating and muted voices and destination guards. The shared
  runner's `proof` mode reads its three result words. The expanded combat
  proof uses the preceding stage's full-RAM fixture with actors 2 and 1.
* `product.py release` builds the ordinary game from the corresponding
  release sources. CLI, ADF and render checks use the normal game entry
  point. The 36 stair samples and 12 death/return samples check visible
  pixels. `record_field.py` compares the ordinary loaded sections, binds
  the completed routes and records the exact tested EXE and ADF.
* `alloc_replay.py <fresh-folder>` diagnoses HUNK placement. Supply a
  copy of the test executable and ELF in that folder under the private
  staging directory. It stops a separately patched copy after the last
  allocation. The 53-case game test runs the ordinary test executable.
