# Arbeidsleveranse etter nattøkten

Nyeste leveranse: [kildebasert rommotor og rippet C64-grafikk](ROOM_RECONSTRUCTION.md), med
[aktiv testliste](ACTIVE_TESTS.md) og [grafikkflyt](AMIGA_ART_PIPELINE.md).
Resten av dette dokumentet er historikk fra M2-arbeidet.

Oppfølging etter spilltest: se [jevnere klatring og hopp fra nettoppen](CLIMB_FIX.md).
MACHINE-0003 tilfører to lengre nettoppforløp, slik at det nå finnes 13 forløp
med totalt 965 observasjoner, hver gjentatt to ganger.
Neste spilltest tilførte MACHINE-0004 med avsatssprang og liggende stilling;
totalt finnes nå 19 forløp med 1 608 observasjoner. Se
[avsats- og liggearbeidet](LEDGE_AND_PRONE.md).

## Hva som er klart

- C64-kandidatens input kjøres gjennom VICEs IO Simulation-enhet og CIA-port.
  Ingen spillkode, spill-RAM eller PC endres under bevegelsesopptakene.
- Elleve forløp med totalt 603 observasjoner er kjørt to ganger hver.
  Hele de to opptakene av hvert forløp er identiske, også CPU-klokker og rasterfase.
- Feilen med gjentatt monitorstopp på samme instruksjon er rettet. Verktøyet
  krever en ny RESUMED → STOPPED-sekvens og kontrollert instruksjonsframdrift.
- Gange/akselerasjon, vending, sats, stående hopp, gjentatt holdt hopp og
  klatrestart/-venting/-retur er justert etter disse sporene.
- Den midtre hengende klatreflaten er funksjonell: hopp under nettet og hold opp
  for å gripe det med overkroppen. Pagodepanelene er nå dekor, ikke stiger.
- Plattformenes skissehøyder er korrigert mot C64-bildets koordinater.
- Skjermbyttet er målt i blankperioden. CPU-renderingen ferdigstilles før venting,
  og spilløkken bruker ingen eksplisitt Copper-restart.
- Testoppstart bruker egen bootmappe, UAE-config og PID-fil, slik at den ikke
  skriver over oppstartsskriptet til den interaktive spilleren.

## Hva testene faktisk beviser

`reference/traces/MACHINE-0001/` har ni forløp à 49 observasjoner;
`MACHINE-0002/` har to klatreforløp à 81 observasjoner. Begge har kildeidentitet,
snapshot-hash, input, klokker og kontrollsummer. Originalressurser følger ikke med.

Posisjonssammenligningen bruker den allerede samplede retningen fra forrige
C64-stopp som input til ett C-spillsteg. Fast transformasjon er
`x = 2 * C64_x - 24`, `y = C64_y`. Verken tidsforskyvning, koordinatoffset eller
toleranse tilpasses per forløp. Alle avvik beholdes i JSON-rapportene.

Hele forløpene samsvarer i posisjon for stillstand, høyregange, vending,
stående hopp, holdt hopp, bevegelse under pagodene og begge midtre klatreforløp.
Venstreforløpet og løpshoppet har eksplisitte delgrenser før henholdsvis
veggreaksjon og landing; resten av observasjonene rapporteres som avvik.
Interne C64-tilstandskoder er ennå ikke oversatt til en full tilstandsfasit.

Amiga-rapportene kontrollerer også feltgap, publisering ved rasterlinje 300–308,
ledig sammenhengende Chip RAM, bevegelseshendelser, gjentatt start og OS-retur.
Soak-testen kjører to økter à 1 800 PAL-felt med gjentatt bevegelse. Diagnostisk
framebufferkopiering har et separat målt opphold og finnes ikke i spillbygget.
100 000 blandede inputsteg på vertsmaskinen kontrollerer grenser og tilstander.
Vanlig spillbygg er dessuten observert i selve WinUAE-vinduet med joystickinput:
gåing, hopp, grep og klatring fungerer. Alle injiserte retninger er sluppet;
figuren er etterlatt hengende på midtre nett i den kjørende spilleren.

## Neste manuelle test

Start med `.\amiga-run.ps1` etter `.\amiga-build.ps1` ved behov.
Numerisk tastatur 4/6 går; 8 hopper/griper/klatrer opp; 2 klatrer ned.
Venstre museknapp avslutter til AmigaOS. Fire har ennå ingen kampfunksjon.

1. Gå fram og tilbake og prøv et stående hopp og et diagonalt løpshopp.
2. Gå under det blå nettet midt i rommet. Hold opp gjennom hoppet til figuren
   griper nettet; klatre opp, slipp opp, og klatre ned igjen.
3. Prøv å forlate nettet sideveis og gå fra en avsats. Se etter grafikkrester,
   dobbelttittel, rykk, feil figuranker eller at input føles hengende.
4. Avslutt og start igjen. Prøv også `.\amiga-run.ps1 -Disk`.

Denne sjekklisten gjelder spillbarhet og presentasjon. Den kan ikke erstatte
maskinmålingene eller bekrefte hvilken originalutgave T64-kandidaten stammer fra.

## Åpent før M2 godkjennes

- Bekreftet 1984-retailreferanse mangler fortsatt; Remember-kandidaten er
  uttrykkelig foreløpig. Meny-/crack-oppstarten bak snapshotet er dokumentert.
- Eksakte kollisjonsmasker, veggreaksjon og løpshoppets landing avviker fortsatt.
  Breddegrenser, tak, øvre nettutgang og flere avsatser trenger egne opptak.
- Inputpulser på ett PAL-felt og inputfasen på Amiga må sammenlignes direkte.
- Kamp, fiender, lanterner, rombytte og ferdig lyd/grafikk er senere arbeid.
- Fysisk A500-test gjenstår. M2 er ikke erklært ferdig.

## Kjør kontrollene igjen

```powershell
python tools/c64_reference.py verify --candidate
python -m unittest discover -s tests -p test_vice_binary.py -v
python tools/verify_evidence.py
.\test-core.ps1
.\test-parity.ps1
.\test-amiga.ps1
.\test-amiga.ps1 -Disk -SkipBuild
.\test-amiga.ps1 -TestFrames 1800
```

Nye C64-opptak krever de lokale, hash-låste referansefilene:

```powershell
.\capture-c64.ps1 -Scenario idle,right,left,standing-jump,moving-jump,reverse,climb,climb-down,held-jump
.\capture-c64.ps1 -Scenario central-climb,central-climb-down -CaptureId MACHINE-0002
```

Ingen commit, push eller utgivelse er utført.

Kampoppdatering: MACHINE-0005 gir totalt 25 forløp / 1902 observasjoner.
Slag, flyvende spark og passiv testmotstander er implementert.
Se [kampstatus og åpne avvik](COMBAT_PROTOTYPE.md).

2026-10-19: 31 forløp / 2196 grensestopp-observasjoner. PHASE-0001/0002
registrerer faktiske CPU-inputlesinger; alle 588 logiske angrepstilstander
samsvarer. Det kjente M2-landingsavviket er beholdt.
Se [angrepsinput](ATTACK_INPUT_PHASE.md).

2026-10-20: sparkposen har to ben og testmotstanderen tar foreløpig falltreff.
2548 bevegelsesobservasjoner og1452 naturlige kampobservasjoner er lagret;
lang fallfart er bekreftet uendret. Se [fall/kontakt](FALL_AND_CONTACT.md).
