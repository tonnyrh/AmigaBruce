# Native motorløft fra milepæl 27. oktober 2026

Git-utgangspunkt: `26fb6d1`, pushet som `main` og annotert tagg
`milestone/c64-source-2026-10-27`. Arbeidet fortsetter på
`optimize/native-amiga-engine`; taggen flyttes ikke.

## Kilde og avgrensning

Frosne bytes: `.reference/c64/work/untrained-memory.bin`, SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Dette er Remember/T64-kandidaten, ikke sertifisert urørt 1984-utgave.
Ingen nye spillregler, inputfrekvenser, bevegelsestabeller eller ressurser.
PAL A500 OCS, 68000, KS1.3 og 512 KiB Chip + 512 KiB slow beholdes.

Produksjonsmotoren henter/dekoder ikke 6502-opkoder ved kjøring. Den statiske
oversettelsen beholder likevel en kilde-RAM og virtuelle registre/stack.
Dette løftet erstatter større avgrensede rutiner med direkte C-beregninger,
med samme kildeutfall. py65 kjører de faktiske bytene bare i vertskontrollene.

## Dekodede rutiner

- `$5212–$52AC`: kontaktpasset går gjennom aktør 2, 1 og 0, sjekker bit 0
  i `$95+X`, bygger masken og behandler opptil fire tegnrader. Kildens
  mellomlagring, per-aktør-service før `$5214`, pikselradtjeneste, masketabeller
  `$1167/$1239` og alle interne JSR-bytes beholdes. `$542C/$542D` kaster
  bare radens returadresse før neste aktør på `$52A4`; dette er nå en lokal
  returstatus fremfor rekursiv gjeninntreden. D=1 bruker tidligere kodebane.
- `$55AB–$55C4`: de 69 klassebytene og tre veksleflagg er en fast sammenhengende
  72-byte nullstilling. Ingen service eller alias med kildens stack finnes
  inni denne løkken. Slutt-A=0, X=255, N=1/Z=0 og uendrede øvrige flagg beholdes.
- `$2E89–$2EE9`: objekter fordeles i original rekkefølge til de opprinnelige
  handlerne. Sluttflagg svarer til sist utførte CMP/ASL, inklusive `$53`-skift
  også ved tomme celler, særtilfellet `$57`, dørområde og faretallområder.
- `$2E39–$2E88`: det samlede objektpasset leser de samme to radene og tre
  cellene per aktiv aktør. `$19` hoppes over og `$17` går gjennom `$2E10`.
  `$1A67`-tabellene `$4338/$434C/$4360/$4374` leses i original rekkefølge; `$0100` og scratch beholdes.
  Tomme celler trenger ikke lenger rekursiv generell dispatch. Faktiske
  hendelser går til opprinnelige dør-/nett-/lanterne-/farehandlere, og alle
  ikke-lokale rom-/livsreturer må passere samme stack- og ventebetingelser.
- `$31D5–$31F3` og `$32EE–$330C`: 24 binære skift med desimal dobling gir
  fire packed-BCD-bytes. Begge ekte kallere nuller BCD-bufferen først.
  Direkte binær til desimal konvertering brukes bare med denne forutsetningen;
  ellers beholdes instruksjonsbanen. `$4398–$439A` tømmes, slutt-A/X/Y og
  statusbyten etter PHP/PLP bevares. Flagg fra inne i løkken er ikke synlige
  etter PLP, som gjenoppretter samtlige inngangsflagg.

Små varme rutiner kompileres med målrettet O2. Den store genererte
`actor_code` og `-mshort`-grensen beholder tidligere innstillinger; global O2
ville øke kode-/minnekostnaden for mye. Ingen nye produksjonsbuffere tilføyes.

## Kontroller

- 3 560 kontaktkontroller, 2 003 606 faktiske C64-instruksjoner. De 256 nye
  helrutinekontrollene dekker alle aktive-aktør-kombinasjoner og 4×8
  pikselfaser. Totalt 480 kontroller sammenligner også alle virtuelle registre
  ved de eksisterende servicestedene. Hele 64 KiB, stack og retur sammenlignes.
