# Aktive tester etter sammenligningen 24. oktober

**Kodegjennomgang 25. oktober:** [T01–T18 mot faktiske C64-bytes](TEST_AUDIT_2026-10-25.md).
Den gjennomgangen korrigerer forventningene under. Manuelle godkjenninger
beholdes; de er ikke samlet kodeparitet. 61 kontrollerte kilde-CPU-fixtures
fastsetter heller ikke naturlig spritekontakt eller Amiga-paritet.

Gjeldende prioritet er kildedata og C64-disassembly, jf. [prosjektreglene](../AGENTS.md).
Ny avgrenset gjennomgang: [kollisjon, lanterner og rom 1→2](C64_CONTACTS.md).
Senere bevegelsesgjennomgang: [spark, hopp og veggkontakt](C64_MOVEMENT.md).
Spark-/hopp-/fallmasker, sparkfaser, svart kontakt/historikk og Bruces grenser
er nå korrigert mot koden. Landing og full aktør-/kampmaskin er fortsatt åpne.
Ståretning, boksing og liggestilling bruker nå kildepositur ved objektkontakt.
De 29 målrettede kildefixturene erstatter ikke åpen naturlig fase-/kanttesting.
Ukjent oppførsel skal avklares i originalkoden før vi finjusterer motoren.
[Romgjennomgangen](ROOM_RECONSTRUCTION.md) beskriver de 20 kildebaserte rommene.
Disse erstatter blokkrommene; aktøradaptere og full naturlig progresjon
gjenstår. [Rippede C64-sprites](C64_SPRITES.md) erstatter nå egenlagde figurer.
Den kildeavstemte positurvelgeren endrer ikke de åpne motor-/kontaktavvikene.
Ny kunst og lyd kommer senere som en eventuell enhanced-utgave.

[Klatrerettelsen](C64_CLIMB.md) følger nå nettmasker10/12 og kildens
separate side-/vertikalrytme.12800 dispatchtilfeller og866 sekvensielle
steg er kildeavstemt. Brukerens rom5-situasjon skal fortsatt prøves naturlig.

[AI-verifikasjonen](C64_AI.md) fastsetter nå Kage/Yamos beslutninger,
venting, inntreden og utgangsbetingelser fra koden. Den endrer ikke dagens
spillbygg og opphever ikke brukerens tidligere manuelle godkjenninger.

Denne listen erstatter den gamle komplette sjekklisten. Godkjente tester er
arkivert i [testhistorikken](history/MANUAL_TEST_2026-10-24.md), ikke slettet
fra dokumentasjonen. T01 og T05 er bestått. T04 er mekanisk akseptert i de
testede situasjonene; den tidligere v2-sparkposituren er satt til side. Brukeren har også
godkjent T12, T13, T15 og T16 for nå, med mulighet for ny vurdering senere.
Tidligere merknader til disse er historikk, ikke krav om en ny full test nå.

## Kjente avvik som skal rettes og testes på nytt

| ID | Test etter rettelse | Referanse / forventning |
| --- | --- | --- |
| T02 | Fall rett ned og hopp skrått ned på Ninja og Yamo. | Kode: angriper må være i tilstand14, ha VIC-kontakt og oppfylle høyde-/kvote-/offerkrav. Vanlig nedadgående hopp er ikke automatisk et falltreff. Undersøk manglende Amiga-treff med tilstandslogg. Kandidatanomalien ved terminal fallskade må avklares særskilt. |
| T03 | Hold slag mens Ninja, deretter Yamo, nærmer seg. | Brukerens C64-utfall beholdes. Koden tillater slag og spark å registreres samtidig; ingen generell Yamo-prioritet. Amiga må få kildebasert spritekontakt og samle alle treffflagg før skade brukes. |
| T06 | Kandidatrettelse: stå ytterst, sats begge veier og land nær en kant. | Kontakt bruker kildens hopp-/spark-/fallmasker og stå-/boks-/liggepositurer. Bruces nettmasker er også rettet. Gang-/reaksjonssekvenser og hele støtte-/landingsgrenen gjenstår; sammenlign sats og landing begge veier. |
| T10-NET | Hopp inn med sluppet input, ren sideretning og skrå input. Prøv alle fire diagonaler mens du henger, så ren opp/ned/side. | Hopp avbrytes av nettkontakt uansett ny input. Diagonaler stopper. Bruces nettgrep/-slipp, positurer10/12, CB og separate ventetellere er rettet mot koden. Sidefarten er4/6 piksler uten ekstra venting; vertikalt3/4 med venting3. Full støtte-/landing og øvrig aktørmotor er fortsatt åpne. |
| T14 | La Bruce dø etter kamp og etter innsamling. | Koden trekker liv, gjenoppretter helse og fiendeinntredentellere, reinitialiserer aktører og laster rommet. Det betyr ikke automatisk at lanterner nullstilles. Amiga laster nå rom/NPC-er, men mangler hele livs-/Game Over-/resetforløpet. |
| GEO-R02 | Gå og hopp gjennom midtforbindelsen i rom 2. | Brukeren beskriver en sammenhengende forbindelse med hvit trapp, ikke to isolerte avsatser. Kontroller takdekor separat fra kollisjon. |

