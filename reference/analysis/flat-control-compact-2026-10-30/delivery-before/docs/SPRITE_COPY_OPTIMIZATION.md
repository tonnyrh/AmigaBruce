# Native spritekopiering,29. oktober2026

Spritekopieringen er skrevet for68000. I den faste rom1-profilen faller
selvkostnaden fra14,468 til11,120 rasterlinjer per kall,23,14 prosent.
Begge profilene inneholder1219 kall. Maksimum faller fra18 til13 linjer.
Dette er en komponentgevinst. Totalmålingen er1428 mot1429 PAL-felt for360
spillsteg, og tapte lydtick er21 mot27. Samlet spillflyt og lydservice er
fortsatt ikke godkjent som ferdig optimalisert.

## Dekodet kildekontrakt

Frossen Remember/T64-kandidat, SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Urørt1984-utgave og naturlig rasterfase er fortsatt egne porter.
Uttrekket i `reference/analysis/sprite-copy-2026-10-29/source-copy-disassembly.txt`
kommer fra disse bytene, ikke Atari-rekonstruksjonen.

- `$2719-$274E` velger glyphbase fra$59BD/$5A8F og høyde fra$5B61.
  Høyden lagres ved$E0+aktør. Begge kallere,$25A4-$25AB og$25CD-$25D4,
  bruker TYA/ASL/ADC$E0 til Y=3*høyde. ASL gir carry0 når høyden<32.
- `$26A0-$2702` velger smal/bred via inngangs-Z. Glyphbasene ligger i de
  selvmodifiserte operandene$26AB/$26E4/$26EE; destinasjonen kommer fra$0E/$0F.
  Data leses og skrives baklengs med nullbytes mellom kolonnene.
- `$277F` starter på63 og dekrementeres etter hver skriving. Mellomverdiene
  beholdes før senere glyphlesninger, også når glyphbasen aliaser telleren.
  Den tidligere C-hjelperen publiserte bare sluttverdien. Dette er korrigert.
- Etter siste glyphlesning er resten en nullstilling. Den nye kjernen bruker
  justerte langtord for denne enden. Ingen flere glyphlesninger eller
  servicepunkter kan observere mellomverdier her. Slutt-RAM, A/X/Y/C/N/Z,
  uendrede V/D og virtuell RTS-stack beholdes.

Hurtigbanen krever binær inngang, høyde<32, destinasjon$8000-$FF00,
trygge glyphbaser og den dekodede Y-verdien for bred kopiering. Destinasjonen
kan dermed ikke overskrive pointerbytes, kodeoperander eller$277F. Andre
adresser og potensielle BRK-grenser bruker de eksisterende oversatte
kildeinstruksjonene. Overlappende glyph/destinasjon behandles bytevis i
original rekkefølge. Med høyde<32 er en allerede negativ teller ved
nullstillingsenden minst225; én ekstra dekrementering forblir derfor negativ,
som i kildegrenen. Ingen spillregel, inputfrekvens eller ressurs er endret.

## Kontroller

1536 vertstilfeller kjører373464 faktiske C64-instruksjoner og sammenligner
hele64KiB, registre, retur og312 BRK-grenser. Tilfellene dekker begge bredder,
variable høyder/Y/SP, statusflagg, overlapp, telleraliaser, lave destinasjoner
og glyphlesninger over$FFFF. De er injiserte kontrolltilfeller.

256 separate68000-kontroller sammenligner den nye primitive rutinen med den
kildeforankrede C-referansen. Det samlede kontrollbygget har710 kontroller
og ingen feil. Det ordinære tidsbygget beholder1046 kontaktkontroller og1536
VIC-kontroller. Profil og fullspillfixturer beholder454 grunnkontroller;
store ekstra referanser pakkes separat for å beholde minnekravet.

Maskinkoden i den nye primitive rutinen skal være identisk i normalbygget,
kontrollbygget, tidsbygget, profilen og fullbygget. Dette bindes av
`tools/audit_sprite_native_kernel.py`. En ny byggkontroll avviser ELF-bilder
som ville startet feil funksjon i første AmigaDOS CODE-hunk. Et faktisk
forkastet `cold`-bygg brukes som negativ kontroll.

Den større kontaktkjernen ble også forkastet:1440 mot1428 felt og16,008
mot15,343 linjer i radprofilen. Kode og avvisninger er bevart under
`reference/analysis/contact-run-2026-10-29/`; den brukes ikke i motoren.

## Videre arbeid

Mer ledig CPU-tid kan gå til venting på vertikalblank. Profilens `wait` er
Amigaens `wait_frame()`, og denne ventingen øker samtidig som
kopieringskostnaden synker. Neste undersøkelse er den faktiske
C64-ventelogikken sammen med Amigaens tegning, planlegging og servicepunkter.
Kildens hastighet og antall spillsteg skal ikke endres for å skjule problemet.
Full PAL-kadens gjennom alle rom, lydservice, naturlig gjennomspilling og
fysisk A500 er fortsatt åpne godkjenningspunkter.

## Verifisert spillbygg

Normal CLI og faktisk ADF starter med samme nye EXE. Meny og rom1-6 er
kontrollert gjennom privat WinUAE IPC; fiendenes synlighetslivsløp og
negative fellefaser i rom6 består. Fullbygget består53 hele-RAM-/register-
fixturer og1200 replay-løkker. Største ledige Chip-blokk er52632 byte,
og896 byte er ledig i utvidelsesminnet etter lasting av dette testbygget.
Testreferansenes plassering og49152-byte-porten er beholdt.

Fulltesten har fortsatt maks fem felt mellom framdriftspunkter og81
tapte lydtick i den kontrollerte kjøringen. Disse portene er fortsatt
åpne. Den nye rutinen skal derfor vurderes som lavere CPU-kostnad med
bevart kildeutfall, ikke som ferdig løst sanntidsytelse.
