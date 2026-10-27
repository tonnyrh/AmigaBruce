# Cheat-brettvalg og tidligere lanterner

26. oktober 2026. Brettvalget skal gi en brukbar testtilstand i senere rom.
Tidligere flyttet det bare Bruce og lot alle tidligere lanterner stå igjen.

## Ny testfunksjon

Ved start i et valgt rom fullføres lanterner i alle **lavere romnumre**.
Rom 10 gir dermed fullførte lanterner i rom 1–9. Valgt rom og senere rom
beholder lanternene sine. Dette er en uttrykkelig Amiga-cheat, ikke en
påstand om at C64 hadde et tilsvarende brettvalg eller en lineær romrute.

F1/F2-brettbytte under testing bruker samme forberedelse og beholder
innsamlinger som allerede er gjort. Et hopp bakover fyller ikke opp eldre
rom igjen. Et nytt spill begynner med den valgte testtilstanden fra bunnen.
Vanlig start i rom 1 og de rå rominspeksjonene i kildeverktøyene er uendret.

Forberedelsen gir ingen poeng, bonusliv eller falske pickup-lyder. Ved
to spillere får begge samme startgrunnlag, men videre innsamling og
eventuelle senere cheat-hopp lagres separat for hver spiller.

## C64-data som må stemme

Kilde: den uendrede `.reference/c64/work/untrained-memory.bin`, SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Remember/T64-kandidaten er ikke sertifisert som en urørt 1984-utgave.

| Kilde | Betydning |
| --- | --- |
| `$4CE2 + 2×rom` | Peker til firebytes-records: aktivstatus, erstatningstegn, kolonne og rad. Negativ første byte avslutter listen. |
| `$331C–$336D` | Finner en aktiv lanterne; `$335F–$3365` nullstiller recordens første byte og dekrementerer romteller `$2A + rom`. |
| `$336E–$33B2` | Erstatter allerede innsamlede lanterner med deres faktiske erstatningstegn ved romlasting. |
| `$33B3–$33BC` | Tilbakestiller rommets engangsflagg før videre init. Cheat-hopp bruker den vanlige loaderen etter forberedelsen. |
| `$2F2D–$2F36` | Normal innsamling gir poeng og lyd; cheat-forberedelsen kaller ikke denne belønningsgrenen. |
| `$1856–$1870` | Spillerskifte bytter spilltilstand og gjenoppretter hver spillers lanternegrunnlag. |

Det holder ikke å sette bare Amiga-masken `collected[]`, eller bare C64s
gjenstående teller. Cheat-forberedelsen oppdaterer både C64-recordene,
romtellerne og Amiga-maskene før valgt rom lastes. De samme dataene tas med
i sesjonens spillerlagring.

Rom 14 og 20 har hver en tilsynelatende aktiv record ved `(0,0)` selv om
romtellerne starter på null. Disse er plassholdere, ikke ordinære lanterner.
Forberedelsen stopper når den faktiske telleren er null og lar disse
oppføringene stå slik kildekoden gjør. Den nullstiller ikke hele tabellen.

## Kontroller

Alle 20 startvalg sammenlignes med **1075 faktiske kjøringer av `$331C`**
fordelt over starttilstandene. De opprinnelige instruksjonene gjør bare
recorddelen av innsamlingen i kontrollen; belønningsgrenen er med hensikt
utelatt for denne cheaten. Alle tellere og firebytes-records, også valgt
rom, senere rom og nullteller-plassholdere, sammenlignes.

Den delte session-fixturen prøver tre startrom på 68000, vanlige starter,
levende brettbytte, hopp bakover, bevart målromsinnsamling, uendret poeng/liv
og to uavhengige spillere over flere dødsfall. Kildekontrollene er injiserte
testtilstander, ikke en naturlig C64-gjennomspilling.

[Kildekontroller](../reference/analysis/cheat-progress-2026-10-26/report.json)
og [disassembly](../reference/analysis/cheat-progress-2026-10-26/source-disassembly.txt).
En PAL A500-kjøring med 68000, OCS, Kickstart 1.3 og 512+512 KiB består
session-fixturen og alle øvrige inkluderte aktør-, kontakt-, rom-, lyd- og
DMA-kontroller. Kjøringen fortsetter i 900 spilløkker og gjenoppretter
AmigaOS; største ledige Chip-blokk er 60832 byte. Full host-regresjon består
også. Dette er funksjonelle kontroller; den generelle feltkadensen er
fortsatt åpen (største ordinære feltgap 2 i dette løpet).

Vanlig EXE er 224420 byte, ADF-en 901120 byte, og AmigaDOS-kommandoen `start`
er oppdatert. Nytt spill må startes for å bruke den nye forberedelsen.
[Leveranse og filidentiteter](../reference/validation/cheat-progress-delivery.json).
