# Bruce på PAL A500 – samlet OP-kontroll

**Målet for vanlig spilling er tre PAL-felt per spillsteg.** Det tilsvarer
14,4 s for 240 steg. Romlasting og motorarbeid er blitt raskere. Målet
for kamp med begge fiendene er fortsatt åpent.

Alle tidspar bruker WinUAE med sykluseksakt 68000, OCS, Kickstart 1.3,
512 KiB Chip og 512 KiB slow. Ett PAL-felt er omtrent 20 ms. En visningsløkke
kan gå uten at et spillsteg forfaller. Tabellen teller faktiske spillsteg.

| Kontrollert rute, 240 steg | Før, felt | Samlet bygg, felt | Tid i samlet bygg |
| --- | ---: | ---: | ---: |
| Rom 1, begge fiender aktive, Bruce i ro | 959 | 766 / 758 | 15,32 / 15,16 s |
| Rom 1, løp, hopp og kamp | 981 | 821 / 823 | 16,42 / 16,46 s |
| Rom 12, trapp | 822 | 779 | 15,58 s |
| Rom 13, Yamo | 725 | 720 | 14,40 s |

På kampruten hadde referansen åtte felt uten Paula-publisering og
spillbygget seks i begge gjentakelser. På to lengre kampruter tok
1 833 og 1 834 steg 6 000 felt hver. Der ble det målt
19 og 9 tomme Paula-felt. En nøytral joystick gir et annet forløp.
På den fritt kjørende ADF-en ga 6 027 felt 1 959 steg uten økning i
telleren for tapte lydservicetikk. Den telleren måler service. Den
private kampruten tidsstempler også skrivingen til Paula.

## Rombytte

24 romforespørsler per kjøring dekker alle 20 rom, to gjentatte forbindelser
og innlasting av samme rom. Hver forespørsel går gjennom den faktiske
romlasteren. Målingen starter ved debug-forespørselen og slutter når den
ferdige Copper-listen er installert ved rasterlinje 300–308. Denne ruten
kontrollerer lasting etter valg av målrom. Utgangsobjektene har en separat
[kontroll av vanlig rombytte](ROOM_ENTRY_STATE.md).

| Rombytte | Før | Etter |
| --- | ---: | ---: |
| Rom 1 → 2 | 1,50 s | 0,95 s |
| Inn i rom 9 | 3,74 s | 1,61 s |
| Inn i rom 10 | 3,39 s | 1,49 s |
| Median over 24 forespørsler | 1,59 s | 1,05 s |

Summen gikk fra 704 808 til 416 969 rasterlinjer i første par og fra
704 695 til 416 962 i det andre. I rom 9 tok den separate faseprøven av
første leveransetrinn 24 993 linjer fram til publisering og 25 104 fram til
strålen nådde første spillfeltrad. Den siste målingen følger strålen
i emulatoren. Skjermens eller vertsmaskinens visningsforsinkelse inngår ikke.

De tre leverte endringene ved lasting er følgende.

* Romstrømmen ved `$0AD7–$0B2D` dekodes én blokk av gangen. Gjentakelser,
  bokstavelige celler, attributtskrivingene ved `$0B5F`, radskiftet ved
  `$485B`, siste JSR-/PHA-byte og registerflagg er med. 442-cellersrommene
  kan skrive inn i første kontaktmaske. Uvanlige pekere, desimalmodus,
  nulltelling og avslutning går fortsatt gjennom instruksjonsoversettelsen.
* Den skjulte 40 KiB-bakgrunnen og menyflaten tømmes med en D-blitt.
  CPU-en begynner først å tegne etter at blitteren er ferdig.
* I de åtte animasjonsbildene fra `$2CF1–$2D54` gjenbrukes en ferdig
  planarrad innenfor samme tegnrad når både rasterbånd og
  `(fase + (pikselrad >> 1)) modulo 8` er like. 60 sammenligninger med
  den skalare tegneren dekker alle rom, ulike startjusteringer, endrede
  tegnfarger, rulledata og rasterbånd. Begge sider av bufferen kontrolleres.

