# Manuell sammenligning — C64 mot Amiga, 22. oktober 2026

**Historisk testøkt.** Kodebaserte rettelser til tolkningen av T01–T18 står i
[gjennomgangen 25. oktober](../TEST_AUDIT_2026-10-25.md). Teksten under bevarer
datidens observasjoner og hypoteser; påstander om to rom, vertikal prioritet,
treff og reset er ikke gjeldende implementasjonsfasit.

Sluttavklaring fra brukeren 24. oktober: T12, T13, T15 og T16 regnes som
bestått for nå, med mulighet for ny vurdering senere. De tidligere foreløpige
formuleringene er bevart under som historikk. Aktiv liste: ../ACTIVE_TESTS.md.

Målet er C64-logikk. Test først C64, deretter samme handling i Amiga. Gjenta
usikre funn tre ganger og noter rom, sted, retning og hvilke knapper du holdt.
Ulik grafikk gjør at tid, fotpunkt, tilstand og utfall er viktigere enn antall
skjermpiksler. Et manuelt «ser likt ut» erstatter ikke måling av et timingavvik.

Referansen er vår lokale, hash-låste C64-kandidat med begge trenerfunksjoner av.
Den er ikke endelig identifisert som original retail-utgave fra 1984.
Amiga er første M4-del med bare rom 1 og 2. M2 og M3 har fortsatt åpne punkter.
Lyd testes ikke i denne runden; C64-snapshotets SID-gjenoppretting gir en kjent
lydmelding i denne VICE-installasjonen. Lukk «VICE Error» med «Close» hvis den vises.

## Før du begynner

- C64 skal stå til venstre, Amiga til høyre. Aktiver ønsket vindu før input.
  Museklikk avslutter ikke lenger Amiga-spillet. Escape returnerer til AmigaDOS.
- Numerisk tastatur: 4/6 venstre/høyre, 8 opp/hopp/klatre, 2 ned/ligge.
  Joystickens ild uten sideretning er slag; løp noen steg og bruk retning + ild
  for flyvende spark. Kontroller ildtasten i emulatoren hvis tastaturet avviker.
- Ikke endre warp, turbo eller emulatorhastighet. Test i PAL og vanlig hastighet.
- C64 kan startes fra utgangspunktet med `c64-run-reference.ps1` etter at den
  eksisterende referanseinstansen er lukket. Amiga startes med `amiga-run.ps1`.
  Ikke tilbakestill ved å lagre over referanse-snapshotet.
- Skriv «likt», «avvik» eller «ikke testet» per ID. Ikke godkjenn M4 samlet:
  de resterende 18 rommene er ennå ikke spillbare.

## Prioritet 1 — avklar nå

