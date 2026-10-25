# Kilderegister

Inspisert 2026-10-18. Kildepåstand og egen verifisering holdes adskilt.

| ID | Kilde / versjon | Rolle og begrensning |
| --- | --- | --- |
| SRC-001 | [Preservation64 Bruce Lee, revisjon 49459](https://preservation64.de/index.php?title=Bruce_Lee&oldid=49459), Source 1 | Valgt primærutgave: 1984 PAL UK, Rakki, arkivert 2013-06-23, verifisert av enigma ifølge katalogen. Filtilgang krever autentisering; ingen egen boot-verifisering. |
| SRC-002 | [5k3105/bruce](https://github.com/5k3105/bruce/tree/25cf80529f91db064692a9cba9a4621b31828fd5) | Sekundær C64-editor/disassembly. README sier original romkode ignoreres ved editorbygging. Sammenheng med valgt PAL-disk er ubekreftet. Ingen rotlisens funnet. |
| SRC-003 | [jzielinski47/bruce-lee, b0d8b616](https://github.com/jzielinski47/bruce-lee/tree/b0d8b616bcf18d4bf78b5f5e3ebe3c17d5392030) | Hentet og inspisert lokalt 24. oktober. Atari-basert TypeScript-spill med egen AI; inspirasjon, ingen C64-evidens. 22-lanterner-luken er sammenlignet med kandidatens C64-kode; destinasjoner og AI er ikke overført. |
| SRC-004 | Lokalt `harrierattackreloaded` | Bygge-, asset- og testpraksis; utvalgte dokumenter inspisert. Ingen kode kopiert. Commit/lisens må registreres før gjenbruk. |
| SRC-005 | [C64-Wiki Bruce Lee](https://www.c64-wiki.com/wiki/Bruce_Lee) | Sjekkliste for regler, kontroll og spillermoduser. Sekundærkilde; konkrete verdier må måles i valgt original. |
| SRC-006 | [Amiga Hardware Reference Manual, 3. utgave](https://archive.org/details/amiga-hardware-reference-manual-3rd-edition) | Maskinvarefasit i M1; ikke spillfasit. |
| SRC-007 | Brukerens lokale `bruce_lee.t64`, SHA-256 i manifest | Remember-utgave med BRUCE LEE+ og BRUCE LEE CRAZY. BRUCE LEE+ er prøvestartet med begge trainervalg N; originalidentitet er ubekreftet. Se CANDIDATE-0001. |
| SRC-008 | [VICE 3.10](https://github.com/VICE-Team/svn-mirror/releases/tag/3.10.0) | Offisiell portabel GTK3-versjon hentet lokalt. Executable og faktiske C64-ROM-er har SHA-256 i manifest. Joyport-set krever IO Simulation-enheten; se SRC-010. |
| SRC-009 | py65 1.2.0, lokal analyse | CPU-modell for isolerte rutiner fra kandidat-snapshot. Ingen VIC/CIA/SID, IRQ- eller PAL-timingfasit. |
| SRC-010 | [VICE binærmonitor](https://vice-emu.sourceforge.io/vice_13.html), [monitor.c](https://github.com/VICE-Team/svn-mirror/blob/main/vice/src/monitor/monitor.c), [joyport_io_sim.c](https://github.com/VICE-Team/svn-mirror/blob/main/vice/src/joyport/joyport_io_sim.c) | Primærdokumentasjon for monitorprotokoll og simulerte joysticklinjer. IO Simulation er enhet 37; portindeks er nullbasert og linjene aktive lave. Lokalt verifisert gjennom CIA og spillets samplede input i VICE 3.10. |

## Sekundærkildens analysepunkter

`const.go` og `mementry_notes.txt` peker blant annet på romtabeller rundt
`$4B32`, romdata `$68F9`, lanternetabeller `$4CCE`/`$4CE0`,
rom-initpekere `$4E9A` og rom-looppekere `$4EC2`.
Flere kommentarer har spørsmålstegn; adresser og layout er hypoteser til de
er kontrollert mot valgt original. Ikke bruk dem som ferdig minnekart.

Repoet har både `map`, `map_`, `map_original` og `original_data`.
Navnet «original» beviser ikke samsvar med SRC-001. Redigerte kart og
`bruce_the_pro.vsf` skal aldri bli primærreferanse ved en tilfeldighet.
Hashene i manifestet identifiserer analysefiler; de er ikke distribusjonslisenser.
