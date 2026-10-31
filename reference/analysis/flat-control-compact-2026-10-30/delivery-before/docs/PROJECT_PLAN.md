# Prosjektplan — Bruce for Amiga 500

Dato: 2026-10-18. Arbeidsgrunnlag fra planleggingsdialogen.

## Gjeldende prioritet — brukerbeslutning 24. oktober

C64-kildedata og disassembly av original maskinkode styrer alle detaljer.
Usikkerhet avklares i koden og tabellene; vi erstatter ikke ukjente regler med
simulering eller gjetning. Tester kontrollerer implementasjonen.
Ny grafikk, animasjon, lyd og lasteillustrasjon prioriteres lavere og kan
ferdigstilles til slutt. Tidligere kunst-/lydleveranser endrer ikke denne rekkefølgen.

25. oktober: egenlaget grafikk settes helt til side. C64-tegn og rippede
sprites er standard. Først rekonstrueres C64-oppførselen; en eventuell
enhanced-utgave kommer etterpå. Se [spriteuttrekket](C64_SPRITES.md).

Fast arbeidsregel: [AGENTS.md](../AGENTS.md). Nåværende kildegjennomgang og
konkrete romavvik: [romrekonstruksjon](ROOM_RECONSTRUCTION.md).
Alle20 rom, hele aktørmaskinen, posevalg, kamp, AI, liv, poeng og
progresjonskjeden bruker nå statisk oversatt kode fra C64-kandidaten.
Den samlede [milepælgjennomgangen](MILESTONE_COMPLETION.md) beskriver
kontroller, I/O-grenser og gjenstående akseptanse. Maskintiming og naturlig
gjennomspilling er egne porter.
Alle 20 rom er besøkt i native inspeksjon med kontrollerte rom-pikseldata uten
avvik. Den strenge feltkadensen er fortsatt åpen; både tunge romrutiner og
en lengre kampkjøring har vist tidsavvik. Dette skal rettes før ytelsesporten
eller full originaltiming godkjennes.

## Mål og avgrensning

Egen Amiga-implementasjon med 1984 C64-originalen som fasit for bevegelse,

kollisjon, kamp, fiender, rom, feller, poeng, liv, spillermoduser og progresjon.

Grunnutgaven bruker C64-grafikk og kildebasert lyd. Grafikk- og lydforbedringer
vurderes etter at C64-oppførselen er korrekt. Ingen ny balansering eller nye spillregler inngår.

Samme inngangstilstand og input skal gi samme observerbare spillutfall.

Hovedmål: PAL Amiga 500, 68000, OCS, Kickstart 1.3, 512 KiB Chip RAM og

512 KiB slow RAM. NTSC-forskjeller i C64-originalen dokumenteres separat.

Spillrytme må måles; 50 Hz skjermoppdatering innebærer ikke 50 spillsteg/s.

## Referansehierarki

1. Valgt og hash-låst 1984 C64-diskbilde kjørt med dokumentert emulatorprofil.

2. Disassembly og ekstraherte data som er knyttet til samme kjørbare utgave.

3. Sekundære utviklingsrepoer, manualer, kart og gjennomganger.

4. Atari-/nettleserutgaver som inspirasjon, aldri C64-fasit.

Hver regel får evidensstatus og målemetode. Ukjente verdier skal stå åpne.

Originaldisk beholdes uendret; analyse utføres på arbeidskopi.

## Erfaringer fra Harrier Attack Reloaded

Gjennomgå og tilpass byggeskript, m68k-verktøykjede, VS Code/WinUAE-oppsett,

oppstart og maskinvaretilbakeføring, input, VBlank/DMA, planar-konvertering,

Paula-samples, ADF-pakking og automatisert måling. Kontroller lisens og

opprinnelse før kode eller ressurser kopieres.

Lokalt gjennomgått: `README.md`, `amiga/Makefile`,

`amiga/HEADLESS_TESTING.md`, `amiga/PERFORMANCE_TARGETS.md` og