| ID | Milepæl | Gjør dette i begge versjoner | Noter / avklar |
| --- | --- | --- | --- |
| T01 | M2/M3 | Gå utfor en høyere avsats uten hopp. Prøv holdt retning, motsatt retning og sluppet joystick. | Loddrett fall eller sidestyring? C64 er allerede målt med fast X; Amiga-kandidaten låser nå også X i fritt fall. Kontroller endringen i spill. |
| T02 | M2/M3 | Hopp ut fra en høyere avsats mot Ninja/Yamo under deg. Skill fra å gå rett utfor. Gjenta med vanlig hopp over en fiende på samme gulv. | Når kommer falltreffet? Må hoppet først gå over til fritt fall? Noter fiendens positur/angrep og om Bruce faktisk treffer ovenfra eller siden. Nåværende Amiga gir falltreff bare i fritt fall; naturlig C64-falltreff med skade er ennå ikke fanget i opptak. |
| T03 | M3 | Stå foran en fiende, uten sideretning. Trykk ild kort og hold den. Gjenta tett inntil, litt lenger unna og vendt motsatt vei. | Slagets rekkevidde, dødsone på nært hold, første treff, gjentakelsestakt og om synlig knyttneve uten treff føles forskjellig. Amiga treffer nå i alle fire tegnede slagsteg; eksakt C64-pikselkontakt er fortsatt åpen. |
| T04 | M3 | Løp noen steg og bruk retning + ild. Spark både fra venstre og høyre, og prøv bakfra. | Sparkvalg, treffavstand, skade, korrekt retning på rekyl og Yamos glidning. Ingen tredje fot eller feilvendt glidning. |
| T05 | M4-del | Kryss øvre forbindelse rom 1 → 2 → 1. Gjenta nedre forbindelse. Stopp straks etter ankomst. | Ingen fall gjennom gulvet, vertikalt rykk, synlig trinn eller automatisk retur. Øvre gulv er Y98 i begge rom; nedre Y146. |
| T06 | M2 | Sats på løpshopp mot øvre høyre avsats, først litt før kanten og så så sent som mulig. Prøv begge retninger der det er mulig. | Rekkevidde og siste gyldige sats. Det ekstra hoppvinduet er fjernet. Sats krever at logikkens fotpunkt fortsatt har gulvstøtte. |
| T07 | M3 | La Ninja stikke forover. Nærm deg forfra og bakfra. Prøv også å hoppe forbi foran ham. | Aktiv fase for sai, nærgrense, treff bakfra, skade og rekylretning. Hopp gir ikke generell immunitet i C64. |
| T08 | M3 | La fiendene presse deg mot venstre vegg. Prøv å gå ut, hoppe ut og ligge ned før du går/hopper ut. | Kan du slippe unna, og hvor lang tid tar det? C64-venstrehjørnet er målt som mulig å unnslippe; Amiga tar foreløpig lengre tid og gir annet skadepress. |

## Prioritet 2 — bevegelse og kamp fra tidligere milepæler

| ID | Milepæl | Gjør dette | Noter / avklar |
| --- | --- | --- | --- |
| T09 | M2 | Gå samme strekning i begge retninger, stopp og snu. Prøv stående hopp og løpshopp; slipp/bytt retning i luften. | Tid til mål, akselerasjon, låst hopp-retning, startrespons og landing. Ikke vurder fart fra forskjellig vindusstørrelse. |
| T10 | M2 | Grip nettet midt i rom 1. Klatre opp/ned, stopp, snu, slipp sideveis og hold opp gjennom toppen. | Ingen sidebevegelse samtidig som opp/ned holdes; slipp vertikalretningen før sideveis avstigning. Klatretid, gripepunkt, avstigning og gjentatte hopp etter toppen. Animasjonen skal vise armer/bein uten å endre C64-farten eller gli når du stopper. |
| T11 | M2/M3 | Hold ned på gulvet, prøv ned + retning, slipp ned og reis deg. Gjør det under fiendeangrep. | Liggestilling, stillstand, når du reiser deg, og hvilke angrep som går over/treffer. Ned på nettet skal klatre ned. |
| T12 | M3 | Stå stille på samme plan som fienden, flytt deg litt og gå forbi/bak ham. Stå også nede mens Ninja går mot høyre utgang oppe. | Gjenåpnet feil: brukeren ser fortsatt fastlåsing i rom 1 øverst til høyre. Den avgrensede C64-ruten og to A500-kjøringer viser utgang og retur etter 160 steg (~9,6 s), deretter venstrevendt gange. Test manuelt i nytt bygg; full navigasjon er fortsatt åpen. |
| T13 | M3 | Ta ett sai-/slag-/sparktreff om gangen. Prøv deretter tett kontakt og to fiender samtidig. | Rekylavstand og retning, synlig skadereaksjon, glidetid og beskyttelse mellom treff. Samtidige treff og eksakte kollisjonsmasker er ikke ferdig verifisert. |
| T14 | M3 | La Bruce og hver fiende bli slått ned og beseiret. Observer hele forløpet uten input. | Når kroppen forsvinner, respawn-sted, forsinkelse og hva som nullstilles. Amiga har foreløpig ubegrensede nye forsøk; liv/Game Over og original reset av verden gjenstår. |

## Prioritet 3 — denne romleveransen og teknisk sluttkontroll

