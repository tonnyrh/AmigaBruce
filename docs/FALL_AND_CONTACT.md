# Fall, treff ovenfra og sparktegning — 2026-10-20

Sparktegningen tegner nå ett bakre ben og ett utstrakt sparkben. Tidligere
ble begge ståbena tegnet først, og sparkbenet kom i tillegg.

## Målt fallfart

MACHINE-0007/mid-net-left-fall måler et lengre fall etter at Bruce forlater
nettet. Etter inngangssteget på én piksel følger 29 positive intervaller
med to piksler per spillsteg. Spillsteget varer tre PAL-felt, altså omtrent
33,3 piksler per sekund ved 50 Hz. Kjernen beholder denne farten.

`candidate-fall-rate.json` fryser denne målingen. Host-testen følger samme
vertikale fall fra y138 til y196 med to piksler per steg. Dette godkjenner
fallfarten, ikke romgeometri, landingsmasker eller hele ruten.

Hele rutesammenligningen ligger i `candidate-fall.json`: nettutgang og
horisontal bevegelse avviker fortsatt. Den andre målte ruten, kalt
upper-ledge-fall, faller faktisk ikke i kandidaten; den stopper ved y102
på originalens kollisjonsgeometri. Begge råopptakene og alle avvik beholdes.

## Treff ovenfra

C64-disassemblyens `$2AFA..$2B39` har et eget kontaktangrep for falltilstand
`$0E`. Offerets fotposisjon må være minst ti piksler lavere, og kontakt må
allerede være registrert av VIC-spritenes pikselkollisjon. `$4F45,Y` må være
positiv og reduseres; den fylles til to av avbruddsrutinen ved `$15C2`.
Gjentatte kontaktflagg og visse offer-/angrepstilstander sperrer også treff.
Kodebanen setter treffbit `$10`; skadekoden ved `$2C0C` trekker fem.
Instruksjonene ved fire sentrale steder er også kontrollert direkte i den
registrerte snapshoten; se `candidate-fall-contact-code.json`. Dette er
statisk analyse av kandidaten, ikke et naturlig stomp-opptak.

Testmotstanderen i Amiga-prototypen kan nå treffes ovenfra mens Bruce er i
fritt fall. Vanlig hoppestigning eller aktiv vanlig hoppkurve gir ikke et
slikt fallangrep. Testen bruker foreløpige bokser, to laboratorie-skadepoeng
og den eksisterende treffbeskyttelsen. Originalens pikselmasker og periodiske
kontaktbegrensning er ennå ikke implementert. Motstanderen er fortsatt en
passiv testfigur, ikke Ninja eller Yamo.

## Naturlige fiendemøter i C64-kandidaten

COMBAT-0001 har fire naturlige ruter, 1452 observasjoner, gjentatt identisk
to ganger. Spillminne og PC endres ikke under opptaket. Helse leses fra
`$D1..$D3`; kontakter fra `$BC..$BE`. Ingen trenere er aktivert.

| Observasjon | Målt resultat |
| --- | --- |
| Starthelse Bruce / Ninja / Yamo | 36 / 7 / 20 |
| Første aktive Ninja fra opptaksgrensen | steg 96, C64 x159/y98 |
| Første aktive Yamo fra opptaksgrensen | steg 232, C64 x159/y98 |
| Treff med bit `$02` (Ninja-angrep) | 13 observerte treff, to skadepoeng hver |
| Treff med bit `$08` (Yamo-spark) | ett observert treff, sju skadepoeng |

Tidsgrensen kommer etter åtte oppvarmingssteg fra baseline-snapshoten;
den er ikke lik tiden fra kaldstart. Ruten med holdt opp skadet ikke
fiendene med vanlige hopp. Ingen naturlige treff med bit `$10` ble fanget
i disse fire rutene. Vi har dermed ikke full runtime-paritet for treff ovenfra.

## Kontroll

Den lange A500-testen har en uttrykkelig test-fixture ved periode 1440:
Bruce starter over testmotstanderen og faller ned på den. `target_stomps`
skal bli positiv, sammen med eksisterende kontroller for slag, spark,
nederlag, gjenoppståing og skjermperioder. Dette er en Amiga-testoppsetting,
ikke et C64-referanseopptak.

```powershell
.\capture-c64.ps1 -CaptureId MACHINE-0007 -ScenarioFile reference/scenarios/MACHINE-0007.json
.\capture-c64-combat.ps1
.\test-core.ps1
.\test-parity.ps1
.\test-amiga.ps1 -TestFrames 1800
```
