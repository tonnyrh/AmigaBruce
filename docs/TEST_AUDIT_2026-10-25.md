# Gjennomgang av T01–T18 mot C64-koden

27. oktober: Adapterbegrensningene under er historikk. Den
[samlede kildeporten](MILESTONE_COMPLETION.md) erstatter aktør-, støtte-,
pose-, kamp-, AI- og livsadapteren i vanlig spill. Naturlig akseptanse og
maskinfasen er fortsatt åpne; brukerens tidligere godkjenninger beholdes.

25. oktober 2026. Dette korrigerer **tolkningen av de tidligere testene** og
registrerer konkrete feil i Amiga-adapteren. Brukerens observasjoner beholdes.
Senere samme dag: [lanterne- og romgrensegjennomgangen](C64_CONTACTS.md) retter
ståretning, slag-/liggemaske og lanterne-lydkall i objektpasset.
Deretter retter [bevegelsesgjennomgangen](C64_MOVEMENT.md) svart kontakt,
historikk, spark-/hopp-/fallmasker, faseforflytning og første fallsteg.
Begrensningene og native tallene i denne eldre gjennomgangen er historiske;
full landing, aktør-/kampmaskin og naturlig paritet står fortsatt åpne.
T01, T05, T12, T13, T15 og T16 er fortsatt manuelt akseptert i sine testede
situasjoner; T04 er mekanisk akseptert. Dette gir ikke samlet kodeparitet.

Kilden er `.reference/c64/work/untrained-memory.bin`, SHA-256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Remember/T64-kandidaten er fortsatt ikke identifisert som valgt urørt 1984-utgave.
Atari-/nettleserrekonstruksjonen og editorens ombygde spill brukes ikke som fasit.

Kjør `python tools/audit_c64_tests.py`. Den utfører de faktiske 6502-bytene i
61 kontrollerte CPU-fixtures og lagrer [rapport](../reference/analysis/test-audit-2026-10-25/report.json)
og [adresset disassembly](../reference/analysis/test-audit-2026-10-25/source-disassembly.txt).
Tilstand, VIC-kollisjonsregister, aktørmapping og kontaktklasser er **injiserte
innganger**. Dette er ikke VICE-opptak, simulering av VIC-piksler, naturlig
gjennomspilling eller bevis på Amiga-paritet. Grenene i koden fastsetter regelen;
fixture-kjøringen kontrollerer at vi har lest dem riktig.

## Resultat per tidligere test

