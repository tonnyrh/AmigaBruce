# Rom 13: hyppig fiendeinntreden

Brukerfunn 30. oktober 2026: stort fiendepress ved første avsats i rom 13.
Denne gjennomgangen endrer ingen spillregel, produksjonskode eller EXE/ADF.

Kilde er de faktiske bytene i den frosne Remember/T64-kandidaten, SHA-256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Kandidaten er fortsatt ikke sertifisert som urørt 1984-utgave.

## Rommet har korte tellere i C64-dataene

GUI-rom 13 er kildeindeks 12. `$0A3F–$0A69` bruker romindeksen til å lese
første tellere fra `$130B/$1347`. Fjerning og senere inntreden bruker
returtabellene `$131F/$135B` gjennom `$0D42` og spawn-tjenestene.

| Rom | Første Kage | Retur Kage, grunnverdi | Første Yamo | Retur Yamo, grunnverdi |
| --- | ---: | ---: | ---: | ---: |
| 1 | 104 | 160 | 240 | 238 |
| 13 | 4 | 4 | 32 | 32 |

Alle tall er hovedløkkeoppdateringer, ikke PAL-felt eller komplette
fiendeliv. Rom 13 har den korteste positive Kage-grunnverdien blant rommene
med aktiv spawn-tjeneste i denne binæren. Kages innledende aktørteller og
Yamos innkomstsekvens kommer i tillegg; en komplett døds-/retursekvens skal
ikke beskrives som bare fire eller 32 oppdateringer.

Tabellkoordinatene `$4BAE/$4BC2/$4BD6/$4BEA` er x24/y92 og x200/y92.
Begge inngangene er dermed på samme høyde ved første avsats. Valget følger
originale gater og RAM-avlesning, ikke en jevn tilfeldig fordeling.

## Gater og tidsenheter

- `$0DA4–$0DB0` dekrementerer `$5D/$5E` én gang i hovedløkkens
  tjenestepass. Den kjører også mens en fiende er aktiv.
- `$0D0F–$0D19` og `$0DD7–$0DDD` krever at den respektive aktørens bit 0
  er null før en ny inntreden. Teller 0 lager ikke flere aktive kopier.
- `$0DB1–$0DD6` kan sette Kages teller til 16 når Yamo er aktiv, runden og
  alderen er riktige, og RAM-leseren `$1159` gir minst 25. Denne grenen
  ligger før Kages egen aktivtest og beholdes også når Kage allerede er aktiv.
- `$3001` fjerner en fiende og kaller den felles returtellerbehandlingen.
  Klokkehi `$88` 25–31 gir halv grunnverdi: 2/16 i rom 13. Fra 32 blir
  returverdiene 3/3. Senere runde gir også 3/3 utenfor halveringsintervallet.
- `$1614–$1626` oppdaterer romalderen per aktivt felt. Det er en annen
  tidsenhet enn spawn-tellernes hovedløkkesteg.

Ved ideell tre-feltskadens er fire oppdateringer nominelt 0,24 sekunder
og 32 oppdateringer 1,92 sekunder, før øvrige gater/animasjonsfaser.
Klokkehi 25 og 32 tilsvarer nominelt 128 og 163,84 sekunder med aktive
PAL-felt. Dette er omregning av kildeenhetene, ikke målte intervaller fra
brukerens spilløkt.

Amigaens lavere oppdateringsfart kan påvirke forholdet mellom framdrift og
den feltbaserte opptrappingen. Det er en mulig forklaring på større press
før man kommer videre, men denne undersøkelsen måler ikke brukerens rute
eller beviser at dette er årsaken til observasjonen.

## Ny kontroll av gjeldende port

`tools/audit_r13_spawn_pressure.py` sammenligner 12 kontrollerte sekvenser
mot faktisk 6502-kjøring: første/senere runde, klokkehi 0/25/32, og
RAM-lesergrenen under/over utsettelsesgrensen. Hver sekvens omfatter
rominitialisering, 40 tjenestepass, fjerning av Kage mens Yamo er aktiv,
24 pass, deretter fjerning av Yamo og 36 nye pass.

Det er 1200 tjenestepass og 3697 komplette RAM-/registersammenligninger
med 267118 originale instruksjoner. Ingen avvik ble funnet. I den første
rundens alders-0-prøve uten utsettelse fødes Kage på pass 4 og Yamo på
pass 32. Kages retur etter fjerning er pass 4; med den kontrollerte
utsettelsesgrenen venter han i stedet mens Yamo forblir aktiv.

60 separate kall til den **aktive** feltkjeden sammenlignes også med
originalens IRQ-fragmenter. Ingen aktører er aktive i denne delprøven.
Tellerne forblir 4/32 gjennom alle 60 felt mens romklokken går fram.
Det er dermed ikke funnet en ekstra feltvis spawn-nedtelling i porten.

Dette er isolerte kildekontroller. RAM-siden `$6000–$61FF` fylles med 0
eller 25 som eksplisitt greninngang; den fastsetter ikke RAM-leserens
naturlige sannsynlighetsfordeling. AI, kamp, bevegelse og døds-/innkomst-
animasjoner oppdateres ikke i tjenesteprøven. Ingen ny naturlig C64-rute,
native maskinvarekontroll av denne avsatsen eller original rasterfase
hevdes. Hvilken fiende og hvilket konkret forløp brukeren reagerer på
er fortsatt ikke avklart.

Data og disassembly: `reference/analysis/spawn-r13-2026-10-30/`.