| ID | Milepæl | Gjør dette | Noter / avklar |
| --- | --- | --- | --- |
| T15 | M4-del | Berør lanterner fra siden, ovenfra og underfra i rom 1 og 2. Gå tilbake til samme plass. | Hvilke posisjoner samler dem? Én innsamling skal gi 125 poeng og ikke telles igjen. C64s supplerende pikselflagg er ikke fullt gjenskapt. |
| T16 | M4-del | Samle noen lanterner, bytt rom og returner. Gjenta etter at Bruce er beseiret. | Innsamlede lanterner skal forbli borte ved vanlig retur. Sammenlign særskilt reset ved død; det er fortsatt åpent mot C64. |
| T17 | M4-del | Prøv begge romutganger med få og mange innsamlede lanterner. | Hva åpnes i C64, og når? Utgangen videre til rom 3 er med vilje stengt i denne Amiga-delen. Bro/feller og alle videre dørvilkår er ikke levert. |
| T18 | M1/M4-del | Spill noen minutter, bytt rom flere ganger, slåss mens lanterner samles. Avslutt og start på nytt. | Grafikkrester, blink, feil figurdeler, hakking, fastlåst input eller krasj. Escape skal returnere til AmigaOS; museklikk skal ikke avslutte. Skriv start i CLI for ny runde. Fysisk A500 gjenstår. |

## Resultatmal

Kopier denne for hvert avvik, gjerne med et kort opptak av begge versjoner:

```text
Test-ID:
Rom og sted:
Input og rekkefølge (inkludert hva som ble holdt/sluppet):
C64: hendelse og omtrentlig tid:
Amiga: hendelse og omtrentlig tid:
Gjentatt: __ av 3 forsøk
Resultat: likt / avvik / usikkert
```

## Skal ikke testes som ferdig ennå

Alle 20 rom, feller/bevegelige broer, full gjennomspilling, originale
spillermoduser, liv/ekstraliv/Game Over, ferdig grafikk/lyd, fysisk A500 og
iPhone/nettspilling er fortsatt åpne leveranser. En god manuell runde i de to
første rommene gjør ikke M4 ferdig og godkjenner ikke hele M2/M3-pariteten.

## Observasjoner fra sammenligningen 22. oktober

### Manuelle resultater, nytt testbygg