| Test | Kodegrunnlag og korrigert konklusjon | Amiga / videre kontroll |
| --- | --- | --- |
| T01 – utfor uten hopp | `$1D7E–$1DC8`: tilstand 14 leser ikke ny sideretning. Uten kontakt går X uendret og Y to kildespiksler ned. `$1D99–$1DB0` har likevel automatisk sidekorreksjon ved kroppskontakt med klasse 1; «X kan aldri endres i fritt fall» var for absolutt. | Manuelt bestått for åpent fall beholdes. Korrigering ved kroppskontakt, svarte vegger og landing er fortsatt del av aktørporteringen. |
| T02 – falltreff | `$2A6F→$2AFA`: bare angriper i tilstand `$0E`, ikke vanlige hopp 5/6/7. VIC-gate først; høydeforskjell minst 10 i normal koordinatregion; fallkvote og offerets tilstand avgjør videre. Skrått hopp kan ha gått over til `$0E` før treffet. | Manglende treff ved rett fall er fortsatt åpent. Ikke gjør alle nedadgående hopp skadelige. Prototypens bokser og hastighetskrav er ikke originalregler. Terminalt falltreff har en egen kandidatanomali, se under. |
| T03 – slag mot spark | `$29C3–$2B4D` samler flagg før `$2B4E` anvender skade. Slag kan treffe en sparkende figur, og spark kan samtidig treffe en slående figur. Ingen generell Yamo-prioritet. Slag har ingen egen tellergate; spark krever restteller <10. | Brukerens observerte utfall beholdes, men «spark kan ikke stoppes med slag» er ikke en universell regel. Amiga anvender fortsatt treff sekvensielt og kan avbryte motangrepet for tidlig. Må erstattes sammen med korrekt spritekontakt. |
| T04 – flyvende spark | `$1E70/$1EB1→$1F64/$1F6D`, `$2048–$20D1`: retning, tidligere gangtilstand, animasjonsteller og ildlesing velger spark. Spark har egen bevegelse og teller; oppvarming er ikke hele treffvinduet. | Mekanisk aksept beholdes, ikke en godkjenning av hele treffområdet eller samtidighetsreglene. Figurpositur er fortsatt grafikkarbeid. |
| T05 – romovergang | `$2E89–$2EA2`, `$2F3C–$30D4`, rommenes init-/løprutiner og ankomsttabeller bestemmer overgangen. Sammenhengende gulv følger faktisk tegnkontakt og ankomst. | Aksept for testede forbindelser R01/R02 beholdes. Beviser ikke alle dører/rom eller full naturlig progresjon. |
| T06 – kantstøtte | `$5212–$52AB` beregner kontakt fra posemasker via `$1167/$1239`; `$1D99–$1DCE` skiller helmaske og kroppskontakt. Animasjonens tegnede bakerste fot er ikke en selvstendig regel. | Pose 2 brukes fortsatt fast i Amiga-kontaktadapteren. Dette er en konkret begrensning for sats/landing, ikke løst ved å flytte et gulvrektangel eller legge til et hoppvindu. |
| T07 – Ninja-stikk | `$2A7B–$2AA3`: restteller <8, retnings-/nærgrense via `$2C54`, samt VIC-kontakt. Ingen egen sjekk som gjør vanlig hopp immunt. Teller 0 avvises ikke av selve skadegrenen; om den nås i vanlig forløp må skilles fra dette. | Tidligere «7–1» var en beskrivelse av forventet aktivt forløp, ikke den bokstavelige betingelsen. Nærgrensen gjelder kilde-X, ikke sentre eller stavens tegnede lengde. |
| T08 – veggpress | `$1CC7–$1D6E` bruker lagret bevegelseshistorikk og flere forsøk ved svart kontakt. Hurt-/knockdown-tilstander gir kontaktbeskyttelse. | Eksisterende veggopptak er et avgrenset observert unnslippingsforløp. Ikke en generell regel om at hjørner er umulige eller alltid enkle å slippe ut av. Amigas horisontale rollback er fortsatt forenklet. |
| T09 – hopp/luftstyring | `$2008–$216A` bruker pågående hopptilstand og restteller; ny sideretning endrer ikke løpshoppets retning. Ny hoppstart avgjøres igjen i inputgrenene når handlingen er ferdig. | Retningslås beholdes. Gjentatte hopp, handlingsventing, posekontakt og landingsgren må kontrolleres samlet; en posisjonsserie alene godkjenner ikke alle interne tilstander. |
| T10 – nett | `$2010/$20D6/$2124→$2504` avbryter vanlige hopp ved klasse 4 uansett ny input. `$1EDF/$1F11/$1F3C/$1F52` stopper alle fire diagonaler ved nettkontakt. Ren opp/ned og ren side går i egne grener. | **Rettet:** diagonal input stopper, i stedet for vertikal prioritet; hopp får nettkontakt også uten sideinput. Dette endrer ikke valgt klatrefart. Slippgrensen krever riktig posemaske, fortsatt åpen. |
| T11 – ligge | `$1E49–$1F29` velger liggestilling; `$2A3E–$2A40` utelukker offer i tilstand `$1A` fra denne kamprutinen. Andre immune offer: 24,15,19,25,27. | Kodebekreftet kampbeskyttelse, ikke generell immunitet mot feller. Oppreisning, inputfase og posekontakt trenger fortsatt kontroll. Historisk manuelt resultat er uklart og blir ikke oppfunnet. |
| T12 – fiender | `$230B–$2404` har retning, avstand, retrett og ulike angrepsvalg. Dørutgang `$2F90/$3001` og ny inntreden er separat logikk; Yamo har også slag. | Brukerens aksept beholdes. Målt R01-utgang/retur beviser ikke full AI. Konstant jakt på spillerens X er ikke kildealgoritmen; dagens AI er fortsatt en adapter. |
| T13 – skadereaksjon | `$2B46` vender offer ved stikk/slag/spark; `$2BA9/$2BCD/$2BF1/$2C15` setter tellere 3/4/12/8. `$29C3` flytter ikke X/Y. Hovedsløyfen kaller først kamp `$1C23`, så aktørbevegelse `$1C29→$179E→$1C5B`: første rekylsteg skjer senere i samme gjennomgang. `$3A6F` er romkode-dispatch, ikke aktørbevegelse. | **Rettet:** kamp før aktøroppdatering, uten et ekstra rekylsteg inne i treffanvendelsen. T13s manuelle aksept beholdes. Full glidning, simultane treff, gren ved negativ helse og Ninja-ekstrasteg er ikke samlet godkjent. |
| T14 – død/nytt liv | `$181B–$1838` trekker liv, setter alle tre helsebytes til 36 og nuller fiendenes inntredentellere. Videre `$1886→$0763` reinitialiserer aktøroppsett og `$188B→$3217` velger romlasting. Fiendeinntreden setter senere egne helsegrenser. | «Hele spillet nullstilles» er for upresist. Amiga laster nå rom og nullstiller NPC-er, men liv/Game Over, dødsforløp, ventetid og alle bevart/nullstilt-data er fortsatt ikke fullført. Ikke fjern alle lanterner ut fra ordet «reset». |
| T15 – lanterner | `$2E55–$2F04` krever supplerende kontaktflagget og riktig cellekode; `$2F04` avviser andre aktører enn Bruce; `$331C` registrerer innsamlingen. `$2F2D` gir 125 til poengrutinen. Slag trenger ingen egen «ødelegge lanterne»-regel. | Brukerens aksept beholdes. Dagens helmaskeflagg + celleskanning er en adapter, ikke hele den originale pose-/cellebehandlingen. 125 poeng er kodebasert; alle treffgrenser er ikke godkjent. |
| T16 – persistens | `$331C` og romlastingens gjenoppretting av lanternerecords er adskilt fra nye aktørtilstander. Nytt liv og ny runde er ulike kodeveier. | Akseptert ved vanlig romretur. Døds-/multiplayer-/rundesekvensen må fortsatt følges fullt før alle persistensregler godkjennes. |
| T17 – progresjon | Romkode, dynamiske celleendringer og `$30D4` bestemmer om en tabellkobling kan brukes. Å ha samlet alle lanterner i ett synlig rom er ikke alltid nok. | De 20 kilderommene erstatter den gamle to-romsbegrensningen. Kontrollert romvalg/22 manglende-lanterne-fixtures er fortsatt ikke naturlig gjennomspilling. Se romrekonstruksjonen. |
| T18 – teknisk | Escape/CLI/start, OCS-tegning, minne og A500-feltbudsjett er Amiga-krav, ikke C64-spillregler. | Gamle beståtte blokkromtester godkjenner ikke dagens rommotor. Tidligere kilde-rommålinger har åpne tids-/Chip-porter. Aktørrettelsene her trenger ny native verifikasjon; gamle rapporter beholdes som historikk. |

