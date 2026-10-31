# Lydpolling etter feltarbeid, 30. oktober 2026

Dette steget legger til ett kall til eksisterende `source_audio_service()`
etter hvert fullførte `bl_c64_field()`-kall i Amigaens feltservice.
Det beregnede antallet spillfelt, input, C64-regler, lyddrivere,
lydbølger, Paula-bufferne og allokeringene beholdes.
Sperrene for aktiv lyd, pågående lydkall og allerede behandlet PAL-felt
er de samme. Det legges ikke til en løkke som spiller tapte lydtick i burst.

## Kildegrunnlag

Frossen Remember/T64-kandidat:
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Urørt 1984-utgave er fortsatt ikke bekreftet.

`$4915` kaller `$15A8`. De faktiske bytene `$15A8-$15B7` gir CLD,
nullstilling av `$44`, X fra romnummeret og kall til `$EB03`, `$EF73`,
`$F073` i den rekkefølgen. Hovedløpet setter `$48=3` ved `$1BC2`,
og feltløpet har dekrementeringen ved `$1676`. Denne endringen flytter
ingen av de operasjonene eller spillfeltkallene. Kildebytene kontrolleres
av `tools/audit_audio_service_probe.py` og lagres som
`reference/analysis/audio-service-2026-10-30/source-audio-contract.json`.

Dette er en endring av Amigaens polling rundt fullførte feltkall.
Den integrerer ikke den isolerte full-IRQ-kandidaten og lukker ikke
spørsmålene om naturlig C64-interrupt-PC, SEI/CLI, stack eller rasterfase.

## Diagnosen

To separate diagnosebygg beholder de originale servicepunktene og skriver
kun tids-/steddata utenfor C64-minnet. Begge består 710 native kontroller,
inkludert 256 spritekontroller, og 360 kildesteg. De viser henholdsvis
10 og 8 tapte lydtick, mot 6 i den umodifiserte kontrollen. Instrumentering
legger til CPU-arbeid og endrer feltfasen; de tallene er ikke en
ytelsesmåling av et levert bygg.

De registrerte foregående lydkallene tar omtrent 26–45 rasterlinjer.
De fleste forsinkelsene møtes ved inngangen til kollisjonsdriveren `$5212`.
Delmålingen viser enkelte feltkall på opptil 306 rasterlinjer, etterfulgt
av arbeid fram til `$5212`. Den tidligere løsningen sjekket lyd før
feltarbeidet og kunne fortsette inn i spillsteget før neste sjekk.

Tiden fra forrige lydkalls slutt til neste start er ikke det samme som
upollet CPU-tid: den inkluderer også frisk venting og polling uten ny tick.
Rapporten klassifiserer bare delintervaller som faktisk ligger innenfor
den registrerte hendelsen. Det hevdes ikke at ett skjermbilde eller en
simulert tidsmodell fastsetter C64-reglene.

## Før og etter uten instrumentering

Begge varianter bruker samme produksjonskjerne, samme kontrollinnganger og
samme diagnostiske hovedløp. Den ubrukte framebuffer-capture-allokeringen
er utelatt i begge målebygg; normalbyggets allokeringer er beholdt.

| Rute | Før: PAL-felt / tapte lydtick | Etter: PAL-felt / tapte lydtick |
| --- | ---: | ---: |
| Rom 1, 360 kildesteg | 1414 / 6 | 1423 / 0 |
| 20 rom, 120 kildesteg per rom | 8892 / 135 | 8972 / 9 |

20-romsruten får 93,3 % færre tapte lydtick og omtrent 0,9 % mer målt tid.
Det er en forbedring av lydservicen med en liten tidskostnad.
Rom 13, 16 og 20 har fortsatt henholdsvis 4, 1 og 4 tapte tick i denne
kontrollerte ruten. Resten har null. Dette er ikke godkjent full sanntidsparitet.
Alle kontroll-/feilporter består og minste største Chip-blokk er 69 016 byte.

Råbygg, faktisk kompilerte hovedfiler og målinger er bevart under
`reference/analysis/optimization-2026-10-27/audio-boundary-*`.
`source_clock_elapsed + source_clock_starts` kontrolleres mot antall
avspilte tick pluss registrerte tap i målebyggene.

## Leveringskontroll

Før integrasjon er hele forrige validerte levering frosset under
`reference/analysis/audio-service-2026-10-30/parent` med hasher.
`tools/audio_boundary_parent.py` kjører forrige strenge kontroll mot
nettopp disse filene. Gamle målinger framstilles ikke som nye kjøringer.
Bare den eksakte pollingendringen tillates i produksjonens C-kode;
C64-kjerne, data og maskinvareprimitiver skal være uendret.

Nytt normalbygg består full 53-fixtur-/1200-løkketest med 52 632 byte
i største ledige Chip-blokk. Ny separat 710-kontrollkjøring, inkludert
256 spritekontroller, består og har null tapte lydtick i rom 1.
Normal EXE/ADF starter; menyen består 78 komplette bilder, ti valgskifter
og begge startbufferne. Rom 12 og død/rombytte består 12 + 12 pauserte
bildevurderinger uten blandede faser, feil statiske piksler eller ulovlig
flimmer. Den normale klokkeprøvens tre intervaller består.

Produksjons-EXE er 315 984 byte, 36 byte mer enn før. Lastet kode/tabeller
øker netto 26 byte; DATA/BSS er uendret, og ingen ny lydbuffer er allokert.
De faktiske native maskinvareprimitivene er fortsatt identiske på tvers av
normal-, fulltest- og referansebygg. Bare Amigaens hovedløkke er endret i
produksjonens spillfiler. Resultatene bindes av
`tools/verify_audio_boundary_delivery.py`.

Første romkontroll startet fra en fast oppstartsventing og kom til rom 1
i stedet for rom 12; den feilen er bevart separat. Etter bekreftet komplett
meny består samme uendrede grafikkontroll. En etterfølgende transient
Windows-lås på startup-sequence ble løst ved å gjenta bare diskettoppstart.
Ingen grafikk-, klokke- eller minnekrav ble senket. Teststyringen venter nå
også på at de eide emulatorprosessene er helt avsluttet.

Gjenværende lydforsinkelser, PAL-budsjett i alle situasjoner, naturlig
IRQ/input-/VIC-fase, komplett gjennomspilling og fysisk A500 står åpne.
Sprite-hurtigbanen fra forrige forsøk tas ikke inn i dette steget.
