# M3 — spillbar kampkandidat

Historisk tekst fra før kodegjennomgangen 25. oktober. Se
[gjeldende kampstatus](../M3_COMBAT.md) og [rettelsene til T01–T18](../TEST_AUDIT_2026-10-25.md).
Eldre treffbokser, rekkefølge, negative-helse-regler og målinger under er ikke
godkjenning av nåværende C64-paritet.

Dato: 2026-10-20. **Spillbar kandidat, ikke fullført C64-paritetsgodkjenning.**

Bygg med `.\amiga-build.ps1`, start med `.\amiga-run.ps1`.
Bevegelse, klatring og liggende stilling bruker samme kontroller som før.
Klatring har to egne positurer med vekslende armer og bøyde bein. Fasen følger
tegnet høyde, slik at stillstanden fryser posituren og nedklatring snur forløpet.
Dette er egen skisseanimasjon; spillfart og kollisjonskoordinater er uendret.
Hold ild uten retning for slag; gå noen steg og hold retning + ild for flyvende
spark. Ninja kommer inn først, Yamo senere. Begge forfølger og angriper Bruce.
Fiendene kan også skade hverandre. Escape avslutter til AmigaOS.

Gul helsestolpe til venstre er Bruce, grønn i midten er Yamo, blå til høyre er
Ninja. Figuren blinker etter korte treff. Flyvende spark slår figuren ned,
og den ligger synlig mens den sklir bakover. Etter nederlag kommer figuren tilbake.
Dette er en kamparena med automatiske nye forsøk; livbegrensning, Game Over og
romprogresjon inngår ikke i denne kandidaten. Grafikken er egen skissegrafikk.

## Regler og kildegrunnlag

| Regel | Kandidaten | Evidens / begrensning |
| --- | --- | --- |
| Starthelse Bruce / Yamo / Ninja | 36 / 20 / 7 | Native COMBAT-0001 |
| Skade sai / flyvende spark | 2 / 7 | Native helseendringer og disassembly |
| Spark mot hoppende Bruce | Tillatt når treffvilkårene er oppfylt; hopp gir ingen generell immunitet | WALL-0001, wall-jump-right, steg 354→355: Bruce i hopptilstand 7, Yamo i sparktilstand 12, helse 32→25 og knockdown 19. AIR-COMBAT-0001 dokumenterer hendelsen; eksakte pikselmasker er fortsatt åpne |
| Sai-treffvindu | Gjenstående teller 7–1; oppvarming 19–8 skader ikke | $2A7B–$2A80 verifisert mot fryst kandidatminne; tidligere for tidlig treff er rettet |
| Sai-retning og nærgrense | Bare foran Ninja, minst 8 Amiga-piksler mellom sentrene | $2A82–$2A8B og $2C54–$2C6F; største rekkevidde og pikselmasker fortsatt foreløpige |
| Slag/spark nærgrense | Bare foran angriperen, minst 12 Amiga-piksler mellom sentrene | $2AA5/$2ADB bruker samme retningsfunksjon med grense seks C64-halvpiksler; overlappende blokkout-bokser gir ikke alene et treff |
| Synlig slagfase | Alle fire slagsteg kan treffe; samme rekkevidde og skade | Rettet 2026-10-22: første og siste tegnede slagsteg var feilaktig uten treff. $2A63→$2AA5 har ingen egen tellergate for slag; C64s eksakte sprite-pikselkontakt er fortsatt åpen |
| Skade slag / falltreff | 3 / 5 | Disassembly; fallgrenen kontrollert i kandidatens snapshot |
| Nederlag | Helse < 0; null lever | Kandidatens fortegnstest |
| Falltreff | Fri falltilstand, minst 10 px høydeforskjell, begrenset kvote | Instruksjonsgrunnlag; C64s sprite-pikselkollisjon er ikke implementert |
| Fallkvote | To, fylles etter 256 PAL-felt | Egen fase, kvantisert til tre-felts spillsteg |
| Første inntreden Ninja / Yamo | 96 / 232 spillsteg | Målt fra oppvarmet snapshot; ikke målt fra kald originalstart |
| Første bevegelse Ninja / Yamo | Steg 112 / 259 | Alle fire native forløp; egen inngangspause etter spawn |
| Fiendegange | 4 px per spillsteg | Målt før plattformkant; ingen spillerakselerasjon |
| Fiende ved dør | Forlater spillerens rom og kommer inn igjen etter romteller; står ikke og løper inn i den åpne grensen | ENEMY-EDGE-0001: Ninja ut steg114 ved X302/Y98, inn igjen274 etter160 steg, første venstresteg290. Hele navigasjonen er fortsatt åpen |
| Angrepsvalg | Ninja sai; Yamo slag/spark; behold retning og bruk retrett | C64-instruksjoner $230B–$2404 kontrollert mot kandidatminnet; full ruteparitet åpen |
| Skadereaksjon | Sai 3, slag 4, spark 12, falltreff 8 spillsteg | Tellere i $2BA9–$2C1B; første steg skjer ved treff |
| Knockdown | Liggende, baklengs glidning 4 px per steg; levende fiender stopper før siste steg | $2440–$24B0; Ninja har særskilt ekstra forskyvning ved teller 10 |
| Vending før rekyl | Ved sai, slag og spark vender offeret motsatt av angriperen før baklengs bevegelse | $2B46–$2B4B; manglende vending ved treff bakfra er rettet. Falltreff bruker en separat gren uten denne vendingen |
| Retrett | Mål 30 px fra Bruce, minst 5 steg; snu ved slutten, eller straks ved 66 px avstand bak ryggen | C64 bruker halve X-piksler; disse avstandene er omregnet til Amiga-koordinater |
| Restitusjon / respawn | Fiendepause 6 steg, etter spark 24; respawn 96 etter synlig nederlagssekvens | Pausene er instruksjonsbasert; døds- og respawnforløpet er fortsatt en kandidat |

