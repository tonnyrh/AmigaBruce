# Bruce som OCS hardware-sprites: separat test, 31. oktober 2026

Checkpointet før forsøket er pushet til `origin/optimize/native-amiga-engine`:
`ccf9572be54db49a33638d52e73c74c9f5eec740`.
Vanlig motor, kildebasert kollisjon og normal EXE/ADF beholdes som utgangspunkt.
Testutgaven og råmålingene ligger separat under
`reference/analysis/hardware-bruce-2026-10-31/`.

## Hva som er flyttet

Bare Bruce tegnes med hardware-sprites. Yamo, Kage og prosjektilene bruker
fortsatt blitteren. Bruce beholder samme rippede bildepiksler, maske,
ankere, positurvalg, retning og plassering som BOB-versjonen. Svart er
ugjennomsiktig pen1; gult er pen2. Transparente punkter er pen0.
Tre vanlige 16-pikslers kanaler håndterer maksimal bredde36. Ingen attached
sprites eller multiplexing trengs for denne figuren.

Første utgave brukte en egen556-byte Chip-blokk. Den siste bruker560 byte
i de eksisterende Copper-buffernes ubrukte halvdeler: hver1024-byte blokk
har en terminert Copper-liste før byte512 og tre DMA-bilder/nullheader ved
512..791. Synlig front og klargjort bakside har egne data. Stillestående
positurer gjenbruker payloaden; posisjon og pekere oppdateres ved publisering.
Det gjøres ingen ny Chip-allokering.

Lasterutinen skjuler sprite-DMA og nuller kanaldata og begge listens pekere.
Spill-/menyvisning styres separat fra PAL-logikklokken, slik at også den
kontrollerte testavspillingen kan bruke hardware-sprites. De to lydpollene
fra den tidligere tegnestien beholdes. Normalutgaven har ingen bilde-selftest
under oppstart; den kjøres bare i diagnostikkbildene.

## Harrier-koden som ble undersøkt

`C:/vscode/_EXT/harrierattackreloaded/amiga/main.c`, SHA256
`b3a0e448128b44a0ff08aa46d0d8e5e75f16c055bca96566611478a9e1499d52`:

- `copSetSprites`, rundt6038: eksplisitte pekere for alle åtte kanaler.
- `setHardwareSpritePosition`, rundt10316: HSTART/VSTART/VSTOP og niende bit,
  knyttet til det faktiske visningsvinduet.
- `buildAttachedSpriteFromCpcPlusHalvesMapped`: sammenkobling for flere farger.
  Bruce trenger bare to synlige farger, så denne kostnaden unngås.
- `selectHardwareProjectileChain` / `updateHardwareProjectileChain`, rundt26330:
  sorterte vertikale bånd, to konservative blanke linjer og neste header som
  erstatter forrige stopphode. Dette er undersøkt, men ikke nødvendig her.

De faktiske rippede maksbreddene er Bruce36, Yamo44 og Kage28:3+3+2 kanaler.
Alle tre kan dermed i prinsippet passe i åtte kanaler samtidig. Delte
fargeregistre, tegnerekkefølge og alle posisjoner må håndteres før en slik
videreføring. Ingen generell multiplexer er lagt til i denne testen.

## Kildegrunnlag og kontroller

Frossen Remember/T64-kandidat, SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Kandidaten er fortsatt ikke sertifisert som urørt1984-utgave.
De eksisterende uttrekkene følger faktisk spritekode `$2584/$25E2` og
tabellene `$59BD/$5A8F/$5B61/$5C33/$5CBF`. Ingen ny kunst er generert.
C64-kjerne og spriteuttrekk er uendret gjennom forsøket.

Hvert tidsbilde består710 native kontakt-/kopikontroller. Spritebildene
har i tillegg176 kontroller: alle70 poseringer/retninger i begge DMA-buffere,
samt36 posisjoner som dekker lave koordinatbiter og vertikalt byteomslag.
Kontrollene kjøres før den målte spillbanen.

Både v2 og v3 består en separat full native-prøve med53 fixturer og
1200 løkker /400 kildeoppdateringer. v2 har52072 byte og v3/v4 har52632 byte
i største ledige Chip-blokk. Kilde-, DMA-, aritmetikk-, bilde- og
presentasjonskontrollene har ingen registrerte feil. Den kontrollerte
én-felt-per-løkkeprøven beholder sine lydtap; den må ikke forveksles med
den separate faktiske PAL-tidsmålingen.

