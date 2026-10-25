# Kampinput — 2026-10-19

Slag og flyvende spark er undersøkt med stoppunkter ved C64-kandidatens
faktiske inputlesinger. Ingen toleranse eller tilpasset tidsforskyvning brukes.

## Hva som forårsaket avvikene

C64-avbruddet ved `$16BD`/`$16CD` oppdaterer retnings- og ildverdiene under
spillets kjøring. En observasjon ved `$1BCE` er derfor ikke nødvendigvis den
verdien som senere blir brukt i samme spillsteg.

PHASE-opptakene registrerer A-registeret etter disse lesingene for Bruce:

| Stopp | Målt verdi |
| --- | --- |
| `$1DD2` | Retning etter `LDA $98,X` |
| `$1EBF` | Ild ved høyrevendt gange etter `LDA $9B,X` |
| `$1E7E` | Tilsvarende ildlesing ved venstrevendt gange |
| `$1F7C` | Ild ved stående slagvalg |

Eksempel: I MACHINE-0005/moving-fire, steg 11, leses fortsatt høyre og ingen
ild ved bevegelsesstart. Ild er oppdatert til trykket før sparkvalget.
I right-fire, steg 25, er input oppdatert til sluppet før retningslesingen;
derfor velger C64 ingen ny bevegelse eller nytt spark.

Alle gamle `$1BCE`-observasjoner, inkludert CPU-klokker og tilstandsverdier,
er kontrollert identiske mot MACHINE-0005/0006. Opptakene er gjort to ganger
med identisk resultat, uten å skrive spillminne eller flytte PC under kjøringen.
Den registrerte baseline-snapshoten gjenopprettes mellom repetisjonene.

## Resultat og kodeendring

`bl_step_phased` kan få separat retningsinput og senere ildinput. `bl_step`
beholder vanlig samlet input for Amiga-spilleren. Sparkvinduet følger nå
fire gjennomførte gåsteg i samme retning; en unødvendig separat ildteller
og grensen som først slo inn etter syv gåsteg er fjernet.

- PHASE-0001: seks forløp / 294 observasjoner samsvarer i både posisjon
  og logisk angrepstilstand, inkludert løping og knappslipp.
- PHASE-0002: fem ekstra forløp / 245 observasjoner samsvarer fullt.
  Alle 49 angrepstilstander i diagonalhoppforløpet samsvarer også.
- Diagonalhopp fra ro med ild er vanlig løpshopp. Posisjonen samsvarer til
  og med steg 16; deretter har kjernen det kjente M2-landingsavviket
  (blant annet fire piksler ekstra horisontalt og annen fothøyde).
  Alle avvik står i rapporten. Posisjonsgrensen er samme bevegelsesvindu
  som den eksisterende moving-jump-testen, uten de ti innledende gåstegene.

Disse resultatene sertifiserer ikke fysisk joysticklatens eller Amigaens
inputfase innen et PAL-felt. Ninja/Yamo, originale treffbokser, skade,
tilbakeslag og liggende forsvar er fortsatt egne åpne kampoppgaver.

## Reproduser

```powershell
.\capture-c64.ps1 -CaptureId MACHINE-0006 -ScenarioFile reference/scenarios/MACHINE-0006.json
.\capture-c64-phase.ps1
.\capture-c64-phase.ps1 -Baseline MACHINE-0006 -CaptureId PHASE-0002
.\test-core.ps1
.\test-parity.ps1
python tools/verify_evidence.py
```

Rapporter: `candidate-attacks-phased.json` og
`candidate-attacks-phased-edges.json` under `reference/validation`.
De gamle sammenligningene med bare grensestoppets input er beholdt separat.
