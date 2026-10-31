# Kontaktmasker: faste 68000-kopier, 31. oktober 2026

Dette steget erstatter løkkestyringen i de faste kopierings- og
nullstillingsløkkene i `bl_contact_align4`. C-kode, spillregler, kilde-RAM,
registerpublisering og eksisterende servicepunkter beholdes. De variable
prefiks- og forskyvningsløkkene beholdes også.

Kildegrunnlaget er den frosne Remember/T64-kandidaten, SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Den er fortsatt ikke bekreftet som en urørt 1984-utgave.
Originalrutinen `$52AD-$5309` nullstiller prefikset, legger til 32 nullbyte
ved fase 3, kopierer 96 byte ved `$52CB-$52D7`, og forskyver maskene etter
fase. Disassembly med faktiske bytes ligger i forsøksarkivet.

Den eksisterende native kjernen grupperer allerede uavhengige bitrader.
Dette steget fjerner bare tellere og tilbakehopp fra fire løkker med kjent
lengde: åtte null-longs, 32 nullbyte, 24 kopierte longs og 96 kopierte byte.
Aliasvern, oddetallsbane og rekkefølgen på hver lesning og skriving beholdes.
Ingen ny IRQ-/lydservice legges inne i originalens sammenhengende arbeid.

| Privat variant | PAL-felt / 360 oppdateringer | Tapte lydticks | Kernelbyte |
| --- | ---: | ---: | ---: |
| Gjeldende utgangspunkt | 1423 | 0 | 346 |
| Long-kopier og forskyvningsløkker utbrettet | 1418 | 0 | 1288 |
| Også bytekopier utbrettet | 1417 | 0 | 1530 |
| Valgt: bare faste kopier/nullstillinger | 1410 | 0 | 642 |

Med begge fiender og faste stillinger faller kontaktkostnaden fra 12 505
til 12 049 rasterlinjer per 64 kall, omtrent 3,6 %. Ved overlapp faller den
fra 13 971 til 13 516. Den valgte varianten beholder største ledige
Chip-blokk på 85 408 byte i denne diagnostikken. Den større bytevarianten
ga bare 69 016 byte og blir ikke brukt.

Samlet gevinst er beskjedne 0,9 % i dette ene kontrollerte måleparet.
Dette er ikke en generell hastighetsgaranti. PAL-tallet inkluderer oppstart
og diagnostikk. Den faste stillingstesten bruker fase 0 og oddetallsdestinasjon;
alle fase-/offsetkombinasjoner kontrolleres separat av 256 native
align-kontroller i hvert av de fire bildene. Hvert bilde består totalt 710
kontakt-/kopikontroller, inkludert 256 spritekopikontroller. Uendrede felt-
og bildekjerner varierer med opptil tre rasterlinjer per 64 kall.

Tidligere bytebaserte C64-kontroller beholdes som historisk evidens gjennom
uendret C-referanse og fryst forrige leveranse. Den nye assemblyen må i
tillegg bestå ferske native fixturer, minne-, bilde- og oppstartskontroller.
Leveranseverifikatoren binder disse til de faktiske nye ELF-/EXE-filene.
Den forrige validatoren kjøres mot sitt fryste inngangssett; bare filnavnet
i objdump-overskriften normaliseres ved denne historiske avspillingen.

Fersk fulltest består 53 fixturer og 1 200 løkker / 400 kildeoppdateringer,
uten kilde-, DMA-, aritmetikk-, bilde- eller presentasjonsfeil. Største
ledige Chip-blokk er 52 632 byte, som før. Denne kontrollerte én-felt-per-
løkkeprøven har fortsatt 81 tapte lydticks, også som før; den er ikke en
normal sanntidsmåling. Nulltallet i tabellen gjelder den separate PAL-testen.
Normalbyggets CODE øker 296 byte, EXE blir 316 412 byte, og RODATA/DATA/BSS
er uendret.

Normalbygget består fersk CLI-/ADF-oppstart med komplett meny og registrert
spillprogresjon fra ADF. Tolv rom12-bilder og tolv bilder etter kontrollert
død/rom13->12-bytte har null piksel-, fase- og ulovlige flimrefeil.
Dette er kontrollerte normalbyggprøver, ikke en naturlig gjennomspilling.

Råmålinger og private kompilatorinnganger ligger i
`reference/analysis/contact-unroll-2026-10-31/` og de fire navngitte
`contact-unroll-*`-mappene under ytelsesarkivet. Kjør
`python tools/verify_contact_unroll_experiment.py` og
`python tools/verify_contact_unroll_delivery.py` for kontroll.

Full PAL-kadens i alle rom, naturlig IRQ-/VIC-fase, naturlig gjennomspilling,
sertifisert originalutgave og fysisk A500 forblir åpne porter.