## Figurer, felt og kildegrunnlag

Kilden er det frosne Remember/T64-minnebildet med SHA-256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Identiteten som urørt 1984-utgave er uavklart.

* `$1C29 → $179E` ble målt både med to klokkeavlesinger og med
  separate intervaller for `$2D7C`, `$1C5B` og `$2780`. Den ytre
  målingen ga 4 290 rasterlinjer med bare Bruce og 15 516 med begge
  fiendene over 240 steg. 240 tomme klokkepar kostet henholdsvis 194
  og 205 linjer. Med Bruce i ro ble historikkløkken utført 0, 124 og
  73 ganger for Bruce, Yamo og Kage. Under løp og kamp var tallene
  159, 108 og 158. Samme skjermposisjon sier lite om dette arbeidet.
* `$1C79–$1C8D` flytter 40 byte baklengs med tre byte mellom
  oppføringene. Den korte veien gjelder de tre aktørene i binærmodus.
  384 direkte kontroller sammenligner alle 65 536 byte og CPU-registrene.
* `$15BD–$169C` oppdaterer spilltellere og klargjør CIA-avlesningen.
  Kombinasjonen `$7F=$FF, $82=$7F` beholder originalens to
  underrutinekall. 1 664 sammenligninger dekker blant annet bankvalg,
  telleromslag, palettgrenen, avbruddsflagg og CIA-byte.
* `$2591` og `$25B9` bygger én aktiv spritekomponent om gangen.
  Motoren gjennomfører feltservice ved `$2586` før hver figur og
  leser figurdataene på nytt etter service. Ved uvanlig høyde,
  adresse eller desimalmodus brukes den opprinnelige banen.
  128 avspillinger av `$2584` ga samme RAM, registre og alle
  384 observerte servicegrenser. 68000-kopieringen har i tillegg den
  separat kontrollerte hurtigbanen for adskilte minneområder.
* Romlasteren ble sammenlignet med kildens 6502-instruksjoner etter
  alle 2 056 blokker og 8 812 celler. Dette dekker romdataene og
  register-/minneresultatet. Naturlig gjennomspilling av alle dører,
  feller og spillermoduser er fortsatt en egen kontroll.

## OP0–OP6

| Del | Resultat |
| --- | --- |
| OP0, måling | Aktørprofilen, uavhengig ytre tidtaking, korte ruter og to lange ruter er gjennomført. |
| OP1, motor | Kildeavstemte veier for historikk, bildebygging og romstrøm er levert. Det samlede stegbudsjettet overskrides med begge fiender. |
| OP2, felt og lyd | Enspillergrenen i feltavbruddet er kortet ned. Tidsstempling ved Paula viser fortsatt hull under falltreff. |
| OP3, visning | 36 bilder i rom 12 og 12 etter kontrollert død og rom 13 → 12 ble kontrollert mot den utførende Copper-listen. Ingen statiske pikselavvik, blandede trappefaser eller ulovlige flimmerpar ble funnet. |
| OP4, felt og input | Vanlig aktørservice og joystickgrense er bevart i spillbygget. Tre-felts kadens og naturlig C64-rasterfase er åpne. |
| OP5, minne | 20-romsturen med stackmerke brukte 2 880 byte ned til laveste skriving i en 16 KiB CLI-stack. 13 496 merkede byte forble urørt. Minste sammenhengende Chip-reserve i 120-stegs romprøven var 69 016 byte. CLI- og ADF-kjøringen plasserte alle fire DOS-segmenter i utvidelsesminnet. Bakgrunn, lyd, figurdata og animasjonsbuffer lå i Chip. |
| OP6, lasting | Begge gjentakelser er raskere ved alle 24 forespørslene. Vanlig CLI- og diskoppstart viser den komplette menyen. I en egen CLI-kjøring klatret Bruce opp nettet i midten av rom 1 og krysset til rom 2 og tilbake med joystick. Diskprøven skiftet til spiller 2 etter dødsfall med fire liv i første rom. |

## Feltavbrudd og skjermkø

