# Varighet av bevegelse — 2026-10-20

Samme logiske start- og sluttpunkter sammenlignes. C64-tiden kommer fra CPU-klokken; A500-tiden fra CIA TOD målt ved hendelsene. Debuggerpauser teller ikke.

| Handling | C64 | A500, kjøring 1 | A500, kjøring 2 |
| --- | ---: | ---: | ---: |
| Gange x32 til x98 | 0.778 s | 0.781 s | 0.781 s |
| Stående hopp: satsvalg til første retur til y196 | 0.838 s | 0.841 s | 0.841 s |
| Fritt fall y138 til y196 | 1.736 s | 1.743 s | 1.743 s |

A500-timeren har omtrent 20 ms oppløsning. De viste tidene er omregnet med maskinens nominelle klokke og målt kort/lang PAL-feltmodus. Små forskjeller under ett felt kan ikke avgjøres som nøyaktige millisekundavvik med denne målingen.

Dette godkjenner de tre handlingsvarighetene innen timeroppløsningen. Kollisjonsgeometri, løpshoppets kjente landing og fysisk input-til-skjerm-latens er fortsatt egne åpne tester. Spillfarten er ikke endret.

Hele tallgrunnlaget og filidentiteter: [movement-timing.json](../reference/validation/movement-timing.json).

Klokkedefinisjoner: [VICE C64](https://github.com/VICE-Team/svn-mirror/blob/main/vice/src/c64/c64.h), [WinUAE PAL-konstanter](https://github.com/tonioni/WinUAE/blob/master/include/custom.h), [WinUAE feltberegning](https://github.com/tonioni/WinUAE/blob/master/custom.cpp).

## Klokkeavvik over lengre tid

Med 313 linjer per A500-felt varer tre felt 60.096 ms, mot 59.851 ms på C64. Modellen gir 0.409% lengre A500-varighet, omtrent 245 ms per C64-minutt dersom alt fortsetter med tre felt per steg. Dette er en klokkeutledning, ikke en målt gjennomspilling. Eksakt langtidsparitet er fortsatt åpen.
