# Resten av kontaktløpet, 28. oktober 2026

Utgangspunkt er `b003d04`, etter [maskeforskyvningen](PACKED_MASK_OPTIMIZATION.md).
Den frosne Remember/T64-kandidaten har SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Den er fortsatt ikke sertifisert som urørt 1984-utgave.

## Kildekontrakt

- `$530A–$537D`, `$55C5–$55E5`: pekeroppsett, tabeller, attributter og tre
  glyphoperander er skrevet som direkte 68000-kode. Alle RAM-/JSR-skrivinger
  beholdes i samme rekkefølge, også når glyph-/attributtpekere peker inn i
  scratch, klassebaner, operander eller stack. 16-bits pekeromslag og
  8-bits Y/SP-omslag beholdes. Tredje kolonne er blank bare ved Y>=40.
  Slutt-A/X/Y/C/N/Z/V/SP publiseres gjennom en åttebytes ABI; D bevares.
- `$5431–$55AA`: hele klassifiseringen nuller de samme sammendragsbytene,
  dekrementerer de faktiske attributtbytene og skriver kildens JSR-frames
  før klassebyttene. Den eksisterende kildegenererte OR-kjernen brukes
  fortsatt for de eksakte operandmengdene, inkludert deduplisert `$4EFE`.
- `$55E6/$5658/$56CA`: de sju byttene i hver 23-byte klassebane utføres
  direkte med byteinstruksjoner. Retur-A er den siste gamle venstrebyten,
  X/N/Z kommer fra aktørindeksen; øvrige virtuelle flagg/Y bevares.
- `$53E0–$5428`: kroppsklassifiseringen beholder de tre attributtsnapshottene,
  body-/fullmaskene og kildens betingede XOR1-bytter. Også ikke-boolske
  attributtverdier beholdes. Y/V/D og virtuell SP er uendret; siste CMP eller
  bytte avgjør A/X/C/N/Z. `$53F1/$5405/$5415/$5425` og nestede klasseframes
  skriver de opprinnelige returbytene.
- `$55AB–$55C4`: nøyaktig 72 bytes nulles. Første byte retter opp oddetalls-
  adressen `$4EED`; 17 langtord etterfølges av ett ord og én byte. Ingen
  ekstra byte berøres. A=0, X=255, N=1/Z=0 og kilde-RTS bevares.
- `$5212–$52AC`: oppsettsberegningene er binære og beholder alle RAM-skrivinger.
  Virtuelle mellomflagg som ikke har en leser før neste pekerberegning,
  fjernes. Første radtjeneste ser fortsatt de eksakte registrene fra kildens
  siste ADC. Alle eksisterende servicepunkter og ikke-lokale returer beholdes.

Aktør0–2 bruker hurtigbanene. Uvanlige indekser og desimalinnganger følger
fortsatt den instruksjonstro koden. De nye kontrollene prøver også indeks
3/127/255 og zero-page-omslag. Dette er injiserte kontrolltilstander, ikke
nye spillregler. Ingen nye vegg-/treffbokser eller AI-regler innføres.

`amiga/contact_prepare.s` bruker bare 68000-instruksjoner. Minnelesninger er
bytevise der oddetallsadresser kan forekomme; lange nullinger er justert.
Den interne kryss-seksjonsdelingen bruker absolutte JSR-relokasjoner som
Hunk-konverteren støtter. Ingen ekstra Chip-buffere/allokeringer opprettes.

## Kontroller og diagnostikkminne

4 239 vertskontroller sammenligner hele RAM og registre med 2 320 683 faktiske
C64-instruksjoner. 489 tilfeller kontrollerer service-registre. Utvidelsen
omfatter 30 uvanlige aktørinnganger som skal beholde originalbanen.

