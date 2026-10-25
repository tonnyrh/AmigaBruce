# Kage og Yamo: verifikasjon mot C64-koden

25. oktober 2026. Kilden er de faktiske bytene i den frosne
Remember/T64-kandidaten, SHA-256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Dette sertifiserer ikke kandidaten som valgt, urørt 1984-utgave.
Originalene og kildeutsjekkingene er uendret. Atari-rekonstruksjonen og
editorens ombygde spill er ikke brukt som fasit.

**Konklusjon:** De vanlige angrepsvalgene ved samme høyde er allerede riktige
i Amiga-adapteren. Hele AI-en er fortsatt ikke kildeidentisk. Venting,
inntreden, kontakt-/aktørtilstander og romutganger har dokumenterte avvik.
Denne leveransen verifiserer og spesifiserer koden; spillmotor og EXE/ADF
er uendret. Den gir ikke en ny native AI- eller ytelsesgodkjenning.

## Aktører og rekkefølge

Kage er Ninja/aktør 2 i koden; Yamo er aktør 1, Bruce aktør 0.
`$95+aktør` inneholder aktiv-/kontrollflagg, `$BF` handling, `$CE` restteller,
`$C2` forrige handling og `$0106` en separat ventelås. Disse er forskjellige
tilstander, ikke én generell venteteller.

`$179E` kaller først `$2D7C`, deretter oppdateres aktive aktører i rekkefølgen
2, 1, 0 gjennom `$1C5B` og `$2780`. `$1C5B` håndterer ventelås og svart
kontakt før handlingsgrenene. Hovedløkkens piksel-/objekt-/kampbehandling
kommer før dette. Den rekkefølgen fastsetter hvilke gamle tilstander AI-en ser.

`$2D7C–$2DBF` setter tilstand 20/teller 20 bare når:

- helsebyten er ikke-negativ;
- kontrollflagget passer: `$81` når `$42CA=0`, ellers/også `$41`;
- handling og restteller begge er 0;
- hele kontaktmasken har klasse 1 eller 4 (`$B6 & $05`).

Yamo initialiseres med `$81`, Kage med `$41`. `$42CA` er her dokumentert som
modusbyten som endrer denne gaten og flere inntredentellere. Det er ikke
innført en ny kontrollmodus i Amiga-versjonen.

## Avstand, høyde og valg i tilstand 20

`$2DDD–$2E0F` beregner avstand til Bruce: signert størrelse i `$62` for Y og
`$63` for X. Størrelsen mettes til 48; bit 7 beholder siden. X-enheten er
to skjermpiksler, Y-enheten én. Dette gjelder aktørankrene, ikke figurmidten.

`$22FA–$23CC` skiller følgende tilfeller:

| Betingelse | Handling |
| --- | --- |
| Ingen klasse 1 eller 4 | Første fallsteg via `$2378 → $1DC4` |
| Klasse 4 uten klasse 1 | Fortsett i eksisterende sideretning; hopp over høyde-/angrepsvalget |
| Klasse 1 og Y-forskjell minst 16, NPC over Bruce | Fortsett i eksisterende retning |
| Klasse 1 og Y-forskjell minst 16, NPC under Bruce | Vend mot Bruce og gå til egen ventetilstand |
| Y-forskjell under 16, Bruce bak, X-avstand minst 33 kildeenheter (66 piksler) | Snu, så gå |
| Bruce bak og nærmere enn 33 | Gå til retrett; ingen umiddelbar vending mot Bruce |

Når NPC-en vender mot Bruce og er i angrepshøyde:

| X-avstand i kildeenheter | Kage | Yamo |
| --- | --- | --- |
| 0–4 | Retrett | Retrett |
| 5–10 | Stikk, tilstand 22/teller 19 | Slagforsøk, tilstand 17/teller 4 |
| 11 | Gå | Slagforsøk |
| 12–18 | Gå | Flyvende spark, tilstand 12/13/teller 12 |
| 19 og mer | Gå | Gå |

Referanser: Kage `$23B8–$23CC`; Yamo `$237B–$23B6`. Slagforsøket går
gjennom `$1F7E`, som kan avvise nett. At AI velger angrep betyr ikke at
angrepet treffer: VIC-gate, positur, aktiv fase og offer behandles separat.
Den ordinære Kage-grenen velger ikke Yamos flyvende spark.

Dette er lokal, kontaktstyrt oppførsel. Tilstand 20 beregner ingen korteste
vei gjennom rommet. At Kage fortsetter mot en øvre utgang mens Bruce står
nede, er forenlig med koden; feil i selve utgangen må skilles fra det valget.

## Bevegelse og retrett

`$2352/$236C` kaller sideretningshjelperen to ganger: normalt fire
skjermpiksler per klar aktøroppdatering. `INC $52` kompenserer decrementet
i `$24F4`, slik at tilstand 20s teller beholdes under denne bevegelsen.