| ID | Resultat | Brukerens observasjon | Avgrensning |
| --- | --- | --- | --- |
| T01 | Bestått manuelt på Amiga og C64, 24. oktober | Går utfor høyre avsats uten hopp. Bruce faller rett ned og kan ikke styres mot noen av sidene i begge versjoner. | Brukeren sammenlignet begge maskiner og ba om å krysse av testen. Nettavstigning og andre avsatser er ikke bekreftet her. |
| T02 | Avvik, gjenåpnet 24. oktober | C64: både Ninja og Yamo tar skade når Bruce faller rett ned på dem; også skrått hopp ned på en fiende gir skade. Brukeren beskriver et forholdsvis romslig treffområde. Amiga: rett nedfall på fienden gir ingen synlig skade i den testede situasjonen. | Tidligere kort observasjon om nødvendig fritt fall godkjenner ikke trefflogikken. Fang tilstand og kontakt ved skrått hopp før endelig tilstandskrav fastsettes. Treffområde, skade og angrepsprioritet må sammenlignes. |
| T03 | Observert avvik mot Yamos flyvende spark, 24. oktober | C64: Stillestående Bruce med ild holdt inne kan beseire Ninja når han nærmer seg, observert gjentatte ganger. Mot Yamo taper Bruce: Yamos flyvende spark går gjennom slagene i forsøkene. Amiga: Bruce kan slå ut Yamo under hans flyvende spark. Slag i lanternens høyde kan også samle/slå ut lanternen i C64. | Undersøk kontakt, treffområde og angrepsrekkefølge før det innføres en generell prioritetsregel. Antakelsen om at Ninja konsekvent holder seg utenfor slagrekkevidde ble trukket tilbake. Kort ildtrykk, alle avstander og bakvendt slag er ikke ferdig avklart. |
| T04 | Mekanikk virker grei i testede situasjoner, 24. oktober | Brukeren opplever sparkets bevegelse og mekanikk som grei. Sparkposituren avviker visuelt: Bruce bør lene seg flatere bakover som i referansen. | Positur noteres til senere grafikk-/animasjonsarbeid. Dette godkjenner ikke særskilt alle treffavstander, skadeverdier, bakfra-treff, rekylretninger eller glidning. |
| T05 | Bestått manuelt, 24. oktober | Brukeren krysser mellom rommene uten nevneverdige problemer. Ingen fall gjennom gulvet og ingen merkbar forskjell i plattformhøyden ved rombytte. Brukeren bekrefter T05 som i orden. | Gjelder de testede forbindelsene mellom de to spillbare rommene. Antall repetisjoner og hver enkelt retning/forbindelse er ikke særskilt oppgitt. |
| T06 | Observert avvik ved kantstøtte, 24. oktober | C64: Bruce kan etter brukerens vurdering stå på kanten så lenge bakerste fot fortsatt har støtte, og hoppe videre med opp + retning. Amiga: Bruce faller for tidlig utfor; brukeren ber om mer korrekt støtte ved kanten, også ved landing. | Mål kroppens støtteområde og forholdet mellom logikk og tegnet fotpunkt. Ikke bruk animasjonens skiftende benstilling direkte som kollisjonsregel, og ikke erstatt riktig støtteområde med et udokumentert ekstra hoppvindu etter fallet har startet. |
| T07 | C64-observasjon; Amiga-sammenligning pågår, 24. oktober | Når Ninja står klar til å stikke, kan et lite hopp framover få ham til å bomme i C64. Brukeren opplever at Bruce må være et stykke foran Ninja for å bli truffet. | Ikke generell hoppimmunitet. Undersøk avstand, angrepsfase og timing. Ninja har foreløpig svært forskjellig grafikk i Amiga, noe som gjør visuell sammenligning vanskeligere. Ingen avsluttende Amiga-konklusjon ennå. |
| T12 | Foreløpig grei ifølge brukeren, 24. oktober | Fiendeoppførselen virker grei i situasjonene brukeren nå observerer. | Brukeren er usikker på testen. Tidligere fastlåsing ved øvre høyre utgang lukkes ikke endelig uten en tydelig gjentatt test av akkurat denne situasjonen. |
| T13 | Foreløpig grei, men Ninja-reaksjon må undersøkes, 24. oktober | Yamos flyvende spark slår Bruce i bakken og lar ham skli bakover i begge versjoner. C64: Ninja-treff dytter Bruce et tydelig hakk sideveis, anslått omtrent figurens bredde. Brukeren mistenker at dette er mindre riktig i Amiga. | Ikke fastsett eksakt avstand fra muntlig anslag. Mål Ninja-rekyl separat; samlet godkjenning av T13 utsettes. |
| T14 | Avvik ved reset etter død, 24. oktober | Bruce starter nede ved venstre lanterne i første rom i begge versjoner. C64 nullstiller brettet ved ny start etter død. Amiga setter bare Bruce tilbake; fiendene blir igjen i den pågående verdenen. | Fastslå nøyaktig hva C64 nullstiller: fiender, ventetellere, lanterner og annen rom-/spilltilstand. Ikke forveksle vanlig skadereaksjon med død/nytt liv. |
| T15 | Foreløpig grei ifølge brukeren, 24. oktober | Innsamling av lanterner virker i orden i de spillbare rommene. | Nøyaktige treffgrenser, poeng og alle tilnærmingsretninger er ikke særskilt bekreftet. |
| T16 | Foreløpig grei ved vanlig romretur, 24. oktober | Brukeren opplever lanternetesten som grei og prøver å la en lanterne stå igjen i rom 1 mens han går til rom 2 og tilbake. | Ikke en ferdig bekreftelse på lanternestatus etter død; resetavviket i T14 er fortsatt åpent. Sluttutfallet av forsøket med gjenstående lanterne ble ikke entydig oppgitt. |
| T17 | Videre progresjon ikke testbar i Amiga-bygget | Bare rom 1 og 2 er spillbare. Utgangen til rom 3 er med vilje blokkert i denne leveransen. | Ikke godkjent som C64-paritet for låste utganger eller lanternevilkår. |

