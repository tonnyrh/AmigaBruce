# Bruce for Amiga 500

Amiga-spillet heter **Bruce**. Navnet Bruce Lee brukes fortsatt om C64-originalen
og i eksisterende repo-/referansebaner. Oppstart: [tittel og karateskrik](docs/BRUCE_STARTUP.md).
Musikk og effekter følger nå [C64-koden med kompakt Paula-avspilling](docs/SOURCE_AUDIO.md).
Etter skriket spiller tittellåten fram til ild trykkes. Bølgeformbanken bruker2260 byte Chip RAM;
de tidligere genererte kamplydene er erstattet av kildens15 effektsekvenser.
Lydavspillingen bruker nå [faste Paula-buffere og PAL-styrt service](docs/PAULA_STREAM.md).

Gjeldende prioritet: **C64-kildedata og disassembly før grafikk og lyd**.

27. oktober: [hele kildekjeden er koblet inn](docs/MILESTONE_COMPLETION.md):
alle aktørtilstander, pikselkontakt, samtidige treff, AI, liv, turbytte og
24-bits poeng.3 034 kontroller sammenligner hele RAM/registre mot faktiske
C64-bytes. A500-feltkadens, rasterfase og naturlig gjennomspilling er fortsatt
åpne akseptanseporter. Se [aktive tester](docs/ACTIVE_TESTS.md).

Samlet maskinkontroll: `./test-source-world.ps1` (PAL A500, 512+512).
Vertskontroller og verifikasjon av levert bygg: `./test-parity.ps1`.
De gamle separate adaptertestene beholdes som historikk; de godkjenner ikke
den nye motoren. Milepæler lukkes etter faktisk akseptanse, ikke bare bygg.

Kage/Yamos innganger, romspesifikke tellere og retur følger nå
[C64-kildens spawn-rutiner](docs/ENEMY_SPAWNS.md). Full aktørparitet og
naturlig gjennomspilling er fortsatt åpne.

[Cheat-brettvalg](docs/CHEAT_PROGRESS.md) fullfører nå lanterner i tidligere
romnumre, med separat spillerlagring og valgt roms lanterner beholdt.

[Rom 10 og elektrisk felle](docs/ROOM10_ELECTRIC.md): prioritert kopiering av
feller og rettferdig fordeling av tegnearbeidet på store rullende nett.

[Rom8-eksplosjoner mot skadde fiender](docs/ROOM8_BLASTS.md): NPC-objektkontakt
bruker nå kildeposituren for treffreaksjon og nedslag, med egne regresjonskontroller.

[Fiendeinnganger og bomber](docs/BOMBS_ENTRY.md): kildevalget mellom
inngangspunkter, NPC-utløsning og Bruces stille dødsreaksjon er nå koblet inn.

[Kages stikk ved vegger](docs/NINJA_WALL.md) bruker nå kildebasert spritekontakt
og felles vegghistorikk; den gamle avstandsboksen er fjernet for dette angrepet.

[Rombytte er optimalisert](docs/ROOM_LOAD_PERFORMANCE.md): omtrent 21% mindre
forberedelsesarbeid i to A500-kjøringer med alle 20 rom og uendrede bildepiksler.
Fargetabellene bruker 23 KiB mindre CPU-RAM. Denne målingen gjelder det
tidligere adapterbygget. [Gjeldende milepælstatus](docs/MILESTONE_COMPLETION.md).

[Bevegelig nett i rom5](docs/MOVING_NET.md): kontakt med tegn `$62` bruker
nå C64-tilstand23 og nettets egen transport, i stedet for en feilaktig
treffreaksjon som kastet Bruce bakover.

Ny [døds-/livs- og veggrettelse med hovedmeny](docs/SESSION_WALLS.md):
faredødens stillstand/lyd, synlige reservefall, separate NPC-kontaktmasker
og korrigert hopp/fall i rom6. Menyen har F3 for spillere og F5 for Yamo;
Shift+D åpner uendelige liv, udødelighet og startrom. F10 åpner menyen igjen.

