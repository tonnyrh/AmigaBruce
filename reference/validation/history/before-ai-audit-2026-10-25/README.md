# Bruce for Amiga 500

Amiga-spillet heter **Bruce**. Navnet Bruce Lee brukes fortsatt om C64-originalen
og i eksisterende repo-/referansebaner. Oppstart: [tittel og karateskrik](docs/BRUCE_STARTUP.md).
Musikk og effekter følger nå [C64-koden med kompakt Paula-avspilling](docs/SOURCE_AUDIO.md).
Etter skriket spiller tittellåten fram til ild trykkes. Bølgeformbanken bruker2260 byte Chip RAM;
de tidligere genererte kamplydene er erstattet av kildens15 effektsekvenser.

Gjeldende prioritet: **C64-kildedata og disassembly før grafikk og lyd**.
Se [prosjektreglene](AGENTS.md) og [gjennomgangen av rombyggingen](docs/ROOM_RECONSTRUCTION.md).
Alle20 rom bruker nå dekodede C64-romdata, rippede tegn og oversatte
init-/løprutiner. De håndlagde blokkrommene og den felles fjellbakgrunnen er
byttet ut. Figurer og deler av aktørmotoren er fortsatt fra Amiga-prototypen.
Full C64-paritet og naturlig gjennomspilling er ikke godkjent.
De tidligere testene er gjennomgått mot kandidatens maskinkode i
[T01–T18: rettelser og åpne funn](docs/TEST_AUDIT_2026-10-25.md).
Nettinput/-grep og rekkefølgen kamp/aktøroppdatering er rettet;
61 kontrollerte kilde-CPU-fixtures kontrollerer tolkningene.
Ny [bevegelsesgjennomgang](docs/C64_MOVEMENT.md) porter svart veggkontakt og
retter spark-/hopp-/fallfaser og masker.500 historikk-,480 spark- og54 hopp-/fall-
kontroller følger faktisk6502-kode. Full landing, aktørmaskin og kamp gjenstår.
Se også [lanterner og romgrensene i rom 1](docs/C64_CONTACTS.md):
kildepositur for stille ståing uten nett, boksing og liggestilling, enkeltinnsamling
med125 poeng/lyd og høyre utgang ved kilde-X≥300. Gang-/klatre-/reaksjonssekvenser
og full aktørmotor gjenstår; hopp-/spark-/fallmasker er korrigert separat.
Den tidligere native inspeksjonen dekket alle20 rom uten avvik i kontrollerte
rompiksler. Den strenge A500-ytelsesporten er fortsatt åpen, med tidsavvik i
blant annet rom 14 og sluttrommet; romlasting tar også flere sekunder.
Native målinger må gjelde kildene som ble bygget; eldre rom-/aktørmålinger
er historiske etter aktørrettelsene. Måling av vanligbyggets Chip-reserve gjenstår.
To nye6000-felts kampforløp matcher verten; den strenge tids-/Chip-porten
er fortsatt åpen. Gjeldende avgrensning: `reference/validation/movement-delivery.json`.

Uttrekk, kildeadresser, tester og avgrensninger er dokumentert i
[romrekonstruksjonen](docs/ROOM_RECONSTRUCTION.md).
F1/F2 velger rom for inspeksjon. Dører, åpninger og romendringer følger
kandidatens maskinkode. Referansekandidaten er fortsatt ikke bekreftet som
valgt, urørt1984-utgave.

Bygg med `.\amiga-build.ps1` og spill med `.\amiga-run.ps1`.
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
separate, brukerbestilte uttrekket av romgrafikk ligger i `assets/c64/rooms-v1/`,
med adresser og kildehash.
Referansefiler kan verifiseres med `python tools/c64_reference.py verify`.
Tilgjengelig T64-kandidat verifiseres med
`python tools/c64_reference.py verify --candidate`.
En valgt original registreres med
`python tools/c64_reference.py register "C:/path/to/BruceLee_rakki_s0.g64"`.
Kommandoen beregner identitet, men bekrefter ikke utgave eller spilloppførsel.