## Viktige kampdetaljer som gamle bokstester overså

`$D01E` er en global spritekollisjonslås. `$29D4–$2A1F` danner
aktørkandidater fra bitgrupper; det er ikke en egen matrise med bekreftede
aktørpar. Deretter behandles offer 2,1,0 og kandidatbiter i stigende rekkefølge.
`$4F40` mapper kandidatsprite til aktør og endres ved inntreden/utgang.

Slag/stikk/spark setter angriperens flagg `$01` og vender offeret under innsamlingen.
Helse endres først etter at alle treffflagg er samlet. Derfor kan begge aktører
få treff i samme gjennomgang. Retningsendringen kan også påvirke en senere
klassifisering; «lag alle par uavhengig, bruk så et prioritetsnummer» er heller
ikke en full oversettelse. Ny C64-spritekontakt og denne rekkefølgen må porteres
sammen; nåværende `bl_combat_contact` er fortsatt en sekvensiell prototype.

Fallkvoten i `$4F45,Y` dekrementeres **før** avvisning på tidligere fallflagg
eller offerets angrepstilstand 12/13/17 (`$2B06–$2B2A`). Stikktilstand 22
inngår ikke i den sistnevnte listen. Prototypens test «offer har ingen angrep»
er derfor feil som originalregel. IRQ `$15C2–$15CC` fyller kvoten til 2;
tre-felts kvantisering er fortsatt en egen Amiga-tilnærming.

