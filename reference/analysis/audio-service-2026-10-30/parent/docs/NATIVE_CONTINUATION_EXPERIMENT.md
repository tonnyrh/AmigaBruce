# Compact native call control, 30 October 2026

This OP1/OP5 change modifies native C call/return plumbing while retaining
the translated source instructions and game rules. It retains every original guest stack store,
register/RAM operation and control-boundary check. There is no guest opcode
fetch or decode. The production generator now emits exactly the target-tested compact
header. The normal EXE/ADF and CLI start command have been rebuilt.

The frozen Remember/T64 candidate is
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Its identity as an untouched 1984 release is still unverified.

The original generated `actor_code` has an 88-byte local 68000 stack frame.
444 ordinary direct JSR wrappers invoke it recursively. The experiment
uses a small native continuation array and direct generated C labels for
these wrappers. The original source bytes at every recorded JSR are
checked against its target and return PC. The virtual C64 stack is retained
byte for byte; it is independent of this new C-only continuation array.

A first wide-frame variant kept three C scratch locals in every native
frame. Its object text grew by 21,424 bytes and its local stack frame by
136 bytes. It is retained as an unsuccessful compiler experiment and was
not selected for runtime testing.

The compact variant checks that every original labelled instruction writes
`address`, `q` and `old` before reading them; these C scratch locals do not
survive a source JSR. Only a continuation index is saved. Sixteen local
slots are available. When full, the original recursive call and its exact
return/error guards are used. A one-slot test implementation deliberately
exercises that fallback during nested source calls. Return mismatches and
non-local source exits unwind until the original caller condition matches,
or return through the existing control boundary.

Unlinked 68000 sections:

| Section | Reference | Compact variant |
| --- | ---: | ---: |
| Text | 176,640 | 161,668 |
| Read-only data | 42,185 | 43,961 |
| Data | 3 | 3 |
| BSS | 195,424 | 195,424 |

The net text/table saving is 13,196 bytes. The local actor frame is 124
bytes rather than 88, while normal internal calls avoid another C frame.
This does not prove whole-call-chain stack headroom or normal HUNK size.

Both default and forced-fallback host builds pass all 3,034 original-byte
actor controls and five integrated modes against 7,055,873 original
instructions each. Whole RAM, registers and control boundaries are checked.
The compact default also passes the complete isolated IRQ-context control:
3,352 cases against 479,308 instructions, including returned PC and SID
gate edges. These are controlled source tests, not natural beam timing.

The first native room-1 pilot completes 360 source steps and all 710
contact/sprite controls (256 sprite-copy variants). It uses 1,413 fields
and six missed audio-service ticks, versus a fresh reference's 1,433/eight.
Largest Chip block is 85,408 versus 69,016 bytes. This diagnostic omits the
unused capture allocation in both runs and retains the original 49,152-byte
reserve gate. Startup/music contributes to the field count; it is not pure
game-loop work. The separate native run passes all 53 fixtures and 1,200 loops, with
52,632 bytes in the largest Chip block and no source/render/DMA faults.
Its real-time gate remains false. The first twenty-room route passes 710 controls and all 2,400 source
steps: 8,965 fields, 2,806,120 HSYNC lines and 126 audio-service misses,
compared with a preceding reference route of 9,044 / 2,831,345 / 131.
The largest free slow-RAM block rises from 2,504 to 15,752 bytes; the
minimum largest Chip block stays 68,136. Room 12 itself takes 422 fields
versus 406 in that reference, so this route does not prove smoother room-12
scrolling. The continuous room history and field phases can change workload.
The fresh repeated pair passes: 9,046 -> 8,956 fields and 127 -> 121
audio-service misses. Both pairs retain the original Chip reserve and
recover 13,248 bytes in the largest slow-RAM block.

Current integrated controls repeat all source domains, including 3,034
actor cases, five integrated modes, 4,239 contact cases, 65,536 object
cases, 1,536 sprite-copy cases, source audio/DMA and exhaustive view queries.
Standard native validation passes 53 fixtures/1,200 loops plus 710 separate
reference controls. CLI and ADF boots pass. All 76 menu snapshots pass the
complete-front contract and both start parities; snapshot count varies with
when the expected completed menu is reached. Ten explicit option changes
and both start scenarios remain mandatory. A clean normal process supplies
12 room-12 and 12 death/room-roundtrip frames, with zero phase/static pixel
errors and no illegal flicker. Source clock progression passes separately.
The initial menu controller was deliberately ended after its completed menu
check so persisted option toggles could not affect the room-12 test.

The new normal EXE is 315,948 versus 343,388 bytes. Loaded CODE/RODATA drops
13,196 bytes; DATA/BSS and renderer allocations are unchanged. File-size
savings also include debug information. All eight contact primitives and
three sprite/VIC helpers match actual linked code in the before, normal,
reference and fixture builds. The real invalid-entry example is still
rejected. This is a small time improvement and a material memory saving;
full PAL cadence is still unaccepted.

Reproduction/proof tools:

- `tools/native_actor_continuations.py` is the production pure transform,
  invoked by `tools/build_c64_actors.py`. The original private compiler
  experiments remain under the analysis folder.
- The archived host controllers in the analysis `controls` folder retain
  explicit private library/output paths; the original auditors are unchanged.
- `tools/audit_native_continuation_experiment.py` binds the source JSR bytes,
  compiled inputs and reports. It never approves production integration.

Results are under
`reference/validation/compact-actor-delivery.json`. The preceding scoped
delivery, its normal executable and 104 direct proof artifacts are frozen
in the analysis `delivery-before` folder. Current canonical delivery
validation checks this new backend stage explicitly; the previous stage
remains archived rather than being described as a test of the new binary.
Full real-time cadence, IRQ/input phase, native stack margin, natural
playthrough and physical A500 acceptance remain open.
