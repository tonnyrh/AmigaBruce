# OP2 – feltkostnad og lydservice på A500

Den eksisterende rom 1-ruten går raskere når den nye 68000-rutinen bygger
maskene for ensfargede sprites med dobbel bredde. To målepar med Kage og
Yamo aktive ga samme resultat. Det brukes 29 færre PAL-felt på 240 spillsteg,
og antall tapte lydservicetikker faller fra 19 til 3.

| Rom og rute | PAL-felt før / etter | Tapte lydtikker før / etter |
| --- | ---: | ---: |
| Rom 1, begge fiender, første par | 1031 / 1002 | 19 / 3 |
| Rom 1, begge fiender, gjentakelse | 1031 / 1002 | 19 / 3 |
| Rom 1, bare tid ved start og slutt av perioden | 1022 / 996 | 19 / 1 |
| Rom 12, opp/ned i klatreområdet | 818 / 814 | 0 / 0 |
| Rom 13, Yamo | 736 / 736 | 0 / 0 |

Rom 1-tallene kommer fra ferske sammenligninger. Referansene for rom 12
og 13 kommer fra OP1 med samme måleprogram og input. Hver rute starter
med 240 oppvarmingssteg og måler de neste 240 på PAL OCS/68000 med
Kickstart 1.3, 512 KiB Chip og 512 KiB slow. Diagnosen bruker stillestående
udødelig Bruce i rom 1. Når feltklokken går fram med mer enn ett felt
mellom to betjente lydtikker, teller kolonnen for lydtap de mellomliggende
feltene. Hørbar lydkvalitet må vurderes separat.

## Når lydservicen kommer for sent

Lydsjekken etter et behandlet spillfelt fant alle de 20 forsinkelsene i
hver av to detaljerte kjøringer. Det hadde gått to PAL-felt siden forrige
lydtikk i hvert tilfelle. Forrige sjekk så ingen ny tikk. Det var ingen
andre lydsjekker inne i feltkallet. Spillet måtte bygge én eller to
spritemasker i hvert av disse feltene. VIC-arbeidet tok 292–392 rasterlinjer
og hele feltkallet 321–422 linjer på tvers av de to kjøringene.
Et eget bygg som bare registrerte kallstedet ga samme sted for alle 20
forsinkelsene. Med Bruce alene ble forrige VIC-resultat gjenbrukt i alle
720 feltkall, og lydtellingen viste null tap.

| VIC-arbeid i første detaljerte rom 1-rute | Antall før / etter | Gjennomsnittlig VIC-tid før / etter, linjer per kall |
| --- | ---: | ---: |
| Gjenbruk av forrige kollisjonsresultat | 931 / 895 | 12,65 / 12,66 |
| Ny pikseltest med gyldige masker | 47 / 47 | 141,74 / 141,83 |
| Ny pikseltest med minst én maske å bygge | 98 / 98 | 251,93 / 178,44 |

De 98 siste kallene krevde til sammen 185 maskebygginger. Selve
maskebyggingen tok 8957 rasterlinjer før og 1730 etter. Dette er tid
**innenfor** VIC-kallet. Den er allerede med i tabellen. Den detaljerte
målingen hadde 20 tapte tikker før og 4 etter. Tidsstempler og registrering
endrer hvor i PAL-feltet arbeidet havner. Derfor viser den første tabellen
gjennomstrømningen fra separate kjøringer uten denne registreringen.

## C64-kilden og Amiga-rutinen

I den frosne Remember/T64-kandidaten setter oppstarten ved
`$07F5–$07FC` multicolor-registeret `$D01C` til null og bredderegisteret
`$D01D` til `$FF`. Ved `$361A–$361E` skrives også `$FF` til
bredderegisteret. Kilden leser sprite-kollisjonslåsen `$D01E` ved
`$29CE` og `$3D20`. Kildehash er
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Identiteten som urørt 1984-utgave er fortsatt uavklart.

Amigaen trenger en maske over de synlige pikslene for å beregne denne
låsen. En tabell på 256 ord utvider hver bit i en kildebyte til to
nabobiter. Rutinen leser tre byte per rad i 21 rader, lagrer de opprinnelige
63 bytene og skriver den utvidede masken i eksisterende buffere. Tidsplanen
for lyd, rekkefølgen på feltkallene og kildens lesing og tømming av låsen
følger samme kode som i referansen. Den portable rutinen håndterer fortsatt
multicolor, vanlig bredde og adresseomslag.

512 native kontroller prøvde alle 256 byteverdier i alle 63 posisjoner
med både oddetalls- og partallsadresse. De sammenlignet alle råbyte og
alle 21 par utgående maskeord med en bitvis referanse, og kontrollerte
kildebufferen, padding og grensebyte.

Normal EXE er 317136 byte, en økning på 724 byte. Lastet kode, inkludert
oppslagstabellen, øker med 672 byte. Størrelsen på DATA og BSS er lik i
lenkekartene. Det lette tidsbygget hadde 85440 byte største ledige
Chip-blokk, og den integrerte prøven hadde 52632. Vertskontrollene bestod
8741 tilfeller av pikselkontakt og låsavlesning samt 25600 kontroller av
maskerepresentasjonen, inkludert 1024 som sjekker hele kilde-RAM.

Den ordinære utgaven åpnet komplett meny fra både AmigaDOS og en
skrivebeskyttet ADF som eneste oppstartsdisk. Spillet gikk videre fra
menyen på ADF. Tolv pauserte skjermprøver i rom 12 og tolv etter død og
rombytte hadde null uforklarte pikselavvik og null blandede faser.

Kjør `python tools/verify_op2_wide_delivery.py` for leveransekontrollen.
`--parent` kontrollerer hashene fra utgaven som ga førmålingene. De
tilhørende filene ligger under `reference/analysis/op2-field-2026-10-31/parent/`.

De korte rutene avklarer denne endringen. Full tre-felts spillkadens,
null tapte lydtikker i lange forløp, original rasterfase, naturlig
gjennomspilling og fysisk A500 gjenstår. Rådataene ligger i
[OP2-målingene](../reference/analysis/op2-field-2026-10-31/diagnosis.json).
