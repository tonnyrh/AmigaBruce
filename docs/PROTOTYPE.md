# Kjørbar prototype — første M4-kandidat 2026-10-21

Nyeste bygg har [kildebasert rommotor og rippet C64-grafikk](ROOM_RECONSTRUCTION.md).
25. oktober: [rippede C64-sprites](C64_SPRITES.md) erstatter egenlagde figurer;
visuell koordinatinterpolering er slått av i standardvisningen.
Amiga-tittelen er nå **Bruce**; se [ny oppstart og karateskrik](BRUCE_STARTUP.md).
Se også [v2-animasjonene og de nye romåpningene](ANIMATION_AND_OPENINGS_2026-10-24.md).
F1/F2 velger rom for inspeksjon, Escape går til CLI, og `start` starter igjen.
Bruk [aktive tester](ACTIVE_TESTS.md). Beskrivelsene under er tidligere
arbeidsstatus og betyr ikke at full C64-paritet er godkjent.



**Spillbar kampkandidat; C64-paritet er ikke godkjent.**



Ett rom, gåing, hopp, klatring, fall, plattformlanding, 50 Hz visuell

interpolering, dobbeltbufret OCS-skjerm og tilbakeføring til AmigaOS er implementert.

Grafikken er egen skissegrafikk. Ninja og Yamo forfølger og angriper Bruce;
skade, nederlag og automatisk respawn er implementert. Se [M3-leveransen](M3_COMBAT.md).
Lanterner og overgang mellom de to første rommene er lagt til; se [M4](M4_ROOMS.md).
Resterende rom, feller, livsystem og ferdig lyd/grafikk gjenstår. Ingen original
programkode eller kunst er bygget inn i Amiga-programmet.



## Bygg og spill



```powershell

.\test-core.ps1

.\amiga-build.ps1

.\amiga-run.ps1

# Alternativ: oppstart fra diskbildet

.\amiga-run.ps1 -Disk

```



BartmanAbyss Amiga-debug-verktøykjeden må være installert lokalt. Host-testene

bruker MSVC Build Tools. Ingen delte filer i extensionen eller Harrier endres.

Runneren bruker egen bootmappe og egen UAE-config under `.tmp/`.



Output: `amiga/out/bruce_amiga.exe` og `amiga/out/bruce_amiga.adf`.

Runnerens mål er PAL 68000, OCS, 512 KiB Chip RAM og 512 KiB slow RAM.

Kickstart 1.3 finnes lokalt i Harrier-oppsettet; bruk `-Kickstart <sti>` på

andre maskiner. Ingen ROM-er kopieres eller versjoneres.



WinUAE bruker joystickport 2 med `kbd1`, normalt numerisk tastatur 4/6 for

venstre/høyre og 8/2 for opp/ned. Opp hopper eller griper en klatreflate.

Ned legger figuren ned på fast underlag; på nettet klatrer han ned. Slipp ned

for å reise deg. Opp+høyre/venstre velger løpshopp ved sats.

Ild gir slag; sideveis+ild gir flyvende spark. Opp+sideveis+ild fra ro gir vanlig løpshopp. Spark velges fra

gå-/løpstilstanden når angrepsvinduet åpner. Den røde figuren er en testmotstander med foreløpige treffregler.

Escape avslutter til AmigaOS. Museklikk avslutter ikke spillet. Skriv `start`
i AmigaDOS for å starte på nytt ved filsystemoppstart.

Dette er CLI-/diskoppstart; Workbench-start og .info-ikon er ikke implementert.

Klatretakten følger kandidatmålingene; klatrevisningen fordeles over hele

tolvfeltsintervallet. Holdt opp gir gjentatte hopp også etter nettoppen.

Se [rettelsen og målegrunnlaget](CLIMB_FIX.md).

Se også [øvre avsats og liggende stilling](LEDGE_AND_PRONE.md).



## Automatisert A500-test



```powershell

.\test-amiga.ps1

.\test-amiga.ps1 -Disk -SkipBuild

.\test-amiga.ps1 -TestFrames 1800

.\test-parity.ps1

```



