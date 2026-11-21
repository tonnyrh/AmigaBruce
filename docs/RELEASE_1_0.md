# Bruce 1.0

The first full release of **Bruce for Amiga**, with Classic and Enhanced presentation and all 20 C64-derived rooms. Release tag: `v1.0.0`, prepared on 21 November 2026.

[Download Bruce 1.0](https://github.com/tonnyrh/AmigaBruce/releases/tag/v1.0.0).

## Downloads

- **Bruce-v1.0.0.adf** — bootable disk with both Classic and Enhanced.
- **Bruce-v1.0.0.zip** — the same disk, Amiga executable, English instructions, release notes, internal checksums and the offline sound-test page.
- **Bruce-v1.0.0-sound-test.html** — standalone browser listening page with the source prompts and before/after compression playback.
- **SHA256SUMS.txt** — checksums for the downloadable files.

Target: **PAL Amiga 500, 68000, OCS, Kickstart 1.3, 512 KiB Chip RAM plus 512 KiB expansion RAM**. Use a clean disk boot on a 1 MiB machine. Emulator software and Kickstart ROMs are not included. Start a new game: old USS snapshots contain the old program.

## Changes since RC2

- Bruce's Enhanced shout now has a one-in-three chance **only when his fist knocks out Kage or Yamo**. Ordinary punches, surviving hits, kicks and other deaths do not trigger it. Cries cannot overlap.
- Enhanced ceiling spears in room 12 stand out from the masonry.
- White top fittings in rooms 15 and 17 use blue steel with bronze trim.
- Vault emblems retain their **yin-yang** motif: black/white ornaments and black/yellow extra-life symbols. The graphics editor includes these assets with English labels.
- C64-source review confirms Yamo's brief post-hit kick recovery; this source-defined delay is retained for both computer and human control.

The release retains the approved Kage weapon swishes and Kick Variant 2, the other Enhanced combat samples, separate attack/jump buttons, pause, room selection and the graphics editor. Classic appearance, source collision and source gameplay rules are unchanged by the changes above.

## Controls

Joystick moves; up jumps or climbs. **Fire 0** attacks and confirms room selection; **Fire 1** also jumps or climbs. **P** pauses, **F10** opens the menu in ordinary play, and **Esc** exits to AmigaDOS. On the menu, **F3** selects player count, **F5** selects Yamo control and **F4** switches the look.

**Shift+D** opens test options. With room selection enabled, **F9/F10** browse rooms, **Fire 0** enters, and **F8** opens the menu. This test route marks earlier lanterns collected and is not normal progression.

## Validation and remaining work

The packaged ADF is the normal build tested in cycle-exact WinUAE with the target 512+512 KiB configuration. Room 15/17 checks cover 64,512 Enhanced pixels and 2,560 Classic pixels, with matching source cells, attributes and glyphs across both looks. The 17 graphics-editor integration tests pass. Host audio checks cover 32 controlled source combat cases, unchanged source RAM/registers and all 65,535 sound-choice states (21,845 selections).

The final release disk also passes the native knockout-audio check: ordinary swings cannot request a cry, both enemies exercise the selected/unselected knockout paths, the complete 8,000-byte Paula sample matches, and switching to Classic detaches the Enhanced observer. Controlled positions, health and sound-choice seeds are distinguished from natural play. The offline listening page contains 21 entries with 42 validated WAV previews.

Source comparisons and controlled native tests support the specific changes. They do not certify a full natural playthrough, uniform timing across all rooms or physical-machine listening/visual acceptance of every change. The frozen Remember/T64 C64 candidate is not certified as an untouched 1984 edition. The outstanding acceptance items remain open for 1.0.

[Release evidence](https://github.com/tonnyrh/AmigaBruce/blob/v1.0.0/reference/analysis/release-1.0-2026-11-21/report.json) · [Active tests](https://github.com/tonnyrh/AmigaBruce/blob/v1.0.0/docs/ACTIVE_TESTS.md) · [Source notes for the graphics](https://github.com/tonnyrh/AmigaBruce/blob/v1.0.0/docs/VAULT_EMBLEMS.md). Earlier release candidates remain available on their original release pages.
