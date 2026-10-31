# OP4: raskere lesing til visningen

29. oktober 2026. Ingen spillregler, innganger, felttellere eller
C64-oppdateringer endres. `source_session_view` henter fortsatt levende
lanternedata for alle20 rom på hvert steg, men bruker ett kall til
`bl_c64_collected_all` i stedet for20 kall over modulgrensen. Den gamle
enkeltromsfunksjonen beholdes med opprinnelig implementasjon.

Grunnlaget er den frosne Remember/T64-kandidaten, SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Den faktiske `$331C-$336D` velger rommets4-byte-poster fra `$4CE2`, stopper
ved en post med bit7 og skriver null til en tatt lanterne ved `$3361`.
Dette begrunner betydningen av postene.13-bit-grensen er den eksisterende
Amiga-visningens representasjon; den innføres ikke som en ny C64-regel.

Bulkfunksjonen leser de samme pekerne og postene i romrekkefølge og
skriver de samme20 maskene til eksisterende `BlProgress.collected`.
Det legges ikke inn en tidsbasert cache eller antakelser om hvilke rom
som kan endres. Død, turbytte, ny runde og testhopp trenger derfor ingen
ny invalideringsregel. All kilde-RAM forblir autoritativ og uendret av lesingen.
ABI bruker en32-bit peker til eksisterende16-bit maskefelt; ingen struktur
eller heltallsbredde i modulgrensen endres. Ingen ny statisk tabell eller
Chip-/slow-allokering er lagt til.

| Måling,360 kildesteg i rom1 | Før | Etter |
| --- | ---: | ---: |
| Profilert visningsarbeid, rasterlinjer/kall | 55,839 | 48,394 |
| Samlet selvkost i visningen | 20102 | 17422 |
| Uprofilert faktisk PAL-tid | 1432 felt | 1426 felt |
| Tapte lydtikker i den uprofilerte prøven | 23 | 17 |
| Viste bilder i den uprofilerte prøven | 360 | 360 |

Visningsdelen bruker13,331 prosent mindre CPU i denne målingen. Det
samlede feltresultatet er ett avgrenset før/etter-par, omtrent0,42 prosent
kortere tid. Det er ikke et løfte om tilsvarende gevinst i alle rom, og
sanntidsporten er fortsatt åpen. To bulkprofiler ga48,336 og48,394 linjer
per kall. Ingen arbeidskostnad er flyttet utenfor samme profilgrense.

Et første forsøk endret bare enkeltmaskens beregning og ble tregere:
57,217 mot55,839 linjer/kall. Det er ikke tatt inn som erstatning for den
opprinnelige enkeltromsfunksjonen. Den enklere maskeberegningen brukes
bare inne i den samlede innhentingen, der kallene kan fjernes og koden
optimaliseres under ett. Forsøkskildene er bevart med kontrollerte hasher.

`test-view-mask.ps1` kontrollerer2293920 enkeltberegninger mot den frosne
forrige C-funksjonen og uavhengig forventet bitmaske.1280 bulkvektorer gir
25600 maskesammenligninger, inkludert full64KiB-kontroll for uendrede
RAM-data. Pekere med adresseomslag og overlapp er med. Dette er
kompatibilitetskontroller av visningsrepresentasjonen, ikke en simulert
regel som fastsetter C64-spilloppførsel.

Målinger og kildesnapshots ligger under
`reference/analysis/view-mask-2026-10-29/`; rå native kjøringer har egne
navn i `reference/analysis/optimization-2026-10-27/`.
`tools/verify_view_projection.py` binder kontrollene og målingene til
faktiske kilder og binærer. Ordinær spiller-/fiende-/romlogikk kontrolleres
fortsatt av de separate originalbyte- og native motortestene.
