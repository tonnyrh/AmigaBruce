# Bruce: prosjektregler

Alle prosjektverktøy skal ha engelsk brukerrettet tekst. Dette gjelder også
ressursnavn i grensesnittet, dialoger, status, feilmeldinger, CLI-hjelp og
rapporttekst som verktøyene genererer.

## Hovedprioritet (brukerbeslutning 24. oktober 2026)

Spilloppførselen skal bygges fra C64-kildedata og disassembly av den faktiske
maskinkoden. Dette gjelder alle detaljer: rom, kollisjon, bevegelse, kamp,
fiender, timing, dører, feller, lanterner, helse, liv, poeng og sluttsekvens.

Ved usikkerhet: finn rutinen og datatabellene i C64-koden, følg relevante
grener og dokumenter adresser og betingelser. Ikke fyll kunnskapshull med
gjetning, nye spillregler, antatt standard plattformlogikk eller en simulert
oppførsel. Uavklarte detaljer skal stå åpne til originalkoden er avklart.

Tester kontrollerer en implementasjon og en kodebasert tolkning. En simulert
regel eller en bestått Amiga-test fastsetter ikke hva C64-originalen gjør.
CPU-modeller er supplerende kontroller, ikke fasit for ukjent spilloppførsel.
Enkeltsteging av originalkode i VICE kan brukes ved behov; skill dette fra
egen modell, manipulerte testtilstander og faktisk naturlig gjennomspilling.

## Kilder og evidens

- Bruk den frosne C64-binærens faktiske bytes og dokumentert disassembly.
  Kontroller ufullstendige eller tvetydige kommentarer mot maskinkoden.
- `.reference/upstream/bruce` er C64-editor/disassembly. Editorens ombygde
  spill ignorerer original romkode; bruk originaldata og originalbinæren.
- `.reference/upstream/bruce-lee` er en Atari-basert nettleserrekonstruksjon
  med egne kollisjonsbokser og egen AI. Den fastsetter ikke C64-regler.
- Noter kildehash, adresser, datatabell, betingelser, effekt og åpne spørsmål
  for hver regel som implementeres. Kildebasert, observert og uavklart er
  forskjellige evidensstatuser.
- Den tilgjengelige Remember/T64-kandidaten er ikke bekreftet som den valgte
  urørte 1984-utgaven. Ikke omtal kandidatfunn som sertifisert originalparitet.
- Behold originale snapshots, binærer og kildeutsjekkinger uendret. Lag
  analyseprodukter separat. Brukerbeslutningen «Bygg alle rom basert på
  dekodet logikk og ripper grafikk fra c64» autoriserer rippede C64-tegn i
  denne spillutgaven. Lag uttrekk separat med kildehash og adresser;
  ikke endre originalene. Nye produksjonsressurser må ha tydelig opprinnelse.
- Brukerbeslutning 25. oktober: egenlaget grafikk settes til side. Rippede
  C64-sprites og tegn er standard mens C64-oppførselen rekonstrueres.
  En eventuell enhanced-utgave kommer etter dette arbeidet.

## Arbeidsrekkefølge

1. Rekonstruer romsystemet fra koden: 8x16-celler, attributter, tegnsett,
   pikselkontakt, init-/løprutiner og dynamiske endringer. Dagens håndlagde
   og grafikkbaserte blokkrom er midlertidige og ikke C64-geometri.
2. Erstatt forenklet spillogikk med dokumenterte C64-regler, og gå gjennom
   utestående detaljer i bevegelse, kamp, fiender og progresjon på samme måte.
3. Kontroller at egen 68000-implementasjon følger de dokumenterte reglene
   og fungerer på PAL A500 OCS / Kickstart1.3 /512KiB Chip+512KiB slow.
4. Ny og forbedret grafikk, animasjon, lyd og lasteillustrasjon har lavere
   prioritet og kan ferdigstilles til slutt. Ikke start nye kunst-/lydløft
   mens kilderekonstruksjonen har høyere prioritet.

Spillet heter **Bruce**. C64-originalens navn og eksisterende repo-/filnavn
beholdes der de er referanser. Eksisterende grafikk og lyd kan brukes under
arbeidet; kollisjon og romregler skal være uavhengige av den nye kunsten.

Dokumenter begrensningene ærlig. Besøk i20 rom, pakking/utpakking og beståtte
ytelses-/minnetester betyr ikke at rommenes funksjon er korrekt rekonstruert.