Ny rettelse: [NPC-rekyl og uventet romstart i rom2](docs/NPC_RECOIL.md).
Se [prosjektreglene](AGENTS.md) og [gjennomgangen av rombyggingen](docs/ROOM_RECONSTRUCTION.md).
Alle20 rom bruker nå dekodede C64-romdata, rippede tegn og oversatte
init-/løprutiner. De håndlagde blokkrommene og den felles fjellbakgrunnen er
byttet ut. [Figurene bruker nå også rippede C64-sprites](docs/C64_SPRITES.md).
Egenlaget grafikk er satt til side til en senere enhanced-utgave.
Vanlig spill bruker nå den komplette kildekjeden. Gamle adapterfunksjoner
beholdes for historiske kontroller og brukes ikke som motor i vanlig spill.
Klatringen er nå [rettet mot C64-koden](docs/C64_CLIMB.md): aktuell nettmaske,
grep i rom5, sidefart4/6 piksler per oppdatering og separate vertikale ventesteg.
Full C64-paritet og naturlig gjennomspilling er ikke godkjent.
De tidligere testene er gjennomgått mot kandidatens maskinkode i
[T01–T18: rettelser og åpne funn](docs/TEST_AUDIT_2026-10-25.md).
Nettinput/-grep og rekkefølgen kamp/aktøroppdatering er rettet;
61 kontrollerte kilde-CPU-fixtures kontrollerer tolkningene.
[Kage og Yamos AI er nå gjennomgått mot originalbytene](docs/C64_AI.md):
4578 kontrollerte kildekjøringer, med588 samsvarende ordinære angreps-/bevegelsesvalg
i adapteren. Venting, inntreden, stikkavslutning, retrettstøtte og NPC-utganger
har fortsatt dokumenterte avvik. AI-gjennomgangen er kodeverifikasjon;
disse motoravvikene er ikke rettet av spriteskiftet.
Ny [bevegelsesgjennomgang](docs/C64_MOVEMENT.md) porter svart veggkontakt og
retter spark-/hopp-/fallfaser og masker.500 historikk-,480 spark- og54 hopp-/fall-
kontroller følger faktisk6502-kode. Full landing, aktørmaskin og kamp gjenstår.
Se også [lanterner og romgrensene i rom 1](docs/C64_CONTACTS.md):
kildepositur for stille ståing uten nett, boksing og liggestilling, enkeltinnsamling
med125 poeng/lyd og høyre utgang ved kilde-X≥300. Gang-/reaksjonssekvenser
og full aktørmotor gjenstår; hopp-/spark-/fallmasker er korrigert separat.
Den tidligere native inspeksjonen dekket alle20 rom uten avvik i kontrollerte
rompiksler. Den strenge A500-ytelsesporten er fortsatt åpen, med tidsavvik i
blant annet rom 14 og sluttrommet; romlasting tar også flere sekunder.
Native målinger må gjelde kildene som ble bygget; eldre rom-/aktørmålinger
er historiske etter aktørrettelsene. Måling av vanligbyggets Chip-reserve gjenstår.
De tidligere6000-felts målingene gjelder den gamle adapterbanen. Gjeldende
kildeport er kontrollert med53 native RAM-/registertilfeller og1 200
repriseløkker på A500 OCS/KS1.3 med512+512KiB. Full sanntidsfart er fortsatt
åpen. [Siste optimaliseringsrapport](docs/CONTACT_REGISTERS_OPTIMIZATION.md)
og `reference/validation/source-world-delivery.json` binder dagens kode,
normalbygg og kontroller. Naturlig gjennomspilling, lydtiming og fysisk
A500 er egne akseptanser.

Uttrekk, kildeadresser, tester og avgrensninger er dokumentert i
[romrekonstruksjonen](docs/ROOM_RECONSTRUCTION.md).
F1/F2 velger rom for inspeksjon når Shift+D-testmodus er aktivert.
Dører, åpninger og romendringer følger
kandidatens maskinkode. Referansekandidaten er fortsatt ikke bekreftet som
valgt, urørt1984-utgave.

Bygg med `.\amiga-build.ps1` og spill med `.\amiga-run.ps1`.
For vanlig WinUAE kan `amiga/out/bruce-a500.uae` lastes med gjeldende ADF.
Profilen samler alle tre lydstemmer på begge utganger; se
[lydoppsett og native musikkopptak](docs/AUDIO_PLAYBACK.md).
Se [M3: Ninja, Yamo, skade og respawn](docs/M3_COMBAT.md).
Se [M4: lanterner og første romovergang](docs/M4_ROOMS.md).
Se [20-romsutgaven og begrensningene](docs/M4_ROOM_EXPLORER.md),
[aktive tester](docs/ACTIVE_TESTS.md) og [grafikkflyten](docs/AMIGA_ART_PIPELINE.md).
Se [prototypestatus, kontroller og testing](docs/PROTOTYPE.md).
Se [korte kamplyder og minnebudsjett](docs/COMBAT_AUDIO.md).
Se også [arbeidsleveranse, målte resultater og neste spilltest](docs/NIGHT_HANDOFF.md).

![Alle20 rom med rippet C64-grafikk](assets/c64/rooms-v1/all-rooms.png)

- [Prosjektplan](docs/PROJECT_PLAN.md)
- [M0-status og neste steg](docs/M0_STATUS.md)
- [C64-referanse og opptaksprosedyre](docs/reference/C64_REFERENCE.md)
- [Kilderegister](docs/reference/SOURCES.md)
- [Paritetsmetode](docs/parity/README.md)
- [Paritetsregister](docs/parity/register.csv)
- [Romregister](docs/parity/rooms.csv)
- [Referansemanifest](reference/manifest.json)

Originale diskbilder, snapshots, ROM-er og lokale referanseutsjekkinger ligger
under Git-ignorert `.reference/`. De lokale originalfilene inngår ikke i kildekoden eller utgivelser. Det
separate, brukerbestilte uttrekket av romgrafikk og sprites ligger i
`assets/c64/rooms-v1/` og `assets/c64/sprites-v1/`,
med adresser og kildehash.
Referansefiler kan verifiseres med `python tools/c64_reference.py verify`.
Tilgjengelig T64-kandidat verifiseres med
`python tools/c64_reference.py verify --candidate`.
En valgt original registreres med
`python tools/c64_reference.py register "C:/path/to/BruceLee_rakki_s0.g64"`.
Kommandoen beregner identitet, men bekrefter ikke utgave eller spilloppførsel.

Nyeste ytelsesrunde: [native kontakt, objekter og poeng](docs/NATIVE_ENGINE_OPTIMIZATION.md).
Git-merke før løftet: `milestone/c64-source-2026-10-27` (`26fb6d1`).

Neste ytelsesrunde: [kontakt-/VIC-kjerner og faste kildespillsteg](docs/CONTACT_KERNEL_OPTIMIZATION.md).

Videre optimalisering: [pakkede kontaktmasker, 28. oktober](docs/PACKED_MASK_OPTIMIZATION.md).

Siste kontaktløft: [pekeroppsett, klassifisering og kildebasert fellerettelse](docs/CONTACT_PREPARATION_OPTIMIZATION.md).

Siste VIC-løft: [gjenbruk av uendret pikselkontakt på 68000](docs/VIC_REPEAT_OPTIMIZATION.md).
