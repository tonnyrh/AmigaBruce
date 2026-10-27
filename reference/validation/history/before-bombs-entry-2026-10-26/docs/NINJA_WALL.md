# Kages stikk ved vegger

26. oktober2026. Brukeren meldte at Ninja/Kage kunne treffe gjennom veggen
i rom6. To avvik i adapteren er rettet: stikk brukte en avstandsboks uten
spritekontakt, og angrepsventingen hoppet over vegg-/bevegelseshistorikken.

Frossen kilde: `.reference/c64/work/untrained-memory.bin`, SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Remember/T64-kandidaten er ikke sertifisert som urørt1984-utgave.
Originalene er uendret.

| Adresser | Betingelse og effekt |
| --- | --- |
| `$29C3–$2A37` | Les `$D01E`, samle potensielle par fra VIC-spritegruppene. Ingen test av vegg mellom figurene. |
| `$2A38–$2A7B` | Beskyttede offerstilstander inkluderer veggretting24. Bare angripertilstand22 går til stikkgrenen. |
| `$2A7B–$2AA4`, `$2C54` | Skade2 ved teller under8, tillatt spritepar og fremoveravstand minst4 halve X-enheter. Ingen egen23-pikslers øvre boks. |
| `$1C5B–$1D6E` | Felles svartkontakt/historikk gjelder også tilstand22; tilbakerulling kan snu figuren og avbryter angrepet. |
| `$22BD–$22F0` | Teller12 ber om lyd`$85`. Ikke-siste steg registrerer én fremoverenhet i `$4F5D,X`/`$4F60,X`, **uten X-flytting**. Teller1 avslutter nå. |
| `$2D7C` | AI-fremming krever ledig tilstand/teller. Pågående veggretting må fullføre før et nytt stikk. |
| `$2584`, `$25E2`, `$07EF–$07FA` | Faktisk spritekopi, lagposisjoner og dobbel X-bredde bestemmer opake piksler. Disse skiller seg fra bakgrunnsmaskene i `$5212`. |

`$D01E` er en samlet latch. En kjede med tre berørende figurer kan tillate
et potensielt par uten direkte paroverlapp. Rettelsen innfører derfor ingen
ny linje-/veggtest og beholder kildegruppenes samlede kontaktbetingelse.

Tilstand22 bruker nå felles veggkontroll, riktig angrepsmaske, historikk uten
X-flytting, lydtidspunkt og avslutning ved teller1. Stikk bruker kildepiksler
og samlet aktørlatch før parbehandlingen. Den gamle23×22-boksen er fjernet
for stikk; Bruces slag/spark/fall har fortsatt foreløpig kontaktgeometri.
Stikk gir ikke skade fra eller mot veggretting24.

210 spritekombinasjoner gir86 ulike kontaktmasker:7644 byte CPU-minne,
0 ekstra Chip-byte. De trekkes ut med originalens faktiske kopierings- og
posisjonsrutiner, inkludert opaque svart.

Et kontrolltilfelle viser den tidligere feilen i begge retninger: ved22
pikslers avstand mot en Bruce som vender mot Kage gav den gamle boksen
skade2. Kildepikslene overlapper ikke, og kildekamp med beregnet latch gir
ingen skade. Ved20 piksler treffer samme oppsett. Dette er injiserte
tilstander, ikke opptak av brukerens hendelse.

`test-ninja-wall.ps1` sammenligner56 ekte6502-oppdateringer i rom6 med
kompilert C: posisjon, retning, positur, kontakt, tilstand, teller, CB og hele
historikken.2450 spritekontroller sammenlignes med ny kjøring av spritekopien.
1080 kampanrop og20 trefigursituasjoner sammenlignes med `$29C3`.
VIC-latchen beregnes og injiseres; dette er ingen VIC-raster-/VICE-måling.
56 vegg- og96 utvalgte aktive/inaktive treffkontroller inngår også i session-
fixturen på verten og68000. AI-auditen beholder58 andre forskjeller.

Full aktørmaskin, reaksjons-/ventetellere, alle positurlåser, VIC-latchehistorikk
og samling av alle treff før påføring er fortsatt åpne. Vegger er ikke
automatisk et skjold etter kildekoden. Brukerens situasjon skal testes
naturlig på nytt; dette er ikke en erklæring om full kampparitet.

[Kildekontroller](../reference/analysis/ninja-wall-2026-10-26/report.json).
Gjeldende native resultater og byggidentiteter samles i
`reference/validation/ninja-wall-delivery.json`.

To A500-CLI-kjøringer har fullført6000 felt hver med0 fixture-/aritmetikk-/
rom-/render-/DMA-feil og gjenopprettet OS. De152 nye kontrollene per kjøring
inngår i session-fixturen. Begge følger vertens kontrollerte kamprute med62
treff,6 fiendenedleggelser og2 Bruce-dødsfall/tilbakestillinger.
Største sammenhengende Chip-blokk er60832 byte, over reservemålet49152.
Det er945/953 forsinkede felt og maksimal avstand3 perioder. Den strenge
feltkadensen er altså fortsatt åpen; dette er en funksjonskontroll.
Normal EXE er215940 byte, ADF901120. `C:start` er oppdatert til normalbygget.
