# OP4. Ett spillfelt fra Kages falltreff til Paula

Varianten som eide feltservicen under begge lange falltreff, reduserte
antall tomme Paula-felt fra 15 til 3 og 4 i to kjøringer. De 240
spillstegene tok samtidig 14–15 PAL-felt mer enn i kontrollbygget med
samme utgangsmåler. Det lengste steget økte fra 4069 til 5009
rasterlinjer. OP2 beholdes som vanlig spillbygg.

## Hva som ble sammenlignet

I rom 1 kan et falltreff på Kage gå rundt ved `$2C51` 26 ganger. Den
vanlige Amiga-rutinen mister lydoppdateringer mens den beregner poengene.
Prøven lar et forfalt spill-IRQ avbryte den løkken på et kjent punkt.
Den oversatte 68000-rutinen kjører SID-driverne for alle tre stemmene.
Etter retur får Paula én publisering av resultatet. Kildens påfølgende
fargeavbrudd velger selv neste vektor og rasterlinje.

Det ekstra avbruddspunktet er avgrenset til X = 2, satt fallflagg
(`$BC+X` bit 4), helse på minst 133 og klare I- og D-flagg. Det er
betingelsene brukt i disse prøvene. Spillets egen skaderegning kjøres
for hvert treff.

Kilden er den frosne Remember/T64-kandidaten med SHA-256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Identiteten som urørt 1984-utgave og rasterfasen ved naturlig spilling
er fortsatt åpne.

## Kildekontroll ved retur

To lagrede kampinnganger fra steg 168 og 207 ble kjørt fra `$29C3` til
retur til `$1C26`. I hvert opptak ble tre spillavbrudd og seks
fargeavbrudd lagt inn på bestemte passeringer av `$2C51`. Første
spillavbrudd går via `$1103 → $48C1`. Kallene til SID-driverne ved
`$EB03`, `$EF73` og `$F073` kommer før joystickavlesningen ved
`$169D`. I disse romdataene går rasterkjeden fra `$48C1` til `$491E`,
videre til `$4982` to ganger og tilbake til `$48C1`.

Py65 kjørte instruksjonene på C64-siden. Det kompilerte 68000-programmet
kjørte hele kampkallet i WinUAE fra samme inngang. Ved alle 18 returer
stemte alle 65 536 minnebyte, inkludert stacken. Det samme gjaldt
A, X, Y, SP og flaggene C/Z/N/V/D/I. Retur-PC, valgte CIA-pinner, 25 SID-registre,
stigende gatekanter og sluttminnet ved `$1C26` ble kontrollert. Den ene
kontrollen byttet aktiv spiller og valgte menneskestyrt Yamo. Feltklokken
passerte 24-bitsoverløp. En tidlig avlesning, maskert IRQ og gjentatt
avlesning på samme tidspunkt ga ingen ekstra avbrudd eller publiseringer.
Begge kampforløpene bestod.

Ved det første spillfeltet i begge opptakene fikk SID-stemme 1 en ny
gatekant. De to neste spillfeltene ga ingen ny gatekant. Ingen av de
seks fargeavbruddene i hvert opptak publiserte lyd.

Denne kontrollen bruker valgte klokkeslett og en kontrollert lydmottaker.
Spritekollisjonen samples med prosjektets separate VIC-modell etter
spillavbruddet. De tidsmålte spillrutene nedenfor bruker den faktiske
Amiga-feltklokken, lydkonverteringen, DMA og Paula-registerskrivingene.

## Måling på A500-konfigurasjonen

Rom 1, begge fiender, 240 oppvarmingssteg og 240 målte steg per rute.
WinUAE kjørte syklusnøyaktig PAL 68000, OCS, Kickstart 1.3 og 512 + 512
KiB. Rutene med bevegelse hadde 96 steg i lufta. «Manglende felt» i
utgangsmålingen betyr et fysisk felt mellom to publiseringer uten en ny
Paula-oppdatering. Referansebyggets eldre teller følger servicekallene.
En egen kontroll måler derfor også klokkeslettet ved registerskriving i
den eksisterende lydbanen. Utgangsmåleren leser feltklokken rett før
første kanals periode og volum skrives. Når IRQ-prøven eier lyden,
leser den klokken igjen etter tredje kanal. En skrivesekvens som går
over feltgrensen, registreres særskilt.

