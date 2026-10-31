# Første optimaliseringsleveranse — 27. oktober 2026

Historikk for første VIC-pilot. Gjeldende kontakt-/visningsrunde er beskrevet
i [andre leveranserapport](CONTACT_OPTIMIZATION.md).

OP0 har nå en første målebane for den aktive kildemotoren. Første pilot fra
OP2 er implementert: gjenbruk av eksakt VIC-spritekontakt mellom uendrede
felt. Full sanntidsakseptanse og resten av [planen](AMIGA_OPTIMIZATION_PLAN.md)
står fortsatt åpne.

## Kildekontrakt

Uendret referanse: `.reference/c64/work/untrained-memory.bin`, SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Kandidaten er ikke bekreftet som urørt1984-utgave.

- `$15B8` kaller `$25E2`, som publiserer kildefigurene til VIC-registre.
- `$29CE` leser `$D01E` før kampfordelingen i `$29C3`.
- `$3D20` leser samme register i en romrutine; bittene for Bruce og
  prosjektilene prøves før `$407D`.
- Låsen i Amiga-versjonens eksisterende feltgrense er en akkumulert
  pikselkontakt for alle åtte sprites. Dette er fortsatt en feltmodell,
  uten sertifisert raster-/grenseområdefase.

Ingen av disse spillrutinene eller aktørreglene er endret. Cachen omfatter
bare maskinvaregrensens beregnede spriteoverlapp. Den gjenbruker resultatet
når aktive sprites, posisjoner, Y-ekspansjon, effektivt layout og samtlige
63 bitmapbytes per aktiv sprite er identiske. Bytes leses gjennom dagens
bank-/skjerm-/spritepekere, så pekeralias og endret bankinnhold oppdages.
En endret posisjon eller piksel utløser ny beregning. Resultatet OR-es inn
i `$D01E` hvert felt, også etter at kilden har lest og tømt låsen. Reset
ugyldiggjør cachen.

## Ny måling

`-SourceProfile` måler23 komponenter i native kode med PAL-linjetelleren.
Hvert kall har start/slutt, inkluderende tid og tid etter fratrekk av målte
underkall. En nestestack kontrollerer balansen. Rapporten inneholder antall
kall, sum, maksimum med rom/aktørtilstand, og histogramintervaller for
median/p95/p99. Histogrammet mettes ved65 535 treff i én bøtte; rapportverktøyet
avviser ufullstendig telling. Disse korte kjøringene har ingen metning.

Tegnetrinn får løkke-ID og gyldighetsmaske. Ikke utførte tegnetrinn rapporteres
som ugyldige, uten å gjenbruke en tidligere løkkes tid. `held_changed` skiller
et nytt kilde-spillsteg fra gjentatt hold av samme steg; dette er en
tilstandsindikator, ikke en påstand om at hver piksel nødvendigvis endres.

Tom profilering kostet139/140 linjer for32 begynn/slutt-par, omtrent4,4
linjer per par. Mange instrumentpunkter påvirker også antall felt som motoren
må hente inn. Derfor brukes separat måling uten profilering for nettoeffekt.
Eksklusiv tid inkluderer uinstrumentert arbeid og noe målebokføring; den er
ikke en syklusnøyaktig instruksjonsprofil.

## Før og etter

Råbygg, kildeidentiteter og rapporter ligger i
`reference/analysis/optimization-2026-10-27/`. `baseline/` bevarer tidligere
normalbygg og godkjente rapporter. Hvert benchmark har eget EXE/ELF/ADF,
`native.txt`, `native.json` og `identity.json`.

Begge målepar bruker68000/OCS/KS1.3 med512KiB Chip +512KiB slow, ordinær
PAL-feltplanlegging og360 ytre løkker/360 kilde-spillsteg. Ingen joystickinput,
udødelighet på som uttrykkelig testutvidelse. Dette er en belastningsscene i
rom1, ikke naturlig gjennomspilling. De to uprofilerte målingene har identiske
runtime-kildefiler bortsett fra `core/c64_rooms.c` med selve cacheendringen.

| Måling | Før | Etter |
| --- | ---: | ---: |
| Profilert VIC-kostnad, gjennomsnitt per kall |160,408 linjer |77,055 linjer |
| Uprofilert medgått aktiv PAL-tid |4 690 felt |2 827 felt |
| Tapte lydserviceticks i denne målingen |848 |261 |
| Verste registrerte presentasjonsgap |29 felt |13 felt |
| Største ledige Chip-blokk |52 632 byte |52 632 byte |
| Løkker med nyere kilde-steg holdt tilbake |358 |358 |

