# Handling og tilstand ved rombytte

Kontrollert 30. oktober 2026 mot den frosne C64-kandidatens faktiske bytes:
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Kandidaten er fortsatt ikke sertifisert som urørt 1984-utgave.

## Funn

Et vanlig rombytte fortsetter ikke det pågående hoppet eller løpstilstanden.
Den felles romlasteren setter Bruce til tilstand 0 med en kort ankomstteller.
Dette er også hva dagens Amiga-kjede gjør.

| Felt | Kildeoperasjon | Effekt |
| --- | --- | --- |
| X/Y | `$2F9A–$2F9D` | Destinasjonens inngangskoordinater |
| Rom | `$2F9F–$2FA1` | Destinasjonsrom fra `$4E` |
| Handlingsstatus `$BF` | `$0A73/$0A7E` | 0, stående |
| Handlings-/ankomstteller `$CE` | `$0A6F/$0A71` | 4 |
| Aktørventing `$0106` | `$0A80` | 0 |
| Retning `$A4` | Ingen nullstilling i denne grenen | Beholdes i kontrollene |

`$2F8E` skiller Bruce (aktør 0) fra fiender. Bruces gren går gjennom
`$2F9A–$2FD3`, nullstiller kildestacken og kaller den faktiske `$09BC`-
lasteren. Etterpå bygges spritebildene gjennom `$2584`, IRQ aktiveres,
og koden går tilbake til `$1BC2`.

Etter første hovedløkke i målrommet er tilstanden fortsatt 0 og telleren 3.
De neste kontrollerte oppdateringene teller videre 2, 1, 0. Deretter brukes
gjeldende input: holdt sideveis retning gir løping igjen, og holdt skrått
opp gir et **nytt** hopp når støtten tillater det. Slippes input, står Bruce.
Det gamle hoppets fase/teller fortsetter ikke.

«Tilstand» må skilles fra tidligere tilstand og gammel spritepositur.
`$C2` og grafikkvalgene `$4F48/$4F4E` kan fortsatt inneholde forrige
handling under selve innlastingen. I kontrollene velger første nye
aktøroppdatering ståposituren. Bevarte grafikk-/historikkfelt betyr ikke at
hoppbevegelsen er bevart. Denne undersøkelsen sertifiserer ikke hvilken
sprite som blir synlig i hvert enkelt originalt rasterfelt under lasting.

## Kontroller

`tools/audit_room_entry_state.py` bruker de faktiske øvre/nedre utgangene
mellom rom 1 og 2 i begge retninger, gjennom originalens objekt- og
utgangskjede `$1BC2 → $2E39 → $2F8E → $09BC`. F1/F2 og debug-romhopp
brukes ikke som erstatning for vanlige rombytter.

36 kontrollerte tilfeller dekker løp, skrått hopp og fall ved utgangen,
med sluppet input, holdt sideretning eller holdt skrått opp etterpå.
252 hovedløkkeinnganger og 2 268 645 faktiske 6502-instruksjoner gir samme
hele 64 KiB, CPU-registre/-flagg og ventegrenser som den aktive native
C-kjeden. Kontrollpunkter lagrer status etter loaderens nullstilling,
ved inngang til målrommets hovedløkke og etter de første oppdateringene.

Inngangsposisjon, handlingsfase, bevegelseshistorikk og input er eksplisitte
testtilstander. Ingen IRQ legges inn mellom oppdateringene. Dette er
kildekodekontroll, ikke naturlig C64-spilling, ny native A500-kontroll av
disse konkrete rutene eller sertifisert input-/rasterfase. Andre roms
init-/faregrener kan påvirke den første etterfølgende aktøroppdateringen;
den felles loaderens nullstilling skal ikke omgjøres til en ny regel om
bevart hopp-/løpetilstand.

Ingen produksjonskode, EXE eller ADF er endret av denne gjennomgangen.
Resultat og adressert disassembly:
`reference/analysis/room-entry-state-2026-10-30/`.
