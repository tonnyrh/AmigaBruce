# Neste A500-ytelsesrunde — 27. oktober 2026

Spillet var merkbart tregt i normal WinUAE-kjøring. Denne runden reduserer
beregningskostnad uten å endre kildeklokke, kampvinduer, spritepiksler eller
den C64-baserte spillrekkefølgen. [Tidligere måling](CONTACT_OPTIMIZATION.md)
er førpunktet. Full sanntidsakseptanse står fortsatt åpen.

## Kilde og ekvivalensgrense

Referansen er de urørte bytene i
`.reference/c64/work/untrained-memory.bin`, SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Remember/T64-kandidaten er ikke sertifisert som valgt urørt 1984-utgave.

- Den eksisterende `$D01E`-grensen bruker C64s aktive sprites, X/Y,
  X/Y-utvidelse, flerpikselflagg, bank, pekere og alle63 bitmapbytes.
  En akkumulert latch tømmes bare når kildekoden leser `$D01E`.
- Rektangler brukes kun til å utelukke par som fysisk ikke kan dele
  piksler. Et mulig par beholder full pikseltest. Bitmap for sprites uten
  mulige par sammenlignes på nytt når de senere blir kandidater. Skifte av
  aktiv maske, posisjon eller høyde ugyldiggjør gjenbruk av resultatet.
- Den frosne kontakt-radløkka `$537E–$53CE` leser pekeroperandene ved
  `$5381/$539B/$53B5` én gang mellom servicepunkter. Kilden skriver bare
  klasseflagg i `$4EED–$4F2A` i disse radene. Pekerne leses om igjen etter
  hvert feltservicepunkt som kan ha endret kildeminnet. Datalesning og
  skriving i de tre banene skjer fortsatt i original rekkefølge.
- C64s spritepeker danner en64-byte-justert adresse innenfor64 KiB.
  Amiga-koden sammenligner de første60 bytene som15 justerte 68000-langord
  og de siste tre som bytes. Cache-raden er64 byte bred og justert; byte64
  teller ikke. Ikke-justerte eller grensetilfeller bruker bytebanen.
  De samme kildebytene bestemmer dermed resultatet; ingen ny hitboks brukes.

Dette er en feltbasert VIC-modell. Naturlig rasterfase og C64-maskinens
grenseområde er ikke sertifisert av pikselkontrollene.

## Målt virkning

Begge native målinger bruker PAL OCS/68000/KS1.3 med512 KiB Chip +512 KiB
slow,360 spillsteg i rom1, ingen joystickinput og udødelighet som eksplisitt
testutvidelse. De bruker normal PAL-planlegging og ingen profileringsmåling
i tidsløpet. Det er én måling per kandidat, ikke en statistisk garanti for
alle rom eller naturlig gjennomspilling.

| Måling | Før denne runden | Sluttvariant |
| --- | ---: | ---: |
| Medgått PAL-tid i benchmarken | 2 857 felt | 2 325 felt |
| Spillsteg | 360 | 360 |
| Tegnede nye bilder | 360 | 360 |
| Manglende lydserviceticks | 210 | 96 |
| Største ledige Chip-blokk | 52 632 byte | 52 632 byte |

Målt tidsreduksjon er18,6 %. Tittelsekvens og oppstart er med i feltallet;
det er ikke en direkte FPS-måling av bare aktivt spill. Et separat kort
normal-klokkeuttak av slutt-EXE-en etter oppstart viste120/118/118 PAL-felt
og24/21/22 spillsteg, mot omtrent119 felt og19 steg i en tidligere prøve. Prøvene er
ikke låst til samme fiendetilstand eller inputfase, så de brukes som kontroll
av faktisk fremdrift, ikke som et kontrollert ytelsespar. Brukeropplevelsen
må fortsatt testes på nytt.

Råbygg og identiteter ligger under
`reference/analysis/optimization-2026-10-27/`. Kandidatene ble målt i
`vic-candidate-timing/`, `vic-contact-candidate-timing/`,
`vic-bytecompare-candidate-timing/`, `vic-m68k-candidate-timing/` og
`vic-final-timing/`. Etterfølgende terskel- og pointereksperimenter ga
ingen netto gevinst og ble fjernet. Forsøk på `-O2` for hele aktørmaskinen
økte test-EXE-en omtrent64 KiB og fullførte ikke på målmaskinoppsettet;
den varianten er forkastet og dokumentert i `actor-o2-candidate-timing/`.
Bare VIC-rutinen får målrettet `-O2`; hele motoren forblir på `-Os`.

## Kontroll og rest

Vertskontrollene omfatter2 248 kontaktforløp mot706 112 faktiske
C64-instruksjoner og6 485 VIC-piksel-/latchtilfeller. Native autotest
sammenligner assembleren med identiske bytes og ett ulikt byte på hver av
de63 relevante posisjonene, samt et ulikt64. byte som skal ignoreres.
Native kontrollen bestod53/53 RAM-/register-fixtures,1 200 løkker/400
logiske steg, og65/65 assembler-tilfeller. Ingen kilde-, lyd-, DMA-,
gjengivelses- eller aritmetikkfeil ble rapportert; AmigaOS-retur var riktig.
Største sammenhengende Chip-blokk var52 632 byte. Av1 200 felt ble1 081
nye bilder tegnet og119 holdt, største holderekke1 felt. Lydservice
manglet100 ticks, mot241 i forrige native kontroll. Største vanlige
feltgap var7, mot8. Bildet har fortsatt42 HUD-bytes og33 uforklarte
scenebytes; ventende bakgrunnskopi forklarte0 av disse i denne kjøringen.

Normal EXE er336 260 byte, SHA256
`30e1736b287c20859c028a64e1b5b591b6a2ded0b58ce2c075fb28b103fcdf0f`.
ADF er901 120 byte. Mot forrige EXE er dette416 byte mindre; BSS økte
12 byte, til `0x29C48`. Faktiske bitplanes fra normal kjøring er lagret som
[rom1-kontroll](images/session-vic-native-final-running.png).

Samtidig lydservice har fortsatt manglende ticks. Full PAL-kadens,
naturlig spilling gjennom alle rom, C64s rasterfase, scene-restbytes og
fysisk A500-akseptanse er åpne. Videre ytelsesarbeid må rette seg mot den
dyre `$537E`-raden og den oversatte hovedkjeden med små dokumenterte
spesialiseringer; å endre tre-feltsrytmen ville endre C64-resultatet.