## Uavklarte tester som beholdes

- AUDIO-MIX: Last den nye `amiga/out/bruce-a500.uae`-profilen i WinUAE og
  lytt gjennom minst24 sekunder av tittellåten. Stemmene kommer inn etter
  omtrent0,02/7,70/2,58 sekunder. Alle tre er påvist i separate native
  opptak med lik lyd på begge utganger; brukerens lyttegodkjenning gjenstår.
  Noter eventuelle rare enkelteffekter med handlingen som utløste dem.
  [Lyddiagnosen](AUDIO_PLAYBACK.md) skiller dette fra SID-klang og tidsavvik.

- CLIMB-R05: Gå til det lange midtfeltet i rom5. Klatre opp på høyre og
  midtre del, stopp og bytt retning. Gå sideveis begge veier og slipp nettet.
  Kontakt skal bruke klatreposituren, og sidebevegelse har ingen3-stegs pause.
  Svarte hindringer skal fortsatt begrense Bruce etter C64-koden. Snapshotet
  er bevart; testen skal kjøres i nytt bygg, siden USS også inneholder gammel kode.

- SPRITES-C64: Kontroller kildefigurene ved gange, klatring, slag, spark,
  liggestilling og Kages stikk i begge retninger. Se også overlapping mellom
  svart Kage, Yamo og Bruce og tegning ved begge skjermkanter. Uttrekk og
  positurvelger er kodeavstemt; naturlig sekvenstiming og kontaktmotoren
  er fortsatt egne åpne punkter. Denne testen gjelder kildevisningen.

- T07: Ninja kan bomme når Bruce hopper litt fram idet stikket starter.
  Sammenlign aktiv angrepsfase, nærgrense og rekyl; hopp gir ikke generell immunitet.
  Selve kodegrenen krever restteller <8, uten særskilt avvisning av teller0.
- T08: Veggpress og rømming. Mål tid og skade ved gåing, hopp og liggestilling.
- T09: Hold opp og veksle hopp ved landing. Retning låses under hvert hopp.
- T11: Kodebekreftet: offer i liggetilstand26 avvises av kamprutinen.
  Dette godkjenner ikke beskyttelse mot feller. Manuelt resultat for oppreisning
  og inputfase er ikke dokumentert og blir stående åpent.
- SRC-COMBAT-ORDER: Kamp bruker eksisterende tilstander før aktøroppdatering;
  aktører oppdateres Ninja, Yamo, Bruce. Dette er rettet. Kontroller naturlig
  treff-/rekylstart; den separate feilen med sekvensielle par og foreløpige bokser gjenstår.
- SRC-EDGE-STEP: Koden går én Y-piksel første steg uten støtte, så to i åpent
  fritt fall. Bruces X-grenser0–302 og Y45–199 er korrigert, inkludert rekyl.
  Kontroller naturlige landinger/kanter; kildeavstemt hoppbane fastsetter ikke
  hele den foreløpige støtte-/landingsadapteren.
- MOVE-WALL: Spark mot svarte hindringer i begge retninger og ulike høyder.
  Kontroller tilbakerulling/restitusjon og at Bruce kommer tilbake til normal
  kontroll. Nett avslutter sparket; synlig dekor/klasse1 er ikke automatisk sidevegg.
- MOVE-JUMP: Hold opp, veksle retning ved landing og prøv motsatt retning i
  lufta. Sammenlign siste hoppfase og første fallsteg; kontroller også kantlanding.
- AI-SOURCE: Før ny samlet AI-test må kildeklokken/ventingen, Yamos
  inntreden/sene vending, Kages stikkavslutning, retrettstøtte og NPC-objektpass
  porteres samlet. De ordinære angrepsavstandene er allerede kodeavstemt.
  Ikke bruk første spawn96/232 eller fast venting6/24 som universell fasit.

## Tester for romløftet

- ROOM-ALL: Besøk hvert av de 20 rommene. Skill testvalg av rom fra faktisk
  gjennomspilling. Ingen rom skal bruke rom 1 som skjult reservegeometri.
- ROOM-LINKS: Kontroller dører, ankomst, retur og naturlig tilgjengelighet.
  Dynamiske åpninger må ikke godkjennes bare fordi statisk tabell har en kobling.
- ROOM-R01-EDGE: Høyre utgang krever kilde-X≥300 og registrert høyrebevegelse;
  C64 bytter før hele figuren er ute. Øvre forbindelse ankommer rom 2 på
  (6,98), nedre på (8,146). Terskel, høydebånd og retur har egne kildefixtures.
  Sammenlign opplevd visuell timing; en senere utgang må ikke innføres uten kildegrunnlag.