Den ordinære native motorprøven beholder alle 53 komplette kildefixturer
og de tidligere 454 kjernekontrollene. Et separat native tidsmålebygg
kjører i tillegg 384 peker-, 96 klasse-, 96 kropps- og 16 nullingskontroller:
**1 046 totalt**. Hele stack-/zero-pageområdet, klasse-/attributtbaner,
SMC-operander og 13 virtuelle kontrollregistre sammenlignes med C-referansen.
Både klasseverdier255 og stack0/1/254/255 er med.

Referansekodene utelates fra produksjonsbygget og fra det store 53-fixtur-
bygget. Profileringsbygget bruker de eksisterende 454 kontrollene og de
samme native spillkjernene. Dette unngår at både nye referanser, alle53
fixturer og profilhistogrammer må ligge i RAM samtidig. Alle kontrollene
kreves separat; minne-/feltportene er uendret.

## Målinger

Samme faktiske PAL-planlegger og nøyaktig 360 spillsteg som før, stasjonær
udødelig test-Bruce i rom1 med begge fiender. Målingene inkluderer vanlig
venting og egen diagnosekostnad; profil og tidsmåling kjøres separat.

| Trinn | PAL-felt | Tapte lydserviceticks |
| --- | ---: | ---: |
| Forrige leveranse | 1 530 | 21 |
| Peker-/klassekjerner | 1 472 | 22 |
| Hele kontaktløpet før opptegningsrettelsen | 1 468 | 22 |
| Kontaktløp og bevart ny maling | 1 466 | 26 |

Sluttmålingen har **4,18 % kortere målt tid** enn forrige leveranse. Den
viser 359 tegnede og 99 kort holdte bilder, største holdrekke ett felt.
Dette er en avgrenset scene, ingen generell FPS-/sanntidsgodkjenning.
Lydtaptallet er dårligere i denne enkeltmålingen; lydporten er fortsatt åpen.

Sluttprofilen viser kontaktoppsettet 162,872 → 122,889 rasterlinjer
eksklusivt per spillsteg, omtrent 24,5 % mindre. Det komplette native
forløpet er bundet separat i verifikasjonsrapporten. Normal EXE er
341376 byte, 1040 byte mindre enn forrige leveranse.

## Nye observasjoner fra testingen

[USS-analysen av fellen i rom6](TRAP_R06_2026-10-28.md) fant en faktisk
opptegningsfeil. Kørettelsen bevarer endringer i allerede malte ruter og
holder køen på høyst 880 unike ruter. Den endrer ikke C64-ventingen.

Kage kan gå ut gjennom øvre høyre åpning i rom1. Den faktiske `$30D4`-gaten
slipper gjennom når rå-X>=162 og høyre bevegelsesrecord er satt; objektpasset
må også finne utgangscellen. `$2F90→$3001` fjerner NPC-en og setter kildens
returteller. Åtte nye direkte kildekontroller bekrefter denne grensen.
Brukerens enkeltobservasjon har ingen tilhørende inputhistorikk og fastsetter
ikke om alle betingelser var oppfylt akkurat da. AI-en er ikke endret.

## Sluttkontroll

- 4239 vertskontroller mot faktiske C64-instruksjoner, inkludert489
  service-/registertilfeller, består. Hele RAM sammenlignes ved grensene.
- 1046 direkte native kjernekontroller består i det separate tidsbygget.
- 53 fulle native RAM-/registerfixturer og454 kjernekontroller består
  sammen med1200 kontrollerte sløyfer og tilbakeføring til AmigaOS.
- Største ledige Chip-blokk etter lasting er52632 byte;49152-porten beholdes.
- Normal CLI-/ADF-oppstart, tre klokkepar, Yamos synlighet og rom6-fellens
  bakgrunn/begge bildebuffere er kontrollert med den leverte EXE-en.

Samlekjøringen godkjenner fortsatt ikke sanntid; normal klokkeprøve
viser også langsommere spillsteg under belastning. Avgrensede kontroller
er ikke en naturlig gjennomspilling eller sertifisert originalparitet.