- 65 536 klassifiseringskontroller dekker alle A- og `$53`-verdier mot alle
  elleve originale retur-/handlergrenser; 2 473 160 kildeinstruksjoner.
- 480 hele objektpass med alle romnumre og aktørmasker, tomme celler,
  avviste dørprober inne på avsatsen og `$62`-nettets fortsettelse gjennom
  `$2EA9`; 194 645 kildeinstruksjoner. Tilstandene er injiserte og fastsetter
  ikke naturlig rom-/fareparitet. De endrer ikke handlernes spillregler.
- 2 852 poengkontroller over 1 042 24-bits tall, begge løkker, 64 kombinasjoner
  av statusbiter og stackgrenser inkludert SP=0/255; 1 791 056 kildeinstruksjoner.
- Eksisterende 3 034 aktørkontroller og fem integrerte liv-/spillermodusforløp
  beholdes. Native 53-kontrollport, lyd/DMA/VIC og normalbygg kontrolleres
  etter siste runtime-endring; rutinetest alene godkjenner ikke A500-bygget.

## Målinger

Målebygg med kilde-/binæridentitet og rårapporter bevares under
`reference/analysis/optimization-2026-10-27/`. Kontrollert input er stille,
udødelig Bruce i rom 1 med begge kildefiender; faktisk PAL-planlegging,
360 kildespillsteg, uten bildeopptak i måleområdet. Milepælen og de første
trinnene bruker 360 ytre løkker; sluttmålingen bruker 370 løkker for å
fullføre samme antall faktiske C64-spillsteg.
Tallene inneholder også den faste tittellyddelen og diagnostikk.

| Trinn | Medgåtte PAL-felt | Tapte lydticks | Tegnede / kort holdte bilder |
| --- | ---: | ---: | ---: |
| Pushet milepæl, `rows-local-o2-timing` | 2 014 | 176 | 360 / 0 |
| Samlet kontakt + objektklassifisering | 1 933 | 68 | 360 / 0 |
| Direkte poengkonvertering | 1 713 | 17 | 337 / 23 |
| Samlet objektpass og kontaktbuffer, 370 løkker / 360 steg | 1 688 | 16 | 322 / 48 |

Siste sammenlignbare trinn bruker 16,187 % færre målte PAL-felt enn milepælen.
En tidligere sluttmåling ga 1 628 felt, men hadde bare 350 spillsteg i
360 løkker og er uttrykkelig forkastet som før-/etter-sammenligning.
Den raskere motoren ventet korrekt i ti løkker på kildeklokkens neste steg.
Ingen ventere eller spillsteg er fjernet for å få bedre tall.
Største ledige Chip-blokk er uendret 52 632 byte. Lengste rekke kort holdte
bilder er ett; største registrerte gap er fortsatt åtte felt i denne målebanen.

Tegneplanleggingen er uendret, men får andre beslutningstidspunkter når
CPU-arbeidet blir kortere. Derfor er feltforskjellen et samlet resultat for
målebanen, ikke en isolert prosent CPU-gevinst eller garanti i alle rom.
Profilert eksklusiv spillstegstid falt fra 263,219 til 112,417 rasterlinjer
etter poengendringen; profileringskostnad og kjøre-/IRQ-faser påvirker også
slike sammenligninger. Historiske før-/etterfiler overskrives ikke.

Full sanntidsport, naturlig spilling, rasterfase, alle rom under belastning
og fysisk A500 står fortsatt som egne akseptanser. Tapte lydticks er ikke
løst ved å hoppe over spillsteg, endre C64-regler eller godta en svakere port.

## Normalbygg og kildeklokke

Normal EXE er 341 160 byte, 3 184 mer enn milepælens 337 976 byte.
Kode øker fra 0x2e4a6 til 0x2edb4 (+2 318 byte), rodata øker 16 byte,
og BSS er uendret 0x29c48. Resten av EXE-økningen er fil-/relokasjonskostnad.
Ingen nye Chip-buffere; målebanen har fortsatt 52 632 byte sammenhengende
Chip-reserve mot portens 49 152. Stackreserve er ikke en ny målt akseptanse.

