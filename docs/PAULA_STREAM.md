# Paula-bølger og PAL-styrt lydservice

Implementert etter Harrier-gjennomgangen 25. oktober 2026.

## Bølgeformbytte

Hver av de tre stemmene eier nå én fast, 1024-byte Chip-buffer. Adresse og
DMA-lengde settes ved oppstart og endres ikke mens stemmen spiller. Kildens
korte tonebølger gjentas til bufferens lengde; støybanken fyller én buffer.
Når bølgeform, pulsbredde eller prøvelengde endres, kopieres det nye mønsteret
inn i stemmens buffer. Frekvens og volum følger fortsatt C64-registerdataene.

Dette fjerner avhengigheten av at en gammel, lang støyblokk må avsluttes før
ny LC/LEN tas i bruk. Vi legger heller ikke inn et helt felt uten lyd for
hvert anslag. Paula kan fortsatt ha et gammelt ord forhåndslest; CPU-kopien
er ikke et atomisk oscillatorbytte, og en gammel periodeteller kan påvirke
de første prøvene. SID-klang og fase er derfor fortsatt en tilnærming.

Den uendrede bølgeformbanken bruker 2260 byte Chip RAM. De tre arbeidsbufferne
bruker ytterligere 3072, totalt **5332 byte**. Alle originalressurser og
register-/notedata er beholdt. Ingen nye genererte lyder er lagt til.

## Klokke og eierskap

Lydservice leser CIA-A sin faktiske PAL-feltteller. Den kalles under venting,
mellom blitteroperasjoner, i lange kopier og ved trygge kontakt-/romtick-
grenser. Dette er kooperativ service på én tråd, ikke en CPU-avbruddsrutine
som kan endre rommodulens delte tilstand midt i en skriveoperasjon.

Et nytt hardwarefelt gir høyst én lydtick per servicekall. Flere tapte felt
spilles ikke i en komprimert burst. Dersom et arbeidsstykke likevel tar for
lang tid, økes `source_clock_missed`; telleren skjuler ikke tempotapet.
`source_clock_elapsed`, antall starter og faktisk spilte lydfelt må balansere.
Service følger hardwarefelt uavhengig av antall tegnede bilder. Spillmotorens
aktør-/romkadens er ikke omskrevet som en del av denne rettelsen.

Oppstartsskriket har separat engangssample og avsluttes før de tre stemmene
overtar kanalene. Musikk stanser ved spillstart. Rommets fulle tegne-/lastefase
demper avspillingen og starter klokkemålingen på nytt ved retur. Ved avslutning
stanses servicen før OS får maskinvaren tilbake.

C64-kandidatens tre effektkøer, prioritet, gate-signaler, noter og ADSR-data
er beholdt. Kilden har SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Den er ikke sertifisert som valgt, urørt 1984-utgave.

## Kontrollgrunnlag

`test-source-dma.ps1` sammenligner hvert bufferbyte i 4554 kanalbilder over
1518 felter fra tittelen og alle 15 effektene med den eksisterende bølgeform-
banken. Den kontrollerer også gjenbruk uten unødvendig kopi og avviser ugyldige
størrelser/adresser. Sju mindre kontroller av samme bufferoperasjon er lagt
inn før maskinvareovertakelsen i68000-testbygget; nye native resultater gjenstår.

De eksisterende 7540 kilde-CPU-kontrollene av effekter/køer og tittelforløpet
beholdes. `source_audio_hash` og `source_music_hash` gjelder nå **logiske
parameterverdier**; de beskriver ikke hardwareadresse/-lengde. Spillhashen
kan ikke sammenlignes med den gamle testen som spilte én lydtick per ytre
spilløkke. Antall lydfelt følger nå faktisk medgåtte hardwarefelt.

Nye native resultater og opptak skal bindes til dagens kilde og program.
De tidligere tre stemmeopptakene og Harrier-gjennomgangen er bevart med
arkiverte kilde-/byggidentiteter. De er ikke ommerket som nye målinger.
En bestått bufferkontroll beviser ikke at alle overganger høres riktige ut.
Den strenge grafikk-/spillkadensen og endelig lyttegodkjenning er separate.

## Status for dette bygget

Normalprogram og ADF er bygget. Kildekontrollen og DMA-bufferkontrollen består
på verten. Senere to6000-felts kjøringer med liv-/veggrettelsen fullførte alle
native regresjonskontroller og beholdt85408 byte sammenhengende Chip RAM.
Lydklokken mistet79/77 felt, med største gap3/2, under dette oppsettet.
Det er ingen godkjenning av streng50Hz-kadens. Nye native musikk-/effektopptak
er fortsatt **uavklart**. Tidligere opptak har sine egne byggidentiteter.

En tidligere, avgrenset prototype nådde6000 felt, men feilet minnekravet og
rapporterte tapte lydfelt. Det var før de siste endringene i testbuffer og
lastepause, og brukes ikke som native godkjenning av nåværende kode.

[Gjeldende status og identiteter](../reference/validation/session-walls-delivery.json).
Den eldre Paula-leveransen er historisk etter liv-/veggrettelsene.
