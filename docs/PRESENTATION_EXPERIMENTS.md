# Skjermplanlegging, 29. oktober 2026

C64-kandidaten setter `$48=3` ved `$1BC2-$1BC5` og venter ved
`$1C32-$1C38` til kilde-IRQ-arbeidet har telt ned. Frosset binær:
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Dette er Remember/T64-kandidaten; urørt 1984-utgave er fortsatt ikke bekreftet.

Amigaens venting på vertikalblank er en annen kostnad enn C64s `$48`.
Et separat målebygg viste bare to muligheter for å gjenbruke en allerede
pågående blankperiode på 460 arbeidsrunder. Det ble derfor ikke innført
en ny regel for når Copper-listen publiseres.

I stedet ble én umiddelbar arbeidsrunde etter første utsatte bilde prøvd.
C64-klokken, IRQ-telleren, rom og spillregler ble beholdt. Vedvarende arbeid
hadde fortsatt en grense på tre utsatte runder/felt. Dette var et avgrenset
forsøk, ikke en godkjent endring i produksjonsmotoren.

| Måling, 360 kildebaserte spillsteg i rom 1 | Før | Forsøk |
| --- | ---: | ---: |
| Faktiske PAL-felt | 1429 | 1415 |
| Registrerte tapte lydtikker | 25 | 44 |
| Publiserte bilder | 360 | 422 |
| Utsatte arbeidsrunder | 100 | 101 |

Samlet tid falt bare 0,98 prosent. Flere bilder ble vist, men lydservicen
ble dårligere. Forsøket er forkastet; motor, bygge-/testskript og
presentasjonstester er tilbake på den verifiserte spritekopieringsversjonen.
Ingen ny spillhastighet eller C64-venteregel er tatt inn.

Begge separate native målebygg besto 710 kontakt-/spritekontroller,
inkludert 256 spritekopieringsvarianter. Kilde-, aritmetikk-, DMA- og
kontrollfeil var null; største ledige Chip-blokk var 52632 byte. Dette
bekrefter ikke naturlig gjennomspilling eller sanntidskravet. En tidligere
kombinasjon av ekstra probe og hele diagnosesettet fikk allokeringsfeil
og er eksplisitt ekskludert fra tidsmålingen.

Alle forsøkskilder, før-kilder og testede binærer er bevart under
`reference/analysis/present-2026-10-29/` og de navngitte målemappene.
`tools/verify_presentation_experiments.py` binder målingene til disse
filene, kontrollerer C64-bytebetingelsene og bekrefter gjenopprettingen.
[Maskinlesbart resultat](../reference/validation/presentation-experiments.json).

Videre prioritering: mål CPU-/Blitter-overlapp og lydpublisering separat.
I siste profil brukte `audio_publish` 22141 rasterlinjer over 1524 kall,
og den samlede kontaktdriverens egenkostnad var 44358 linjer over 360 steg.
Profileringskostnad og kilde-/rasterfase gjør at disse tallene bare
prioriterer neste undersøkelse; de er ikke lovet gevinst. Neste forsøk må
vise bedre samlet PAL-tid uten flere lydforsinkelser eller endret kildeutfall.
