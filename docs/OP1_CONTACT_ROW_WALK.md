# OP1-pilot for kontaktradene på 68000

31. oktober 2026. Radløkken ble raskere isolert. Den første rom 1-kjøringen
sparte 11 PAL-felt, mens gjentakelsen brukte 7 flere. Kandidaten er derfor
arkivert som forsøk. Spillebygget fra før OP1 er fortsatt gjeldende.

| Rute, 240 spillsteg | PAL-felt før | PAL-felt etter | Tapte lydtikker før / etter |
| --- | ---: | ---: | ---: |
| Rom 1, begge fiender | 1033 | 1022 | 19 / 19 |
| Rom 1, begge fiender, gjentakelse | 1031 | 1038 | 19 / 19 |
| Rom 12, klatring | 818 | 824 | 0 / 0 |
| Rom 13, Yamo | 736 | 736 | 0 / 0 |

Hvert par brukte samme OP0-måleprogram, rute og 240 oppvarmingssteg i
WinUAE på PAL A500 OCS med 512 KiB Chip og 512 KiB slow. Bare
objektfilen for kontaktradene ble byttet ved lenking. I rom 1 var begge
fiender aktive gjennom hele måleperioden i begge parene. Ruten i rom 13
måler Yamo mens han er aktiv. Retur etter nederlag står åpen i testlisten.

I gjentakelsen i rom 1 sank målt arbeid med 424 rasterlinjer over hele
ruten. Tiden i ventingen ved bildepresentasjon økte samtidig med 2943
linjer. Den samlede tiden steg dermed selv om arbeidet ble litt billigere.

## Endringen og kildesjekken

I den frosne Remember/T64-kandidaten leser `$5380`, `$539A` og `$53B4`
hver sin pikselkolonne. Hvert treff skriver til `$4E` og to klasseplasser
før neste kolonne leses. `$53CE` øker Y. Deretter testes grensene for kropp,
fot og siste rad. Kildehash er
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Utgaven er fortsatt usikkert identifisert som urørt 1984-utgave.

Kandidaten regner inn første Y når gruppen starter. Tre glyphpekere og én
maskepeker økes automatisk etter lesing. Ved siste rad beregnes utgående Y
fra start og radantall. Kjernen gikk fra 202 til 188 kodebyte.
Eksisterende C-kode velger gruppens størrelse,
håndterer adresseomslag og utfører de samme servicekallene. Den isolerte
målingen vekslet gammel/ny/ny/gammel kode i samme kjøring, 256 kall per
blokk. Med én, fire eller åtte rader og tomme, spredte eller tette treff
brukte den nye rutinen 7,8–24,7 % færre rasterlinjer.

170 konstruerte innganger ble kjørt fra `$537E` til `$53CF` etter siste
`INY` på de faktiske 6502-bytene, til sammen 29 747 instruksjoner. Ytterligere
22 tilfeller kontrollerte Amiga-rutinens tidlige retur ved null rader. Det
lenkede 68000-programmet sammenlignet hele 64 KiB og alle ti byte i
parameterblokken. Alle 192 tilfeller bestod. Prøvene dekker blant annet
ulike start-Y, siste byte ved `$FFFF`, Y som går til null og lesing av
nettopp skrevne klasse-/scratchbyte. Dette er kontrollerte innganger.

Den integrerte Amiga-testen bestod alle 53 motorfixturer og 1200 løkker.
Største ledige Chip-blokk var 52632 byte. Denne særskilte reprisen registrerte
81 tapte lydtikker. De uprofilerte tidsparene i tabellen bruker ordinær
PAL-planlegging og måles separat.

Råmålinger, kildekontroller og forsøkskode finnes i
`reference/analysis/op1-row-walk-2026-10-31/`. Kontroller resultatene med
`python tools/verify_op1_row_walk.py`.

## Neste OP

OP2 følger feltarbeidet i samme rom 1-rute. OP0 registrerte 1270 VIC-kall
og 192,7 eksklusive profilerte rasterlinjer per spillsteg i den profilerte
kjøringen med begge fiendene. Første spørsmål er hvilke felt som trenger
en ny pikselberegning, hva den koster, og når lydservice kommer for sent.
Sammenlign eventuelle tiltak med den uprofilerte spillruten og bevar C64s
akkumulering og nullstilling av kollisjonsbitene ved lesing.