Retrett etableres ved `$2327–$2351`. Den bruker Bruces X ±15 kildeenheter,
forskjellen til NPC-en og minimumsteller 5. Tilstand 21 fortsetter i gammel
retning; den snur først ved restteller 1 og går da til tilstand 20/teller 128
(`$23D7–$23F0`). Manglende **klasse 1** avbryter retretten til fall, også
dersom klasse 4 finnes. Det er ikke samme støtteregel som tilstand 20.

En faktisk bytegren må beholdes: hvis subtraksjonen ved `$232E` gir 0,
faller `BNE` gjennom til addisjonen ved `$2332`. Med Bruce på rå-X15 og
NPC på rå-X13 blir resttelleren 5; Amigaens matematiske målpunkt gir 13.
Dette er et kontrollert kildeeksempel, ikke en ny ønsket retrettregel.

## Venting og romklokke

`$10D0–$10DF` leser **tidsbyte `$88`**, ikke en tilfeldig byte. `$1614–$1626`
øker `$87` når `$0104!=0` og `$0105` er ikke-negativ. Ved byteomslag økes
`$88` så lenge den ennå er under 128. `$0A2A–$0A38` nullstiller romklokken.
Fixturekjøringene av denne IRQ-prefiksen emulerer ikke hele raster-/IRQ-forløpet.

| Tid `$88` / runde `$40` | Ordinær NPC-venting ved `$228C` | Etter avsluttet spark, `$2DC0` |
| --- | --- | --- |
| 0–24, runde 0 | 6 | 24 |
| 25–31 | 3 | 3 |
| 32 og mer | 1 | 1 |
| 0–24, senere runde | 1 | 1 |

Slag-/stikkavslutning og «Bruce er over meg»-grenen bruker den ordinære
ventingen. Stikket slutter ved **restteller 1**, via `$22F0 → $228C`.
Amiga-adapteren lar stikkflagget stå med teller 0 én oppdatering ekstra.

Post-spark-grenen returnerer fra hele `$2D7C`-hjelperen. Testen bruker Yamo
som avsluttet sparkaktør og injiserer et automatisk kontrollflagg på den
lavere aktøren for å gjøre returen synlig. Dette er en strukturell testtilstand,
ikke påstand om at Bruce naturlig styres av denne AI-en.

## Inntreden, gjeninntreden og romutganger

Rominitialisering leser Kages teller fra `$130B+rom` og Yamos fra `$1347+rom`.
Rom 1 har **104/240**. Målebaselinens **96/232** er åtte lavere og må ikke
brukes som universell kaldinitialisering. Senere runder setter begge til 3;
modusbyten `$42CA` kan deretter sette Yamos første teller til 8.

Etter inntreden/fjerning brukes `$131F` og `$135B` gjennom `$0D42`, med hele
grunnverdien ved tid 0–24/runde 0, halv verdi ved tid 25–31, ellers 3.
`$42CA!=0` velger først grunnverdi 48 for Yamo. `$3001–$3048` fjerner aktiv-
og sprite-/mappingtilstand og **hopper videre til `$0D42`**; det er ikke bare
en aktiv-bit som slettes. Rom 1s ordinære returgrunnverdier er 160/238.

Kage kan utsettes 16 oppdateringer ved `$0DB1–$0DD6` når Yamo er aktiv,
`$40=0`, `$42CA=0`, tid under 25 og minneleseren returnerer minst 25.
Amiga-adapteren har ikke denne grenen.

`$1159` øker `$16` og leser `($16),Y` ved `$1163`; demo returnerer 1.
Testene injiserer **dataen som leses**, ikke nye instruksjoner. Ingen uniform
tilfeldigfordeling eller ny RNG er antatt.

`$0BFA–$0C4B` velger mellom standardankomst (`$4BAE/$4BC2`), alternativ
(`$4BD6/$4BEA`) og lagrede koordinater/helse (`$8A/$8C/$8E + aktør`).
Yamo bruker gate `$136F`; Kage tester først `$1333`, men leser deretter
faktisk **fortegnet fra `$136F`** ved `$0C38`. Det er kontrollert mot bytes;
det er ikke korrigert til hva tabellnavnet kunne få oss til å forvente.
Verdier under/over `$C0` og en ekstra minnebytes lave bit styrer de andre valgene.
Ved Bruces rombytte lagrer `$2FA5–$2FBD` ankomst/helse for aktive NPC-er.
En universell ny fullhelse og én fast NPC-inngang bevarer ikke dette.

