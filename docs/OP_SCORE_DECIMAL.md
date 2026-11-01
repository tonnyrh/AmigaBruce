# Desimalkonvertering ved falltreff på Kage

## Hva C64-koden gjør

Ved en poengtildeling kopierer `$32DC–$32EB` poengtallet fra
`$41–$43` til arbeidsområdet `$4398–$439A` og nullstiller de fire
BCD-bytene ved `$439B–$439E`. Løkken ved `$32EE–$330C` lagrer
status med PHP, slår på desimalmodus og skyver 24 bit gjennom de fire
BCD-bytene. PLP gjenoppretter flaggene. Den parallelle løkken ved
`$31D5–$31F3` brukes etter klargjøring fra `$4388`.

Ved retur er arbeidsverdien null, A er det første BCD-bytet, og X
og Y er 255. SP og flaggene er bevart. Selv etter PLP ligger den
lagrede statusbyten på `$0100+SP`. Kontrollene kjører maskinkoden
fra den frosne Remember/T64-kandidaten med SHA-256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Identiteten som urørt 1984-utgave er fortsatt åpen.

## Hva Amigaen gjør

Den tidligere rutinen hentet ut fire sifferpar med fire 32-biters
divisjonskall. Den nye rutinen deler poengtallet i grupper på fire
sifre. Tall fra 0 til 9999 trenger bare den nederste gruppen. For
større tall gir én `DIVU.W` både kvotient og rest ved deling på
10 000. Maksimumsverdien 16 777 215 gir kvotient 1677 og rest 7215,
godt innenfor instruksjonens 16-biters resultat.

Hver gruppe deles i to sifferpar. En tabell på 100 byte oversetter
hvert par til pakket BCD. For maksimumsverdien skrives dermed
`16 77 72 15` i heksadesimal form. Begge kildeinngangene beholder
vakten som krever nullstilt BCD-buffer, og den opprinnelige
instruksjonsbanen håndterer en forhåndsutfylt buffer.

## Kontroller

Vertskontrollen sammenligner alle 65 536 minnebyte, registre og flagg
med C64-instruksjonene i 2852 tilfeller. En egen 68000-prøve bruker
forventede resultater fra begge PHP/PLP-løkkene. Den omfatter 5041
forskjellige poengverdier og 5809 tilfeller, inkludert åttesifrede
poeng, alle kombinasjoner av de seks statusbitene ved utvalgte
grenseverdier og innganger på begge sider av hver mulig 10 000-grense.
For hvert tilfelle kontrolleres BCD-bytene, det nullstilte arbeidsområdet,
registrene, flaggene, hele stacksiden og nabobytene til arbeidsområdet.

Kampkontrollen bruker de samme to opptakene og 18 IRQ-returene ved
`$2C51` som i [prøven for poengvisning](OP_SCORE_DISPLAY.md).
Ved det første treffet øker poengsummen fra 425 til 6975 og ved det
andre fra 6975 til 13 525.
Det andre treffet passerer dermed skillet mellom én og to grupper.
De tidsmålte rutene kjører i syklusnøyaktig WinUAE på PAL A500 med
Kickstart 1.3 og 512 + 512 KiB. Naturlig rasterfase og fysisk A500
er fortsatt åpne kontroller.

## Resultater i rom 1

Hver kjøring hadde 240 oppvarmingssteg og 240 målte steg med begge
fiender aktive. I andre par ble prøvebygget kjørt først. Bruce var i
lufta i 96 steg i hver bevegelseskjøring. Et tomt Paula-felt betyr et
felt der ingen ny publisering begynte. Forrige lyd kan fortsatt spille.

| Måling | Før, to kjøringer | Etter, to kjøringer |
| --- | ---: | ---: |
| Bevegelse, PAL-felt | 984 / 984 | 980 / 982 |
| Lengste spillsteg i bevegelse, rasterlinjer | 3130 / 3130 | 2817 / 2817 |
| Felt uten ny Paula-publisering i bevegelse | 10 / 10 | 7 / 7 |
| Felt med dobbel publisering i bevegelse | 2 / 2 | 1 / 1 |
| Stillstand, PAL-felt | 966 / 966 | 961 / 960 |
| Felt uten ny Paula-publisering ved stillstand | 0 / 0 | 0 / 0 |

I et separat målebygg ble Amigaens linjeteller lest rett før og
etter hvert konverteringskall. De 53 kallene på første falltreff gikk
fra 476 til 159 rasterlinjer. På andre treff gikk de 53 kallene fra
479 til 190. Til sammen er det 955 mot 349 linjer, omtrent 63 %
mindre tid i det målte intervallet. Klargjøringen av poengtallet og
de seks skrivingene til skjermminnet ligger utenfor dette intervallet.

Lengste observerte steg gikk fra omtrent 200 til 180 ms. Over hele
bevegelsesruten var forskjellen 0,04–0,08 sekunder. Tabellen bruker
bygget med den tidligere sifferoptimaliseringen som utgangspunkt.

Normalprogrammet økte fra 326 376 til 326 592 byte. De 53 native
systemkontrollene og 1200 spilløkker bestod. Største ledige
Chip RAM-blokk etter lasting var 52 632 byte mot kravet på 49 152.
De fem integrerte kildeforløpene stemte i minne og registre gjennom
til sammen 7 055 873 utførte C64-instruksjoner.
AmigaDOS startet til komplett meny. Fra skrivebeskyttet ADF gikk
rom 1 fra spillsteg 9 til 46 uten registrert motorfeil.
[Byggidentiteter](../reference/analysis/op-score-decimal-2026-10-31/build.json).

## Gjenta forsøket

[Analysemappen](../reference/analysis/op-score-decimal-2026-10-31/) inneholder
`build_decimal.py` for `reference` og `candidate`, samt `--profile`
for tidsstemplene ved konverteringskallet. Referansekoden leses fra
Git-commit `d44ef0d`. Ruteskriptet fra poengvisningen tar
`-StageName op-decimal` og bruker rom, fiendemaske og inputrute
`1 3 2` for bevegelse og `1 3 0` for stillstand. `proof.py`
lager den native tallprøven fra den lokale C64-kandidaten. Med
argumentet `combat` bruker det de to opptakene fra poengvisningen.
[Målerapporter og prøvebygg](../reference/analysis/op-score-decimal-2026-10-31/measurements.json).
