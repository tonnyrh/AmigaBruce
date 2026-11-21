# Enhanced vault caps and emblems — 21 November 2026

Rooms 15 and 17 now have blue-steel caps with bronze trim instead of flat white top fittings. The vault emblem is a black/white yin-yang symbol; the extra-life variant is black/yellow. The initial pierced-coin design was rejected by the user and is superseded. The frozen source glyphs show opposing lobes and contrasting dots, which the new art retains at single-pixel resolution. These are hand-authored native-resolution pixels using the existing 16-colour OCS palette. No image model or resampling is involved.

The new art uses the existing CPU stamp renderer. Twelve appended 8×8 stamps and a 12-entry word index preserve all 256 earlier editor stamp IDs and their bytes. The eight emblem stamps replace the rejected coin art in place; the four cap stamps are unchanged. The editor exposes the new assets in English. The normal executable is 390,928 bytes (976 bytes above the build before the cap/emblem changes); the actor/panorama Chip buffer and compressed actor art are unchanged.

## Source identity and conditions

Frozen candidate: `.reference/c64/work/untrained-memory.bin`, SHA256 `092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`. This candidate is not certified as an untouched 1984 release. [Bytes and disassembly](../reference/analysis/vault-emblems-2026-11-21/source-disassembly.txt).

| Item | Source | Presentation rule |
| --- | --- | --- |
| Top fittings | Vault `$43/$C3` at `$AA18/$AE18`; `$45/$C5` at `$AA28/$AE28` | Replace only character rows 3–4 of rooms 15 and 17. Keep the original opaque silhouette and apertures. Other uses of these character codes retain their existing appearance. |
| Emblem | `$2D/$AD` at `$A968/$AD68` and `$2E/$AE` at `$A970/$AD70` | A 16×16 yin-yang fits the original two-cell bounds, with an S-shaped division and two opposing dots. Black/white normally; black/yellow when the live cell colour is 7. Applies only to the vault character bank, before the finale. |
| Extra-life colour | Room 17 init `$359F–$35B6` writes `$FF` to `$DB1C/$DB1D/$DB44/$DB45/$DB6C/$DB6D/$DB94/$DB95` | The low three colour bits select gold for both halves of both extra-life emblems. No coordinate-based guess or separate pickup state is added. |
| Pickup | `$2EEA–$2EF3` accepts this object handler only in source room `$10` (displayed room 17). `$2FD6–$2FDE` requires actor X=0 and source Y≥`$A0`. `$2FE0–$2FE7` decrements the current player's `$4E95+X` flag, increments lives `$28`, and refreshes the source HUD. `$2FEF–$2FFE` draws removal string `$56` at rows `$0A/$0B`, column `$24`. | Retain these source conditions. The upper white emblems are decorative; they are not new pickups. Changed screen codes remove the Enhanced emblem through the normal painter. |

The source character RAM, colour RAM, contact masks, collection code, score, lives and Classic drawing are unchanged. Stamp rows retain their source-byte signatures so changed live glyph rows fall back to the source painter.

## Verification

`tools/check_vault_emblems.py` boots the normal ADF on an owned PAL A500 OCS / Kickstart 1.3 WinUAE instance with 512 KiB Chip + 512 KiB slow memory. It enters rooms through the test menu and compares Classic pixels against live source data, Enhanced pixels against the editor masters, and the affected source cells/attributes/glyphs across both looks. This is a controlled room-entry check, not natural-play or physical-Amiga acceptance.

The existing 17 graphics-editor integration tests pass, including packing edited images into real game data. All previous stamp IDs and artwork remain byte-identical. The published RC2 is not updated by this local fix.

The [initial cap/coin report](../reference/analysis/vault-emblems-2026-11-21/report.json) and captures are retained as historical evidence for the rejected artwork. They do not validate the revised yin-yang pixels.

The revised yin-yang ADF passes 30,720 Enhanced pixel checks in room 15 and 33,792 in room 17, plus 2,560 Classic pixels. Source cells, attributes and glyphs match across modes. Native captures show both contrasting dots and opaque black lobes; both white and yellow variants were visually reviewed. All 17 editor integration tests were rerun and passed. [Current report and build hashes](../reference/analysis/yin-yang-2026-11-21/report.json) · [Room 17](../reference/analysis/yin-yang-2026-11-21/room17-enhanced.png) · [Native emblem detail](../reference/analysis/yin-yang-2026-11-21/yin-yang-detail.png).