Testen kjører programmet to ganger i samme OS-økt, 360 skjermperioder per

start. Ruten går under midtre nett, hopper og griper nettet, klatrer opp og

slipper sideveis for å falle. Slag prøves også i starten. Den lange varianten starter en egen testtilstand

ved periode 1080 og går gjennom slag, spark, nederlag og gjenoppståing

for testmotstanderen. Tilstandstellere kontrollerer at klatring,

fall og hopp faktisk skjer. En kort Paula-kanal-0-testtone aktiveres i starten; dette er en

DMA-test, ikke dokumentasjon av ferdig lyd eller verifisert hørbart resultat.

Rapporter lagres som `amiga/out/autotest-1.txt` og `autotest-2.txt` etter

systemtilbakeføring. Framebuffer fra periode 120 lagres som `autotest-frame.bpl`.



```powershell

python tools/preview_planar.py amiga/out/autotest-frame.bpl docs/images/prototype.png

```



Vanlig rendering og framebufferfangst må vurderes separat: kopiering av

40 KiB framebuffer gir en diagnostisk pause. Rapporten viser både totalt

maksimum, maksimum uten denne kjente fangstperioden og selve fangstgapet.

En release inneholder verken denne fangsten, testtone eller teststyring.

Rapportene kontrollerer også publisering i blankperioden, største ledige

Chip RAM-blokk og samme minnetilgang/sluttposisjon ved gjentatt start.

Soak-varianten fortsetter med blandede input etter den første ruten.



### Rettelse av skjermbytte



Brukerens emulatorbilde avdekket gjentatt tittel og ødelagte bitplan nederst.

Renderingen skjedde etter venting på blankperioden, og en eksplisitt Copper-restart

kunne derfor laste bitplanadressene på nytt midt i synlig bilde. Nå ferdigstilles

bakbufferen før ventingen; COP1LC oppdateres i blankperioden, og maskinvaren

starter Copper-listen ved neste felt. Ingen COPJMP1-strobe brukes i spilløkken.

En korrekt rå framebuffer og jevn felttakt beviser ikke korrekt skjermutlesning;

faktisk emulatorvisning må også kontrolleres.



## Gjenstående før M2 kan godkjennes



- Primærutgaven fra 1984 må bekreftes. Tilgjengelig T64 er en Remember-utgave

  med to trainervalg; begge ble slått av, men dette beviser ikke originalidentitet.

- Stabil maskinbasert input-/tilstandssammenligning må etableres. De første

  VICE-monitoropptakene stoppet på feil grenser og er forkastet som timingbevis.

- MACHINE-0001/0002 gir repeterbare fullmaskinspor av kandidaten og støtter

  tre PAL-felt per spillsteg. Se [arbeidsleveransen](NIGHT_HANDOFF.md) for hvilke

  posisjonsforløp som samsvarer; dette er fortsatt ikke retailsertifisering.

- Rommet er en geometrisk skisse etter observert første rom. Eksakte

  kollisjonsmasker, vegg-/takregler og nettgrenser er ikke portet ferdig.

- Landingsavrunding, veggreaksjon, tak/avsatsgrenser og inputfasen trenger videre

  sammenligning. Kjernetestene inkluderer nå målte kandidatspor og separate

  interne kontrakter; tilstands-/hendelsesparitet er ikke ferdig.



Planens M0/M2-paritetskrav står ved lag. Den spillbare prototypen er en

arbeidsleveranse på vei mot M2, ikke et påstått identisk originalspill.



2026-10-20: spark har to ben. Treff ovenfra virker ved fritt fall på

testmotstanderen; vanlige hopp er en separat tilstand. Den lange testen

setter opp dette fallet ved periode 1440 og kontrollerer `target_stomps`.

Fallfarten er beholdt etter måling mot C64-kandidaten.



Den lange A500-testen måler nå også faktisk emulert handlingsvarighet med

CIA TOD ved faste bevegelsesmarkører. Den skriver `movement-timing.json` og

[sekundtabellen](MOVEMENT_TIMING.md), med start-/sluttdefinisjoner og timeroppløsning.