`amiga/assets/ASSET_WORKFLOW.md` i søsterprosjektet.

Det finnes bygg-/pakke-/paritetsskript og grafikk-/lydverktøy å vurdere.

Bruk målemetoden; Harriers spillspesifikke motor skal ikke bli Bruce Lee-motoren.

Historiske ytelsespåstander erstatter ikke målinger av det nye spillet.

## Teknisk utgangspunkt — må bekreftes i prototypen

- Portabel C-spillkjerne, eksplisitte heltall, deterministisk tilstand og input.

- Separate moduler for regler, romdata, Amiga-rendering og lyd.

- Originalens logiske koordinater og kollisjoner beholdes uavhengig av ny kunst.

- Foreløpig 320 x 256 skjerm. Sammenlign 16 og 32 farger før endelig valg.

- Mål om 50 skjermoppdateringer/s med målt C64-spillrytme separat.

- Prøv hardware-sprites og blitter-BOBs i en representativ kampscene.

- Tegn statisk rombakgrunn ved rombytte og oppdater bevegelige objekter effektivt.

- Paula-lyd med eksplisitt prioritet mellom musikk og samtidige effekter.

- DMA-kilder i Chip RAM. CPU-kode og øvrige data i utvidelsesminne der mulig.

- Oppstartbar ADF og AmigaDOS-kjørbar fil som distribusjonsmål.

## Foreløpig Chip RAM-budsjett

| Ressurs | Ramme |

| --- | ---: |

| To 320 x 256-buffere, fem bitplan | 100 KiB |

| Figurer, masker, arbeidsområder | 80 KiB |

| Aktiv romgrafikk og dekor | 80 KiB |

| Samples og øvrige DMA-lyddata | 80 KiB |

| Copper-lister og annen DMA | 16 KiB |

| Sum planlagte ressurser | 356 KiB |

Dette er et arbeidsbudsjett, ikke dokumentert forbruk. Resterende minne skal

dekke systembehov, topper ved lasting/dekomprimering og allokeringsmargin.

Slow RAM, stack, kode og permanente romdata budsjetteres separat i M1.

Mål faktisk allokert minne og største ledige blokk gjennom hele levetiden.

## Grafikk og lyd

Lag ett prøverom med Bruce, Ninja, Yamo, lanterner, klatreflater og en felle.

Bevar rommenes lesbarhet, silhuetter og plasseringer. Definer fotpunkter og

animasjonsankre; dekor eller ekstra animasjonsbilder endrer ikke kollisjon.

Kartlegg lydhendelser og timing før Amiga-arrangement og effekter produseres.

Prøv kanalprioritet under samtidig musikk, kamp og farehendelser.

## Milepæler og akseptanse

| ID | Leveranse | Ferdigkrav |

| --- | --- | --- |

| M0 | Referansemanifest, kilde-/rom-/paritetsregister, første opptak | Original er hash-låst og prøvestartet; første bevegelsesmålinger er reproduserbare |

| M1 | Bygging, input, skjerm, lydtest og ADF | Starter på 68000/OCS/512+512, minne målt, maskinvare gjenopprettes ved avslutning |

| M2 | Ett rom med gåing, hopp, fall og klatring | Representative inputforløp samsvarer med C64-evidens |

| M3 | Ninja, Yamo, treff, skade og respawn | Kampforløp og fienderegler verifisert |

| M4 | Alle rom, koblinger, feller og progresjon | Hele spillet og originalens spillermoduser kan gjennomføres |

| M5 | Ferdig grafikk, animasjon og lyd | Spillregler og hendelsestiming bevares; nye animasjoner er lesbare og består OCS-/ressurskontroll |

| M6 | Dokumentasjon, ADF og installasjonspakke | Sluttkontroll, fysisk maskintest og publiseringsgrunnlag fullført |

Fra M1 skal hver milepæl avsluttes med en kjørbar Amiga-versjon.

Endelig kunstproduksjon følger etter stabil bevegelse og kamp.

