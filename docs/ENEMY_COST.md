# Stillestående fiender: CPU-kostnad, 30. oktober 2026

Brukerens observasjon er bekreftet: tregheten skyldes ikke bare AI eller
bevegelse. Faste figurer gir vesentlig mer arbeid i kontaktberegning og
spritebygging. Yamo har to kildekomponenter; Kage har én. Antall komponenter
og hvilke figurer som faktisk er aktive må skilles fra fiendenavn i en
naturlig gjennomspilling.

## Målemetode

Isolerte WinUAE-bygger bruker PAL OCS, 68000, 512 KiB Chip og 512 KiB slow.
Mikrotesten setter faste posisjoner, kildeposer og aktiveflagg, først med
figurene adskilt og deretter overlappende. Hver del får åtte oppvarmingskall
og 64 målte kall. Ingen AI, hovedlogikk eller Amiga-figurtegning kjøres
inne i de målte blokkene. Posisjon, pose, aktiveflagg og feilkode kontrolleres
etter hver blokk. Kilderammen ligger i CPU-minne, ikke Chip (`TypeOfMem=5`).

Dette er manipulerte testtilstander for kostnad, ikke observasjoner av
naturlig C64-spilling. Feltkallene kjøres med den faktiske fireplans-DMA-en
aktiv. Tid er målt i PAL-rasterlinjer via CIA-klokken.

Adskilte figurer, gjennomsnitt per kall:

| Aktive figurer | Feltarbeid | Kontaktberegning | Spritebygging |
| --- | ---: | ---: | ---: |
| Bruce | 18,1 | 67,3 | 47,7 |
| Bruce + Yamo | 21,5 | 134,1 | 91,5 |
| Bruce + Kage | 18,3 | 128,6 | 70,1 |
| Alle | 21,8 | 195,4 | 113,8 |

Ved overlapp bruker kontaktberegningen 75,6 linjer med Bruce alene og
218,3 med alle tre. Det forklarer en kostnad også uten bevegelse. Det
fastsetter ikke normal spillets samlede bildefrekvens.

## Kildespor

Frossen kandidat: `.reference/c64/work/untrained-memory.bin`, SHA-256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Remember/T64-kandidaten er fortsatt ikke sertifisert som urørt 1984-utgave.

- `$5212–$52AC` går gjennom aktørene 2, 1, 0 og kontrollerer bit 0 i
  `$95+aktør`. Aktive aktører beregnes også når posisjonen er uendret.
  Kontaktmasker og klasseberegning følger `$5380–$542D`.
- `$2584–$25E1` bygger aktørenes kilde-spritebilder. Første komponent
  velges fra `$276D+aktør`. Aktør 2 hopper over sekundærkomponenten;
  øvrige aktører bruker den når `$2770+aktør` ikke er negativ.
- `$2704–$2718` velger mål fra `$274F` og bankflagget `$277D`.
  `$2719–$274E` henter grafikk, høyde, farge og bredde fra tabellene
  `$59BD/$5A8F/$5B61/$5C33/$5CBF`. `$26A0–$2702` kopierer bildet.

Ingen C64-regel om aktivitet, kontakt, AI, takt eller fiender er endret.

## Isolert optimalisering, ikke levert

En direkte 68000-vennlig bildebygger beholder alle relevante RAM- og
stackskrivinger. Mellomliggende registerverdier holdes lokalt til retur.
En ren forhåndskontroll krever binær modus, høyde under 32 og sikre
adressegrenser; ellers brukes den eksisterende oversettelsen uendret.

Hver av tre varianter består 3 328 sammenligninger mot 3 836 708 faktisk
utførte instruksjoner fra den frosne binæren: hele 64 KiB, registre,
returadresse og stack. Prøvene inkluderer alle stackposisjoner og
overlappende grafikkdata. Native kjøringer består 710 kontakt-/kopikontroller,
inkludert 256 kontroller av den faktiske 68000-kopiprimitiven.

Variant 2 reduserer spriteblokken med alle figurer fra 7 283 til 3 803
rasterlinjer per 64 kall, omtrent **48 %**. Kontakt- og feltkostnad er
uendret innen to rasterlinjer per blokk.

Helhetstesten kjører 360 kildeoppdateringer med begge fiender:

| Variant | PAL-felt | Tapte lydticks |
| --- | ---: | ---: |
| Gjeldende spillbygg | 1 423 | 0 |
| Direkte bildebygger, første variant | 1 389 | 28 |
| Lokale registre, variant 2 | 1 376 | 8 |
| Hastighetskompilert variant 3 | 1 375 | 5 |

PAL-telleren inkluderer oppstart og diagnostikk. Lydens testhashing gir
dessuten kostnad som normalbygget ikke har. Resultatet viser bare rundt
3 % lavere samlet tidsbruk i denne kontrollen, og lydtimingen regresserer.
Kandidatene er derfor **ikke integrert**. Normal EXE/ADF og motorens
produksjonskode er uendret i denne undersøkelsen. Ingen nye brukertester
er nødvendige for de isolerte kandidatene.

## Neste avgrensede arbeid

Kontaktberegningen er det største målte arbeidet med faste fiender.
Neste optimalisering skal bevare pikselmasker, klasseflagg, stackdata og
de eksisterende servicegrensene, og måles med samme stillestående prøve.
En lavere kildeoppdateringsfrekvens, utkoblet kontakt for stillestående
fiender eller ny spillregel er ikke en løsning.

Før en kandidat tas inn må den også bestå integrerte kildekontroller,
full native-fixturtest og samlet lyd-/ytelsesmåling uten regresjon.
De tidligere åpne sanntids-, IRQ-, naturlig spilling- og maskinportene
forblir åpne.

Rådata, private kompilatorinnganger og hashbundet rapport finnes i
`reference/analysis/enemy-cost-2026-10-30/report.json` og tilhørende
`enemy-cost-*`-mapper under ytelsesarkivet.
Kjør `python tools/verify_enemy_cost.py` for å kontrollere evidensen.
