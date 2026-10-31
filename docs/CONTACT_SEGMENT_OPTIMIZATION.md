# Kontaktsegmenter: tre målte forsøk,29. oktober2026

**Ingen av variantene ga kortere samlet kjøretid. Motor og spillbygg ble
gjenopprettet til71cb4c6, byte for byte, etter denne runden.** Forsøkskoden er arkivert separat.

| Variant | PAL-felt /360 spillsteg | Tapte lydtick |
| --- | ---: | ---: |
| Validert utgangspunkt |1428|21|
| Grensevalg i68000-kjernen |1428|21|
| Samme kontaktstruktur gjennom radløkken |1431|25|
| Utsatt flaggberegning til observerbare punkter |1428|24|

Dette er samme WinUAE68000/OCS/KS1.3/512KiB Chip+512KiB slow-scene i rom1,
begge fiender, stasjonær udødelig test-Bruce og ekte PAL-planlegging.
Det er en avgrenset målebane, ikke naturlig spilling eller tall for alle rom.
Profilering kjøres separat; profiltall skal ikke sammenlignes med totaltiden.

## Kildegrunnlag

Frossen Remember/T64-kandidat, SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Kandidaten er fortsatt ikke sertifisert som urørt1984-utgave.
Det separate bytebaserte uttrekket ligger i
`reference/analysis/contact-segments-2026-10-29/source-row-disassembly.txt`.

Ved$5380/$539A/$53B4 behandles tre pikselkolonner i rekkefølge, med
umiddelbare skrivinger til scratch$4E og klasseslottene$4EED-$4F2A.
Etter INY$53CE sammenlignes Y med kropp$4F38, fot$4F39 og del$4F3A.
Kroppsgrenen$53E4-$5428 klassifiserer og reagerer på kontakt.
Fotgrenen$5429 klassifiserer, forkaster returadressen med to PLA og går
til$52A4. Delgrenen$53E1 lagrer Y i$52 og returnerer normalt.

Forsøkskjernen valgte opptil8-(Y&7) rader, begrenset av korteste ikke-null
åttebitsavstand til de tre grensene. Null må ignoreres fordi originalen
sammenligner etter INY. Pekere over$FF00 brukte C-reservebanens adresseomslag.
Kolonnerekkefølge, aliaser, C64-stackskrivinger og eksisterende servicepunkter
ble beholdt. Ingen ny spillregel ble innført.

## Hva kontrollene viste

Alle4239 vertskontroller mot faktiske C64-instruksjoner besto, inkludert489
registeravlesninger ved servicepunkter. De tre tidsbyggene besto1558 native
kontaktkontroller hver: de eksisterende1046 og512 nye tilfeller for alle256
Y-verdier, like/allerede nådde grenser, byteomslag og klasse-/scratch-aliaser.
1536 native VIC-kontroller besto også. Detaljprofilene beholdt454 kontaktkontroller.
Dette erstatter ikke et komplett53-fixturpass for forsøksvariantene; de ble
forkastet før slik leveransegodkjenning.

Detaljprofilen målte radløkkens selvkost til14,795 rasterlinjer før,
14,359 for grensevalg og14,292 for siste variant. Samtidig økte arbeidet
inne i den profilerte kjernen fra4,680 til5,088 linjer fordi grensevalget
ble flyttet dit. Selvtotalen alene ville derfor gitt et misvisende bilde.
Samlet tid og lydservice ble ikke bedre, og endringene er ikke tatt i bruk.

Kode, bygg, profiler og avvisningsgrunner er bevart under
`reference/analysis/contact-segments-2026-10-29/` og de navngitte profil-
mappene i `reference/analysis/optimization-2026-10-27/`.
[Maskinlesbar verifikasjon](../reference/validation/contact-segment-experiments.json)
binder målingene til kildekode og testede binærer. Kildene, normal EXE/ELF/ADF
og CLI-starten ble gjenopprettet ved avslutningen av denne runden. Senere
produksjonsendringer dokumenteres separat.

Neste relevante forsøk er å måle kontaktpassets samlede C-/68000-overganger
ved$5212-$52AC, spesielt pekerforberedelse fulgt av radkontakt. Det krever en
større sammenhengende kjerne med samme kilde-RAM, stack og servicepunkter;
små flyttinger av bokføring i radløkken er ikke dokumentert som en gevinst.
Full feltkadens, lydservice, naturlig rasterfase og fysisk A500 står fortsatt åpne.