Ingen kalenderestimater låses før M0 har avklart datagrunnlaget.

## Nåværende leveranse — samlet kildeport, 27. oktober 2026

Aktiv ferdiggjennomgang: [kildekjeden og resterende ferdigkrav](MILESTONE_COMPLETION.md).
[Spawn-leveransen](ENEMY_SPAWNS.md) er fulgt av hele kildekjeden for
aktører, kontakt, kamp, AI, liv, turbytte, poeng og progresjon.
Den naturlige gjennomspillingsporten er fortsatt åpen.

Alle 20 rom bruker kandidatens dekodede C64-data og oversatte init-/løprutiner,
med rippede tegn og sprites. Blokkgeometrien og V2-kunsten er satt til side.
Meny, reservefall, to spillere, separat framdrift og Shift+D for testvalg er
implementert. Dette er en kildebasert kandidat med åpne maskintiming- og
gjennomspillingsporter.

| Område | Verifisert nå | Utestående ferdigkrav |
| --- | --- | --- |
| M0 / referanse | Frosset kandidat og kildeidentiteter | Bekrefte valgt urørt 1984-utgave; kandidaten gir ikke sertifisert originalparitet |
| M1 / A500 | Oppstart, CLI, ADF, 512+512, gjentatt kjøring og OS-tilbakeføring | Stabil feltkadens og ressursmargin i hele spillet |
| M2 / aktør | Hele aktørmaskinen, støtte/landing, historikk, nett, kildepositur og pikselkontakt | Naturlig timing og kant-/vegg-/nettforløp |
| M3 / kamp og AI | Hele kamp-/AI-/objektkjeden, innsamling før skade, samtidighet og reaksjon | VIC-/IRQ-fase og naturlig kampkontroll |
| M4 / rom og progresjon |20 kilderom, liv, poeng/bonus, turbytte og progresjons-/sluttgrener i felles RAM | Naturlig hel gjennomspilling, forbindelser/feller og ny runde |
| M5 / presentasjon | Rippede C64-figurer/tegn og kildebaserte musikk-/effektforløp | Naturlig positur-/hendelsestiming og lydgodkjenning; enhanced-grafikk/lyd utsatt |
| M6 / leveranse | Byggeskript og lokal EXE/ADF | Sluttkontroll, fysisk A500-test og ferdig distribusjonspakke |

[Kages stikk og vegghistorikk](NINJA_WALL.md) er rettet mot kildekoden26. oktober.
[Fiendenes inngangsvalg og bombekontakt](BOMBS_ENTRY.md) er også koblet inn,
med kildebasert skrik/stillstand ved bombedød. Den nye kjeden følger hele
aktørmaskinen; naturlig gjennomspilling står fortsatt åpen.
[Tidligere rombyttekontroll](ROOM_LOAD_PERFORMANCE.md) gjelder adapterbygget.
Neste prioritet er A500-feltkadens og naturlig progresjon. Renderingen skal bevare
kandidatens romminne, mutasjoner og kontaktregler. Romvalg og beståtte
bilde-/CPU-fixtures beviser ikke naturlig tilgjengelighet.

Den aktive listen er [ACTIVE_TESTS.md](ACTIVE_TESTS.md). Bekreftede tester
T01, T05, T12, T13, T15 og T16 beholdes som bestått; T04 er mekanisk akseptert
i de testede situasjonene. R05-nett, R06-vegg/hopp, død/liv, NPC-rekyl og
meny/to spillere venter på de beskrevne manuelle nytestene.

Tidligere milepæltekst er [arkivert](history/PROJECT_PLAN_M4_CANDIDATE_2026-10-24.md).
Den er historikk for grafikk, romgeometri og antall spillbare rom.

Optimaliseringsløftet etter `milestone/c64-source-2026-10-27` dokumenteres i
[NATIVE_ENGINE_OPTIMIZATION.md](NATIVE_ENGINE_OPTIMIZATION.md). Sanntidsporten står fortsatt åpen.
