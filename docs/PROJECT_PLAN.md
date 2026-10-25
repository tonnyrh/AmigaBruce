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
Alle 20 rom bruker nå dekodede init-/løprutiner, kildebasert pikselkontakt og
rippede tegn fra C64-kandidaten. Neste motorarbeid er komplett kildebasert
aktørtilstand, posevalg, kamp og AI. Maskinvarekontroll av rommotoren og
kildebundet dokumentasjon er en egen leveranseport.
Alle20 rom er besøkt i native inspeksjon med kontrollerte rom-pikseldata uten
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

## Nåværende leveranse — første M4-kandidat

Spillet heter nå **Bruce**. [Oppstarten](BRUCE_STARTUP.md) får et kort
karateskrik og en lasteflate; brukerens illustrasjon avventer bildevedlegget.

Nyeste arbeid 24. oktober: [flere animasjonsfaser og dynamiske åpninger](ANIMATION_AND_OPENINGS_2026-10-24.md).
Brukeren tillater friere Amiga-animasjon. V2 har vekslende klatresider,
flere kamp-/løpefaser og Ninjas bambusstav. C64-kildene styrer de første
dynamiske åpningene fra rom 2 via rom 6/7 og tilbake til rom 3.
Yamos hud og kroppsform er deretter korrigert, og helsefeltene har fått
navnene KAGE, YAMO og BRUCE; se [den visuelle rettelsen](YAMO_AND_HEALTH_HUD.md).
Den [første grafikk- og spillbarhetskandidaten](NEXT_CANDIDATE_2026-10-24.md) beholdes som historikk.
Dette viderefører M4 og starter M5 med nye figurer/bakgrunn; ingen av de to
milepælene er godkjent som fullført. M4s krav om naturlig gjennomspilling og
M5s krav om ferdig presentasjon gjelder fortsatt.

Oppdatert 24. oktober: Se [20-romsutgaven](M4_ROOM_EXPLORER.md). Alle 20 rom
har nå inspeksjon med egen blokkgeometri og to bakgrunnsslots, mens naturlig
progresjon, øvrige dynamiske dører og feller fortsatt gjenstår. Denne utvidelsen
erstatter ikke M4s ferdigkrav. [Aktive tester](ACTIVE_TESTS.md) erstatter den
gamle komplette manuelle listen. [Grafikkflyten](AMIGA_ART_PIPELINE.md)
beskriver uttrekking, lagret prompt og formatkontroll for senere AI-kunst.

Den første leveransen nedenfor er beholdt som historikk:

To rom er spillbare, lanterner kan samles og innsamlingen beholdes ved retur.
Koordinater og koblingstabeller for alle20 rom er ekstrahert fra C64-kandidaten.
Se [M4-kandidaten](M4_ROOMS.md) for rute, tester, avvik og ressursmålinger.

M4 er ikke fullført. Resterende rom, nøyaktig geometri, bro-/fellelogikk,
spillermoduser og full gjennomspilling gjenstår. M3s kampforløp og M2s tidligere
kollisjonsavvik er fortsatt åpne; denne leveransen godkjenner dem ikke.
