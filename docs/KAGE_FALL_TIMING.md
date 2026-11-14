# Falltreff på Kage i rom 1

Den videre undersøkelsen dekker også Yamos poengtildelinger og avlesingen
av joystick under kamp. [Feltarbeid på PAL A500](FIELD_WORK.md).

## Hva C64-koden gjør

I den frosne Remember/T64-kandidaten går Kage inn på `$2BF9` med X lik 2.
Når både bit 4 og bit 7 i `$BE` er satt, gir `$2C03` 50 poeng. Koden trekker
deretter fem fra helsebyten ved `$2C0C`. Er fortegnsbiten satt etter
subtraksjonen, gir `$2C40` ytterligere 200 poeng. Hoppet ved `$2C51` går
tilbake til samme treffbehandling. Å sette helsen rett til null ville gitt
både feil poengsum og feil fiendetilstand.

| Målt forløp | Helse inn → ut | Poeng inn → ut | Tildelinger | Omløp |
| --- | --- | --- | ---: | ---: |
| Treff ved steg 168 | 2 → 123 | 425 → 6 975 | 53 | 26 |
| Treff ved steg 207 | 3 → 124 | 6 975 → 13 525 | 53 | 26 |
| Treff funnet med joystick alene i VICE | 0 → 126 | 475 → 6 775 | 51 | 25 |

Ved hver tildeling har `$313A–$3144` tre separate bytevise sammenligninger.
Første byte under sin terskel avslutter testen. Ved ekstraliv oppdaterer
`$3146–$3157` terskelen og antall liv og kaller visningsrutinen. Amiga-koden
avslutter sammenslåingen før en slik tildeling. Siste ordinære 50/200-par
går gjennom hele rutinen og skriver også HUD, desimalarbeidsområde og stakk.
Desimalmodus, lave stakkpekere og andre aktører går gjennom den eksisterende
instruksjonsoversettelsen. Den avgrensede beregningen har ingen feltservice
inni seg i denne versjonen av motoren.

## Tid og inndata

VICE kjørte PAL med spillets egne maskinvareavbrudd. I de to matchede
prøvene ble Kages treff, helse, poeng, ekstralivsterskel og liv satt ved
spillets egen trefftest. CPU-en tok selv alle grener videre. I den tredje
prøven kom treffet etter 3 047 spillsteg med joystick fra startsnapshotet.
Minnebildets SHA-256 er
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Identiteten som urørt 1984-utgave er fortsatt åpen.

Fra `$2C03` til retur ved `$1C26` brukte VICE 178 693 sykluser i begge
matchede prøver, omtrent 181 ms. Ni spillavbrudd kjørte. Første avleste
retning kom etter omtrent 16 ms. Separat kjøring med holdt venstre og høyre
ga forskjellig Bruce-tilstand etter omtrent 188 ms. To repriser med høyre
ga identiske spor. I det joystickdrevne treffet tok returen omtrent 176 ms.
Der ga de to retningene samme Bruce-tilstand gjennom de første 16 prøvene.

I WinUAE ble retningen endret ved inngangen til treffet, før den ordinære
inndatabehandlingen. Med den nye kampberegningen kom første avlesing etter
14–15 ms, mot 66–68 ms i kontrollbygget. Ved steg 168 ga retningene
forskjellig tilstand etter omtrent 89–92 ms, mot 163–168 ms før endringen.
Ved steg 207 var Bruce i luften. Her kom forskjellen etter 468–514 ms, mot
602–610 ms før. Dette er emulert tid frem til tilstandsendring, og omfatter
ingen forsinkelse fra en fysisk kontroller eller skjerm. VICE-prøvene
matcher treffdataene. Bruce har ulik startposisjon og bevegelsestilstand
på de to plattformene. Eksakt paritet for respons i naturlig spill er åpen.

[Måleskript for VICE og WinUAE](../reference/analysis/kage-paula-2026-11-01/)