Fallets første overgang er særskilt: `$1DC4→$1DBC` utfører én Y-forflytning
når en annen ferdig tilstand først mister støtte; senere åpent fall i
tilstand14 går gjennom begge kallene `$1DB9/$1DBC` og flytter to. Det er
ikke en generell akselererende tyngdekraft. T01s aksept gjelder sidestyringen
i det testede fallet, ikke hele overgangs-/landingsforløpet.

Også X-grensene må leses før og etter operasjonen: `$1E86` tillater rå X13
og dekrementerer så til12, altså skjerm-X0. Høyresiden `$1EC4` kan øke162
til163, altså skjerm-X302. Prototypens minsteklemme2 og reaksjonsklemme4–314
er ikke disse kildegrensene. Dette føres som et eget aktøradapteravvik;
svart kontakt/bevegelseshistorikk kan begrense reell plassering ytterligere.

Vellykkede angrep setter også angriperens venting/restitusjon (`$2B58–$2B98`).
Hjelperen `$10D0` leser tidsbyte `$88`; den er **ikke en tilfeldig generator**.
Bruce får fire handlingsventinger og restteller 3,8 eller10 ved tidsbyte
henholdsvis <25,25–31 eller≥32. Dette forklarer hvorfor en målt gjentakelsestakt
uten treff ikke skal brukes som universell takt etter vellykkede treff.

### Kandidatanomali ved terminalt falltreff

En kontrollert inngang med offerhelse 4, normal fallkontakt og fallflagg gir
`$2C13→$2C24→$2C51→$2BF9`. Den samme fallbiten behandles igjen, med gjentatte
helsetrekk til byten blir ikke-negativ. Fixture-resultatet er helse 125 og
tilstand27, ikke prototypens umiddelbare nederlag. Dette er faktisk utførte
kandidatbytes, men **ikke et observert naturlig C64-forløp**. Kandidatens utgave,
kjøretilstand og mulig betydning i full maskin må undersøkes før vi omtaler
dette som original spillregel. Det gamle utsagnet «all negativ helse gir
samme nederlag» er derfor trukket tilbake som full kodekonklusjon.

## Leveranse og gjenværende arbeid

Motorrettelsene er begrenset til nettinput/-grep og rekkefølgen kamp/aktøroppdatering,
med ett første rekylsteg i aktørbevegelsen. Koordinatkommentaren er rettet til sprite-venstre/bunn+1.
Ingen kunst, klatrehastighet eller nye kampprioriteter er innført.
`test-core.ps1` kontrollerer disse adapterrettelsene og eksisterende romforløp;
de 61 kildefixture-kjøringene er separat evidens. De gamle blokkromstestene
er historiske og brukes ikke til å fastsette C64-regler.

To native CLI-kjøringer på PAL A500 OCS/Kickstart1.3/512+512 fullfører
6000 felt hver og matcher verten:62 treff,6 fiendenederlag,10 inntredener,
2 dødsfall/respawn for Bruce og sluttposisjon4/196. Hver rapporterer2
tidsavvik med maksimalt to PAL-perioder og28 224 byte sammenhengende Chip.
Den strenge kjøreren feilet reservemålet49 152; diagnoseoppføringen omgjør
ikke dette til en bestått minne-/tidsport. Hele rominspeksjonen er ikke kjørt
på nytt etter aktørendringene. Vanligbygg er kompilert og CLI-kommandoen
`start` oppdatert; den interaktive emulatoren er ikke startet på nytt.
Resultater: [avgrenset leveranse](../reference/validation/test-audit.json).

Åpne motorfeil er nå tydeligere avgrenset: fast pose2, boksbasert kamp,
sekvensiell treffanvendelse, restitusjon, deler av AI/aktørhistorikk og komplett
nytt-liv-forløp. De skal løses fra koden, ikke ved å justere testen til prototypen.
