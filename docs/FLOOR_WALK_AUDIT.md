# Ujevne gulv: kildekontroll, 30. oktober 2026

Brukeren opplever mer hakking/trøbling over ujevne gulv enn på C64.
Den konkrete strekningen er foreløpig ikke oppgitt. Dette er en avgrenset
undersøkelse; ingen gulvregel eller produksjonskode er endret.

## Kildebasert forklaring på små stopp

Kilde er de faktiske bytene i den frosne Remember/T64-kandidaten, SHA-256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Identiteten er fortsatt ikke sertifisert som urørt 1984-utgave.

- `$1C0D` kaller `$5212` med gjeldende figurmaske, før objekt- og
  aktørbehandlingen. Både fotkontakt `$B6` og kroppskontakt `$A7` er med.
- `$1DCA–$1DCE` tester kontaktbitene `$05`. Ved manglende støtte går
  `$1DC4` via `$1DBC/$1E39` til nedoverbevegelse og falltilstand 14.
- Når forrige tilstand er 14, går behandlingen gjennom `$1D7E–$1DBF`.
  Gjenfunnet fotkontakt kan avslutte fall uten å flytte Bruce sideveis
  i den samme oppdateringen. Retningsbevegelsen fortsetter senere.
- Svart kontakt, bit `$08`, går gjennom `$1C68–$1D6E` og den eksisterende
  bevegelseshistorikken. Det kan gi tilbakerulling og tilstand 24.
- `$1BC2/$1BC4` setter ventetelleren `$48` til tre felt før arbeidet.
  `$1C32–$1C36` venter på at originalens IRQ-teller skal bli null.

Et konkret kontrollert forløp fra rom 12, med venstre holdt fra originalens
startanker x104/y76, gir dette i både faktisk C64-maskinkode og native C:

| Oppdatering | Skjerm-X | Fot-Y | Tilstand | Sideveis endring |
| --- | ---: | ---: | --- | ---: |
| 0 | 100 | 76 | Løper venstre | −4 |
| 1 | 96 | 76 | Løper venstre | −4 |
| 2 | 96 | 77 | Fall, 14 | 0 |
| 3 | 96 | 77 | Står, 0 | 0 |
| 4 | 92 | 77 | Løper venstre | −4 |

Denne lille stoppen ved et én-piksels høydefall finnes altså i kildekoden.
Eksemplet er en kontrollert inngang, ikke en naturlig C64-gjennomspilling.

## Ny sammenligning

`tools/audit_floor_walking.py` sammenligner 48 forløp: venstre/høyre fra
de 20 kilde-startankrene, samt åtte tak-/avsatsforløp i rom 1 og 2.
2 271 hovedløkkeinnganger og 14 565 502 faktiske 6502-instruksjoner gir
ingen avvik i hele 64 KiB, registre eller stoppgrenser.

Romseed, kontaktbank og første positur/bilde initialiseres gjennom
originalkode. Hver hovedløkkeinngang har eksplisitt klar venteteller,
input, register-/stackramme og aktiveflagg. Fiendene er deaktivert ved
inngangen, men originalens hovedløkke kjører fortsatt spawn-, rom- og
overgangsgrener. Aktivering og romnummer lagres i resultatet: 505 av
inngangene aktiverer en fiende, og noen ruter bytter rom. Dette er ikke
en prøve der fiendene garanteres fraværende gjennom hele kallet.

Ingen IRQ legges inn mellom disse hovedløkkeinngangene. Derfor verifiserer
prøven de konkrete hovedløkkeoperasjonene, ikke naturlig IRQ-/inputfase,
hele emulatorforløpet eller maskinvareimplementasjonens resultat på hver
av de nye posisjonene. Tidligere native primitive-/motorprøver er separate.

Det er ikke funnet en ekstra Amiga-gulvregel i disse kontrollene. Resultatet
utelukker ikke en feil på den konkrete strekningen brukeren beskriver.
Lavere oppdateringsfart kan dessuten gjøre en uendret C64-pause lengre i tid;
den må skilles fra flere logiske stopp eller annerledes kollisjon.

Rådata og adressert disassembly ligger under
`reference/analysis/floor-walk-2026-10-30`. Normal EXE/ADF og motoren er
uendret av denne undersøkelsen.

## Tid i dagens normalbygg

En separat WinUAE-kjøring bruker uendret normal EXE med SHA-256
`f1e66b765482900374d9c020426d3a42e34301872f4e95a3c1e989e31ef84112`.
PAL OCS/68000/KS1.3/512+512 KiB, testvalg for rom12, uendelig liv og
udødelighet. Ingen profiler, avlesninger, opptak eller input under det
140 sekunder lange måleintervallet. Bare skalartellere leses pauset ved
endepunktene. Dette er samme målemetode som NORMAL_RUNTIME_BASELINE.md.

6936 PAL-felt / 2078 kildesteg = 3,3378 felt per steg. Tre-feltsmålet er
ikke nådd: gjennomsnittlig oppdatering tar omtrent 11,26 prosent lengre
tid. Ingen lydticks mistes i intervallet; kilde-/DMA-feiltellere er null.
Rom og loader-epoke er uendret; begge fiender er inaktive ved endepunktene.
Dette er en stasjonær scene, ikke måling av brukerens konkrete løperute
eller bevis for fiendestatus gjennom hele intervallet.

En pause på to logikksteg tilsvarer 120 ms ved tre PAL-felt per steg.
Med målt gjennomsnittskadens blir den illustrativt omtrent 134 ms. Dette
er en beregning fra gjennomsnittet, ikke målt varighet av et bestemt stopp.
Målingen støtter at sen oppdatering kan forsterke opplevelsen; den beviser
ikke at tidsbruken alene forklarer brukerens observasjon.

Rårapport: reference/analysis/normal-runtime-2026-10-30/floor-walk-room12-current/report.json.
Gulv-/støttereglene beholdes mens den konkrete strekningen avklares.