Den fulle prøven la beslag på feltservicen gjennom alle 240 steg. Den
avgrensede prøven eide to spillavbrudd og seks fargeavbrudd ved første
lange falltreff, før den ga servicen tilbake. I begge gjentakelser av
den avgrensede prøven var retur-PC `$2C51` ved alle åtte avbrudd.
De to spillavbruddene ga seks kanalskrivinger. Mellom første og siste
skriving i disse to publiseringene var det ingen krysning av feltgrensen.
På hele bevegelsesruten fikk likevel to felt dobbel publisering og
14 felt manglet publisering. Den fulle prøven hadde to tomme og to doble
felt i første bevegelseskjøring og fire av hver i andre. Tidsstemplene
ved Paula-registrene skiller dette fra en logisk oppdatering per
planlagt kildefelt.

Den første private utgaven ble stående på spillsteg 241. IRQ-er fortsatte
å kjøre mens `present_frame` ventet på linje 300–308. I prøvebygget fikk
Copper-listen et reservert ventevindu fra linje 235. Etter dette
fullførte spillet ruten. Linje 235 er en diagnoseinnstilling for denne
Amiga-konfigurasjonen.

| Bygg og rute | PAL-felt for 240 steg, to kjøringer | Tomme felt, to kjøringer |
| --- | ---: | ---: |
| Vanlig OP0-referanse, bevegelse | 985 / 991 | 12 / 12 ved servicekall |
| Vanlig OP0-referanse, stillstand | 968 / 964 | 0 / 0 ved servicekall |
| IRQ eier hele ruten, bevegelse | 1426 / 1425 | 2 / 4 ved Paula |
| IRQ eier hele ruten, stillstand | 1289 / 1301 | 0 / 1 ved Paula |
| To spillavbrudd ved første treff, bevegelse | 998 / 998 | 14 / 14 ved Paula |
| Samme bygg, stillstand | 972 / 972 | 0 / 0 ved Paula |
| Kontroll med utgangsmåler, bevegelse | 998 / 998 | 15 / 15 ved Paula |
| IRQ under begge lange treff, bevegelse | 1013 / 1012 | 3 / 4 ved Paula |

I den siste varianten fikk begge kampene fullføre den pågående
rasterkjeden før feltservicen gikk tilbake til den vanlige motoren.
Spillklokken fortsatte fra siste behandlede kildefelt. Lydklokken
fortsatte fra feltet som faktisk fikk siste Paula-publisering. Begge
kjøringer behandlet 20 spillavbrudd, 60 fargeavbrudd og 60 sett
med kanalskrivinger under de to treffene. I de intervallene var det
ingen doble eller manglende publiseringer. Over hele ruten målte vi
henholdsvis én og null doble publiseringer.

Alle 16 tidskjøringer fullførte med begge fiender aktive og uten
registrerte kilde-, lyd- eller DMA-feil. Dette er kontrollerte
WinUAE-ruter i rom 1. Naturlig spilling, øvrige rom og fysisk A500
gjenstår. [Målinger, byggidentiteter og kontrollsummer](../reference/analysis/op4-field-owner-2026-10-31/result.json).

## Gjentakelse

Bruk filene i [analysemappen](../reference/analysis/op4-field-owner-2026-10-31/).
Kjør `build_owner.py reference` først, så `build_owner.py candidate`
og `proof.py`. Kontrollen henter de to private kampopptakene fra
`.reference/c64/work/op4-moving-audio-2026-10-31`. De forventede
minnebildene genereres under `.tmp`. Kjør `run.ps1 proof` med en ny
etikett. Bygg de tre variantene med `build_owner.py handoff`,
`build_owner.py combat` og `build_owner.py meter`. Spillrutene bruker
`run.ps1 <bygg> <ny-etikett> 1 3 2` for
bevegelse og `1 3 0` for stillstand. Bruk `verify.py` for å kontrollere
de arkiverte rapportene og byggidentitetene.
