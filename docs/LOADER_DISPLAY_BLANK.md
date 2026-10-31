# Skjermfeil ved rominnlasting, 30. oktober 2026

Brukerdump: `.tmp/30.10.2026.uss`, SHA-256
`48b20637149ec00aef4d9b15f9ddc99b8fb4d9810a82b7d00d0db2f0f3afb6c1`.
Originalen er beholdt uendret. Analyse og avspilling bruker egne produkter
under `reference/analysis/screen-corruption-2026-10-30` og en arbeidskopi.

## Funn og kildespor

Dumpen viser rom 6. Det rekonstruerte Amiga-bildet inneholder et gjentatt
mursteinsmønster, mens kilde-RAM inneholder vanlig romgeometri. Loaderen er
aktiv, og kilde-registeret `$D011` er `$0B`: skjermvisning er deaktivert.
Ved videre avspilling av arbeidskopien kommer riktig rom tilbake.

Alle 179 044 programkodebyte i dumpen stemmer med den arkiverte normal-ELF-en
før lydservice-rettingen, etter at 11 495 relokeringer er anvendt.
Dumpen kjører derfor den eldre koden, ikke de isolerte fiendekost-kandidatene.
Den berørte tegneveien var fortsatt den samme i siste normalbygg.

Frossen C64-kandidat:
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.

- `$09BC–$09C1`: les `$D011`, AND `$EF`, skriv tilbake. Dette slår av DEN
  før rommet bygges om.
- `$09CD`: skriv null til `$D015` og skjul kildespritene.
- `$0A9B–$0B2D`: dekod rommets tegnstrøm.
- `$0B30`: gjenopprett blant annet innsamlede lanterner gjennom `$336E`.
- `$0B33` kaller `$50DB–$50E5`: AND `$7F`, ORA `$10`, STA `$D011`.
  Visningen aktiveres etter tegnstrømmen. Kildens rom-init fortsetter
  gjennom `$3A6F` før Amiga-versjonen publiserer sitt ferdige bilde.

Bytekontroller og disassembly følger analysen. Remember/T64-kandidaten er
fortsatt ikke sertifisert som en urørt 1984-utgave.

## Retting

Amiga-versjonen tok ikke med skjermblankingen i loaderens visning.
Eksisterende load-callback blanker nå begge Copper-listenes `BPLCON0`-ord
og maskinvarens `BPLCON0` ved innlasting. Det forhindrer at en gammel
eller mellomliggende bitmap blir stående synlig under arbeidet.

Load-callbackens avslutning aktiverer ikke visningen. `present_frame`
aktiverer bare listen som skal publiseres, ved den eksisterende kontrollen
for rasterlinje 300–308, etter at erstatningsbildet er tegnet. En fortsatt
aktiv loader beholder blank visning. Menyen kan fremdeles publiseres når
spillkjøringen er deaktivert.

Bare `amiga/main.c` endrer kjørende spillkode. C64-motor, geometri,
kollisjonsberegning, kontakter, AI, lyddata og bildeinnhold er uendret.
Normal EXE øker med 132 byte, hvorav 98 byte er CODE; RODATA, DATA og BSS er uendret. Ingen nye buffere
eller minneallokeringer innføres.

## Kontroller og begrensninger

Kontrollerte dødsforløp i rom 6 og 12 bruker den eksisterende terminale
aktørtilstanden fra C64-fixturen, i et ferskt normalbygg med testvalg.
Avlesningen finner kilde-DEN av, loader aktiv og begge Copper-listene
blanke. Etter innlasting er DEN på, loader avsluttet og en ny liste aktiv.
Disse er kontrollerte Amiga-prøver, ikke naturlige C64-opptak.

Bakgrunnspikslene sammenlignes med kilde-RAM. Kildeendringer som allerede
står i den eksisterende tegnekøen rapporteres separat; de øvrige pikslene
skal stemme eksakt. I én rom 6-prøve var 24 piksler i to lanterneceller
ennå i kø. Det innføres ingen pikselmargin eller endring av tegnekøen.
Den separate rom 12-kontrollen kontrollerer også rullende tegnfaser og
hele lovlige flimmerpar uten slik pikselmargin.

Native pausekontroll sammenligner hele CPU-/rasteravlesningen før og etter
et ventetidsrom. Et debugger-watchpoint åpnet en modal debugger og blokkerte
IPC i denne WinUAE-versjonen; den metoden brukes ikke som godkjent evidens.
Sluttprøven poller loader/listemodus og pauser deretter. Den beviser ikke
hver rasterposisjon eller identisk C64-rasterfase.

Tidligere leveranse og validatorer er frosset og kontrolleres separat.
Ingen tidligere sanntids-, IRQ-, originalutgave- eller naturlig spillport
markeres bestått av denne skjermrettingen.

Bruk en fersk EXE/ADF ved ny prøving. Gjenoppretting av den gamle USS-en
gjenoppretter også den gamle programkoden.

Sluttkontroll: 53 native motorfixturer og 1200 løkker består med
52 632 byte største ledige Chip-blokk. De åtte kontaktprimitivene og
sprite-/VIC-primitivene er bundet til normal-, fixtur- og referansebygg.
24 rom12-/døds-/rombyttebilder har null fase-/statiske/flimmeravvik.
80 menybilder består, inkludert F10-retur og begge startpariteter.
CLI og ADF viser komplett meny; ADF bekrefter faktisk spillframdrift.
Samlet spilltempo og de opprinnelige åpne portene er fortsatt uavklart.
