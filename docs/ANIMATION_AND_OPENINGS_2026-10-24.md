# Flere animasjonsfaser og veien videre fra rom 3

Denne teksten beskriver den første animasjons-/åpningskandidaten.
Se [nyere Yamo- og HUD-korrigering](YAMO_AND_HEALTH_HUD.md) for grønn hud,
kraftigere kropp og navngitte helsefelt. Tallene nedenfor er den tidligere
byggen; `reference/validation/visual-candidate.json` viser seneste målinger.

Ny figurkunst ligger i `assets/graphics/v2/`. Hver figur har 16 bildeplasser:
fire løpefaser, fire klatrefaser, hvile, opptrekk, treff, retur, tre
sparkfaser og liggestilling. Ninja bærer en lang bambusstav og bruker
begge hendene ved stikk. Han bærer staven på ryggen ved klatring.

Bruce klatrer med vekslende sider uavhengig av hvilken vei han sist vendte.
Genereringen gjentok samme side i to klatrebilder; motoren bruker derfor
speilvendt visning av motsatt halvsyklus. Dette er en visningstransformasjon,
og endrer ikke retning, klatrefart, angrep eller kollisjon. Syklusen følger
vist høyde: den stopper når han stopper og går baklengs ved nedklatring.

Alle bilder bruker 48 × 26 piksler med fast anker 24,25, én delt palett
med 16 OCS-farger og transparensindeks 0. Den bredere flaten gir plass til
Ninjas stav. Pakkede bilder tar 29 952 CPU-byte; utpakkede bitplan og masker
tar 74 880 CPU-byte, mot tidligere 218 400. En 2 304-byte Chip-buffer brukes
til DMA. Vanlig plassering bruker blitterens A-/B-skift; skjermkantene
forskyves først til en midlertidig Chip-flate og klippes etterpå. Den første
CPU-klippingen overskred PAL-budsjettet i kamptesten og er erstattet.
Minnet og PAL-budsjettet kontrolleres på 512+512-profilen.
Sammen med de større pakkede bildene er selve figurdataene redusert fra
227 136 til 104 832 byte, før små metadata- og kodeforskjeller.

Bakgrunnen gjenopprettes bare innenfor figurens faktiske gamle bildegrenser.
Ved testbildet kontrollerer motoren at det ikke finnes endrede byte utenfor
de gjeldende figurflatene og helseindikatorene. Dette fanger tegnespor etter
gamle positurer; det er en grafikkontroll, ikke en test av C64-treffmasker.

Originalprompter og korrekturprompt er lagret i `generation.json`, og
utsnitt, ankre og kildehash i `fighters-manifest.json`. Den gamle v1-kunsten
beholdes. Dette er friere Amiga-animasjon etter brukerens ønske; det er
fortsatt ikke en full oversettelse av alle originale spritekomponenter.

## Kildeavstemt progresjon

Romnummer her er 1–20. C64-koden bruker indeks 0–19.

| Åpning | Betingelse i C64-kandidaten | Videre til |
| --- | --- | --- |
| Gulvluke i rom 2 | Alle 6+6+10 lanterner i rom 1–3 tatt; rom 7 har fortsatt lanterner | Rom 6, x64/y50 |
| Øverst i rom 6 | Rom 7 tomt og minst én av de to angitte øvre lanternene i rom 6 tatt | Rom 2, x152/y102 |
| Nederst til høyre i rom 3 | Rom 7 tomt | Rom 4, x8/y196 |
| Nederst til venstre i rom 6 | Den venstre nedre lanternen i rom 6 tatt | Rom 5, x288/y81 |

Å ta bare lanternene i rom 3 skal dermed ikke åpne høyre utgang der.
Først åpnes gulvluken i rom 2 etter alle 22. Etter rom 7 går turen tilbake
via rom 6 og rom 2, til den nye åpningen i rom 3. Luken og returportalen
utløses ved kontakt; en ekstra ned-knapp er ikke nødvendig.

Det var en faktisk mangel i Amiga-motoren: den hentet bare dører som
fantes i rommets statiske tiles. Disse dynamiske dørene var dermed borte.
Åpningene tegnes nå synlig, og bakgrunnscachen fornyes også ved gjenbesøk
når betingelsene har endret seg. Gulvluken lukkes igjen når rom 7 er tomt,
slik rom 2-koden bestemmer ved innlasting.

