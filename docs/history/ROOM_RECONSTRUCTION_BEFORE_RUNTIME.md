# Romrekonstruksjon før motorintegrasjon24.oktober

## Hva Amiga-versjonen faktisk gjør nå

`core/game.c` inneholder håndlagde plattformer og klatrerektangler for rom1–2.
`tools/build_room_geometry.py` lager rom3–20 ved å lete etter brede grafiske
overkanter og slå sammen forhåndsvalgte tegn-ID-er til nett-rektangler.
Den maskerer bort bit7 før dette arbeidet og bruker ikke originalens fulle
pikselkontakt eller romspesifikke programkode.

`tools/build_room_backgrounds.py` tegner disse flatene som enkle bjelker og
rutenett over samme fjellbakgrunn. Den lager fire bitplan, pakker dem og lar
Amigaen laste dem i to bakgrunnsbufferplasser. Figurene kommer fra separate
AI-genererte ark. Rommene er derfor foreløpige blokkrom, ikke gjengivelser av
C64-rommenes komplette oppbygning. Pakkingens roundtrip-test bekrefter at
våre egne bilder kan pakkes ut riktig; den bekrefter ikke C64-samsvar.

## Kildene som er kontrollert

- `5k3105/bruce`, commit25cf80529f91db064692a9cba9a4621b31828fd5:
  C64-data, editor og delvis disassembly. Alle20 `map_original/level*`-
  strømmer er byteidentiske med romstrømmene i vår frosne C64-kandidat.
  README sier at editorbyggingen ignorerer original romkode. Derfor må
  init-/løplogikk hentes fra originalbinæren, ikke editorens testspill.
- `jzielinski47/bruce-lee`, commitb0d8b616bcf18d4bf78b5f5e3ebe3c17d5392030:
  README beskriver en Atari-basert TypeScript-rekonstruksjon. `scenes.ts`
  bruker egne rektangler; `Background.ts` viser JPG-bakgrunner. Dette er
  nyttig sammenligningsmateriale, men fastsetter ikke C64-mekanikk.

Den registrerte C64-kandidaten er fortsatt ikke bekreftet som valgt urørt
1984-utgave. Alle adresser og funn her gjelder denne identifiserte binæren.

## Hva originalkoden forteller

Den uavhengige lesemodellen i `tools/c64_room_model.py` bygger på følgende
kode og tabeller, ikke på hvordan vi tror et plattformspill bør fungere:

| Del | Originalkode / data | Betydning |
| --- | --- | --- |
| Rompekere | `$4B34` / `$4B49` |20 komprimerte romstrømmer |
| Dekoder | `$0AD7–$0B2D` | Repetisjoner og literalblokker; `$80` avslutter |
| Celler | `$0AEA–$0AEE`, `$0B12–$0B16` | Hver celle gir øvre tegn og nedre tegn med bit7 satt:8×16piksler |
| Attributt | `$0B5F–$0B69` | Cellens bit7 velger svart attributt `$F8`; det er ikke del av tegn-ID-en |
| Standardfarge | `$09DA–$09EF`, `$47A0+rom` | Romavhengig farge før svarte overstyringer |
| Tegnsett | `$0A9B–$0AAD`, `$15D0–$15EC` | R01–R10:`$A000`; R11–R18/R20:`$A800`; R19:`$B000` |
| Pikselkontakt | `$5212–$572C` | Figurens kildemaske mot tegnpiksler og fargeattributt; kropp og hel figur får separate resultater |
| Objekter | `$2E39–$312B` | Dører, lanterner og spesial-/faretegn, med ytterligere betingelser |
| Romprogrammer | `$4E9C`, `$4EC4` og dispatchkode | Egne init-/løprutiner endrer rommet under spill |

Synlig romfelt består av40×11celler fra skjerm-y24:320×176piksler under
C64-statusområdet. Spillkoordinater, synlig felt og Amigaens ekstra32-pikslers
HUD må holdes fra hverandre. `$1C39` har dessuten egen Y-justering for R14;
en generell global gulvforskyvning er derfor ikke en kildetro rettelse.

Den opprinnelige pikselkontakten gir følgende bitklasser. Betydningen må
leses sammen med bevegelses-/objektgrenen som bruker biten:

