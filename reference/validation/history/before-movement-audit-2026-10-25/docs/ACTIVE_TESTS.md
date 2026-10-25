# Aktive tester etter sammenligningen 24. oktober

**Kodegjennomgang 25. oktober:** [T01–T18 mot faktiske C64-bytes](TEST_AUDIT_2026-10-25.md).
Den gjennomgangen korrigerer forventningene under. Manuelle godkjenninger
beholdes; de er ikke samlet kodeparitet. 61 kontrollerte kilde-CPU-fixtures
fastsetter heller ikke naturlig spritekontakt eller Amiga-paritet.

Gjeldende prioritet er kildedata og C64-disassembly, jf. [prosjektreglene](../AGENTS.md).
Ny avgrenset gjennomgang: [kollisjon, lanterner og rom 1→2](C64_CONTACTS.md).
Ståretning, boksing og liggestilling bruker nå kildepositur ved objektkontakt.
De 29 målrettede kildefixturene erstatter ikke åpen naturlig fase-/kanttesting.
Ukjent oppførsel skal avklares i originalkoden før vi finjusterer motoren.
[Romgjennomgangen](ROOM_RECONSTRUCTION.md) beskriver de 20 kildebaserte rommene.
Disse erstatter blokkrommene; aktøradaptere og full naturlig progresjon
gjenstår. Ny kunst og lyd kommer senere.

Denne listen erstatter den gamle komplette sjekklisten. Godkjente tester er
arkivert i [testhistorikken](history/MANUAL_TEST_2026-10-24.md), ikke slettet
fra dokumentasjonen. T01 og T05 er bestått. T04 er mekanisk akseptert i de
testede situasjonene; den nye v2-sparkposituren vurderes under ART-01. Brukeren har også
godkjent T12, T13, T15 og T16 for nå, med mulighet for ny vurdering senere.
Tidligere merknader til disse er historikk, ikke krav om en ny full test nå.

## Kjente avvik som skal rettes og testes på nytt

| ID | Test etter rettelse | Referanse / forventning |
| --- | --- | --- |
| T02 | Fall rett ned og hopp skrått ned på Ninja og Yamo. | Kode: angriper må være i tilstand14, ha VIC-kontakt og oppfylle høyde-/kvote-/offerkrav. Vanlig nedadgående hopp er ikke automatisk et falltreff. Undersøk manglende Amiga-treff med tilstandslogg. Kandidatanomalien ved terminal fallskade må avklares særskilt. |
| T03 | Hold slag mens Ninja, deretter Yamo, nærmer seg. | Brukerens C64-utfall beholdes. Koden tillater slag og spark å registreres samtidig; ingen generell Yamo-prioritet. Amiga må få kildebasert spritekontakt og samle alle treffflagg før skade brukes. |
| T06 | Kandidatrettelse: stå ytterst, sats begge veier og land nær en kant. | Støtte og landing bruker nå kildepose 2 mot faktiske tegnpiksler og attributter. Fullt originalt posevalg gjenstår; sammenlign sats og landing begge veier. |
| T10-NET | Hopp inn med sluppet input, ren sideretning og skrå input. Prøv alle fire diagonaler mens du henger, så ren opp/ned/side. | Rettet fra kode: hopp avbrytes av nettkontakt uansett ny input. Diagonaler stopper på nettet; de gir ikke vertikal prioritet. Fullt posebasert grep/slipp og aktørtellere gjenstår. Klatrefarten er uendret. |
| T14 | La Bruce dø etter kamp og etter innsamling. | Koden trekker liv, gjenoppretter helse og fiendeinntredentellere, reinitialiserer aktører og laster rommet. Det betyr ikke automatisk at lanterner nullstilles. Amiga laster nå rom/NPC-er, men mangler hele livs-/Game Over-/resetforløpet. |
| GEO-R02 | Gå og hopp gjennom midtforbindelsen i rom 2. | Brukeren beskriver en sammenhengende forbindelse med hvit trapp, ikke to isolerte avsatser. Kontroller takdekor separat fra kollisjon. |

## Uavklarte tester som beholdes

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
  fritt fall. X-grensene etter forflytning er0–302 før svart kontakt/historikk;
  dagens gang-/reaksjonsklemmer avviker. Kontroller dette sammen med pose-/veggporteringen.

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
  rundt hver lanterne. Én innsamling gir 125 og effekt $8E. Gang-/hopp-/klatre-
  masker i objektpasset er fortsatt del av den åpne aktørporteringen.
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
- PERF-COMBAT: Før aktørrettelsene: to6000-felts CLI-kjøringer matchet vertens kampforløp, men
  hver har8 tidsavvik med opptil to PAL-perioder mellom oppdateringer.
  Etter rettelsene matcher begge nye kjøringer verten med62 treff,6 fiendenederlag
  og2 Bruce-dødsfall/respawn. Hver har2 tidsavvik og maksimal avstand to PAL-perioder.
  Dette er diagnose, ikke en bestått tidsport. Se `reference/validation/test-audit.json`.
  Med kildebasert lyd matcher de to nye kjøringene fortsatt kamp- og
  Paula-signaturene, men har9 tidsavvik hver. Gjeldende lydrapport:
  `reference/validation/source-audio-delivery.json`.
- MEM-CLI: Mål fri og sammenhengende Chip i vanligbygg med16 KiB CLI-stakk.
  Testutgaven har en ekstra40 KiB framebufferkopi og fikk28 224 byte
  sammenhengende Chip ledig, under testens48 KiB-reservemål.

## Grafikkrunde

- ART-01: Kontroller de nye figurene i begge retninger: stå, løpe, slå, sparke,
  ligge og klatre. Se særlig etter fotkontakt, tydelig Ninja og Yamo, og at
  sparkets grafikk er forståelig sammen med de fortsatt foreløpige treffboksene.
  V2 har fire klatrefaser med vekslende sider og flere løpe-/angrepsfaser.
  Stopp midt i nettet og klatre ned igjen: syklusen skal stoppe og reversere.
  Ninja har nå bambusstav i begge hender ved stikk. Kontroller særlig at
  posituren er lesbar sammen med dagens uendrede treffrekkevidde.
  Yamo har grønn hud og kraftigere kroppsform. HUD-navnene er KAGE
  (Ninja), YAMO og BRUCE; kontroller at riktig helsefelt reduseres ved treff.
- ART-02: Kontroller figurkontrast mot de rippede rommene. Alle rom har nå egne
  kildebaserte tegnbilder og rasterfarger. Figurene er fortsatt Amiga-prototyper.

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

Ninja-silhuett, Bruce sin bakoverlente sparkpositur og tydelige stå-/gå-/klatre-
bilder vurderes sammen med nye tiles. Alle ressurser skal ha fast anker,
OCS-palett, kilde-ID, lagret AI-prompt og valideringsrapport.