VIC-kostnaden falt omtrent52 % per profilert kall. Samlet aktiv tid falt
omtrent40 % i det uprofilerte måleparet. Tidtelleren inneholder også den
faste tittelsekvensen; den er ikke et rent mål på CPU-instruksjoner i spill.
Dette er ett målepar per konfigurasjon, uten statistisk usikkerhetsestimat
eller garanti for tilsvarende gevinst i alle rom. Antall felt/AI-innganger
endres naturlig når faktisk kjøretid endres; kildeutfall kontrolleres separat
med faste innganger.

Reproduksjon:

```powershell
./test-source-performance.ps1 -Label nytt-navn -Profile
./test-source-performance.ps1 -Label nytt-navn-uten-profil
```

`-Controlled` bruker ett injisert kildefelt per løkke med53 kontroller før
oppstart. Standard benchmark bruker faktisk PAL-klokke, uten disse fixturene
eller bildeopptak i målingen. Ingen av variantene erstatter normalfeltkravet,
det filbundne native kildepasset eller naturlig testing. Gamle målenavn
overskrives ikke.

## Kontroller og neste prioritet

- 6 485 piksel-/latchkontroller, inkludert uendrede felt etter tømming,
  endring i bitmap, pekere, bank, ekspansjon, aktive sprites og eksternt
  akkumulerte latchbits. Samme kontroller bestod før og etter cachen.
- 3 034 bytevise RAM-/register-/returkontroller mot faktiske kildeinstruksjoner.
- Fem integrerte forløp,7 055 873 kildeinstruksjoner, med liv, turbytte og Game Over.
- 7 540 kildebaserte SFX-felt/effektprioritetskontroller, to tittelpass og
 1 518 felt/4 554 bytevise DMA-bilder. Lydparametrene er uendret.
- Native kontroll av53 tilfeller, RAM-reserve og OS-retur rapporteres fortsatt
 i den filbundne kildeleveransen; benchmark alene er ikke et slikt pass.

Sluttkontrollen bestod53/53 native tilfeller og1 200 repriseløkker/400 steg,
med52 632 byte sammenhengende Chip-reserve, null kilde-/lyd-/DMA-feil,
null avvik i bakgrunnskontrollen og korrekt OS-retur. Feltporten er fortsatt ikke bestått: verste gap er8
felt og275 lydserviceticks mangler.587 løkker holdt tilbake nyere spillsteg,
med største sammenhengende rekke29. Dette er den kontrollerte reprisen,
ikke den uprofilerte PAL-belastningsscenen i tabellen.

Restkontrollen av bildet er nå delt:75 avvikende bytes utenfor figurgrenser,
hvorav42 i HUD-området og33 i selve scenen. HUD inneholder dynamisk poengtekst
som bakgrunnsbildet ikke har. De33 scenebytene er fortsatt uforklarte;
de er ikke godkjent som et rent bilde av at bakgrunnskontrollen ga null feil.
Tegnekø/pågående bakgrunnsendringer og faktiske figurrester må skilles videre.

Normal EXE er335 472 byte,468 mer enn utgangspunktet. Linkeren viser254
ekstra kodebytes og36 ekstra BSS-bytes; rodata er uendret. Profileringens
tabeller og kall er utelatt fra normalbygget. EXE og ADF er bygget, CLI-start
og faktisk normal-PAL-klokke er kontrollert i en separat eid emulator.
Den korte normalprøven dekker354 felt/58 steg, omtrent6,1 felt/steg i dens
situasjon. Den tidligere korte normalprøven traff andre kildefaser og gir
ikke et kontrollert A/B-par. Ingen påstand om tre-felts normalspill gjøres.

`./test-parity.ps1 -RefreshEvidence` kjører kilde-/lyd-/DMA-/VIC-kontrollene
og fornyer filbindingen etter at rapportene er generert. Fornyelsen krever
fortsatt at native kildefiler, testbygg og alle native porter samsvarer;
den erstatter ikke en native test når motorkoden endres.

Profilen viser fortsatt høy kostnad i kontakt-/klasseradene (`$537E`),
kontaktoppsettet og den instruksjonstro motorens bokføring. Dette er neste
CPU-pilot. Tegnegrensen må også avgrenses: i denne scenen ble bare to av360
bilder tegnet, mens358 nye spillsteg ble holdt tilbake. Ny timingmaskering
eller lavere spillfart er ingen løsning. Lydservice mister fortsatt ticks,
og ordinær tre-felts rytme er ikke nådd.

OP0 er ikke en ferdig profil av alle20 rom: rombytte, alle feller og
naturlig input/rasterfase må måles videre. To6000-felts normaltester,
fysisk A500 og full sanntidsakseptanse er fortsatt åpne.