| Tegnets2-bitspiksel | Kontaktbit | Kodebasert bruk |
| --- | --- | --- |
|00 |0 | Ingen pikselkontakt |
|01 |1 | Brukes i overflate-/bevegelsestester |
|10 |2 | Brukes som betingelse for blant annet lanterne-/farekontakt |
|11, fargens lave3bit er0 |8 | Svart blokkering; blant annet `$1CC7` tester bit8 |
|11, fargens lave3bit er ulik0 |4 | Annen kontaktklasse, blant annet brukt ved klatring; enkelte tegn har særregler |

Det er derfor feil å likestille et bestemt bilde med Â«gulvÂ» eller Â«nettÂ»
uten attributt og kode. Tegn`$62` går for eksempel til egen kontaktkode
`$310C`, ikke bare en generell nettfunksjon. Farger og pikselmønstre er en
del av logikkdataene, selv om Amiga-versjonen senere får helt annen kunst.

## Nytt, konkret analysegrunnlag

Primærkontrollen er `python tools/inspect_c64_room_code.py`: den leser den
frosne binæren, disassemblerer relevante rutiner og kontrollerer11 konkrete
instruksjonssteder samt init-/løpadressene for alle20 rom. Ingen6502-
instruksjoner kjøres i denne kontrollen. Se
[kodekontrollen](../reference/validation/c64-room-code.json) og det lokale
adresse-/byte-/instruksjonsuttrekket i
`.reference/c64/room-reconstruction/room-code.txt`.

`python tools/audit_c64_room_model.py` lager en separat rekonstruksjon:

- Alle20dekodede rom er sammenlignet med den faktiske6502-dekoderen.
-20kontroller av piksel-/fargeklassene og3000kontaktkontroller sammenligner
  den kodeavledede lesemodellen med originalens kontaktfunksjon i en CPU-modell.
  Dette er supplerende regresjonskontroll, ikke maskinvare-/timingfasit.
-276brukte statiske tegn er katalogisert med bank, ID, fargevarianter,
  rombruk og kildehash. Ulike banker og attributter beholdes.
- Tegnbilder, komplette kart og kontaktbilder ligger kun i lokal
  `.reference/c64/room-reconstruction/`. Sammenligningsbildet viser C64-
  tegnlayout, kontaktklasser og nåværende Amiga-blokkrom ved siden av hverandre.
  Fargene er diagnostiske; originalens rasterfarger emuleres ikke i bildet.

[Analyserapport](../reference/validation/c64-room-reconstruction.json) og
[tegnkatalog](../reference/validation/room-tile-catalog.json) inneholder fakta
og signaturer. Kildeminnet er et frosset snapshot; animerte tegn er i snapshotets
fase. Init-/løprutiner og IRQ-farger er ennå ikke rekonstruert av dette verktøyet.
Ingen Amiga-spillfiler eller produksjonsressurser endres når analysen kjøres.

## Prioritert videre arbeid

Brukerbeslutning24.oktober er lagret i rotens `AGENTS.md`: originalkode og
kildedata styrer alle detaljer. Ukjent oppførsel avklares i disassembly og
binærkode; egen simulering eller grafisk gjetning fastsetter ikke regelen.

1. Følg hvert roms init-/løprutine og registrer tilstand, tellere, endringer
   av tegn, attributter og tegnsett, samt dørenes faktiske betingelser.
2. La Amiga-motorens kontakt, objekter og romendringer bruke samme dokumenterte
   rommodell. Erstatt håndlagde overflater og ID-baserte nettantakelser.
3. Kontroller øvrig bevegelse, kamp, fiender og progresjon mot originalkode.
   Uavklarte grener forblir åpne; midlertidige løsninger merkes som slike.
4. Lag ny kunst fra katalogiserte romdeler når denne strukturen er korrekt.
   Sammenhengende tak, vegger og statuer kan forbedres samlet og deles i tiles
   etterpå, med bevarte skjøter og uavhengig kollisjonsdata. Grafikk og lyd
   har nå lavere prioritet og kan ferdigstilles til slutt.

De gamle native testene dokumenterer at den nåværende prototypen starter,
holder minne-/tidsbudsjett og besøker rom. De godkjenner ikke blokkrommene som
korrekt C64-geometri. Denne analysen har ikke oppgradert statusen til full M4.