Yamo starter i tilstand 16/teller 10, snur mot Bruce ved teller 1 og går til
tilstand 18/teller 16 (`$2235–$2269`). Første bevegelse kommer på den 28.
aktøroppdateringen regnet fra før første oppdatering etter init. Kage snur
ved inntreden og beveger seg på den 17. Første oppdatering skjer i samme
hovedrunde som spawn; dette forklarer de målte +27/+16-stegene. Yamos
retning bestemmes senere enn i dagens Amiga-initialisering.

NPC-utgang går gjennom det samme objektpasset og `$30D4` som Bruce, deretter
`$2F90 → $3001`. I rom 1s høyre forbindelse kreves rå-X minst162
(skjerm-X300) og høyre bevegelsesrecord, i tillegg til at utgangscellen er
funnet. Dagens `bl_enemy_leave_room` bruker en statisk horisontal dørtest,
skjerm-X302, og ikke denne samlede betingelsen. Den dekker heller ikke hele
det dynamiske/vertikale objektpasset. Den gamle ruten som faktisk landet på
X302 beviser derfor ikke at alle mellomliggende terskler er riktige.

## Resultat mot Amiga-adapteren

- 588 isolerte, vanlige valg på fast underlag ved tid 0/runde 0 samsvarer:
  slag/stikk/spark, snu, retrett og forhold til høydeforskjell.
- 59 konkrete fixtures beholder forskjeller fordelt på fem grupper:
  ordinær venting (20), post-spark-venting (20), retrettstøtte (16),
  nullmålet ved venstrekanten (2) og stikkavslutning (1).
- Inntredentabeller, fasevalg og ankomst/helse er kildeavklart, men dagens
  motor bruker fortsatt forenklet spawn-/resetlogikk. `bl_c64_field` viderefører
  ikke `$87/$88`-klokken som disse AI-grenene trenger.
- Kontakt, NPC-positurer, vegghistorikk, reaksjoner og hele livs-/aktørmaskinen
  må inngå i en samlet port. Lik beslutning på injisert kontakt godkjenner
  ikke gangbane, fysisk kollisjon, dørrute eller naturlig oppførsel.

Kjør `test-c64-ai.ps1`. Den utfører **4578** kontrollerte kjøringer av
originalbytene. Den kompilerer også eksisterende `enemy_step` med eksplisitte
bevegelses-/dørstubber for å registrere beslutninger. Stubbene simulerer
ikke C64-regler og skriver ikke nye forventninger for ukjent fysikk.

[Rapport og alle fixtures](../reference/analysis/ai-audit-2026-10-25/report.json),
[adresset disassembly](../reference/analysis/ai-audit-2026-10-25/source-disassembly.txt).
`python tools/audit_c64_ai.py --verify` kontrollerer kilde-/artefaktidentitetene
uten å starte eller bygge spillet.

## Romtabeller

Følgende er uendrede grunnverdier fra kandidatbinæren. De er resttellere,
ikke sekunder. En sperret spawn-tjeneste betyr at `$7A!=0` lar hovedløkken
hoppe over de vanlige inntreden-/tellerkallene; tabellverdien alene gir ikke
naturlig tilgjengelighet eller en ferdig NPC-rute.

| Rom | Første Kage `$130B` | Første Yamo `$1347` | Retur Kage `$131F` | Retur Yamo `$135B` | Alternativ inngang (skjerm-X/Y) | Spawn-tjeneste `$4C9E` |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 104 | 240 | 160 | 238 | 294/98 | åpen |
| 2 | 120 | 238 | 160 | 238 | 274/146 | åpen |
| 3 | 120 | 238 | 160 | 238 | 276/196 | åpen |
| 4 | 0 | 0 | 0 | 0 | 88/196 | sperret |
| 5 | 112 | 192 | 112 | 238 | 276/180 | åpen |
| 6 | 24 | 192 | 12 | 96 | 56/194 | åpen |
| 7 | 48 | 160 | 48 | 238 | 234/114 | åpen |
| 8 | 80 | 176 | 24 | 192 | 38/116 | åpen |
| 9 | 0 | 0 | 0 | 0 | – | sperret |
| 10 | 0 | 0 | 0 | 0 | – | sperret |
| 11 | 8 | 48 | 12 | 48 | 276/92 | åpen |
| 12 | 0 | 0 | 0 | 0 | – | sperret |
| 13 | 4 | 32 | 4 | 32 | 200/92 | åpen |
| 14 | 18 | 192 | 8 | 238 | – | sperret |
| 15 | 8 | 32 | 8 | 48 | 268/190 | åpen |
| 16 | 8 | 48 | 8 | 80 | 220/196 | åpen |
| 17 | 8 | 32 | 8 | 48 | 234/142 | åpen |
| 18 | 18 | 192 | 8 | 238 | – | sperret |
| 19 | 0 | 0 | 0 | 0 | – | sperret |
| 20 | 0 | 0 | 0 | 0 | – | sperret |
