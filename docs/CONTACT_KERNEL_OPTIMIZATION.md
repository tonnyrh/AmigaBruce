# Kontakt- og VIC-kjerner, 27. oktober 2026

Utgangspunkt er `3b90e04` på `optimize/native-amiga-engine`.
Dette fortsetter [forrige native løft](NATIVE_ENGINE_OPTIMIZATION.md).
Spillregler, tre-felts kildeventer, grafikk og lyddata er uendret.

## Kildekontrakt

Frosset kandidat: `.reference/c64/work/untrained-memory.bin`, SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Remember/T64-kandidaten er fortsatt ikke sertifisert som urørt 1984-utgave.

- `$52AD–$5309` og `$530A–$537D`: målrettet O2 på små hjelpefunksjoner,
  uten global O2 på den store instruksjonsoversettelsen. Pointerforberedelsen
  skriver samme RAM og interne JSR-frames i samme rekkefølge. Mellomlagring
  av virtuelle A/N/Z/C/V som overskrives før bruk er fjernet. Ingen I/O-søm
  finnes inne i denne hjelpefunksjonen; slutt-A/X/Y og samtlige flagg beholdes.
  De opprinnelige separate instruksjonsinngangene beholder sin oversettelse.
- `$5380–$53CB`: 68000-kjernen leser tre maskerte pikselbaner i original
  rekkefølge, skriver `$4E` og de samme høye/lave nibbleslottene i
  `$4EED/$4F04/$4F1B`. Inntil åtte rader behandles per kall. Den stanser før
  nærmeste kropp-/fot-/delgrense: INY `$53CE`, CMP `$53CF/$53D4/$53D9` mot
  `$4F38/$4F39/$4F3A`. Den stanser også før neste **eksisterende Amiga-søm**
  ved Y delelig med åtte. Dette er ikke en påstand om at C64 har slike
  servicekall; naturlig IRQ-/rasterfase er fortsatt uavklart.
- Pixelkjernen kan bare skrive `$4E` og de seksten slottene i hver
  23-byte klassebane. Den kan ikke endre grensebytene `$4F38–$4F3A` inne i
  en blokk. Alle lesninger og skrivinger mellom banene forblir ordnet,
  også når glyphpekere peker inn i klasse- eller scratchområder.
  Pekere over `$FF00` bruker C-banen med eksplisitt 16-bits adresseomslag.
  Y-omslag og kroppen/foten beholder det opprinnelige returforløpet,
  inkludert `$542C/$542D` og fortsettelsen `$52A4`.
- `$5431–$55AA`: klasseoversiktene har samme fire eksakte OR-operandsamlinger
  fra `$545C/$54B2/$5508/$554C`. Generatoren leser instruksjonsoperandene
  direkte og grupperer bare sammenhengende bytes som faktisk inngår.
  Ord/langtord må starte på partallsadresse; ingen ekstra byte leses.
  Duplikatet `$4EFE` kan dedupliseres fordi resultatet er en boolsk OR.
  Native maskebit 0–3 svarer til `$4F3C–$4F3F`. Sammendragsbytes ender null,
  `$B6+X`, A=0, X, C/N/Z, øvrige flagg og stack er som tidligere. Midlertidige
  sammendrags-/maskeskrivinger har ingen observatør i denne I/O-modellen;
  hurtigbanen brukes fortsatt bare med aktørindeks under tre.
- VIC-sømmen følger fortsatt `$15B8/$25E2` og lesing av `$D01E` på blant
  annet `$29CE`. Bare rektangelparene mellomlagres ved eksakt samme aktive
  bits, X/Y og bredde-/høydeutvidelse. Bank, spritepekere og alle relevante
  63 bitmapbytes kontrolleres fortsatt hvert kandidatfelt. Låsen OR-es inn
  igjen etter lesing/tømming. Cachegyldighet nullstilles ved reset.
  Ingen nye treffbokser eller veggregler er lagt inn.

## Kontroller

3 953 kontaktkontroller kjører 2 066 781 faktiske C64-instruksjoner og
sammenligner hele RAM, registre, stack og retur. 489 forløp kontrollerer
registrene ved servicestedene. Nye tilfeller dekker scratch-/operand-/
tabellalias, SP=0/255 og rad-/pekeromslag gjennom kropp-/fotgrenser.

6 709 piksel-/latchkontroller inkluderer alle åtte spritebiter, null/treff,
endret geometri, bredde/høyde, høy X-bit, bitmap, bank og peker samt
akkumulering etter at latchen er tømt. Disse kontrollerer Amiga-sømmen;
de beviser ikke original raster-/grenseområdefase.

