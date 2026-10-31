# Yamo i rom2 og neste ytelsesrunde

27. oktober 2026. Brukerens `27.10.2026.uss` ble lest uten endring. SHA256:
`a0b53ffc9e88dbf9377271e50ae00b30818bac494efc4de79032575fd1c712a0`.
Uttrekk og tilstandsrapport ligger i `reference/analysis/yamo-r02-2026-10-27/`.
Den reproduserbare leseren er `tools/inspect_source_snapshot.py`.

## Feilen i bildet

Kilde-RAM i lagringen viser rom2 og Yamo med `$96=$80`, X=128, Y=145,
helse15 og respawn-venteteller `$5E=89`. Kage har `$97=$41` og er aktiv.
`$D015=$13` aktiverer Bruces og Kages VIC-komponenter; Yamos er slått av.

De faktiske C64-bytene gjør følgende:

- `$17BE–$17C2` tester `$95,X AND #$01` før aktøroppdatering.
- `$2588–$258C` og `$25EF–$25F3` tester samme bit før spritebygging og
  publisering. Kontroll-/AI-biter alene betyr ikke en synlig aktør.
- `$3001–$3023` fjerner bit0 og slår av aktørens VIC-komponenter. Øvrige
  kontrollbiter beholdes. `$81` kan dermed bli `$80`.
- `$0D0F–$0D1B` venter på `$5E=0` før ny Yamo-inntreden når bit0 er null.

Amiga-projeksjonen brukte `flags!=0`. Den tegnet derfor en fjernet fiende
på gammel posisjon. Den bruker nå `flags&1`. Eksisterende restaurering av
begge bildebuffere fjerner den tidligere tegningen; kilde-AI og respawn
kjøres videre med originaltilstanden. Gamle USS-filer inneholder gammel
programkode; selve USS-filen blir ikke endret av et nytt bygg.

`test-source-visibility.ps1` sammenligner alle256 flaggverdier for tre
aktører med de tre faktiske C64-grenene:768 projeksjoner/6 912 kilde-
instruksjoner. Testen kontrollerer også at projeksjonen ikke endrer kilde-RAM
utover de uttrykkelig injiserte flaggene.

## Ekvivalent kontaktforberedelse

`$530A–$537D` er oversatt til en direkte C-rutine for binærmodus. Spillets
CLD setter denne modusen. Den beholder de tre ordnede attributt-/glyph-
lesningene, kolonnegrensen40, toggling og klassebytter, skriver hver intern
JSR-returbyte og setter de samme selvmodifiserte operandene ved
`$5381/$539B/$53B5`. Slutt-A/X/Y/C/Z/N/V/D og SP kontrolleres.
Desimalmodus beholder den tidligere instruksjonsbanen. Tilfeldig injisert
D=1 viste et eksisterende NMOS-flaggavvik i generell ADC; det brukes ikke
som godkjenning av den nye D=0-banen og er en separat åpen kontrollrest.

De3 240 kontaktkontrollene kjører825 140 faktiske kildeinstruksjoner.
736 nye adresseforløp inkluderer X/Y-kanter, blank tredje kolonne,
stack-/klasse-/kodealias og adresser som krysser `$FFFF`. De eldre
maskeforskyvnings-, klasse- og ikke-lokale returkontrollene er beholdt.
En skrive-løkke ved `$55AB` og en første generell `$530A`-variant ble målt
uten netto gevinst og forkastet. Visningen kopierer heller ikke lenger
44 historikkbytes to ganger per aktør; kildehistorikken i RAM er uendret,
og den kanoniske tegnebanen bruker den ikke.

Kildegrunnlaget er `.reference/c64/work/untrained-memory.bin`, SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Remember/T64-kandidaten er fortsatt ikke sertifisert urørt1984-utgave.
Naturlig rasterfase og gjennomspilling er egne akseptanser.

## Målinger og kontroll

Råbygg og identiteter ligger under `reference/analysis/optimization-2026-10-27/`.
`visibility-final-all-timing/` bruker begge fiender, mens
`visibility-final-none-timing/` bruker en uttrykkelig testrestriksjon som
holder fiendene inaktive, deres inntredentellere ikke-null og deres faktiske
VIC-komponenter avslått. Dette er kostnadsfordeling, ikke en spillregel
eller bevis på naturlig C64-oppførsel. Kildemotoren kjøres ellers likt.
Begge bruker PAL OCS/68000/KS1.3,512+512KiB og360 kilde-spillsteg.

| Måling | Forrige bygg | Nytt, fiender tillatt | Nytt, test uten fiender |
| --- | ---: | ---: | ---: |
| Medgåtte PAL-felt | 2 325 | 2 085 | 1 564 |
| Tegnede bilder | 360 | 360 | 360 |
| Manglende lydserviceticks | 96 | 207 | 0 |

Den ordinære målebanen er10,3 % kortere enn forrige bygg. Forskjellen til
prøven uten fiender bekrefter kostnaden du opplever. Dette er korte ruter
med ulike naturlige kildefaser når kjøretiden endres, ikke et mål for alle
rom. Den faste tittelsekvensen inngår i totalen. Lydservice er en åpen feil;
flere manglende ticks i denne målingen skjules ikke av den raskere totalen.
Full feltakseptanse er fortsatt ikke oppnådd.

Den samlede kontrollen bestod3 034 bytevise aktørkontroller, fem integrerte
forløp/7 055 873 kildeinstruksjoner,3 240 kontaktkontroller,768 aktivbit-
projeksjoner,6 485 VIC-tilfeller og lyd-/DMA-/kopieringskontrollene.
Native A500-kjøring bestod53/53 fixtures og1 200 løkker/400 logiske steg,
med null kilde-, gjengivelses-, lyddecoder-, DMA- og aritmetikkfeil.
Den hadde91 manglende lydserviceticks,1 080 tegnede bilder,120 holdte,
største holderekke1 og største vanlige feltgap7. Sanntidsporten er ikke
bestått. Største ledige Chip-blokk var61 592 byte; minimumskravet er49 152.
Restkontrollen har fortsatt42 HUD-bytes og33 uforklarte scenebytes.

En separat normalprosess i rom2 brukte injiserte kildeflagg `$81→$80→$81`
og originalens VIC-komponentmasker. Begge faktiske bildebuffere ble tegnet,
tømt og tegnet igjen uten kildefeil. Bildene viser
[Yamo skjult](images/session-yamo-hidden.png) og
[Yamo tilbake](images/session-yamo-returned.png). Rapporten
`reference/validation/source-visibility-native.json` markerer denne testen
som kontrollert injeksjon, ikke naturlig C64-gjennomspilling.

Slutt-EXE er337 456 byte, SHA256
`364a711483fca983ce559ee9a327ae647d1f83ed0f86ed3189c7fdf42f50c7cc`.
ADF er901 120 byte. Mot forrige EXE økte `.text`920 byte og BSS er uendret.
Tre korte normalprøver målte119/116/117 PAL-felt med23/24/23 spillsteg;
kildeklokken fulgte PAL-tid og ingen kildefeil oppstod. Omtrent fem felt per
steg er fremdeles tregere enn tre-feltsmålet. Det er fortsatt nødvendig med
naturlig nytest av død, rombytte og inntreden.
Tidligere måling og åpne sanntidskrav står i [68000-rapporten](VIC_NATIVE_OPTIMIZATION.md).
