# VIC-cache i en gjennomgang, 29. oktober 2026

OP2/OP5: kald pikselcache leste tidligere alle63 source-bytes til raw-cache,
og leste dem deretter igjen for21 rader med opake kollisjonsmasker. Den nye
rutinen leser hver byte en gang og publiserer samme raw-cache og radmasker.
Ingen ny versjonsteller, tidsmessig gjenbruk, kilde-RAM-skriving eller
endret kollisjonsregel.64-byte stride og pad-byte63 beholdes.

Dette er Amiga-implementasjonen av den eksisterende feltbaserte VIC-seamen,
ikke en ny spillregel fra6502. Kildens $D01E-lesing og akkumulering beholdes;
kildereferanser og begrensninger er beskrevet i VIC_REPEAT_OPTIMIZATION.md.
Frozen Remember/T64-kandidat har SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Urørt1984-identitet og full rasterparitet er ikke sertifisert.

| Kontroll | Før | Ny | Gjentatt ny |
| --- | ---: | ---: | ---: |
| Uprofilert, PAL-felt for360 source-steg |1426|1422|1422|
| Tapte lydservicetikker |17|9|9|
| Minste observerte ledige Chip-blokk |52632|61592|52632|
| Separat native kontakt/sprite-kontroll |710|710|710|

Profilert VIC-selvkostnad25,188->24,803 linjer/kall, topp293->279.
Antall VIC-kall er1567->1571 og hele profilkjøringen1687->1691 felt;
profilen alene gir derfor ingen samlet fartsakseptanse. De to uprofilerte
målingene er grunnlaget for den avgrensede gevinsten på fire felt.
Ingen påstand om ny generell RAM-gevinst: allocatorens største blokker
varierer mellom oppstarter; den laveste marginen brukes.
Sanntidsporten er fortsatt åpen, siden lydtikker fortsatt tapes.

Vertskontroll:25600 før/etter-tilfeller mot frosset C, alle256 byteverdier
i hver av tre byteposisjoner, fire kombinasjoner av multicolor/bredde og
alleåtte sprites. Hele raw-/pad-/metadataområdet og alle21 high/low-rader
sammenlignes.1024 tette/omsluttende pekertilfeller kontrollerer også at
hele64KiB source-RAM er uendret. De8741 eksisterende VIC-kontrollene består.
Dette er representasjons-/maskinprøver, ikke naturlig gjennomspilling.

Forkastede varianter er bevart separat. En utbrettet tre-bytevariant bestod
vertstesten, men profilbygget fikk allokeringsfeil (365812 mot365644 byte
EXE). En kompakt variant med løpende short-peker feilet omslag ved$FFFF i
MSVC/O2-kontrollen; ingen slik variant tas inn. Den valgte varianten bruker
samme eksplisitte16-bits adresseuttrykk som den frosne radfunksjonen.
Kompakt profil-EXE er365628 byte; dette er16 byte mindre enn før.

Råkjøringer har navn `vic-cache-*` under
`reference/analysis/optimization-2026-10-27/`. Før-/etterkilder og avviste
forsøk ligger i `reference/analysis/vic-cache-2026-10-29/`.
`verify_vic_cache_optimization.py` binder målingene og kontrollene til
faktiske kildefiler og binærer. Full motor, normal CLI/ADF og renderer
kontrolleres separat før leveranseregisteret kan godkjennes.

Full native motor:53 fixturer og1200 l�kker best�r, Chip52632 byte,
expansion2208 byte f�r eksplisitte grafikkallokeringer. Ingen scene-
eller uforklart pikselrest;42 HUD-bytes er forventet dynamisk status.
Normal EXE er343016 byte,12 byte mindre enn forrige leveranse.
