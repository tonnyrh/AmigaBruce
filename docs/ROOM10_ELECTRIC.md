# Rom 10: elektrisk felle og forsinket opptegning

26. oktober 2026. Brukeren meldte hakking og en vanskelig synlig elektrisk
felle nederst. Feilen undersøkes separat fra selve C64-fellereglene.

## Kildegrunnlag

Den uendrede binæren er `.reference/c64/work/untrained-memory.bin`, SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Remember/T64-kandidaten er ikke sertifisert som en urørt 1984-utgave.

| Rutine/data | Betydning |
| --- | --- |
| `$348F–$34C7` | Initialiserer rommets felleposisjoner og tellere. |
| `$3BB2–$3C8D` | Rom 10s løprutine. `$4E11 OR $4E15` bestemmer hvilken gren som flytter `$6E`; `$70` lagrer forrige posisjon. `$77/$78` styrer de andre fellene. |
| `$404E–$4060` | Ber om lyd `$89`, tegner streng `$1C` ved gammel posisjon og `$1B` ved ny, med rad fra `$6F`. |
| `$43BE`, `$45DC/$45DE` | Strengpekerne og de faktiske tegnkodene i de to en-celles strengene. |
| `$40A4–$40B7` | Strengvalg for de andre fellestadiene. |
| `$5212–$52AC` | Faktisk kontakt fra tegnpiksler og aktørmaske; synlig rektangel alene er ikke treffregelen. |

480 kontroller kjører originalinstruksjonene og den kompilerte romkoden
med samme kontrollerte leseside og feltinngang. De sammenligner posisjoner,
tellere, skjermtegn, farger og tegnsett gjennom 240 oppdateringer med og
uten fullførte lanterner. Alle stemmer. Dette er injiserte kildekontroller,
ikke en naturlig C64-gjennomspilling. Se [maskinkoden](../reference/analysis/room10-electric-2026-10-26/source-disassembly.txt)
og [kontrollene](../reference/analysis/room10-electric-2026-10-26/source-controls.json).

## Amiga-feilen og rettelsen

Den gamle kopieringen fra bakgrunn til skjerm startet alltid på øverste
rad. Store, kontinuerlig rullende nett kunne bruke opp 5000-bytebudsjettet
før nederste rad. I en belastningskontroll ble de nederste radene aldri
kopiert i 90 kall. Den målte A500-kjøringen viste også at den nederste
fellestripen ofte lå etter den ferdige bakgrunnen.

Direkte tegnendringer, blant annet elektriske feller, dører og lanterner,
får nå en egen kopieringskø foran store animasjonsblokker. Den vanlige køen
fortsetter fra forrige stoppested. Budsjettet er fremdeles 5000 byte per
tegning. Under kontinuerlig full belastning blir alle radene nå betjent
innen åtte kall; en liten prioritert fellestripe kommer først hver gang.

Hele, umaskerte animasjonsord bruker dessuten blitterens A/D-kopi og slipper
den overflødige lesingen av målet gjennom C. Halve kantord beholder den
tidligere maskerte kopien. Originalgrafikk, farger, kontakt, fellebevegelse
og C64-tellere er ikke endret.

## Målemetode

`test-room10-electric.ps1` kjører 900 ytre spilløkker i rom 10 med Bruce i ro.
Målingen sammenligner de to nederste tegnradene, kolonne 6–24, i bildet som
skal vises, med den gjeldende kildebakgrunnen. Figurens område til venstre
er utelatt. Dette teller synlig kopieringsforsinkelse, ikke C64-treff.

Før- og etterbygg bruker samme målekode og PAL A500, 68000, OCS,
Kickstart 1.3, 512 KiB Chip og 512 KiB slow. Den nye kjøringen kontrollerer
også hele bakgrunnen mot kildepikslene ved avslutning. Målearbeidet påvirker
feltkostnaden; tallene er en sammenligning med samme instrumentering og
godkjenner ikke et generelt 50 Hz-krav. Kontrollerte oppstarter og
stillestående spill erstatter ikke brukerens naturlige spilltest. Feltgap
måles separat: `missed_frames` teller spilløkker med mer enn ett maskinvarefelt
mellom bildene, ikke summen av alle tapte felt. `electric_max_streak` er
antall påfølgende bildekontroller, ikke målt antall maskinvarefelt.

Baseline er bevart med eksakte kilder og binær. Den fullførte rapporten ble
gjenopprettet etter at samleren traff EXE-fillåsen fra den andre CLI-starten;
den eide emulatoren ble stoppet og arkivhashene kontrollert etterpå.
Samleren er rettet til å lukke sin emulator før denne hashkontrollen.

## A500-resultat

| Måling, 900 spilløkker | Før | Etter 1 | Etter 2 |
| --- | ---: | ---: | ---: |
| Fellestripe forskjellig fra gjeldende bakgrunn | 614 | 234 | 234 |
| Lengste sammenhengende rekke slike bilder | 60 | 4 | 4 |
| Spilløkker med feltgap over ett | 689 | 740 | 740 |
| Lengste arbeid, HSync-tikk | 506 | 558 | 555 |
| Beholdt forrige bilde | 440 | 444 | 445 |
| Største ordinære feltgap | 3 | 3 | 3 |
| Feil i hele kildebakgrunnen ved slutt | — | 0 | 0 |

Fellestripens forsinkelse er redusert, men rettelsen **løser ikke generell
hakking**. Målingen har flere spilløkker med feltgap og høyere arbeidstopp
etterpå. Den er en prioritering av synlige feller, ikke en ytelsesgevinst;
videre reduksjon av tegnearbeidet er fortsatt åpen.

Begge nye løp består alle inkluderte aktør-, rom-, kontakt-, DMA-, lyd- og
livskontroller og gjenoppretter AmigaOS. Største ledige Chip-blokk er 60832
byte. Kilde-/spilltilstandens sluttsignatur er lik baselinen; hele
host-regresjonen består også. De lagrede skjermbildenes FNV stemmer med
native pakkings-/utpakkingshash. Samleren er i tillegg strammet inn etter
kjøringen: den venter nå på skjermfilens native hash før prosessen lukkes;
samlerkoden som faktisk ble brukt, er bevart i hvert kjørearkiv.

Vanlig spill er bygd som 224056-byte EXE og 901120-byte ADF. AmigaDOS-
kommandoen `start` bruker den oppdaterte EXE-en. Pågående spill må startes
på nytt. [Leveranse og filidentiteter](../reference/validation/room10-electric-delivery.json).
