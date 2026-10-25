# Jevnere klatring og hopp etter nettoppen

Brukerens valg er å beholde C64-farten og gjøre klatrevisningen jevnere.

## Endring

Spillkjernen beholder tre ventesteg mellom klatrehandlingene. Før ble hver
forflytning tegnet over tre PAL-felt, fulgt av ni felt uten bevegelse. Den egne
presentasjonsmodulen fordeler nå klatrehandlingen over hele intervallet på tolv
felt. Nye logikksteg med samme målposisjon starter ikke interpoleringen på nytt.
Ved fall, gange og hopp brukes tre felt. Kollisjon bruker fortsatt spillkjernens
posisjon. Presentasjonen interpolerer mot kjente posisjoner, uten prediksjon;
figuren kan visuelt ligge inntil ett klatretrinn etter logikken.

De nye C64-opptakene viser at nettet starter visuelt ved y104, men at ståhøyden
over det er y101. Romdata skiller nå mellom nettkant og ståhøyde. Spilleren
beholder klatrehandlingens tre ventesteg ved utgang, og holdt opp starter deretter
gjentatte hopp. Figuren griper ikke nettet igjen i hoppets satsfase på toppen.

## Evidens og kontroll

- `MACHINE-0003/central-top-held.csv`: to identiske opptak à 181 observasjoner.
  Kjernens X/Y samsvarer på alle observasjonene, fra gulv via nett til gjentatte
  hopp på toppen og fullføring av siste hopp etter at opp slippes.
- `central-top-release.csv`: eget slipp-/trykk-forløp. Et kjent ettstegs avvik
  ved ny inputfase på toppen er synlig i rapporten; det er ikke skjult med
  tidsforskyvning eller toleranse. Dette er videre inputfasearbeid.
- Målingen av C64-takt korrigerer nå klokkeintervallet for observert rasterfase.
  Resultatet skal være nøyaktig `3 * 312 * 63` sykluser per spillsteg. Dette
  skiller arbeidsmengde innenfor feltet fra faktisk tap av et felt.
- Host-testene kontrollerer gjentatte topphopp, at samme nett ikke gripes igjen,
  tolvfeltsovergang uten pauser fra reinitialisering, og overgang til fall.
- Se oppdaterte Amiga-rapporter for feltgap, blankperioder og minnemargin.

Originalutgavens identitet og full M2-paritet er fortsatt åpne. Hele visningen
og logikken er også kontrollert i det vanlige spillbygget: joystickinput tok
figuren fra gulv, opp nettet, og videre til gjentatte hopp på plattformen.
CLI-start, ADF-oppstart og to stresstester à 1 800 PAL-felt består med ett felt
per oppdatering og skjermbytter innenfor blankperioden.
