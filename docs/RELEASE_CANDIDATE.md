# Bruce v0.1.0-rc.2

Second downloadable release candidate, prepared on 14 November 2026.

Download from [GitHub Releases](https://github.com/tonnyrh/AmigaBruce/releases/tag/v0.1.0-rc.2). RC1 remains available on its original release page.

## Downloads

- **ADF:** bootable disk containing Classic and Enhanced.
- **ZIP:** the same disk, the Amiga executable, English instructions, checksums and the offline sound-test page.
- **Sound-test HTML:** the standalone browser listening page, with generation prompts and before/after quantization playback.
- **SHA256SUMS.txt:** checksums for the published downloads.

Target: PAL Amiga 500, 68000, OCS, Kickstart 1.3, 512 KiB Chip plus 512 KiB expansion RAM. A clean disk boot is recommended on a 1 MiB machine. Emulator software and Kickstart ROMs are not included. Start a new game; old USS saves contain the old program.

## Changes since RC1

- Enhanced uses the user's imported Bruce shout, with a one-in-three chance on a punch while no shout is already playing. Other punches retain their ordinary sounds. This replaces the RC1 lethal-punch-only cry.
- Both Kage weapon swings use the selected quick and broad air swishes.
- Kage Kick Variant 2 uses the regenerated take; Variant 1 and Yamo's sounds are retained.
- The long clips play directly from a dedicated Chip-memory segment. They retain their approved lengths, finish without footstep interruption, and require no runtime decompression. Bruce's shout cannot overlap itself.
- The browser test plays its chosen sound every time and shows the source and recorded generation prompt.

Classic sound mapping and the C64-derived gameplay routines are unchanged. The sound-choice generator is independent of game state and the original RNG.

## Validation and limits

The normal ADF boots in WinUAE with the target 512+512 KiB configuration. Classic -> Enhanced -> Classic, both enemies, visible punches/kicks, separate attack/jump buttons and primary-Fire room confirmation pass. Ordinary Fire produces both normal punches and the imported shout. Four separately identified controlled playback requests verify the new PCM data, periods and completion in the normal program.

Host checks cover 17 unique samples, routing and buffer boundaries, 16 combat cases with unchanged source RAM/registers, and all 65,535 states of the independent sound-choice generator (21,845 select a shout). Source audio passes 7,540 cases; DMA comparisons pass 1,518 fields / 4,554 images. The listening page contains 21 entries / 42 valid WAV previews and passes JavaScript syntax validation.

The tested normal disk is packaged unchanged. On the inspected clean boot, 68,976 bytes of Chip RAM and 3,432 bytes of expansion RAM remain free. The three long clips use 13,600 bytes in Chip RAM, while the large working-data segment stays in expansion RAM. These figures are run-specific, not guarantees for a populated Workbench environment.

This is a **prerelease**. Physical-Amiga listening acceptance, natural full-game progression and timing across all rooms remain open. The reported Enhanced ceiling-spear visibility issue in room 12 is not fixed by this audio release. The frozen C64 reference candidate is not certified as an untouched 1984 edition. No complete original-game parity or steady-PAL claim is made.

[RC2 evidence](../reference/analysis/release-rc2-2026-11-14/report.json) · [Active tests](ACTIVE_TESTS.md) · [RC1 evidence](../reference/analysis/release-rc1-2026-11-14/report.json).
