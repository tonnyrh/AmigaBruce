# Rombytte på A500

26. oktober 2026. Rombytte og full romopptegning var unødvendig dyrt i
Amiga-rendereren. Den tidligere målingen på 102 PAL-felt inneholdt også
testprogrammets fulle pikselkontroll. Den skal ikke brukes som en ren
tidsmåling av normalutgaven eller som en målt sammenligning med C64.

## Endring

- Kontakt-/spredningstabellene bygges én gang. De avhenger bare av byteverdien.
- Fargetabellen deles i palettavhengig bakgrunn og uavhengig forgrunn.
  Selve tabellene bruker 23 KiB mindre CPU-RAM og trenger færre beregninger.
- Bakgrunnsdelen av piksel-/bitplantabellen gjenbrukes etter eksakt sammenligning av alle 12
  effektive palettfarger. Rasterbånd og linjefarger oppdateres ved hver lasting.
- Det eksisterende DMA-området for rullende nett kan gjenbrukes når buffer,
  kapasitet, 24 mønsterbyte, 12 palettfarger, 200 rasterbånd og alle animerte
  cellers tegn/farger stemmer. Endringer gir ny bygging. Ingen ekstra stor
  bakgrunnsbuffer eller DMA-cache allokeres.
- Ved ny bygging brukes ferdige kildevarianter og løpende pekere. Det
  erstatter gjentatt mønsterberegning og offsetmultiplikasjon per utbyte.

Kollisjon bruker fortsatt kilde-RAM og kildemasker. Ingen romtilstand,
lanterne, dør, fiendebeslutning eller inngangsterskel bestemmes av grafikkcachen.
Kildens last-/init-/løprutiner kjøres som før.

Kildegrunnlag: uendret frosset kandidat, SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Romlastingen starter ved `$0A9B`, palettpekere ved `$480B`, rasterpekere ved
`$4833`, og rullende tegn følger `$2C70–$2D54` med tabeller `$42F1/$4309`.
Kandidaten er ikke bekreftet som urørt 1984-utgave.

## Målemetode

`test-amiga.ps1 -RoomLoadTest` bruker 29 kontrollerte romvalg på 900 ytre
spilløkker, med alle 20 rom, returer og samme-rom-lasting. Det er en
ytelses-/renderkontroll, ikke naturlig dørrute eller gjennomspilling.

`-RoomLoadBaseline` kjører den tidligere beregningsbanen som kontroll.
Kontrollbyggets kilde og binær er bevart i
[baseline-mappen](../reference/analysis/room-load-2026-10-25/baseline).
Begge moduser bruker samme romrute på PAL 68000/OCS, Kickstart1.3 og
512+512 KiB RAM. Den optimaliserte utgaven har i tillegg den delte
fargetabellen; filidentitetene beskriver hvilke kilder hvert bygg brukte.

Rapporten skiller kilde-/aktørarbeid, statisk opptegning, pikselkontroll,
animasjonsforberedelse og HUD. `room_event_*_work` er summen av målt arbeid
uten testens pikselkontroll; det er ikke hele veggklokketiden fram til neste
synlige bilde. Skjermkopiering/blanking og øvrig feltarbeid kommer i tillegg.
Rå feltgap og kontrollkostnaden beholdes separat. PAL-linjetelleren gir
måleenhet; kilde-/inputforløp og bildepiksler kontrolleres separat.

23 målrettede vertskontroller prøver blant annet endrede farger, raster,
rullemønster, tegn, cellefarger, tegnsett, buffer og kapasitet. De bruker
kontrollerte RAM-endringer og endrer ingen originale referansefiler.
[Vertskontroller](../reference/analysis/room-load-2026-10-25/host-reuse.json).

## Resultat fra A500-kjøring

Én kontrollkjøring og to optimaliserte CLI-kjøringer er fullført. Hver
kjøring har 29 romvalg, 900 ytre spilløkker og 30 kilde-/bildekontroller.
Alle 20 rom inngår; de tidligere 430 nett-, 324 sprite-, 390 klatre-, 70
bevegelses-, 29 objekt-, 24 NPC-rekyl- og livs-/menykontrollene passerer også.
Det native bildet ved målepunktet er pikselidentisk før og etter.

| Målt størrelse | Kontroll | Optimalisert 1 | Optimalisert 2 |
| --- | ---: | ---: | ---: |
| Samlet forberedelsesarbeid, HSync-tikk |793045 |628025 |628019 |
| Gjennomsnitt per romvalg, HSync-tikk |27346 |21656 |21656 |
| Lengste forberedelse, HSync-tikk |67783 |45289 |45294 |
| Største ledige Chip-blokk etter lasting, byte |60832 |85408 |85408 |
| Avvik i kilde-/rombilder |0 |0 |0 |

Forberedelsesarbeidet er **20,81% kortere** i begge optimaliserte kjøringer.
I det kontrollerte samme-rom-tilfellet i rom5 er arbeidet omtrent 46% kortere.
Tallene holder testens ekstra pikselkontroll utenfor. Med den nominelle
PAL-linjetiden 64 µs i [tidsmodellen](MOVEMENT_TIMING.md) tilsvarer gjennomsnittet
omtrent 1,75→1,39 sekunder arbeid per romvalg. Dette er en omregning av
arbeidsmålingen, ikke en separat måling av hele den synlige overgangen.

Spillprogrammet er 206720 byte; ingen ekstra stor DMA-buffer er lagt til.
Rå feltgap, kontrollkostnader, kilde-/byggidentiteter og avgrensninger er
bevart i [leveranserapporten](../reference/validation/room-load-delivery.json).

Den strenge 50Hz-porten er fortsatt åpen: inspeksjonsruten har 32/29 tapte
oppdateringer og største ordinære oppdateringsgap 3 felt. Målingen av
romforberedelsen godkjenner ikke hele spillets feltkadens.

Naturlig rombytte og hele M4 er fortsatt åpne til sine egne krav er oppfylt.
Se [milepælstatus](PROJECT_PLAN.md#nåværende-leveranse--m4-kandidat-26-oktober-2026)
og [aktive tester](ACTIVE_TESTS.md).
