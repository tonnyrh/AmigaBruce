# Alle tre figurer som OCS-sprites, 31. oktober 2026

Separat lokal v5-test etter checkpoint `ccf9572`. Vanlig motor, normalbygg,
kilde-RAM, C64-regler og tidligere testutgaver er uendret. Ingen ny push.

## Tegning og minne

Bruce bruker kanal0–2, Yamo3–5 og Kage6–7. Dette beholder eksisterende
BOB-tegnerekkefølge: Kage, Yamo, Bruce. Alle spritepar deler svart pen1,
gult pen2 og grønt pen3. Yamo bruker svart/grønt, Bruce svart/gult og Kage
svart. Ingen nye bildepiksler eller nye treffbokser er laget.

Alle tre passer i åtte vanlige16-pikslers kanaler. Ingen attached-sprites
eller multiplexing trengs. Copper-listen er252 byte. Åtte92-byte DMA-bilder
og en4-byte nullheader ligger ved byte256–995 i hver eksisterende1024-byte
Copper-allokering. Totalt1480 byte reserveres i allerede allokert plass;
ingen ny Chip-allokering. Det eksisterende dekomprimerte figurcachet beholdes.

Den private native formatprøven dekker alle210 rippede positur-/retningsbilder
i begge buffere og36 kontrollordposisjoner:456 kontroller uten pikselfeil.
Levende DMA-peker-/fargekontroller har også observert alle tre figurer,
begge buffere og et slag med to kanaler. Dette beviser ikke at alle positurer
er naturlig gjennomspilt. Faktisk WinUAE-video er lagret separat fra
programvarekomposittene. Menyretur og ADF-oppstart er kontrollert.

## Avgrensede tidsmålinger

PAL A500 OCS68000,512KiB Chip+512KiB slow,360 kildeoppdateringer, begge
fiender aktive. Hvert bilde består også710 eksisterende kontakt-/kopikontroller.
Bevegelsesbanen bruker tidligere dokumentert240-stegs joysticksyklus og
diagnostisk udødelighet; den er ikke naturlig gjennomspilling.

| Bane | BOB, PAL-felt | Alle sprites, PAL-felt | Kortere tid | Tapte lydticks, BOB/sprites |
| --- | ---: | ---: | ---: | ---: |
| Fast input |1411|1395|1,1%|0/1|
| Skriptet bevegelse |1502|1481|1,4%|15/16|

Gevinsten er liten og lydtapene er ikke løst. Dette er enkeltpar av
kontrollerte målinger, ingen generell hastighetsgaranti. Utgaven beholdes
derfor som privat forsøk. CPU-arbeidet mot rommets kontaktklasser og den
kildebaserte aktørlogikken består. Kostnaden kan ikke anslås ved å gange
Bruce-alene-gevinsten med tre.

Alle testkjørere monterer de private v5-mappene direkte. Ingen private
testfiler kopieres over `amiga/out`. Den første private oppstarten feilet
på en feilmontert mappe; den tomme r01-mappen er ikke en måling.

## Kollisjonsobservatøren erstatter ingen regler

En egen `moving/observe`-variant leser CLXDAT ved skjermpublisering og
sammenligner spritegruppebitene med en CPU-referanse for de publiserte
bildemaskene. CLXCON=$F000 inkluderer alle oddetallskanaler. Bare bit9–14
brukes; playfield-bitene representerer ikke C64-kontaktklassene.
Referanseberegningen er diagnostikk og utelates fra vanlig v5-spill.

Observasjonen ga460 prøver,22 med forventet gruppeoverlapp. Ingen prøve
manglet en forventet gruppebit, men fire prøver hadde ekstra gruppebiter.
Årsaken til disse fire er fortsatt uavklart. Akkumulert OR av begge sider
var$2A00. Dette er ikke godkjent kollisjonsparitet og brukes ikke til å
hoppe over dagens beregninger, heller ikke ved et registrert nullresultat.

Amiga grupperer0/1,2/3,4/5 og6/7 i kollisjonsregisteret. Med vår pakking
inneholder gruppe2/3 deler av både Bruce og Yamo, og gruppe4/5 er Yamo.
Dermed kan samme registerbit være utvetydig for noen kanaler og tvetydig
for andre. Registreringen følger rasteret og nulles ved lesing.
Se [Hardware Reference Manual, CLXDAT](https://www.amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node015C.html)
og [CLXCON](https://www.amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node015D.html).

C64-grensen er annerledes: de faktiske lesingene ved$29CE og$3D20 gjelder
$D01E og åtte opprinnelige VIC-komponenter, inkludert separate komponenter
og våpen. Akkumulering, lesing og nulling beholdes i kjernen. Se
[kildegrensen](VIC_REPEAT_OPTIMIZATION.md). Observatøren sammenligner ikke
disse avlesningsfasene med originalrasteret og kan ikke etablere ekvivalens.
Kollisjon mot tegnpiksler, vegger, nett, lanterner og feller er uendret.

Kildehash er fortsatt
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Remember/T64-kandidaten er ikke sertifisert som urørt1984-utgave.

## Starte og kontrollere forsøket

```powershell
.\launch-hardware-actors.ps1 -ShowWindow
python tools/verify_hardware_actors_probe.py
```

`-Disk` starter den private ADF-en. Ved vanlig CLI-oppstart starter `start`
samme private utgave fra AmigaDOS. Shift+D og de eksisterende menyvalgene
beholdes. Normalutgaven bruker ingen hardware-kollisjonsavgjørelser.

Rådata og native fixturer ligger under
`reference/analysis/hardware-bruce-2026-10-31/v5/`, tidsparene under
`reference/analysis/optimization-2026-10-27/hardware-actors-v5-*/`.
Den fulle native testen best�r53 kildebaserte fixturer og1200 l�kker
med400 kildeoppdateringer,456 hardware-formatkontroller og ingen
kilde-, sprite-, DMA-, aritmetikk- eller presentasjonsfeil. St�rste ledige
Chip-blokk er52632 byte, uendret fra f�r fors�ket. Den kontrollerte
fulltesten har82 tapte lydticks mot81 i forrige Bruce-only-pr�ve og best�r ikke sanntidsporten;
den er forskjellig fra PAL-tidsparene over. De faktiske filene bindes av
verifikatoren.
Full PAL-kadens, naturlig gjennomspilling, original rasterfase og fysisk
A500 står fortsatt åpne.