Native testbygg kjører 128 direkte 68000/C-sammenligninger av radkjernen
og 70 klassemaskeforløp, inkludert hver enkelt av de 69 klasseslottene og
nullmasken. Strukturstørrelse og byteoffset er compile-time-kontrollert.
Disse 198 kontrollene erstatter ikke de 53 opprinnelige native RAM-/
registerfixturene eller de 3 034 bytevise aktørkontrollene.

## Målemetode og resultater

Den nye målebanen stopper etter **360 faktiske kildespillsteg**, med 1 200
løkker som sikkerhetsgrense. `SourceSteps` finnes bare i testbygget.
Kildeventer/IRQ er uendret. Den tidligere ytre løkkestoppen er fortsatt
standard for andre tester. Bygg, rapporter og kildeidentiteter er bevart i
`reference/analysis/optimization-2026-10-27/`.

| Trinn | PAL-felt | Ytre løkker | Tegnede bilder | Tapte lydserviceticks |
| --- | ---: | ---: | ---: | ---: |
| Før, ny fast-steg-målebane | 1 689 | 368 | 326 | 21 |
| Målrettet kompilering | 1 670 | 382 | 328 | 20 |
| Færre midlertidige registre | 1 670 | 413 | 342 | 22 |
| VIC-rektangelpar gjenbrukt | 1 647 | 428 | 349 | 20 |
| 68000-radkjerne | 1 631 | 442 | 353 | 23 |
| Genererte klassegrupper | 1 614 | 442 | 352 | 29 |

Siste trinn har cirka **4,44 % kortere målt kjøretid** enn før denne runden
og cirka 8 % flere tegnede bilder. Alle rader har 360 kildespillsteg; ulikt
antall ytre løkker er venting/opptegning, ikke ekstra eller hoppede spillsteg.
Førmålingen stemmer godt med forrige leveranses 1 688 felt.

Profilert kontaktoppsett: 184,847 → 161,819 rasterlinjer i gjennomsnitt;
radbehandling: 22,264 → 16,954; VIC: 35,266 → 28,709. Profilen inneholder
målebokføring, og kilde-/IRQ-faser endres når faktisk kjøretid endres.
Dette er enkeltkjøringer i rom 1 med uttrykkelig testudødelighet og begge
fiender, ingen naturlig full gjennomspilling eller isolert CPU-syklustest.

**Lyd-/sanntidsporten er fortsatt åpen.** Sluttmålingen har flere tapte
lydserviceticks enn førmålingen (29 mot 21). Maksimalt servicegap og den
kontrollerte reprisen rapporteres separat. Lavere CPU-kostnad godkjenner
ikke manglende lydticks eller en strengere feltport som ikke er bestått.
Normal maskin er fortsatt PAL A500 OCS/68000/KS1.3 med 512+512 KiB.

## Native sluttest

53/53 originale RAM-/registerfixturer og 198/198 assemblerkontroller består.
Reprisen fullfører 1 200 løkker/400 spillsteg med 992 tegnede og 208 kort
holdte bilder, største holdrekke ett felt. Null kilde-, lyddekoder-, DMA-,
aritmetikk-, pikselkontroll- og kernel-feil; korrekt retur til AmigaOS.
Største ledige Chip-blokk er uendret 52 632 byte mot portens 49 152.

Den strenge feltporten er fortsatt ikke bestått: største gap er fem felt,
og 81 lydserviceticks mangler. Det er samme tall som forrige kontrollerte
reprise, et annet forløp enn PAL-målescenen i tabellen. Bildediagnosen har
fortsatt 42 HUD-bytes, 33 uforklarte scenebytes og null ventende kopier.
Ingen av disse åpne sakene godkjennes av lavere CPU-kostnad.

## Normalbyggets størrelse

Normal EXE er 341 744 byte, 584 mer enn utgangspunktets 341 160.
`.text` øker 620 byte (0x2edb4 → 0x2f020), rodata og data er uendret.
BSS øker netto åtte byte (0x29c48 → 0x29c50). Nye kernelkontekster er små
stackverdier; de oppretter ingen nye Chip-buffere. Faktisk sammenhengende
Chip-reserve verifiseres med native kjøring, ikke fra størrelsestall alene.

Normal CLI og faktisk ADF starter og fullfører ny spillstart. Begge
normalprøvene har null kildefeil. Tidlig prøve uten fiender ligger på tre
felt per steg; med begge fiender aktive ligger de tre korte intervallene
på cirka 4,6–4,8 felt per steg. Det er ikke et kontrollert A/B-par mot eldre
normalprøver. Tre felt med begge fiender er fortsatt ikke nådd.
Yamos synlig → skjult → tilbake består i begge bildebuffere i rom 2.
`start` i AmigaDOS er oppdatert til samme EXE som er testet.
