# Native CPU-forsøk, 31. oktober 2026

Forsøkene nedenfor er isolerte. Normal motor og normal EXE/ADF er uendret.
Ingen av variantene er valgt for produksjon: gevinstene er for små i forhold
til kompleksiteten, eller forsvinner når figurene overlapper. Tregheten er
fortsatt et åpent problem.

## Sammenlignbar måling

WinUAE kjører PAL OCS, MC68000, Kickstart 1.3, 512 KiB Chip og 512 KiB slow.
Hvert par bruker samme private testprogram, 360 kildeoppdateringer, begge
fiender, stillestående testudødelig Bruce og faktisk PAL-planlegging.
Telleren inkluderer fast tittelarbeid og diagnostikk. Tallene er ikke FPS,
naturlig gjennomspilling eller bevis for fysisk A500-ytelse. Bare målinger
innen samme par skal brukes til å beregne en gevinst.

| Forsøk | Referanse, PAL-felt | Kandidat | Konklusjon |
| --- | ---: | ---: | --- |
| Fire tomme kontaktrader om gangen | 1411 | 1408 | Liten samlet gevinst, dyrere overlapp |
| Tom klasseoppsummering | 1411 | 1411 | Ingen samlet gevinst |
| Begge tomhetskontroller | 1411 | 1401 | Dyrere overlapp; ikke valgt |
| Cache av justerte kontaktmasker | 1411 | 1410 | Ingen vesentlig samlet gevinst |
| Cache med 16 plasser | 1411 | 1411 / 1416 | Ingen samlet gevinst |
| Egen tom kropp-/klassebane | 1404 | 1415 | Samlet regresjon |
| Native ADDX/SUBX, separate flagg | 1423 | 1415 | Liten gevinst |
| Native aritmetikk, samlet flaggord | 1423 | 1413 | Liten gevinst; ikke levert |
| Samlet flaggord også for N/Z | 1423 | 1430 | Regresjon; ett mistet lydtick |
| Virtuell A i MC68000 D7 | 1411 | 1407 | 0,28 %; ikke valgt |
| Fast kilde-RAM-base i MC68000 A4 | 1411 | 1408 | Omtrent 0,2 %; ikke valgt |

Det siste paret bruker en referanse med en liten ABI-kontroll som
A4-programmet ikke har. Den ligger før den målte perioden, men dette er
likevel en pilot, ikke en endelig akseptanse. Ingen av disse resultatene
gir grunnlag for å hevde at spillet nå kjører vesentlig raskere.

## Bevarte resultater og kilderegler

Den frosne Remember/T64-kandidaten har SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Den er fortsatt ikke sertifisert som en urørt 1984-utgave.

- Kontaktforsøkene gjelder `$52AD–$55AA`. Tomhetskontroller beholder
  de opprinnelige ordnede minneskrivingene på alle øvrige baner. Kontroll
  av overlapp er nødvendig fordi senere lesinger kan se tidligere skrivinger.
- 4239 kontaktkontroller følger 2320683 faktiske kildeinstruksjoner.
- Egen tom kropp-/klassebane kontrolleres med 1536 hele RAM-/registerforløp
  mot 339748 faktiske instruksjoner: kropp `$53E4` til `$53D4`, klasse
  `$5431` gjennom faktisk RTS. Dette dekker ikke fot-/deltesten etter kroppen.
- Binær ADC/SBC kontrolleres uttømmende: 262144 innganger mot de faktiske
  opkodene ved `$0A11` og `$2DE0`. Desimalbanen beholdes; den er ikke
  sertifisert av denne kontrollen. Native MC68000-bygger sammenligner alle
  inngangene med den uendrede portable aritmetikken.
- D7-forsøket endrer lagringen av virtuell A. Offentlige funksjoner bevarer
  Amiga-ABI, og callbacks publiserer og henter A via en speilverdi.
  256 native kontroller sjekker returverdi, åtte argumenter og callerens D7.
- A4-forsøket endrer bare baseregister for samme 64 KiB RAM. Offentlige
  broer bevarer callerens A4. A5 ble først forsøkt, men kompilatoren trenger
  det som framepointer i én funksjon; det forsøket ble avbrutt ved byggfeil.

Alle fullførte ytelsesbilder består sine 710 native kontakt-/kopikontroller
uten rapportert kilde-, aritmetikk- eller DMA-feil. Slike kontroller erstatter
ikke en naturlig C64-gjennomspilling eller kjente åpne IRQ-/rasterspørsmål.

D7-kandidaten består dessuten en fersk full kontroll: 53 RAM-/register-
fixturer og 1200 kontrollerte løkker. Ingen kilde-, DMA-, gjengivelses- eller
aritmetikkfeil rapporteres. Største Chip-blokk er 69024 byte. Den kontrollerte
løkken har fortsatt 81 mistede lydticks og består ikke sanntidskravet. Dette
er en annen test enn PAL-paret i tabellen, som har null mistede lydticks.

## Evidens og videre avgrensning

Private kompilatorinnganger, referanser og rårapporter ligger under
`reference/analysis/contact-zero-2026-10-31`, `contact-memo-2026-10-31`,
`contact-empty-2026-10-31`, `native-arithmetic-2026-10-31`,
`native-d7-2026-10-31` og `native-a4-2026-10-31`.
Hashbundne ytelsesrapporter ligger under
`reference/analysis/optimization-2026-10-27`.

Kjør `python tools/verify_native_cpu_experiments.py` for å kontrollere
oppsummeringen og kilde-/byggidentitetene. Rapporten dokumenterer avviste
forsøk; den godkjenner ikke en ny normalbygning.

Det større potensialet ligger fortsatt i kontaktberegning og kilde-sprite-
bygging med flere aktive figurer. Neste endring bør erstatte en avgrenset
varm rutine med direkte 68000-kode, med samme RAM-resultat og servicegrenser.
Flere generelle cacher og globale registerbindinger prioriteres ikke videre
på grunnlag av disse målingene.
