# Rom 20: direkte kildefargeskriving

30. oktober 2026. V3 er bygd og kontrollert i lokal normal EXE/ADF.
Dette er et avgrenset OP1/OP5-løft; sanntidsakseptansen er fortsatt åpen.

Frosset Remember/T64-kandidat SHA256:
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Utgaven er ikke sertifisert som urørt 1984-utgave.

`$4272-$4276` tester timerordet `$49/$4A`. Null går til sluttforløpet;
den grenen endres ikke. `$4298-$429F` velger fargen med `$1159`, maskerer
laveste tre bit og setter høye bit til `$F8`; også dette beholdes.
`$42A1-$42BA` skriver A til åtte rader, 29 kolonner:
`$DAAC/$DAD4/$DAFC/$DB24/$DB4C/$DB74/$DB9C/$DBC4 + X`, synkende X fra 28.

Ny privat native løkke beholder alle 232 lagringer i original rekkefølge.
Den bruker en egen kopi av fargeobservatøren; den generelle skribentens
C-kode beholdes uendret. DEX-resultatet er X=$FF,N=1,Z=0; A/Y/C/V/D/SP
beholdes. Guard X<=$1C lar ukjente innganger bruke original oversettelse.
Ingen ny servicegrense innføres inne i lagringene. Den etterfølgende
`$42BC->$17E2`-strengen beholdes.

7424 prøver kjører de faktiske bytene `$42A1-$42BA`: alle 256 A-verdier
og 29 X-innganger, med varierte øvrige registre, status og stack. Hele
64 KiB RAM og alle virtuelle registre sammenlignes. 192 ekstra prøver
sammenligner cacheinnhold/-referanser, relative cachepekere, skitne celler,
malekø, animasjons-/kontaktmetadata og faktisk bitmap mot frosset tidligere C.

V1 og V2 er arkivert og ikke levert: begge ga rundt 13 % lengre R15-intervall.
Disassembly viste at GCC hadde endret den vanlige skribentens animasjonsvakt
til et ekstra kall også uten animasjonscache. V3 har en separat fargeløkke,
en eksplisitt innfelt nullsjekk og en separat aktiv metadatakropp.

Den opprinnelige 810-byte skribenten og den aktive 200-byte metadatakroppen
beholdes bytevis, inkludert oppløste relokeringer, i normal-, 53-fixtur-,
710-kontroll- og 20-romsbildet. Den nye fargeløkken er identisk mellom disse
fire 68000-bildene. Dette erstatter ikke kontrollene mot C64-bytene.

V3s kontrollerte 20-romspar bruker 2815577 mot 2851927 HSYNC-linjer
(1,275 % mindre samlet arbeid), med 163 mot 255 tapte lydtikker.
R20 er 13,236 % raskere, og R15 er 1,801 % raskere i dette paret.
Enkelte rom bruker litt lengre tid; størst er R10 med 1,117 %.
Ruten bærer historikk mellom rom og har ekte PAL-faseforskjeller;
dette er ikke isolerte instruksjonskostnader eller naturlig gjennomspilling.
Begge ruter har minst 69016 byte største Chip-blokk i alle 20 rom.
Bare en ubrukt diagnoseopptaksallokering er utelatt i denne tidsprøven;
produksjonsallokeringene er urørt.

To korte R01-prøver med samme binær gir begge 1425 totalfelt og 11 tapte
lydtikker, mot tidligere 1430/9. Telleren inkluderer tittel og spill.
R01s lokale lydservice er altså ikke forbedret. Profilbygget med ekstra
tellertabeller feilet allokering; et tidligere RoomTour-bilde hadde bare
44440 byte Chip-reserve. Disse avviste diagnosebildene er ikke minnegodkjenning.

Den ordinære vertsammenligningen, 53 native fixturer og 1200 repriseløkker
består. Motorprøven har 52632 byte største ledige Chip-blokk.
Ny normal EXE/ADF har 76 kontrollerte menybilder, 12 R12-bilder og 12 etter
kontrollert død og rombytte, med null animasjons-/statiske pikselavvik.
CLI/ADF-oppstart, rom 1–6, synlighetslivsløp, negativ fellefase og
PAL-klokke består. Dette er kontrollerte prøver.

Normal EXE er 343276 byte (+172); lastet .text øker 92 byte.
RoData/Data/BSS er uendret. GCCs egne funksjonsrammer er 88 byte for actor_code,
42 for source_written og 54 for den nye fargeløkken. Dette er ikke
maksimal kallkjedestack. IRQ/input, null tapte lydtikker, ordinær feltkadens,
hele kallkjeden, naturlig spilling og fysisk A500 er fortsatt åpne porter.

[Originalbytes og måleprodukter](../reference/analysis/final-colors-2026-10-30/).
