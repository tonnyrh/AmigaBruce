# Kamplyd, kandidat v1

**Historisk ressurssett.** Vanligbygget bruker nå
[C64-kodens effektsekvenser og musikk via Paula](SOURCE_AUDIO.md).
AudioGen-filene under er bevart, men inngår ikke i den nye spillavspillingen.

Fire lokalt genererte AudioGen-medium-lyder: to slag (100 ms) og to spark
(150 ms). Dette er egne lydressurser, ikke opptak fra C64-originalen.

Kilde og ferdige lyttefiler ligger i `assets/audio/combat-v1/`. Generatoren
brukte ett sekund og to varianter per prompt:

* Slag: `One isolated dry fist punch impact, short tight low thud and crisp smack, martial arts arcade fighting sound effect, no speech no music no ambience`
* Spark: `One isolated powerful martial arts kick impact, fast air swish then deep tight body thump, dry short arcade fighting sound effect, no speech no music no ambience`

Modellen kjørte lokalt fra `D:\Audiogen\audiogen-medium`, uten fast seed.
De lagrede kilde-WAV-filene er derfor fasit for deterministisk konvertering.
`tools/build_combat_audio.py` finner sterkeste transient, beholder litt ansats,
filtrerer/nedsampler til 8 kHz mono, fjerner DC, normaliserer og fader endene.
Deretter kvantiseres lyden til 16 logaritmiske nivåer, to samples per byte.
Dette er tapsbasert komprimering. Firebits-lyden har bevisst begrenset kvalitet;
lytt til de konverterte filene før eventuell ny kandidat velges.

De fire lydene utgjør **2000 pakkede byte**, som dekodes én gang ved oppstart
til **4000 byte signed 8-bit PCM** og fire byte DMA-stillhet i Chip RAM.
Pakking sparer plass i programmet; korte samples og lav samplerate sparer
Chip RAM. Paula spiller ikke firebits-formatet direkte. Kilde-WAV følger
utviklingsrepoet, men bygges ikke inn i spillet.

Paula-periodene 422, 432, 443, 454 og 465 gir omtrent ±5 % tonehøyde og
tilsvarende endring i varighet. Ingen ekstra PCM-kopier er nødvendige.
Varianter veksler per lydtype. Slag har volum 40/64 og tunge treff 48/64.
Inntil fire kanaler kan brukes samtidig; en opptatt kanal avbrytes ikke.
Musikk må senere få en eksplisitt kanalfordeling.

Lyden utløses ved bekreftet helsetap hos Bruce eller fiendene. Foreløpig
velges tung lyd ved minst fem skadepoeng, ellers slaglyd. Dette inkluderer
falltreff og Ninja-treff som passende tunge/lette treff, uten nye egne samples.
Luftslag gir ingen trefflyd. Lydlaget leser kampresultatet og endrer ingen
kampregler, timing eller tilfeldig tilstand i motoren.

DMA-startens første AUDx-flagg avleses neste videofelt. Da settes neste DMA-
buffer til stillhet slik at effekten ikke løkker. Normal romlasting skjer bare
ved revisjonsbytte, der nye trefflyder undertrykkes; eldre lyder er allerede
betjent før lasting. Denne rekkefølgen må bevares dersom motorløkken endres.
En kanal stoppes etter ti videofelt. Minste effektvarighet er omtrent 95 ms,
lengre enn den normale serviceperioden på ett PAL-felt.

Paula-DMA og omlasting følger Commodores maskinvaremanual:
https://amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node00E0.html
https://www.ikod.se/wp-content/uploads/2020/08/Amiga_Hardware_Reference_Manual_3rd_Edition.pdf

Native autotest spiller alle fire varianter på felt 20, 40, 60 og 80. Den
krever variantmaske 15 og én stillhetsomlasting per startet lyd. Dette tester
DMA-banen og minnebudsjettet; det er ikke en subjektiv godkjenning av klangen.
Tidligere milepælrapporter beholder sine opprinnelige kildesignaturer og er
historiske der lydendringen gjør dem utdaterte. Bare nykjørte rapporter gjelder
denne kandidaten.

24. oktober 2026: Ny ADF-kamptest over 6000 PAL-felt bestod med 69 starter,
69 stillhetsomlastinger, alle fire varianter, null droppede lyder og null
tapte videofelt. Kamputfall samsvarte med kjernetesten. To påfølgende CLI-
oppstarter på 360 felt bestod også. Eksplisitt Chip-allokering i kampfixture
var 170948 byte, hvorav 4004 byte er lyd. Dette er emulatorverifikasjon,
ikke lyttetest eller fysisk A500-godkjenning. Kjør `python tools/verify_combat_audio.py`
for kontroll av ressursene og de nye kildesignerte rapportene.
