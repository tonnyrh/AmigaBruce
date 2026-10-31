# VIC-hurtigbane på 68000, 28. oktober 2026

Utgangspunkt er `cb7224a`; produksjonskoden er fra `c34174c`. Den frosne
Remember/T64-kandidaten har SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Urørt1984-utgave, naturlig VIC-rasterfase og fysisk A500 er fortsatt åpne.

## Uendret kildegrense

`$29CE` og `$3D20` leser `$D01E`. Den eksisterende feltbaserte VIC-grensen
akkumulerer spritekontakt før slike avlesninger og nuller låsen bare ved
kildens faktiske lesing. `$1703` publiserer posisjoner/aktive komponenter;
`$2584/$25E2` og kopikjernene bygger kildebildene. Disse kildeinstruksjonene,
figurmaskene, fiendeoppdateringene og servicepunktene er ikke endret.

Rutinen etterligner pikseloverlapp for åtte sprites, Xs niende bit, X/Y-
utvidelse, multicolor/hires, VIC-bank, skjermmatrise og spritepekere.
C64s VIC er maskinvare, så dette er en eksplisitt Amiga-grense mot kildekoden,
ikke en ny rutine som påstås å finnes i C64-maskinkoden. Pikselkontrollene
fastsetter ikke naturlig raster-/borderoppførsel.

## Endringen

Den eksisterende hurtigbanen utførte fortsatt mye C-oppsett hver PAL-periode.
`bl_vic_repeat` ligger nå foran den store arbeidsrammen til den gamle
pikselberegningen. Den krever følgende før forrige kontaktresultat brukes:

- Gyldig forrige resultat, samme aktivmaske, samme X/Y-utvidelse og samme
  ni-bits X/åtte-bits Y for alle aktive sprites.
- Gyldige bitmapcacher for alle geometrisk mulige kollisjonskandidater.
- Samme effektive multicolor-/breddeoppsett og nøyaktig samme63 faktiske
  bytes, lest gjennom de nåværende bank-/matrise-/spritepekerne.

Samme bytes kan ligge ved en ny peker eller bank; det endrer ikke pikslene.
Endrede bytes kontrolleres selv om ingen separat skriveteller ble oppdatert.
Bilder uten geometrisk mulige par trenger ingen innholdslesing før de igjen
blir kandidater. Paddingbyte64 ignoreres. Dette er samme betingelser som den
forrige resultatcachen, med kontrollene skrevet direkte for68000.

Ved treff OR-es de lagrede bitene inn i `$D01E`, også etter en tidligere
avlesning/nulling. Et mellomlagret nullresultat sletter ikke allerede
akkumulerte biter. Ved avvik returnerer rutinen uten å skrive kilde-RAM
eller cachens tilstand, og den eksisterende fullberegningen kjøres.

Cachens eksisterende arrays er samlet i en568-byte struktur med kontrollerte
feltforskyvninger. Ingen ny bitmap-/DMA-buffer eller ekstra grafikkcache er
lagt til. Byteinnhold har64-byte stride og4-byte justering. Spritepekeren er
alltid64-byte justert og de63 lesningene ender senest på `$FFFE`.
Sammenligningen er15 langtord og tre bytes, uten DBRA per langtord.
Store RAM-forskyvninger bruker egen adresseregisterbase, slik68000 krever;
68020-adressering eller høyere CPU-krav brukes ikke.

## Kontroller og måling

- 8741 vertskontroller dekker piksler, lås, cache, aktive/inaktive sprites,
  alle modi, bank/pekerendringer og hver enkelt av63 bytes i alle åtte
  spriteplasser. Enkeltpiksler brukes slik at andre rader ikke skjuler en
  eventuell feil i en bytesammenligning.
- 1536 nye direkte68000-kontroller sammenligner hurtigbanen med en separat
  C-referanse. Alle63 bytes og padding i hver plass prøves, sammen med
  tom aktivmaske, cachetreff/-avvik, koordinater, størrelser, modus, ugyldige
  cacheflagg, like bytes via ny peker/bank og eksternt akkumulerte låsbiter.
  Hele cachestrukturen sammenlignes bytevis for utilsiktede skrivinger.
