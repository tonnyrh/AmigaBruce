# Kostnaden ved spriteoppdateringen i rom 1

## Kildegrunnlag

Hovedløkken kaller `$2584` ved `$1C2C` og fortsetter ved `$1C2F`.
X starter på 2. Ved `$2586` lagres aktørnummeret i `$51`. Aktivbiten
ved `$95+X` avgjør om bildet skal bygges. Amiga-motoren betjener
feltklokken ved dette punktet før den leser aktivbiten. Alle tre
aktørene passerer derfor servicepunktet i hver gjennomgang.

For hver aktiv komponent velger `$2704–$2718` måladresse fra tabellen
ved `$274F`, med bank valgt av `$277D`. Ved `$2719–$274E` leses
bildedata fra tabellene, som blant annet setter kildeoperandene ved
`$26AB`, `$26E4` og `$26EE`. Kallet ved `$26A0` kopierer og fyller
bildedataene. Kage (X = 2) hopper over sekundærkomponenten ved
`$25B2`. For Yamo og Bruce bestemmer fortegnsbiten i `$2770+X` om
sekundærkomponenten skal bygges. Ved slutt nullstilles `$277E`.

Kontrollen kjørte den faktiske maskinkoden i Remember/T64-kandidaten
med SHA-256 `092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Fra de to kampopptakene fortsatte originalprogrammet til kallet ved
`$1C2C`. Begge bildebankene ble undersøkt med fire fiendemasker.
Koden besøkte Kage, Yamo og Bruce i denne rekkefølgen. Antall
komponenter var 2 med Bruce alene, 3 med Kage, 4 med Yamo og 5 med
begge. Alle åtte kontroller stemte med den kompilerte vertsmotoren i
alle 65 536 minnebyte, registre, flagg, SP og retur-PC. Vertsmotoren
bruker C-varianten av kopieringen. På Amigaen går kallet via den
ordinære [68000-kopieringen](SPRITE_COPY_OPTIMIZATION.md) med de
eksisterende inngangsvernene. Disse kildekontrollene er styrte
enkeltkall. Kandidatens identitet som urørt 1984-utgave er åpen.

## Målemetode

Alle ruter bruker rom 1, nøytral joystick, 240 oppvarmingssteg og 240
målte spillsteg i syklusnøyaktig WinUAE på PAL A500, 68000, OCS,
Kickstart 1.3 og 512 + 512 KiB. Fiendemasken deaktiverer de utelatte
aktørene i målebygget. Antall visningsløkker kan variere selv om antall
spillsteg er likt. Kontrollen med begge fiender bruker vanlige aktive
aktører. Ingen inndata styrer fiendenes posisjoner eller positurer til
bestemte testverdier.

Referansen gjenbruker det verifiserte måleprogrammet fra
[desimalkonverteringen](OP_SCORE_DECIMAL.md). En annen variant leser
linjetelleren bare ved inngang og retur fra hovedløkkens spriteanrop.
Den gir et uavhengig mål på hele rutinen. Detaljbygget deler 60 av
240 anrop i fem ikke-overlappende intervaller. Utvalget tar ett steg
fra hver blokk på fire og roterer plasseringen mellom blokkene.

Intervallene dekker service, valg av målbuffer, poseoppslag, kopiering
og øvrig driverarbeid. Hjelperkallene inkluderer sine JSR- og RTS-baner.
Service kan også behandle et forfalt spillfelt. Etter målevinduet
gjentas tidsavlesingene uten spillarbeid med samme rekkefølge og
samme antall observerte komponenter per aktør. Differansen gir et
anslag per intervall. Service- og rasterfasen kan forskyves av
instrumenteringen, derfor brukes referansebygget til forløpt spilletid.

## Rom 1 uten detaljmåling

| Aktive figurer | PAL-felt for 240 spillsteg | Arbeid, rasterlinjer | Visningsløkker |
| --- | ---: | ---: | ---: |
| Bruce | 720 / 720 | 136 869 / 136 886 | 480 / 480 |
| Bruce og Kage | 720 | 173 211 | 253 |
| Bruce og Yamo | 730 | 192 490 | 240 |
| Bruce, Kage og Yamo | 961 / 961 | 256 049 / 255 121 | 240 / 240 |

Bruce alene tok 14,4 sekunder, mot 19,22 med begge fiender. Kage alene
økte arbeidsmengden selv om hele ruten tok like lang tid som med bare
Bruce. Forskjellen i målt arbeid mellom ytterpunktene er gjennomsnittlig
494,6 rasterlinjer per spillsteg. Det inkluderer hva resten av motoren
og skjermvisningen gjør i de ulike rutene. De kontrollerte maskene har
også ulik kostnad for å holde ekskluderte fiender inaktive.

## Hvor tiden i rutinen ble brukt

Tabellen viser rasterlinjer per detaljmålt spillsteg etter fratrekk av
tomløypen. Tall for ytterpunktene er gjennomsnittet av to kjøringer.
Det ble registrert null poenghendelser ved `$3175` og null endringer i
poengtallet i alle seks detaljkjøringene.

| Del av `$2584` | Bruce | Med Kage | Med Yamo | Med begge |
| --- | ---: | ---: | ---: | ---: |
| Feltservice ved `$2586` | 6,0 | 44,0 | 33,1 | 57,6 |
| Valg av målbuffer, `$2704` | 6,4 | 9,5 | 13,2 | 16,6 |
| Poseoppslag og kildeoperander, `$2719` | 7,3 | 10,6 | 14,2 | 17,7 |
| Kopiering og utfylling, `$26A0` | 22,1 | 35,4 | 46,6 | 59,3 |
| Øvrig driverarbeid | 11,3 | 14,8 | 17,1 | 20,8 |

Med begge fiender stod Kage på samme X/Y i 239 av 239 sammenligninger
mellom nabosteg. Poseindeksen var lik i 222. Yamo hadde uendret X/Y
i 115 sammenligninger. De 60 detaljmålte stegene i hver kjøring gikk
gjennom alle fem komponenter. Lik posisjon alene er derfor utilstrekkelig
som vilkår for å gjenbruke et bilde.

Da bare Bruce var aktiv, forfalt ingen spillfelt ved de 180 detaljmålte
servicepunktene per kjøring. Med begge fiender ble 68 og 67 spillfelt
betjent der. Henholdsvis 50 og 49 av dem falt ved første besøk, når X
var 2. Det forklarer hvorfor en kostnad ført på Kage også omfatter
felles feltarbeid. Detaljmålingen brukte selv rundt 40 rasterlinjer
per utvalgt steg alene og 79 med begge i tomløypen. Den kan flytte
hvilket servicepunkt som treffer feltgrensen.

## Hvor mye forklarer spriteoppdateringen?

Den uavhengige målingen rundt hele `$2584` ga **49,9 rasterlinjer per
spillsteg alene og 158,7 med begge fiender**, etter fratrekk for de
to tidsavlesingene. Differansen på 108,9 linjer tilsvarer omtrent
**22 % av de 494,6 ekstra arbeidslinjene** i referansen. Med den ytre måleren tok rutene 720 og 966
PAL-felt, mot 720 og 961 i referansen.

Servicepunktet inne i rutinen betjente 0 spillfelt alene og 241 med
begge fiender over de 240 stegene i den ytre målingen. I detaljbygget
var summen av intervallene rundt 53 og 172 linjer per utvalgt steg.
Forskjellen fra den ytre målingen viser hvorfor den brukes for
totalandelen. Detaljtallene rangerer arbeidet inne i rutinen.

**Neste mål er aktørkallet `$179E`.** Rundt 78 % av merarbeidet ligger
utenfor spritevinduet. Hovedløkken kaller `$179E` ved `$1C29`. Koden
kaller først `$2D7C` og går deretter gjennom aktørene ved `$17BC`.
I rom 1 kaller den `$1C5B` og `$2780` for hver aktiv aktør. Mål de
tre delene med samme fiendemasker før en privat 68000-erstatning
velges. Rom 1-målingen gir ingen fordeling av tidsbruken i disse
delene ennå.

## Etterprøving

[Analysemappen](../reference/analysis/op-sprite-cost-2026-10-31/) har
`build_probe.py` for variantene `reference`, `profile` og `outer`.
Ruteskriptet fra poengvisningen bruker `-StageName op-sprite-cost`,
rom 1, maske 0–3 og inputrute 0. `source.py` gjentar originalinstruksjonene
fra de to lokale opptakene med DLL-en fra `test-source-score.ps1`.
`measure.py` kontrollerer de arkiverte rapportene. Registeret binder
de 14 WinUAE-kjøringene til målebyggene og spillutgaven fra
[desimalkonverteringen](OP_SCORE_DECIMAL.md). [Måleresultater](../reference/analysis/op-sprite-cost-2026-10-31/result.json).
