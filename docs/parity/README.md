# Paritetsregister

`register.csv` inneholder planlagte observasjoner/tester med stabile PAR-ID-er.
`rooms.csv` har R01–R20 fra den hash-låste C64-kandidatens romdata. Alle init-/
løprutiner og pikselkontakt er nå implementert som avgrenset romportering.
Kandidaten er ikke bekreftet som den valgte urørte 1984-utgaven.
Se [romrekonstruksjonen](../ROOM_RECONSTRUCTION.md) og `ROOM-RUNTIME-0001`.
Gjennomgangen [T01–T18 mot koden](../TEST_AUDIT_2026-10-25.md),
evidens `TEST-AUDIT-0001`, korrigerer tidligere testtolkninger uten å slette
brukerens observasjoner. Avklarte grener og uavklart naturlig kontakt føres separat.

## Status

- `unverified`: ikke fastslått i valgt original; beskrivelse er et undersøkelsespunkt.
- `secondary_only`: kildeinformasjon finnes, men er ikke bekreftet i primærkjøring.
- `observed`: direkte opptak i valgt original med identifisert evidens.
- `confirmed`: reprodusert måling med klart utgangspunkt, input og koordinater/tid.
- `candidate_observed`: direkte observert i brukerens hash-låste T64-kandidat;
  bekrefter ikke identitet med valgt 1984-arkivutgave.
- `candidate_code_derived`: avledet fra faktiske kandidatbytes og dokumenterte
  grener/tabeller; bekrefter ikke urørt retailutgave eller naturlig gjennomspilling.
- `candidate_code_derived_partial`: kildeavledet romgrunnlag med åpne aktør-/progresjonsdetaljer.
- `candidate_analysis`: støttet av isolert 6502-analyse av kandidaten, uten
  full maskinemulering. Skal ikke brukes som bekreftet timing eller paritet.
- `candidate_replayed`: minst to identiske fullmaskinopptak av den hash-låste
  kandidaten, med dokumentert inputfase og stoppgrense. Bekrefter ikke retailutgave.

Amiga-resultat føres separat: `not_implemented`, `not_tested`, `pass`, `fail`.
Et C64-funn er ikke automatisk en bestått Amiga-test.
`candidate_partial` betyr at en avgrenset del av implementasjonen er kildeavledet
eller sammenlignet med kandidaten; hele PAR-punktet eller Amiga-inputfasen er ikke godkjent.
Alle rader starter med tom forventet verdi til reell måling foreligger.
Ingen standardtoleranse opprettes: eksakte heltalls-/tilstandssammenligninger
brukes når mulig; videoavlesning må ha eksplisitt usikkerhet. Avvik ved optimalisering
eller ny animasjon skal være synlige, aldri skjult ved å øke toleransen.

## Romarbeid

For hvert rom registreres skjermbilde, koordinatrom, flater og klatreområder,
lanterner, inn-/utganger, spawnpunkter, fiendeadgang og ventetid, feller med
fase, init-/loop-hendelser, persistens ved gjenbesøk og overganger ved død.
Hver overgang skal ha kilde, trigger, vilkår, mål og ankomstpunkt. Ikke importer
editorens dør- eller fiendetabeller som bekreftede originaldata.

Første prioritet er PAR-001–PAR-011 og et faktisk R01-opptak. Full romdekning
fortsetter frem til M4. Fremgang måles i bekreftede regler og evidens, ikke antall rader.
