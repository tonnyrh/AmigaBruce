# Milepælstatus — 2026-10-18

| Milepæl | Faktisk status |
| --- | --- |
| M0 | Referanse- og evidenssystem etablert. Lokal T64-kandidat hash-låst og prøvestartet; tretten fullmaskinforløp er reprodusert to ganger. Verifisert 1984-arkivoriginal mangler. |
| M1 | Egen 68000-bygging, OCS-skjerm, input, Paula-test, EXE/ADF og emulatoroppsett implementert. Gjentatt CLI-start og OS-retur er testet på 512+512-konfigurasjonen. Se valideringsrapportene for diskbootstatus. |
| M2 | Spillbar ettromsprototype med gåing, hopp, klatring og fall. Avgrensede posisjonsforløp samsvarer eksakt med kandidatspor. Vegg-/landingsavvik, flere kollisjoner og originalidentitet holder M2 åpen. |

Motorarbeid ble startet etter brukerens beskjed om å fortsette mot M2 med de
lokale filene. Dette endrer ikke kriteriene for å erklære originalparitet.

## Etablert referansegrunnlag

- Brukerens repo er klonet fra riktig origin; kildefiler er lagret lokalt.
- 25 paritetspunkter og 20 foreløpige romplasser er opprettet.
- Sekundærkilden 5k3105/bruce er commit-låst med 55 verifiserte filidentiteter.
- Brukerens fire mediefiler er identifisert og SHA-256-registrert.
- `brucelee.d64` inneholder R.O.F+, ikke originalen. T64-ens `BRUCE LEE+`
  brukes som uttrykkelig foreløpig analysekandidat; CRAZY brukes ikke.
- VICE 3.10 er hentet lokalt. Valgt PAL-modell og faktiske C64-ROM-hasher er
  registrert. Begge trainervalg ble besvart N og kjente patchsteder kontrollert.
- Tittel/meny, første rom og baseline-snapshot finnes lokalt; evidensindeks
  CANDIDATE-0001 er versjonerbar uten originalressurser.

## Begrensninger som fortsatt gjelder

Preservation64s valgte G64 svarte HTTP 401 og er ikke hentet. Katalogens
PAL/1984-metadata er ikke egen kontroll av brukerens T64.
Den lokale kandidaten har crack-intro, dokumentasjonsleser og trainer.
Debuggergrenene som ble brukt for oppstart er dokumentert i manifestet.
Dette er ikke en uendret retail-oppstart eller bevis for identisk spillkode.

Tidlige VICE-bevegelsesspor fikk feil stoppgrenser og er forkastet som
paritets-/timingbevis. Offline 6502-analyse kjøres separat med py65 og merkes
uten VIC/CIA/SID-/IRQ-emulering. Ingen av disse sporene sertifiserer PAL-timing.
Nye MACHINE-0001/0002-opptak bruker derimot full VICE-maskinemulering med
IO Simulation-input, verifiserte stoppgrenser og CPU-klokker. Begge repetisjonene
av hvert forløp samsvarer. Dette bekrefter kandidatmålinger, ikke retailidentitet.
MACHINE-0003 følger nettet helt til toppen. Hele 181-posisjonsforløpet med opp
holdt gjennom gjentatte topphopp samsvarer; egen slipp-/trykk-test viser fortsatt
et inputfaseavvik. Se [klatre- og nettopprettelsen](CLIMB_FIX.md).

## Veien til godkjent M2

1. Bekreft originalutgave og forholdet til kandidatens upatchede spillkode.
2. Utvid MACHINE-opptakene med ettfelts inputpulser og flere starttilstander;
   sammenlign Amigaens inputfase, ikke bare den samplede spillsteggrensen.
3. Port eksakte romkollisjoner, vegger, tak og nettgrenser fra bekreftede data.
4. Sammenlign vending, gå-/løpshastighet, hoppforsinkelse/kurver, fall og
   klatring mot repeterbare C64-spor. Ingen toleranse økes for å skjule avvik.
5. Godkjenn relevante PAR-ID-er først når disse sammenligningene består.

Se [kjøreinstruksjoner og prototypegrenser](PROTOTYPE.md),
[manifest](../reference/manifest.json) og [valideringsrapporter](../reference/validation).
Ingen commit, push eller GitHub-utgivelse er gjort.

MACHINE-0004 utvider grunnlaget til 19 forl�p og 1608 observasjoner.
H�yre avsats og liggende stilling er unders�kt; se [detaljer](LEDGE_AND_PRONE.md).

F�rste M3-arbeid: slag, flyvende spark og passiv testmotstander finnes.
MACHINE-0005 gir seks nye angrepsforl�p; se [kampstatus](COMBAT_PROTOTYPE.md).

2026-10-19: angrepsvalg sammenlignes n� ved faktiske CPU-inputlesinger.
Se [inputfase](ATTACK_INPUT_PHASE.md); M2-landingen og originale treffregler st�r �pne.

2026-10-20: lang fallfart bekreftet; fire naturlige kampopptak gir helse-
og skadedata for fiendearbeidet. Se [fall/kontakt](FALL_AND_CONTACT.md).
