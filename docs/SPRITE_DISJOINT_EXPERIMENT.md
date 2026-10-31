# Avgrenset spritekopiering, 30. oktober 2026

Dette isolerte OP1-forsøket er avsluttet uten integrasjon. Produksjonskode,
normal EXE og ADF er uendret. Kandidaten er bevart for senere arbeid med
lydservice og feltfase; den er ikke et godkjent spillbygg.

## Kilde og kontrakt

Frossen Remember/T64-kandidat:
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Utgaven er fortsatt ikke bekreftet som urørt 1984-original.
Disassembly: `reference/analysis/sprite-copy-2026-10-29/source-copy-disassembly.txt`.

`$26A0-$2702` kopierer glyphdata baklengs og dekrementerer `$277F` etter
hver skriving. Den telleren kan selv være glyphkilde. Derfor kan vi ikke
generelt erstatte rutinen med en vanlig minnekopi. `$26C6-$26D6` nullstiller
slutten med en do-while-løkke: selv en allerede negativ teller gir én ekstra
skriving. `$2703` er en faktisk BRK-grense. Begge detaljene beholdes.

Kandidaten bruker bare hurtigbanen når:

- Det eksisterende inngangsvernet har godkjent binærmodus, høyde under 32,
  destinasjon `$8000-$FF00` og glyphbaser uten adresseomslag.
- Destinasjonen er partallsjustert og utenfor `$CF00-$DFFF`.
- Alle tre glyphbasene ligger i `$3000-$7F00`. Dette konservative vinduet
  utelukker telleren, pointere, kodeoperander, destinasjon og mapped I/O.
- Y er nøyaktig tre ganger høyden. Smal høyde er 0–20; bred høyde er 1–21.

Dermed er det ingen lesing som kan observere mellomliggende skrivinger.
Hurtigbanen nullstiller 64 byte med 16 langtord og plasserer glyphbytene
forover: smal `dest[3*i]=first[i]`, i=0..høyde; bred
`dest[3*i]=right[2*i]`, `dest[3*i+1]=left[2*i+1]`, i=0..høyde-1.
Sluttverdiene er `$277F=$FF`, X=$FF, Y=64, A=0, Z=0, N=1 og SP+2.
Carry beholdes smalt og blir 0 bredt; V/D beholdes. Original returdekoding
og kontrollgrenser endres ikke. Alle andre tilfeller bruker eksisterende
byteordnede 68000-kode uendret.

## Gjennomført og gjenstående

`test-sprite-disjoint.ps1` kjører en separat C-variant mot faktisk frossen
6502-maskinkode: 1 872 injiserte tilfeller, 485 136 kildeinstruksjoner,
312 BRK-grenser og 568 aliaskontroller. Hele 64 KiB, registre, retur og
feiladresse sammenlignes. 32 tilfeller tilfredsstiller hele hurtigbanevernet,
inkludert binærmodus; 32 ellers like tilfeller bruker decimal-fallback.
Dette er en kontroll av kildekontrakten, ikke naturlig
gjennomspilling eller en kjørt 68000-test.

Begge 68000-variantene består 710 native kontroller, inkludert 256
spritekontroller, og AmigaDOS-entry-kontrollen. De første 64 spritekontrollene
bruker glyphbase `$5D91` og Y=3*høyde for å dekke hurtigbanen og dens
høydegrenser. De øvrige 192 alias-/teller-/sluttilfellene beholdes.
Begge målebygg bruker nøyaktig samme private C-fil og aktørheader;
bare `sprite_copy.s` skiller dem. C-forskjellen mot produksjon er den
ubrukte vertshjelperen og de beskrevne selvtestinngangene.

Kandidatens test-EXE er 335 428 byte mot 335 208 for kontrollbygget.
ELF `.text` øker 222 byte; `.rodata`, `.data` og `.bss` er uendret.
Ingen ekstra RAM-cache er lagt til.

R01 med 360 identiske kildesteg gir følgende måling:

| Variant | PAL-felt | Tapte lydtick | Største Chip-blokk |
| --- | ---: | ---: | ---: |
| Før | 1414 | 6 | 85408 |
| Kandidat | 1388 | 45 | 85408 |
| Før, gjentakelse | 1414 | 6 | 85408 |
| Kandidat, gjentakelse | 1386 | 45 | 85408 |

Dette er omtrent 1,84–1,98 % kortere tid, men et gjentatt uheldig utslag på lydservice.
Det beviser ikke en universell lydregresjon: feltfase og romhistorikk
påvirker dagens servicepunkter. Det er heller ikke et godkjent leveringsresultat.

Første WinUAE-forsøk stoppet før Amiga-koden: prosessen brukte nesten ingen
CPU, ingen oppstartslogg/testfil kom, og Windows hadde aktiv LogonUI.
Kun den eide emulatorprosessen ble stoppet. Dette er ikke et måleresultat
eller bevis på feil i spillet. Windows må være opplåst for ny måling.

20-romsruten bruker 120 kildesteg per rom, med oppsett og romtegning utenfor
tidsintervallet og samme kontinuerlige romhistorikk i begge bygg.
Begge består kontrollene og har minst 69 016 byte i største Chip-blokk.

| Variant | PAL-felt | Rasterlinjer | Tapte lydtick |
| --- | ---: | ---: | ---: |
| Før | 8937 | 2796433 | 128 |
| Kandidat | 8829 | 2762847 | 124 |

Dette er 1,21 % kortere samlet tid. Resultatet varierer per rom; det er
ikke en generell garanti om raskere eller jevnere spilling. Den korte
R01-testen gjentar økningen fra 6 til 45 tapte lydtick. Kandidaten velges
derfor ikke til produksjon, selv om RAM-/registerkontrollene består og
20-romssummen er bedre. Raskere måling med flere tapte lydtick kan ikke
regnes som et ekvivalent forbedret resultat.

Dette målet er ferdig undersøkt. Ingen ny manuell test eller ny normal
EXE er levert. Full 53-fixturtest og normal CLI-/ADF-runde er ikke kjørt
for kandidaten, siden den ikke velges til integrasjon. Dagens ferdige
kompakte backend og dens tidligere validerte normalbygg beholdes.

Neste anbefalte avgrensning er å måle blokkering av lydservice under
tegning/venting og kontrollere feltfasen. Det arbeidet er ikke startet her.
En eventuell senere integrasjon av hurtigbanen krever nye timingkontroller,
fulltest og leveringsbevis. Sanntid, naturlig IRQ-fase, full gjennomspilling
og fysisk A500-godkjenning står fortsatt åpne.

Kandidat og kontroll er bevart under
`reference/analysis/sprite-disjoint-2026-10-30/`.
Generatorene er `tools/probe_disjoint_sprite_copy.py` og
`tools/build_disjoint_sprite_benchmark.py`. Begge bruker dagens kompakte
aktørkode; ingen tidligere eksperimentell backend tas tilbake.
