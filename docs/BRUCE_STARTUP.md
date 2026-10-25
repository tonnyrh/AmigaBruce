# Bruce: navn og oppstart

Oppdatert25. oktober: Etter skriket spiller [kildens tittellåt](SOURCE_AUDIO.md)
mens **FIRE TO START** vises. Ild går videre til spillet og stopper låten.
Escape går til CLI også på tittelskjermen.

Amiga-spillet heter **Bruce** fra 24. oktober 2026. HUD-tittelen og ADF-
volumnavnet er endret. C64-originalens navn og eksisterende repo-/filbaner
beholdes som referanser; `bruce_amiga.exe` og CLI-kommandoen `start` fungerer
som før. Spillreglene er uendret.

## Lastebilde

Brukeren ønsker å bruke sin illustrasjon under lasting. Det kom ikke noe
tilgjengelig bildevedlegg med forespørselen. Illustrasjonen er derfor
**ikke implementert ennå**. Oppstarten viser foreløpig en enkel BRUCE-tittel
og LOADING mens rom og figurdata klargjøres. Dette er en midlertidig tekstflate,
ikke en AI-generert erstatning for brukerens illustrasjon.

Når bildet foreligger, skal kilden bevares og konverteres til et validert
320 × 256 OCS-bilde. Eksisterende skjermbuffer skal gjenbrukes. En eventuell
egen lastepalett må byttes tilbake til spillets palett ved overgangen.

## Karateskrik

[Lyttefilen](../assets/audio/intro-v1/kiai-paula.wav) er en ny lokal AudioGen-
kandidat, ikke et opptak av en bestemt utøver. Prompten ber om én kraftig,
langtrukken «Haaaaaiiiii-yahhhhh» uten musikk eller kamplyder. Eksakt uttale
og naturlig klang er ikke bekreftet ved lytting. Brukeren må vurdere kandidaten.

[Genereringsloggen](../assets/audio/intro-v1/generation.json) inneholder prompt,
modell, varighet og hash for begge kildene. Første kandidat er valgt; begge
originale WAV-filer er bevart uten overskriving. Bare valgt komprimert lyd
bygges inn i programmet.

- 2,402 sekunder ved PAL-perioden 322, omtrent 11 kHz mono.
- 26 460 signed 8-bit PCM-samples, komprimert til 13 230 byte IMA ADPCM.
- Firebits-formatet dekodes på 68000 før Paula-DMA starter. Endene fader kort.
- PCM og fire stillhetsbyte ligger midlertidig i den andre skjermbufferen.
  Ingen ekstra Chip-allokering er nødvendig; dette reduserer ikke lyden til
  13 KB mens den spilles. Hele den dekodede lyden må være tilgjengelig for DMA.
- Stillhet armeres ved første DMA-flagg, før CPU-klargjøringen fortsetter.
  Etter avspilling stoppes DMA og får tid til å stanse før skjermbufferen
  fylles med romgrafikk. Kamplydene og de fire spillkanalene er deretter ledige.

Oppstartstiden omfatter også klargjøring av figurer og rom. `intro_fields` i
emulatorrapportene er **hele lastestadiet**, ikke skrikets samplevarighet.
Første kontroll målte 228 PAL-felt, omtrent 4,56 sekunder, mens lyddataene
varer 2,402 sekunder. En første testgrense blandet disse størrelsene; de to
opprinnelige rapportene er bevart under `reference/validation/history/`.

DMA-omlasting og ventetid ved stopp bygger på Commodores
[Amiga Hardware Reference Manual, kapittel 5](https://www.ikod.se/wp-content/uploads/2020/08/Amiga_Hardware_Reference_Manual_3rd_Edition.pdf).

## Kontroll

`python tools/verify_intro_audio.py --assets-only` verifiserer pakkede byte,
dekoding, lyttefil og minnegrense uten emulator. Native testene må kontrollere
samme PCM-hash på 68000, armering av stillhet, avsluttet lyd, avslått DMA,
gjenopprettet skjermbuffer og tilbakeføring til AmigaDOS. Samlet test kjøres
med `python tools/verify_intro_audio.py` når de ferske emulatorkjøringene foreligger.

Lyttefilen er også sammenlignet byte for byte med den uavhengige IMA-
dekoderen `audioop.adpcm2lin` i Python 3.10; kontrollen bestod. Det bekrefter
format og dekoding, ikke at den genererte stemmen høres naturlig ut.

Manuelt: lytt etter naturlig stemme, uønsket repetisjon og knepp. Test Escape
under oppstart og i spillet, og kjør `start` igjen fra CLI. Lasteillustrasjonen
og lyttingen står åpne; tidligere godkjente bevegelses-/kamptester forblir godkjent.

## Resultat 24. oktober

Fem ferske kjøringer består på PAL A500 OCS / 68000 / Kickstart 1.3 med
512 KiB Chip + 512 KiB slow: to CLI-oppstarter med 900 felt, ADF-kamp på
6 000 felt, ADF-romoverganger på 900 felt og ADF-tur på 7 200 felt gjennom
alle 20 rom. Alle har samme PCM-hash 508731667 og bekrefter avsluttet lyd,
stoppet DMA og gjenopprettet skjermbuffer. De tidligere kamplydene består også.

Vanlig spillrytme har ingen tapte PAL-perioder; skjermkontrollene har ingen
rester utenfor figurene. Romlastinger og kontrollbilder måles fortsatt separat.
Eksplisitt Chip-allokering er uendret, 172 228 byte. Alle ti kildefilene i
spillkjernen har samme hash som v3. Dette er emulatorverifikasjon; lytting
og den manglende illustrasjonen er fortsatt åpne.

Den vanlige spillfilen er 198 304 byte, ADF-en 901 120 byte. Ny utgave er
startet og `start` peker til samme kjørbare fil. Full M4/M5 og naturlig
gjennomspilling blir ikke godkjent av denne oppstartsleveransen.