En kort normalprøve uten fiender gikk rundt tre felt per steg. Med begge
kildefiender aktive var tre intervaller 83/18, 114/22 og 125/24 felt/steg,
altså cirka 4,6–5,2 felt per steg. Den tidligere prøven var rundt 6,2 med
andre aktør-/IRQ-faser. Dette er ikke et kontrollert A/B-par, og tre felt
med begge fiender er fortsatt ikke nådd. Ingen kildefeil ble registrert.

Normal EXE og faktisk ADF er startet i separate eide emulatorer. Meny og
nytt spill, rom 1/2, kildeklokke og feilkode er kontrollert. ADF-proben
måtte vente til disklasting og intro var ferdig; første for tidlige probe
ble forkastet. `source-native-boot.json` binder de beståtte prøvene til EXE,
ADF, faktiske bitplanes og klokkerapporter. AmigaDOS-kommandoen `start` er
oppdatert og har samme SHA256 som normal EXE. Yamos synlig → skjult → tilbake
består igjen i begge bildebuffere i rom 2. Dette er kontrollerte prøver,
ikke en naturlig full gjennomspilling.

## Siste native samlekontroll

53/53 originale RAM-/registerfixturer består i 68000-bygget. Den separate
kontrollerte reprisen fullførte 1 200 løkker/400 spillsteg, gjenopprettet OS
og rapporterte null kilde-, lyddekoder-, DMA-, pikselkontroll- og aritmetikkfeil.
979 bilder ble tegnet og 221 holdt kort; lengste holdrekke er ett felt.
81 lydserviceticks manglet, og største gap er fem felt mot feltportens ett.
Feltporten er derfor fortsatt ikke bestått. Dette er et annet testforløp
enn den faktiske PAL-belastningsscenen med 16 tapte ticks i tabellen.

Bildediagnosen er uendret: 42 HUD-bytes og 33 uforklarte scenebytes utenfor
figurgrenser, med null ventende kopier. De 33 bytene er fortsatt en åpen sak.
Profilert objektpass falt fra 111,083 til 62,619 eksklusive rasterlinjer per
kall; øvrig spillsteg falt fra 263,219 til 111,011. Kontakt-/VIC-arbeidet er
nå blant de største gjenværende CPU-kostnadene. Neste løft bør måle og
optimalisere disse og visnings-/lydpubliseringen videre med samme kildeporter.

Testbyggene arkiveres nå med EXE-/ADF-hash i `native-builds/` før kjøring.
Sluttkontrollen krever at både arkivet og det faktisk kjørte byggutdataet
fortsatt har samme hash. Senere ytelsesbygg kan dermed ikke overskrive
binærbeviset for en tidligere godkjent native kjøring. Før arkiveringen ble
en godkjent kjørings byggutdata overskrevet av en ny måling; filporten avviste
dette, og sluttesten ble kjørt på nytt med arkiverte binærer.

## Neste mål fra siste profil

Den profilerte målebanens eksklusive tid fordeler cirka 27,1 % på
kontaktoppsett/masker/rader, 11,4 % på VIC-låsen og 11,1 % på visning,
bakgrunn, restaurering og tegning. Ventetid er separat og skal ikke fjernes
som en ytelsesforbedring. Prosentene inkluderer måle-/testbokføring og er
ikke en generell profil av alle rom.

Neste avgrensede forsøk er kontaktadresseforberedelsen `$530A` og masken
`$52AD`: målrettet kompilering eller lokal registerbruk med samme alias-,
stack- og servicekontroller, før større cacheendringer vurderes. VIC- og
spritepublisering må fortsatt oppdage enhver relevant bitmap-/bank-/peker-
endring. Å anta uendret bitmap fordi en figur står stille er ikke en gyldig
optimalisering. Den testede leveransen her beholdes som nytt sammenligningspunkt.
