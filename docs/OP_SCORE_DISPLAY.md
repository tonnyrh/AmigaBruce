# Poengvisning ved falltreff på Kage

I de to kampopptakene fra rom 1 behandler Bruce 53 poengtildelinger per
falltreff på Kage. Hver tildeling går gjennom `$3175 → $312C`. Koden
legger poengene til i `$41–$43` og sammenligner med de tre bytene ved
`$4392`. Grenen ved `$3157` oppdaterer visningen av ekstraliv når
kildens betingelse er oppfylt.

Etter konvertering til pakkede desimaler ved `$32DC` viser
`$315D–$3172` tre sifferpar fra `$439C–$439E`. To JSR og et avsluttende
JMP går til `$1B17`. Den skriver først øvre og så nedre siffer, begge
med bit 4 satt. De seks skjermbytene ligger på `$8C30–$8C35`.
Amiga-motoren begynner å indeksere spillflaten ved `$8C78`.

I den profilerte kontrollen ble hvert av de 106 poengkallene på de to
treffene delt i fire tidsintervaller. Oppsettet ved `$3175` tok samlet
169 rasterlinjer, poeng- og terskelberegningen fra `$312C` tok 692,
desimalforberedelsen og konverteringen fra `$315A` tok 1267 og
sifferskrivingen fra `$315D` tok 2107. Det siste intervallet var
størst. Tidsstemplingen inngår i denne rangeringen. Før/etter-rutene
nedenfor kjørte uten denne seksjonsmålingen.

Den avgrensede 68000-rutinen skriver de samme seks bytene ved hver
tildeling. Den beholder PHA- og JSR-bytene på stack-siden, også når
stackpekeren passerer null. Ved retur er A siste siffertegn, Y er
`$34` og carry er bit 3 i siste sifferpar etter den fjerde
høyreforskyvningen ved `$3211`. X, V, D og I er bevart. Den vanlige
RTS-banen leser fortsatt den faktiske returadressen fra stacken.

## Kontroller mot maskinkoden

Kildegrunnlaget er Remember/T64-kandidaten med SHA-256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Vertstesten kjørte de faktiske 6502-instruksjonene og sammenlignet
alle 65 536 minnebyte, registre, flagg og retur-PC. De 256 prøvene ved
`$315D` dekker alle stackposisjoner og alle byteverdier i hver av de
tre sifferposisjonene. 30 hele kall ved `$3175` dekker blant annet
byteoverløp og 12 tildelinger av ekstraliv.

På 68000 i WinUAE ble de to komplette kampopptakene kjørt med den nye
rutinen. Minne og registre stemte ved alle 18 kontrollerte IRQ-returer
til `$2C51` og ved sluttreturen til `$1C26`. Dette er kontrollerte
innganger fra Amiga-ruten. Naturlig avbruddsfase, fysisk A500 og
identiteten som urørt C64-utgave fra 1984 er fortsatt åpne.

## Tid på PAL A500 i WinUAE

Hvert bygg kjørte rom 1 med Kage og Yamo aktive, først i 240
oppvarmingssteg og deretter i 240 målte spillsteg. Bevegelsesrutene
hadde 96 steg i lufta. Begge bygg leser feltklokken rett før de tre
Paula-kanalene oppdateres. Et tomt felt betyr at ingen ny publisering
begynte der. Forrige lyd kan fremdeles spille.

| Måling | Før, to kjøringer | Etter, to kjøringer |
| --- | ---: | ---: |
| Bevegelsesrute, PAL-felt | 992 / 993 | 984 / 984 |
| Lengste steg på bevegelsesruten, rasterlinjer | 3756 / 3756 | 3131 / 3130 |
| Felt uten ny Paula-publisering i bevegelse | 13 / 13 | 10 / 10 |
| Felt med dobbel publisering i bevegelse | 1 / 1 | 2 / 2 |
| Stillestående rute, PAL-felt | 965 / 963 | 966 / 960 |
| Felt uten ny Paula-publisering ved stillstand | 0 / 0 | 0 / 0 |

Det lengste steget gikk fra omtrent 240 til 200 ms. Tiden for hele
bevegelsesruten gikk ned med 0,16–0,18 sekunder. Feltservicen bruker
den vanlige OP2-banen i begge bygg.

Systemtesten bestod 53 native kontroller og 1200 spilløkker på PAL OCS
med Kickstart 1.3 og 512 + 512 KiB RAM. Største ledige Chip RAM-blokk
etter lasting var 52 632 byte mot minstekravet på 49 152. I tillegg
bestod 3034 kontroller av figur- og kampkoden og fem integrerte forløp
med til sammen 7 055 873 utførte C64-instruksjoner.

Det vanlige AmigaDOS-programmet vokste med 220 byte, fra 326 156 til
326 376 byte. Maskinkoden for aktørmotoren i normalbygget samsvarer
med den målte varianten.
AmigaDOS startet til komplett meny. Fra skrivebeskyttet ADF startet
rom 1 og gikk fra spillsteg 7 til 45 uten motorfeil.
[Målerapporter](../reference/analysis/op-score-2026-10-31/measurements.json)
og [byggidentiteter](../reference/analysis/op-score-2026-10-31/build.json).

En ny kompilering fra kildefilene ga de samme adressene, størrelsene
og innholdet i de lastbare ELF-seksjonene for begge målebyggene.
Referanseprogrammets Hunk-fil hadde én ulik utfyllingsbyte etter
den 17 byte lange dataseksjonen.

Måleverktøy og rapporter er samlet i
[analysemappen](../reference/analysis/op-score-2026-10-31/). `build_score.py`
bygger variantene `reference`, `candidate` og `profile` med samme
68000-verktøykjede. `run.ps1` bruker `1 3 2` for bevegelse og `1 3 0`
for stillstand. `host.ps1` kontrollerer scoretilfellene. `proof.py`
bruker de to lokale kampopptakene klargjort i [OP4-feltprøven](OP4_FIELD_OWNER.md).
