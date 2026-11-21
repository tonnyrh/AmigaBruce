# Room 12 spears and Yamo kick recovery — 21 November 2026

The local build makes the Enhanced vault spears visible against the blue masonry. Yamo's post-hit recovery remains unchanged because the reported suspension is present in the frozen C64 code.

## Ceiling visibility

Room 12 uses tile `$40`, with character halves at `$AA00` and `$AE00`. Its blade uses multicolour pair 2. The source palette selected through `$4821` gives this pair colour 11. Enhanced also uses palette entry 11 for the body of the blue bricks, so the blades blended into the wall.

The Enhanced painter now draws only those blade pixels with light ink 1 in the vault bank. The mounting cap retains its live colour. Source glyphs, cell attributes, collision masks and Classic are unchanged. This also restores the same spear shape elsewhere in the vault rooms; the change is not a new collision rule.

The normal PAL A500 512+512 KiB ADF was checked in WinUAE 6.0.3. All 1,044 blade pixels across the 58 ceiling character halves match in both Classic and Enhanced. The Enhanced structure check additionally covers 21,888 pixels, including the lower spear groups. The sampled ceiling screen, colour RAM and glyph bytes match across modes. The captured visible frame was inspected.

[Native evidence](../reference/analysis/room12-spears-2026-11-21/report.json) · [Corrected room](../reference/analysis/room12-spears-2026-11-21/room12-enhanced.png)

## Yamo after a successful flying kick

Frozen candidate SHA256: `092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.

- `$2AD4–$2AF8` accepts the active kick through the existing contact, facing and distance checks. `$2AE9` calls `$2B3E`, which sets the attacker's hit-success bit.
- `$2B52–$2B65` handles that bit: state 0, a four-update wait in `$0106+actor`, a recovery counter initially set to 24, and a latched pose.
- `$10D0` and `$2B68–$2B98` select the recovery length using `$88` and `$40`. Human-Yamo selection at `$42CA` does not bypass this recovery.
- `$1C5F–$1C67` returns while the initial wait counts down. The state counter then runs through `$1D75–$1D7B` and `$24F4–$2503`. With no floor contact, vertical movement resumes after recovery rather than during it.

Forty controlled cases cover human/computer Yamo, hitting Bruce/Kage, the `$88` boundaries 24/25 and 31/32, and `$40` zero/nonzero. Executing the frozen instructions and the current C port produces identical full RAM and registers across 696 calls. The first downward move occurs on update 29, 15 or 8 for the tested post-hit counters 24, 10 or 3 respectively, including the initial four-update wait.

This is source-based recovery behaviour, so no movement change was made. These are injected contact/position fixtures and instruction comparisons, not a natural VICE playthrough or a measurement of the user's wall-clock pause. The available C64 candidate is not certified as an untouched 1984 release.

[Recovery evidence](../reference/analysis/yamo-kick-hold-2026-11-21/report.json) · [Addressed original instructions](../reference/analysis/yamo-kick-hold-2026-11-21/source-disassembly.txt)
