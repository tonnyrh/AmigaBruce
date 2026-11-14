# Bruce v0.1.0-rc.1

First downloadable release candidate, prepared on 14 November 2026.

## Downloads

- **ADF:** bootable disk containing Classic and Enhanced.
- **ZIP:** the same disk, the Amiga executable, English instructions and file checksums.
- **SHA256SUMS.txt:** checksums for the published downloads.

Download from [GitHub Releases](https://github.com/tonnyrh/AmigaBruce/releases/tag/v0.1.0-rc.1).

Target: PAL Amiga 500, 68000, OCS, Kickstart 1.3, 512 KiB Chip plus 512 KiB expansion RAM. A clean disk boot is recommended on a 1 MiB machine. Emulator software and Kickstart ROMs are not included.

## Included

- All 20 reconstructed rooms, Classic graphics and optional Enhanced artwork and audio.
- Main menu, pause, second joystick button for jump/climb, and Shift+D test options.
- Room browsing with F9/F10 and primary Fire confirmation.
- Enhanced scenery corrections, half-buried bomb artwork and the requested one-pixel bomb contact allowance.
- Bruce's stiff death pose, non-vocal Yamo impacts and an Enhanced-only finishing cry for a lethal Bruce punch.
- English project README and graphics editor interface.

## Validation and limits

The normal disk boots in WinUAE with the target 512+512 KiB configuration. Classic → Enhanced → Classic, actor artwork, joystick attacks, separate attack/jump buttons and room confirmation pass. Both enemies are active and the source engine reports no fault in the combat smoke window. The editor passes 17 tests. The finishing cry passes 16 controlled combat cases, 517 frozen-source comparisons and a native Paula-page check.

A fresh complete build produces an executable byte-identical to the tested program. The published disk is the exact disk used for the successful smoke tests. Cold loading/menu routines are compiled for size to keep the program's large working-data segment in expansion RAM; gameplay compilation settings are unchanged. The inspected run has 82,592 bytes of free Chip RAM and 1,968 bytes of free expansion RAM after loading. These are measurements of that clean-boot run, not guarantees for a populated Workbench environment.

This is a **prerelease**, not final acceptance. Natural full-game progression, new-sound listening on physical hardware and timing across all rooms remain open. A broader automatic room tour stopped when a room-5 lantern check sampled a later room after an automatic transition; it is not counted as a successful tour. The frozen C64 reference candidate is not a verified untouched 1984 edition, and no complete original-game parity or steady-PAL claim is made.

[Smoke and memory evidence](../reference/analysis/release-rc1-2026-11-14/report.json) · [Finishing-cry evidence](../reference/analysis/bruce-finisher-2026-11-14/report.json) · [Active tests](ACTIVE_TESTS.md).