## Avgrensede målinger

| Prøve | BOB, PAL-felt | Hardware, PAL-felt | Tapte lydticks, BOB/hardware |
| --- | ---: | ---: | ---: |
| Første utgave |1411|1394|0/1|
| v2, beholdt lydpolling |1404|1394|0/0|
| v4, eksisterende Copper-plass og rettet prioritet |1411|1402|0/0|
| v4, skriptet bevegelse |1502|1492|15/13|

Hver rad har360 kildeoppdateringer med begge fiender aktive i diagnostikken.
v4-paret gir omtrent0,6% kortere samlet kjøretid i denne banen. Dette er
bare Bruce, og den tunge kildebaserte kontaktberegningen er beholdt.
Tidsbyggenes største Chip-blokk er85408 byte for BOB og69016 for v4-sprites;
større diagnostikk-/kodefotavtrykk endrer lastesituasjonen selv uten ekstra
Chip-allokering. Fulltestens mer relevante reserve er uendret52632 byte.

Bevegelsesparet bruker samme private v4-kode med en240-stegs joysticksyklus:
40 høyre/opp/ild,40 venstre/opp/ild,40 høyre,40 venstre,40 opp og40 ned.
Det er en skriptet diagnostikk med udødelighet, ikke naturlig gjennomspilling.
Råresultatene og de faktiske private kompilatorinngangene bindes av
`tools/verify_hardware_bruce_probe.py`.

Native DMA-inspeksjon kontrollerer de faktiske publiserte Copper-pekerne,
Chip-dataene, DMA-flaggene og pikslene mot de rippede PNG-filene. Dens
komposittbilder rekonstrueres fra levende bitplanes og sprite-data i
programvare; de er ikke skjermbilder av emulatorens videoutgang.
Den endelige v4 er ogs� kontrollert med faktisk WinUAE-videoutgang,
lagret som `v4/native-display/video-window.jpg`. Bruce er synlig uten
�penbare skj�ter. Native inspeksjon av et slag bekrefter to samtidige
spritekanaler uten pikselfeil. Tre kanaler dekkes av formatkontrollene,
men er ikke dokumentert som naturlig observert spillpositur.
Menyretur er kontrollert mot den komplette menybitmappen og faktisk
videoutgang; sprite-DMA er avsl�tt i menyen.

v1�v3 hadde feil prioritet: korrekt DMA-innhold kunne skjules bak det
fargede playfieldet. Disse er kun tidligere tidsfors�k. v4 bruker
BPLCON2=$0024; PF2P=4 legger spriteparene foran det vanlige playfieldet.
Dette f�lger [Hardware Reference Manual, tabell7-2](https://amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node0159.html).
Begge Copper-lister bruker samme prioritet. Den endelige verifikasjonen
krever denne innstillingen i de faktiske publiserte listene.

BOB-baselinene gjenbruker v3-m�lingene fordi v4-BOB-bildenes `.text`,
`.rodata` og `.data` er byteidentiske, med samme BSS-st�rrelse.
Dette er kontrollert separat for begge ruter i `v4/bob-baseline-linkage.json`.
R� EXE-filer er ikke identiske, siden blant annet debug-stier varierer.
Bevegelsespr�ven har fortsatt13 tapte lydticks mot15 i BOB-baselinen;
lyd-/ytelsesproblemet er dermed ikke l�st av denne endringen alene.

## Starte testen

Etter at den lokale testutgaven er bygget:

```powershell
.\launch-hardware-bruce.ps1 -ShowWindow
```

Bruk `-Disk` for ADF. Testen har egen oppstart og WinUAE-konfigurasjon.
Ved vanlig CLI-oppstart starter `start` samme hardware-utgave fra AmigaDOS.
ADF-en startes separat fra disk; `start`-aliaset gjelder CLI-oppsettet.
Eksisterende hovedmeny og Shift+D-valg fungerer som før.

Ingen samlet50Hz-akseptanse, naturlig VIC/IRQ-fase, komplett naturlig
gjennomspilling eller fysisk A500-test er lukket av dette forsøket.
