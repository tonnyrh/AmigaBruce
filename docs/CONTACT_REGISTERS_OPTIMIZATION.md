# Lokale registre i kontaktløkken

27. oktober 2026. Neste målte OP1-endring reduserer arbeid per aktiv aktør
uten å endre C64s antall spillsteg, tilstander eller kontaktpiksler.
Sanntidsakseptansen er fortsatt åpen.

## Kilde og ekvivalens

Kilden er de frosne bytene i `.reference/c64/work/untrained-memory.bin`,
SHA256 `092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Remember/T64-kandidaten er fortsatt ikke sertifisert urørt1984-utgave.

Den varme radløkken `$537E–$53E3` behandler de tre kontaktkolonnene i
original rekkefølge. Nye lokale C-variabler holder virtuelle A/X/Y og
siste sammenligningsflagg mellom observerbare punkter. Kilde-RAMs klasse-
og scratchskrivinger skjer fortsatt umiddelbart og i samme rekkefølge;
glyphpekere kan fortsatt lese bytes som en tidligere kolonne nettopp skrev.

Registerverdiene skrives tilbake før hvert eksisterende feltservicepunkt,
før klassehjelpere og ved normal eller ikke-lokal retur. Etter service
leses registre og selvmodifiserte glyphpekere på nytt. Den første
serviceavlesningen får også de faktiske N/Z-flaggene fra `$537E LDY $52`.

Grenene `$53E4–$542E` beholder kropp/fot-skillet. Direkte hjelpere skriver
samme JSR-returbytes `$53F1/$5405/$5415/$5425/$542B` på kilde-stacken.
To PLA og fortsettelsen `$52A4` beholdes. Klasseinnganger utenfor de tre
aktørene har fortsatt den instruksjonstro reservebanen. Det er ingen nye
kollisjonsbokser, AI-regler eller avkortede felt i denne endringen.

Bare denne lille radfunksjonen får målrettet `-O2`. Resten av den store
kildeoversettelsen er fortsatt `-Os`. Generell kallruting alene ble målt til
bare seks felt gevinst og var ikke tilstrekkelig; nettogevinsten nedenfor
gjelder hele den valgte register-/kallvarianten.

## Måling

Normal PAL-planlegging på68000/OCS/KS1.3 med512KiB Chip +512KiB slow,
rom1,360 spillsteg, ingen joystickinput og eksplisitt testudødelighet.
Benchmarken omfatter også fast tittelarbeid og diagnostisk bokføring; den
er ikke en direkte FPS-måling eller naturlig gjennomspilling.

| Måling | Før | Etter |
| --- | ---: | ---: |
| Medgåtte PAL-felt uten profilering | 2 085 | 2 014 |
| Tegnede bilder | 360 | 360 |
| Manglende lydserviceticks | 207 | 176 |
| Profilert radløkke, gjennomsnitt | 41,361 linjer | 36,210 linjer |

Det er3,4 % kortere samlet tid og omtrent12,5 % billigere radkall i disse
avgrensede rutene. Profilering og nettotid er separate kjøringer. Begge
profiler slår av de svært hyppige detaljpunktene med
`BL_C64_DETAIL_PROFILE=0`; de påvirket tidligere målinger vesentlig.
Enkeltmålinger har ingen statistisk garanti for alle rom, og kildefaser
kan variere når faktisk kjøretid endres.

Råbygg og rapporter ligger i
`reference/analysis/optimization-2026-10-27/rows-{before,after}-profile/`
og `rows-local-o2-timing/`. `rows-baseline/` bevarer forrige normalbygg,
kilder og utvalgte leveransebevis. `rows-direct-timing/` og `rows-local-timing/`
bevarer de mellomliggende kandidatene.

## Kontroller

`test-source-contact.ps1` sammenligner3 304 forløp/936 230 faktiske C64-
instruksjoner, alle64KiB RAM, CPU-registre, flagg, stack og returgren.
704 radforløp dekker nå alle tre aktørindeksene.224 av disse avleser også
alle ti virtuelle registre ved hvert servicepunkt mot den faktiske
instruksjonstilstanden ved `$5380`. Tilleggstilfellene krysser flere
servicepunkter og kropp/fot-grenen i samme løp. Dermed kontrolleres også synkroniseringen etter flere radgrupper.

Hele vertskjeden bestod3 034 bytevise aktørkontroller, fem integrerte
forløp/7 055 873 kildeinstruksjoner,768 aktivbitprojeksjoner,6 485 VIC-
tilfeller og de etablerte lyd-/DMA-/kopieringskontrollene.
Native A500-kjøring bestod53/53 fixtures og1 200 løkker/400 logiske steg,
med null kilde-, gjengivelses-, lyddecoder-, DMA- og aritmetikkfeil, samt
korrekt AmigaOS-retur. Største ledige Chip-blokk var52 632 byte, over
kravet49 152. Den kontrollerte reprisen hadde85 manglende lydserviceticks,
1 080 tegnede bilder/120 holdte, største holderekke1 og største vanlige
feltgap6. Forrige reprise hadde91 manglende ticks og gap7. Sanntidsporten
er fortsatt ikke bestått. Restkontrollen har42 HUD-bytes og33 uforklarte
scenebytes; ventende bakgrunnskopi forklarte0 av disse.

Normal EXE er337 976 byte, SHA256
`03a17d43c8d6e5f7ced1537f49cb11650689852595fd8f5c4c099d03733075e1`.
ADF er901 120 byte. EXE økte520 byte, `.text`390 byte og BSS er uendret.
Normal oppstart og den kontrollerte Yamo-livssyklusen i begge bildebuffere
bestod på denne binæren.

Klokkeuttaket inneholder nå aktive flagg, aktørtilstander og spawn-teller.
I en sen rom1-situasjon med `$95..$97=01/81/41`, begge fiender aktive og
alle tre i tilstand0, ble123/125/124 kildefelt og20/20/20 spillsteg målt.
Ingen kildefeil oppstod og kildeklokken fulgte PAL-tid. Omtrent seks felt
per steg i denne situasjonen er fortsatt for tregt. Den tidligere korte
oppstartsprøven, bevart som `rows-early-clock.json`, viste110/119/117 felt
og36/35/25 steg i ulike kildefaser. Dette er ikke et kontrollert før/etter-
par; fiender og kontaktsituasjon må inngå i tolkningen av slike prøver.
Kildeutgave, naturlig IRQ-/VIC-fase,
hele spillet, restbytes i scenen og fysisk A500 er fortsatt egne porter.

## Videre prioritet

Etter denne endringen ligger radløkken fortsatt øverst, men den generelle
delen av hovedsteget er nesten like dyr. Neste kildeavgrensning bør måle
hovedkjedens resterende arbeid og objektpasset `$2E39` mer presist, og
spesialisere bare en dokumentert varm rutine. Lydrapporten legger de første
forsinkelsene i spillsteget; feltservice og lydtiming må fortsatt løses
uten å hoppe over kildeoppdateringer eller slakke sanntidskravet.
