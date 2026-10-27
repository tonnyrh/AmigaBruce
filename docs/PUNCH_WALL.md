# Ståretning ved boksing nær venstre vegg

26. oktober 2026. Denne typen vending finnes i C64-koden vi bruker som
referanse. Den kommer fra den generelle vegg-/historikkgrenen, som kjøres
før handlingsvalget. Selve slagvalget gir ikke en ny ståretning.

Kilde: uendret `.reference/c64/work/untrained-memory.bin`, SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Remember/T64-kandidaten er ikke bekreftet som urørt 1984-utgave.

## Betingelser og effekt fra maskinkoden

- `$1C68–$1C9A` flytter bevegelseshistorikken når det finnes en forflytning.
- `$1CC7–$1CCD` tester svart kontakt med `$B6 & 8` før vanlig handling.
- `$1CF0–$1CFA` angrer tidligere venstreflytting med høyrehjelperen `$1EC4`.
  Når flyttingen godtas, setter `$1ECA–$1ED1` både X og `$A4=1` (mot høyre).
  Motsatt retning bruker `$1E86` og setter `$A4=0` ved godkjent venstreflytting.
- `$1D66–$1D6C` går deretter til veggrestitusjon 24/teller 64. Den ordinære
  slaggrenen blir ikke valgt i denne oppdateringen.
- `$1F76–$1F86` velger slag17 ved nøytral retning, ild og uten nettkontakt.
  Denne grenen skriver ikke `$A4`. `$226A–$22BC` er den videre slaggrenen.

Veggkontakten kommer fra gjeldende figurmaske i den neste aktøroppdateringen.
Derfor kan vendingen bli synlig akkurat når man slipper venstre og trykker
ild etter et steg inn i veggen. Samme veggkontakt kan snu Bruce når man bare
slipper retningen. En synlig vegg eller et slag alene er ikke nok; masken og
den faktiske kontakten/historikken bestemmer utfallet.

## Kontroll i rom6

`python tools/audit_punch_wall.py` kjører fire kontrollerte inputforløp fra
`(60,196)`, vendt venstre, på rom6s kildegeometri. 140 steg sammenligner
faktiske 6502-bytes med Amiga-kjernens vertskjøring: X/Y, ståretning, positur,
kontakt og veggtilstand/teller.

Etter 12 venstresteg står Bruce på `(2,196)`. I neste oppdatering gir både
**ild uten sideretning** og **sluppet joystick** svart kontakt $09 og samme
utfall: `(8,196)`, mot høyre, veggtilstand 24/teller 64. I kontrollene som
stopper tidligere og bokser uten svart kontakt, beholdes venstre ståretning.

Dette er kontrollerte starttilstander med statisk romgeometri, ikke et opptak
av naturlig C64-spill. Romløp, IRQ og kamp mellom figurer kjøres ikke her.
Skjermbildet alene fastsetter ikke brukerens eksakte forhistorie. Kontrollen
viser at den beskrevne typen vending følger samme kildegren i begge kjerner.
Spillkoden og den kjørende Amiga-utgaven er ikke endret av undersøkelsen.

[Rapport](../reference/analysis/punch-wall-2026-10-26/report.json) ·
[Disassembly](../reference/analysis/punch-wall-2026-10-26/source-disassembly.txt).