Under den pågående testøkten 24. oktober skal observasjoner bare noteres.
Ingen nye motorendringer, bygg, deployer eller emulatoromstarter før brukeren
ber om det etter testingen. Dokumentasjon av testfunn kan oppdateres løpende.

- Bruce mister helse ved enkelte nedfall på fiender i C64. Det er en observert
  situasjon, ikke bevis for at alle slike kontakter skader Bruce eller fienden.
- «Første flyvende spark vinner» er en hypotese som trenger separate opptak
  med begge angrepsrekkefølger. Kamprekkefølgen endres ikke ut fra dette alene.
- Hopp låser retning i luften; holdt opp og motsatt sideretning ved neste
  landing skal tillate raske vekslende hopp. Vertstesten dekker gjentakelse.
- Figurfinish vurderes senere; denne runden prioriterer bevegelse og utfall.

### T06: røde takdetaljer i første C64-rom

Brukeren observerer at Bruce løper vannrett gjennom de forhøyede røde,
trinn-/takformede detaljene på øvre venstre avsats uten å måtte klatre opp
dem. Etter hopp kan han tilsynelatende lande på en høyere del av taket.
Dette må undersøkes som retnings-/tilstandsavhengig kollisjon; hele den
tegnede røde formen skal ikke automatisk behandles som en solid vegg.
Amiga-blokkutgaven har foreløpig ikke disse grafiske detaljene.

Et eksisterende skjermbilde av første rom viser takdetaljene:
[C64-referanse, første rom](../.reference/c64/captures/CAP-0001/room1.png).
Bildet dokumenterer utseendet; brukerens bevegelsesobservasjon må fortsatt
måles mot spilltilstanden. Ingen ny opptaksøkt eller omstart ble gjort.

### Ekstra funn ved T07: nettgrep og sideveis avstigning (T10-tillegg)

24. oktober rapporterer brukeren et eget avvik etter sammenligning med C64:

- Ved skrått hopp fra en avsats inn i et nett/en klatrevegg griper Bruce
  automatisk når sideretningen i bevegelsesretningen holdes. Brukeren
  beskriver at han går over til klatring uten separat opp-input.
- Bruce kan bevege seg sideveis gjennom nettet. Ifølge brukerens observasjon
  slipper han først når hele kroppen har mistet kontakt med nettet.
- Etter at han slipper, faller han rett ned uten sidestyring.

Før rettelse må gripevilkår, kroppsoverlapp og nøyaktig slippunkt måles.
Dette er et separat bevegelsesfunn, ikke en konklusjon på T07 om sai-treff.
Brukeren fortsetter T07; ingen motorendring, nye bygg eller omstarter nå.

### Flere observasjoner fra testøkten 24. oktober

- Yamo har også bokseslag i C64. Brukeren så dette etter først å ha antatt at
  han bare brukte flyvende spark; den første antakelsen er trukket tilbake.
  Slagene oppleves sjeldnere enn sparkene, uten målt frekvens.
- C64: Yamo kan stoppe å gå når Bruce klatrer opp og er utilgjengelig over
  ham. Noteres som et AI-funn som må knyttes til posisjon og tilstand.
- Amiga rom 2: Det store nettet nede til høyre kan stikke litt opp gjennom
  avsatsen på nivået over. Visuell detalj til kontroll mot geometrien.
- C64 rom 2: Området som er tegnet som to separate avsatser i Amiga, oppleves
  som én sammenhengende forbindelse med en liten hvit trapp. Røde/brune
  takfelt kan ha skjult sammenhengen ved tidligere tolkning. Undersøk
  referansegrafikk og kollisjon før geometrien endres.
- Det tidlige fallet ved avsatskanter (T06) gjør fortsatt spillingen vanskelig
  og prioriteres i rettelsesrunden etter testøkten.