`core/combat.c` skiller fiender og kamp fra den målte bevegelseskjernen.
`BlTarget` beholdes bare som isolert regresjonslaboratorium i den eldre
autotesten. Den passive dukken brukes ikke i vanlig spillmodus.
Figurposeringene for Bruce, Ninja og Yamo forhåndsberegnes i CPU-minne; skjermen
tegnes med forhåndsforskjøvne byte og masker (218 400 byte CPU-cache).
Maskerte figurer og bakgrunnsrestaurering bruker OCS-blitteren. En 1024-byte
arbeidsbuffer og to 40 KiB rombilder ligger derfor i Chip RAM etter første M4-del.
Autotesten reserverer nå totalt 166 944 byte eksplisitt Chip RAM.

## Testing

- `.\test-core.ps1`: bevegelsesregresjoner, angrepsvalg, skade, gjentatte treff,
  null-/negativhelse, liggende immunitet, fallkvote, naturlig jakt og respawn,
  samt 100 000 deterministiske kampsteg.
- `.\test-parity.ps1`: eksisterende C64-regresjoner og fire komplette
  kampforløp. Alle avvik logges i `candidate-combat.json`. Inntreden, første
  bevegelse og sju ti-stegs gangvinduer passerer; Yamos åttende vindu består av
  to steg før han forlater rommet i originalen. NPC-utgang og Ninjas retur er
  nå kontrollert særskilt i [ENEMY-EDGE-0001](parity/evidence/ENEMY-EDGE-0001.md);
  øvrige romgrenser og hele forløpet er fortsatt åpne.
- `python tools/analyze_combat_reactions.py`: atten instruksjonskontroller mot
  fryst C64-minne og fem påfølgende intervaller med 4 px rekyl i native opptak.
  Yamos fulle knockdown-varighet er foreløpig utledet fra kode, ikke målt i et
  eget naturlig opptak av Yamo som treffes av spark.
- `.\test-amiga.ps1 -CombatTest -Disk -TestFrames 6000`: faktisk kampkode fra
  ADF, begge fiender, helsetreff, Bruce-nederlag/respawn og målt feltflyt.
  De første 3000 feltene er uten input, så holdes ild i 3000 felt. Sluttilstanden
  sammenlignes med samme 2000 spillsteg kjørt på vertsmaskinen.
- `.\test-amiga.ps1 -TestFrames 1800`: eldre isolert rute med CIA-tidsmåling.

Resultater og kildeidentiteter lagres under `reference/validation/`.
Ingen full fiendeparitet påstås av hosttester eller A500-ytelsesmåling.

## Målt leveranse

Full ADF-prøve: 6000 faktisk tegnede bilder, uten logisk oppvarmingssnarvei.
Det gir 2000 spillsteg: 61 treff, seks fiendenederlag, tre Bruce-nederlag og
tre respawn. Alle sju kontrollerte sluttverdier er identiske på 68000 og MSVC.
Maksimalt ett PAL-felt mellom visninger utenom den eksplisitte skjermdumpen;
ingen felt tapt i den fullførte prøven, og Copper publisert på linje 301–302.
Største ledige Chip RAM-blokk etter lasting: 272 360 byte i ADF-prøven.
Det er en måling av dette forløpet i den oppgitte emulerte profilen.

Tidligere målebygg hadde overskridelser og er ikke godkjenningsgrunnlag.
Den fullførte byggvarianten har både feltteller og uavhengige HSync-prøver.
Råfeltet `first_missed_hsync` er en diagnostisk terskeloverskridelse ved 314
HSync-pulser, ikke en separat dom om tapt skjermbilde; samplingsfasen varierer.
Se den kildehash-låste `a500-m3-combat.json` for faktiske tellere.

## Gjenstår før M3 godkjennes

Mål komplette angreps-, skade-, døds- og respawnsekvenser fra samme C64-baseline
med originalens tilstandstellere. Sammenlign fienderuter og tider direkte, og
avklar prioritet ved samtidige treff, livtap og reset av omverdenen. M2s åpne
landings-, vegg- og klatrenettavvik påvirker også fiendenes navigasjon. Disse
avvikene står fortsatt åpne i paritetsregisteret. Den valgte 1984-originalens
utgaveidentitet er fremdeles ikke bekreftet.

Emulatorprofilen setter `synchronize_clock=no` eksplisitt. Dette hindrer at en
vertsklokkesynkronisering brukes som tidsgrunnlag for CIA-måleren. Innstillingens
kobling til TOD finnes i [WinUAEs konfigurasjonskode](https://github.com/tonioni/WinUAE/blob/master/cfgfile.cpp)
og [CIA-kode](https://github.com/tonioni/WinUAE/blob/master/cia.cpp). Dette alene
er ikke dokumentasjon på årsaken til et bestemt tidligere tidsutslag.

For korte ytelsesdiagnoser finnes `-CombatWarmupSteps`. Prefikset kjøres da
uten tegning før den målte sekvensen. Slike resultater heter `a500-m3-debug.json`
og godtas ikke som den fullstendige 6000-bilders prøven; der må oppvarming være null.