- LAMP-POSE: Sammenlign stående mot begge retninger, boksing og liggestilling.
  Ett kildeflagg gjelder seks celler; ikke forvent en egen streng pikselboks
  rundt hver lanterne. Én innsamling gir 125 og effekt $8E. Hopp-/spark-/fallmasker
  og nettmaskene er nå kildeavstemt; gang-/reaksjonssekvenser gjenstår i aktørporteringen.
- ROOM-GATES: Lanterner, låste veier, broer, feller og sluttrom må testes mot
  C64 før full M4 eller gjennomspilling godkjennes.
  Ny kandidat retter gulvluken i rom 2, returportalen i rom 6 og høyre
  utgang i rom 3. Spill først inn alle 22 lanterner i rom 1–3, bruk luken
  i rom 2 til rom 6, tøm rom 7 og finn øvre retur i rom 6. Minst én av de
  angitte øvre lanternene i rom 6 må også være tatt. Høyre utgang i rom 3
  åpnes etter rom 7. Lukens originale init-/løprutine og åpningstid er nå med. Kontroller hele ruten naturlig; romvalg er ikke bevis på tilgjengelighet.
- ROOM-GRAPHICS: Nett skal ikke stikke gjennom feil etasje. Takdekor skal ikke
  automatisk bli solid vegg. Fotpunkt og kollisjon må være uavhengige av ny kunst.
- A500: Kaldstart, Escape til CLI, start-kommando, romlasting og 512+512-minne.
  Lange romlastinger måles separat fra jevn spillrytme. Nye kilder krever nye
  rapporter; gamle måleresultater er historiske etter motorendringer.
- PRESENTATION: Kontroller figurlesbarhet og forsinkelse i rom med store
  animerte flater. Motoren kan beholde forrige bilde for å holde spilltakten;
  feltkadens alene godkjenner ikke jevn 50 Hz animasjon.
- PERF-R14/R20: Den strenge A500-porten er åpen. Flytting av plattformceller i
  rom 14 og arbeid i sluttrommet kan alene overskride feltbudsjettet. Diagnosemodusen registrerer
  dette under full rominspeksjon; den teller ikke som en bestått ytelsestest.
- PERF-COMBAT: Gjeldende bygg med C64-sprites har to6000-felts A500-CLI-kjøringer
  med324 beståtte positur-,70 bevegelses-,29 objekt- og390 klatrekontroller per start.
  Kamp-/lydresultat matcher verten. Kjøringene har242 forsinkede felt hver, maksimal avstand
  2/3 PAL-perioder. Dette er diagnose; den strenge tidsporten er fortsatt åpen.
  Se `reference/validation/c64-sprites-delivery.json`. Tidligere målinger ligger
  i historiske rapporter og godkjenner ikke dagens bygg.
- MEM-CLI: Testutgaven består49152-målet med88480 byte største sammenhengende
  Chip-blokk. Tilgjengelig utvidelsesminne før runtimeallokering er42048 byte.
  Testen har ekstra40 KiB framebufferkopi. Mål fortsatt vanligbyggets minne
  og timing separat med16 KiB CLI-stakk.

## Utsatt enhanced-grafikk

ART-01/02 for de egenlagde figurene er tatt ut av den aktive listen.
Brukerbeslutningen25. oktober setter dette arbeidet til side.
Figurtestingen gjelder nå SPRITES-C64 over. HUD-navn og helsefelt er fortsatt
en foreløpig Amiga-visning, ikke en ferdig kildeport av C64-grensesnittet.

AUDIO-01 er akseptert for nå av brukeren (24. oktober: «Høres ok ut så langt»).
Lydkvalitet kan vurderes igjen senere; det er ikke krav om full ny lyttetest nå.

AUDIO-01 gjelder de tidligere genererte kamplydene. Ny leveranse følger
[originalens lydkode](SOURCE_AUDIO.md) og har en egen kontroll:

- AUDIO-SOURCE: La tittellåten gå rundt én23-sekunders løkke, trykk ild og
  kontroller at musikken stopper ved spillstart. Lytt til gang/klatring,
  spark, stikk, treff, lanterner og dynamiske rom. Romlasting skal stilne
  gamle toner. Escape og `start` skal fungere også fra tittelskjermen.
  Dette er en ny lydvurdering, ikke en oppheving av den gamle godkjenningen.

- START-01: Vurder det nye oppstartsskriket: naturlig «Haaaai-yah», passende
  volum, ingen løkke eller knepp. Dette gjelder den nye stemmen, ikke ny
  godkjenning av alle kamplydene. Test Escape og deretter `start` fra CLI.
- LOAD-ART: Brukerens lasteillustrasjon mangler som tilgjengelig vedlegg.
  Den midlertidige BRUCE/LOADING-teksten er ikke ferdig lastekunst.

Planen for forbedrede figurer/tiles og lagrede AI-prompter er bevart i
[grafikkflyten](AMIGA_ART_PIPELINE.md) til en eventuell enhanced-utgave.