- De eksisterende65 sammenligningstilfellene for63-byte-kjernen beholdes.
  Kontaktkjernens1046 separate kontroller og53 hele-RAM-/registerfixturer
  med454 kontaktkontroller kreves fortsatt i de respektive byggene.
  Profileringsbygget utelater bare1536-testens ekstra referansekode og
  prøve-cache etter en faktisk allokeringsfeil før målesløyfen. Det kjører
  fortsatt65 bytekontroller og454 kontaktkontroller. De1536 kontrollene
  kreves separat i tidsbygget. Fullbyggets53 fixturer og profileringsdata
  kjøres hver for seg uten den ekstra referansen. Produksjonskjernen er den
  samme, og49152-byte-porten senkes ikke.

Førpunktet er1466 faktiske PAL-felt for360 spillsteg i den faste rom1-scenen,
med begge fiender og stasjonær udødelig test-Bruce. Førprofilen bruker
31,288 rasterlinjer per VIC-kall. Tidsmåling og profilering kjøres separat.
Dette er ikke et løfte om tilsvarende prosentgevinst i alle rom eller en
naturlig gjennomspilling.

Sluttresultater bindes i [verifikasjonsrapporten](../reference/validation/source-optimization.json).
Full feltkadens, lydservice, rasterfase og fysisk A500 er fortsatt egne porter.

Det første kombinerte fullbygget ble også stoppet før rapport etter at
CLI-hunkkjeden viste BSS ved `$015060` i Chip RAM, mot tidligere plassering
i slow RAM. Dette er dokumentert som en avvist diagnosepakking, uten
påstand om observert allokeringsfeil eller bestått minneport i det løpet.
Ingen slik ekstra prøve-cache finnes i normalbygget.

## Sluttresultat

| Fast rom1-sekvens, 360 spillsteg | Før | Etter |
| --- | ---: | ---: |
| Faktiske PAL-felt, uten profilering | 1466 | 1428 |
| VIC-kostnad per feltkall, eksklusive rasterlinjer | 31,288 | 25,075 |
| Tapte lydserviceticks i tidsmålingen | 26 | 21 |
| Største ledige Chip-blokk | 52632 | 52632 |

Dette er **2,59 % kortere samlet målt tid** og **19,86 % mindre VIC-kostnad
per kall**. Innledende/andre pilotpar ga1426–1428 felt. Det er enkeltmålinger
med endret kildefelt-/tilstandsfordeling når beregningen tar kortere tid,
ikke statistiske FPS-garantier. Lyden mister fortsatt ticks; full sanntid
er ikke godkjent.

Tidsbygget består1536 VIC-hurtigbanekontroller og1046 kontaktkontroller.
Det separate fullbygget består53 hele-RAM-/registerfixturer,454 kontakt-
kontroller og1200 testsløyfer med tilbakeføring til AmigaOS. De eksisterende
65 bytekontrollene for63-byte-kjernen kjøres i alle native testvariantene.
Minneporten er uendret49152 byte;52632 byte største Chip-blokk gjenstår.

352 bytes i `bl_vic_repeat` og88 bytes i `bl_vic_equal63` er kontrollert
identiske i de faktiske linkede normal-, tids-, profil- og fulltestbildene.
[Maskinkodebinding](../reference/analysis/vic-repeat-2026-10-28/native-kernel-bytes.json).
Fullbyggets BSS ligger igjen i slow RAM, ved `$C54608` i sluttkjøringen.

Vanlig EXE er341496 byte,120 byte mer enn førpunktet. CLI-kommandoen
`start` er oppdatert. Normal CLI-/ADF-oppstart, rom1–6 via debugvalg,
Yamos synlighet, tre PAL-klokkepar per prøve og rom6-fellens bakgrunn/begge
bildebuffere er kontrollert med sluttbygget. Debugvalg og eksplisitt injisert
synlighetstest er ikke naturlig gjennomspilling. Ingen nye spillregler,
figur-/romdata, oppdateringsrater eller lydressurser inngår i dette løftet.