`tools/analyze_c64_openings.py` sjekker kandidatens tellere, instruksjoner,
strenger og destinasjonstabeller. Resultatet ligger i
`reference/validation/candidate-openings.json`. Viktige kildepunkter er
`$3679`, `$36AE`, `$38CB`, `$38E8`, `$39AA` og dørkontakt ved `$2E89/$2F51`.
Nullside `$30` er antall gjenværende lanterner i rom 7, ikke en felles
tellervariabel for de første rommene.

Begge de medbrakte repoene er inspisert og commit-låst i rapporten.
`5k3105/bruce` inneholder C64-disassemblyen. `jzielinski47/bruce-lee`
beskriver seg selv som en Atari-basert nettleserimplementasjon fra video
og emulator. Dens 22-lanterner-luke støtter tolkningen, men romkoblinger
og AI derfra brukes ikke som C64-fasit.

## Avgrensning og tester

Åpningene kommer umiddelbart i denne kandidaten. C64s firetrinns
lukeanimasjon, eksakt åpningstid, pixelmasker og dynamiske fiendeutganger
er ikke sertifisert. Øvrige romspesifikke bevegelige objekter, feller og
sluttsekvens gjenstår. Full M4/M5 er fortsatt ikke godkjent.

`tests/gate_fixture.h` setter opp kjente kontaktposisjoner og kjører vanlig
progresjonskode. Verten og 68000 må bekrefte 7 kontrollpunkter, 3
overganger, 31 innsamlinger og 3 875 poeng. Hver av de 22 forutsetningene
for gulvluken testes også enkeltvis som manglende. Dette viser at
utløserne virker, ikke at alle rommenes foreløpige geometri kan spilles
naturlig fra start til slutt.

Manuell retest: klatre opp/ned og stopp midt i nettet; vurder vekslende
armer/bein og Ninjas stav; spill 22-lanterner-ruten via rom 2 og kontroller
returen etter rom 7. Tidligere godkjente tester forblir godkjent for nå.

De ferske native kontrollene er lang ADF-kamp, første romoverganger,
20-romsturen og to CLI-kjøringer av åpningsruten. CLI-kjøringene kontrollerer
også at minnet er likt før begge starter, etter full opprydding. Gamle
rapporter fra den passive bevegelseslabben og den tidligere korte
kampdiagnosen beholdes som historikk; de regnes ikke som ferske v2-kjøringer.
`tools/verify_visual_candidate.py` og `tools/verify_combat_audio.py` krever
hashene fra de ferske profilene, ikke en omskriving av gamle rapporter.
Vanlig spillarbeid må rekke én PAL-periode; testens eksplisitte
skjermdumpkontroll og romlasting måles separat som pauser.

Ferske resultater på PAL A500 OCS/68000, 512 KiB Chip + 512 KiB slow:

| Profil | Kjøringer og rammer | Maks vanlig arbeid, rasterlinjer | Tegnespor utenfor figurene |
| --- | --- | --- | --- |
| ADF-kamp | 1 × 6 000 | 300 | 0 byte |
| Åpningsrute, CLI | 2 × 900 | 212 / 213 | 0 byte |
| Første romoverganger, ADF | 1 × 900 | 219 | 0 byte |
| Alle 20 rom, ADF | 1 × 7 200 | 232 | 0 byte |

Alle fem kjøringer gjenopprettet systemet og holdt én PAL-periode for
vanlig spillarbeid. De to CLI-startene hadde identisk ledig minne før start.
Eksplisitt Chip-bruk var 172 228 byte, og største gjenværende Chip-blokk var
minst 265 952 byte. Figurcache tok ingen Chip RAM. Romturen besøkte alle
20 rom med 19 innlastinger; lengste romlastingspause var 26 PAL-perioder.
Kampens 69 lyder fikk korrekt overgang til stillhet, uten bortfall.

Den vanlige utgaven er 183 320 byte som Amiga-program, med en 901 120-byte
ADF. `start` i AmigaDOS er oppdatert til samme program. Ferske kilde- og
artefakthasher samles i `reference/validation/visual-candidate.json`.

Blitterplasseringen følger Commodores beskrivelse av
[A-/B-skift og carry mellom ord](https://www.amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node011F.html).
Nullord ved radslutt og nulling av dataregistrene etter valg av skift
hindrer at biter fra forrige rad eller figur lekker inn i neste tegning.