Den vanlige enspillergrenen i feltavbruddet behandles nå
direkte. 960 innganger gjennom denne grenen og 64 gjennom den opprinnelige
tospillergrenen ga samme RAM og registre. Med begge fiender aktive i hele
stillstandsruten gikk tiden fra 893 til 872 felt. Den bevegelige ruten
tok 850–852 felt, men Kage var ute av rommet i en del av forløpet.
Trapperuten tok 832 felt mot 817 i første leveransetrinn. Det isolerte
feltforsøket ble derfor fulgt av en måling av det samlede arbeidet med
spritekopiering og visning.

Det leverte bygget kombinerer direkte feltbehandling, den avgrensede
spritekopieringen og tidlig valg av neste Copper-liste. Det installerer
pekeren mens inneværende liste kjører og venter til neste felt før den
gjenbruker den gamle frontbufferen. Det stiller neste liste på linje
44–285. Sent ferdige bilder og rombytter bruker fortsatt linje 300–308.
Begge kodebaner har egne vinduskontroller. Ingen Copper-restart utføres
midt i bildet. Den gamle frontbufferen blir først tilgjengelig etter at
feltklokken har gått videre og strålen har passert linje 44.

De tidligere pikselkontrollene leste
`COP1LC` for å finne det viste bildet. Med en kø kan dette registeret
allerede peke på *neste* bilde. Kontrollen følger nå `COPPTR` for å finne
listen som faktisk kjøres. Første private 12-bildersprøve viste bare én
fakkelvariant. Gjentakelsen med 36 bilder viste flere varianter og bestod
flimmerkontrollen. Begge prøver er bevart. Det endelige bygget har egne
bilder, disk-/CLI-prøver, pauseprøve og kilde-/native-kontroller.

Den native spritekopieringen kontrollerte 96 kombinasjoner av smal/bred
maske, høyde, kilder, destinasjonsjustering og overlapp mot den
kildekontrollerte C-rutinen. Hver kombinasjon sammenlignet hele 64 KiB og
kopikonteksten. Hurtigbanen krever adskilte kilde-/målområder. Den vanlige
ordnede kopieringen håndterer de øvrige prøvene.

Den samlede native testen bestod 53 kildefixturer og 1 200 løkker med
52 632 byte i største ledige Chip-blokk. 1 143 av publiseringene brukte
køen. Begge publiseringsbaner hadde null avvik fra sine vinduer.
Den strenge tidsporten er fortsatt åpen og gir feilstatus ved kjøring
med `--require-realtime`.

En privat variant for tre inaktive objektceller tok 746 felt i
stillstandsruten og 812 i kampruten. Den er bevart som et avgrenset
forsøk. Det leverte objektpasset beholder den tidligere rutinen.

## Gjentakelse

* Kjør `test-parity.ps1` for kilde-, register-, bilde- og lydkontroller.
  `test-source-world.ps1 -TestFrames 1200` kjører den native fixturpakken.
* `check_blocks.py`, `check_images.py` og `check_irq.py` i analysemappen
  sammenligner avgrensede kodebaner. `build_pipeline.py candidate` bygger
  det gjeldende spillet med den lette måleren. Deretter kan `long` og
  `tour` bygges. `build.py` beskriver de historiske pilotene.
  Samme ruteskript brukes for alle korte og lange målinger med
  `-StageName op-pipeline` for sluttbygget og `op-finish` for pilotene.
  Bruk nye etiketter for nye kjøringer.
* `normal.ps1` starter en egen WinUAE-prosess med ordinær CLI eller
  skrivebeskyttet ADF. Styringen velger spillmodus fra menyen.
  Spillminnet leses for målingene. Romturens private måleprogram bruker
  debug-romforespørsler, og dødsbildetesten bruker en injisert dødstilstand.
* `python tools/verify_op_finish.py --require-realtime` kontrollerer den
  strenge tidsporten og returnerer feilstatus når den overskrides.

Kontroller og råtall ligger i [analysemappen](../reference/analysis/op-finish-2026-10-31/).
