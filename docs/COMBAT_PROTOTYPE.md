# Kamp-prototype â€” 2026-10-18

Slag og flyvende spark er implementert med egen skisseanimasjon. Den rÃ¸de
figuren pÃ¥ gulvet er en passiv testmotstander, ikke Ninja eller Yamo.

- Ild uten retning: slag. Holdt ild gjentar slag.
- Sideveis + ild: flyvende spark etter innledende gÃ¥steg.
- Opp + sideveis + ild fra ro: vanlig løpshopp. Flyvende spark velges fra gå-/løpstilstanden når angrepsvinduet er åpent.
- Opp + ild uten sideveis retning: vanlig stÃ¥ende hopp.
- Ned + ild pÃ¥ bakken: liggende stilling.

## MÃ¥legrunnlag

MACHINE-0005 har seks forlÃ¸p, hver med 49 observasjoner og to identiske
fullmaskinrepetisjoner. RLE-input ligger i
`reference/scenarios/MACHINE-0005.json`. Opptak bruker samme hash-lÃ¥ste
C64-kandidat og mÃ¥legrense som bevegelsesopptakene.

Ild alene velger logisk tilstand 17 i fire spillsteg, med ny aktivering hver
Ã¥ttende ved holdt knapp. Sideveis ild velger tilstand 12/13 for flyvende
spark. MÃ¥lt hÃ¸yreforlÃ¸p beveger seg 24 piksler med to piksler per spillsteg,
stiger tre piksler og gÃ¥r tilbake til gulvhÃ¸yden. Dette er en egen kurve.

## Rettelse 2026-10-19: input under samme spillsteg

`candidate-attacks.json` beholder sammenligningen med bare input ved den gamle
spillsteggrensen. Denne forenklingen gir avvik ved løping og knappslipp.
PHASE-0001 måler i tillegg CPU-verdien etter de faktiske retning-/ildlesingene.
Alle seks forløp samsvarer da i alle 294 posisjoner og logiske angrepstilstander;
se `candidate-attacks-phased.json`. Ingen tidsforskyvning eller toleranse brukes.
De opprinnelige grensestoppene er kontrollert mot MACHINE-0005, også CPU-klokkene.

Kjernen har nå en eksplisitt funksjon for separat retningsinput og senere ildinput.
Vanlig Amiga-input bruker samme sampling for begge. Dette er ikke en godkjenning
av fysisk joysticklatens eller identisk inputfase innen et PAL-felt på Amiga.
Angrepsvinduet følger nå fire gjennomførte gåsteg, fremfor en grense som først
var riktig etter syv. Opp+side+ild fra ro er korrigert til vanlig løpshopp.

## Testmotstander og forelÃ¸pige treffregler

Testmotstanderen viser treff med fargeblink, flyttes Ã¥tte piksler, har tre
testhelsepoeng og kommer tilbake etter 60 spillsteg ved null helse. Slag
trekker ett poeng, spark to; treffbeskyttelsen varer Ã¥tte spillsteg.
Disse verdiene er laboratorieregler, ikke C64-mÃ¥linger eller ny spillbalanse.

Testgeometrien har separate stÃ¥ende og liggende kroppsbokser; et hÃ¸yt slag
passerer over den lave boksen. C64-originalens faktiske bokser, treffvinduer,
skade, tilbakeslag og liggende forsvar mÃ¥ mÃ¥les fÃ¸r disse reglene brukes for
Ninja og Yamo. Testmotstanderen angriper ikke og blokkerer ikke bevegelse.

KjÃ¸r `test-core.ps1`, `test-parity.ps1` og A500-testene som beskrevet i
[prototypeinstruksjonene](PROTOTYPE.md).

Se [inputfase og ekstra kanttilfeller](ATTACK_INPUT_PHASE.md) for rettelsen
2026-10-19, alle 588 angrepstilstander og det kjente diagonalhoppavviket.

Oppdatering 2026-10-20: to-bens sparktegning og treff ved fritt fall er lagt
til. Fallfarten og første naturlige Ninja/Yamo-møter er målt; se
[fall og kontakt](FALL_AND_CONTACT.md). Treffer og skade på testfiguren
er fortsatt laboratorieregler.
