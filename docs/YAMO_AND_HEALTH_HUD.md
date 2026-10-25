# Grønn Yamo og navngitte helsefelt

Dette beskriver v3. Nyere navn-/oppstartsarbeid står i
[Bruce: navn og oppstart](BRUCE_STARTUP.md); størrelser og målinger nedenfor
tilhører den arkiverte v3-kandidaten.

Brukerens referansebilde viser Kage, Yamo og Bruce med hvert sitt navngitte
helsefelt, og en tung Yamo med grønn hud. Dette er visuell styring for
Amiga-utgaven. Kampregler og helseverdier hentes fortsatt fra C64-kandidaten.

Yamo har et nytt AI-generert ark med grønn hud, bar overkropp og rund mage,
kraftigere armer og lår og mørke bukser. Den gamle figuren med brun hud og
grønn drakt er beholdt som tidligere kildekunst. Det nye arket er laget med
innebygd image_gen; [den nøyaktige prompten og kildene](../assets/graphics/v2/yamo-green-v3-generation.json)
er lagret sammen med [den nye kildefilen](../assets/graphics/v2/yamo-green-source-v3.png).
Brukerbildet er bevart lokalt under Git-ignorert `.reference/art/`.

Konverteringen bruker samme 16-fargers OCS-palett og samme 48 × 26-flate,
anker 24,25 og bildeantall som før. Grønne kildetoner prioriteres mot den
grønne palettrampen; spredte høylys hindrer at hele huden blir gul ved
fargereduksjon. Nabosko er tatt ut av utsnittene for sparkets returfase.

Øverst står nå KAGE, YAMO og BRUCE fra venstre mot høyre. Kage er kun
visningsnavnet på den eksisterende Ninja-figuren; AI og våpenregler er
uendret. Hvert felt har åtte segmenter og viser andel gjenværende helse.
Maksverdiene i spillkjernen er fortsatt Ninja 7, Yamo 20 og Bruce 36.
Lik visningsbredde gir ikke lik helse. Romnummeret står øverst til høyre.

Grafikkminnet er uendret: 29 952 byte pakkede bilder, 74 880 byte CPU-cache
og samme 2 304-byte Chip-arbeidsbuffer. Navn og segmenter tegnes uten å
endre høyden på spillefeltet eller rommenes fysiske koordinater.

Retest: vurder grønn hud og kraftigere silhuett i løp, slag, spark og fall;
kontroller navnene over riktig figur og at skade reduserer riktig felt.
Tidligere godkjente manuelle tester beholdes som godkjent.

Fem ferske emulatorkjøringer består på PAL A500 OCS, 68000 og 512+512 RAM:
6 000 rammer kamp, to CLI-kjøringer med 900 rammer, 900 rammer romoverganger
og 7 200 rammer gjennom alle 20 rom. Ingen vanlig presentasjon mistet en
PAL-periode, og kontrollbildene hadde ingen tegnespor utenfor figurene.
Maks vanlig arbeid var 304 rasterlinjer i kamp, 213 i åpningsruten, 218 i
første romovergang og 229 på romturen. Eksplisitt Chip-bruk er fortsatt
172 228 byte; minste største ledige Chip-blokk var 265 952 byte.

Alle `core/`-filenes hash er identiske med før denne utseenderettelsen.
Spillkjernens logikk er dermed uendret. Det vanlige Amiga-programmet er
183 576 byte, ADF-en er 901 120 byte, og CLI-kommandoen `start` er oppdatert.
