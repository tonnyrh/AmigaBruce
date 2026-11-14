# Liv, død, rom6 og testmeny

25. oktober 2026. Denne rettelsen følger de faktiske bytene i
`.reference/c64/work/untrained-memory.bin`, SHA-256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Remember-kandidaten er fortsatt ikke bekreftet som den urørte1984-utgaven.

## Død og gjenværende forsøk

- `$3057-$3059` ber om **effekt `$8C`**, ikke `$88` slik den tidligere
  lydtabellen feilaktig sa. `$3068->$407D` setter Bruce i tilstand25 med
  teller16. `$1CB5` omgår vanlig veggrestitusjon under denne tilstanden.
- `$216B-$217A` lar Bruce stå stille gjennom de16 aktøroppdateringene.
  `$27B8-$27BE` velger kildepositur8. Ved teller1 går koden til `$1818`.
  Amiga viser nå denne posituren og viderefører den eksisterende
  kildebaserte effekten gjennom Paula. SID-klang og brukerens lytteprøve
  må vurderes separat fra at riktig sekvens er utløst.
- Kampdød er et annet forløp: `$2C24-$2C4F` velger tilstand19/teller12,
  og `$2D55-$2D79` venter på avsluttet reaksjon før livtrekk. Det er ikke
  lagt på et nytt generelt skrik eller en ekstra16-stegs pause i denne grenen.
- `$1826` trekker én fra `$28`. Negativ verdi går til Game Over; ellers
  gjenopprettes helse, aktører og rom. Prototypens ekstra96-stegs venting
  etter spillerens reaksjon er fjernet. Oppsamlede lanterner beholdes.
- `$0FBC-$0FC7` gir fire reservefall, eller ni når menneskelig Yamo velges.
  **FALLS04 betyr fire gjenværende fall etter det pågående forsøket**, altså
  fem forsøk ved start. Dette er originalens telling. HUD viser også aktiv
  spiller. Kildens objektbaserte livstillegg synkroniseres med telleren;
  full poeng-/bonuslogikk er fortsatt en separat portering.

## Henging ved venstre avsats i rom6

`25.10.2026II.uss` er lest uten endringer. SHA-256:
`85eb10b47ee05ca0275ff7aa46abf844c81749764d207aca1a9203dce8eeab3b`.
Kilderam ble funnet ved `$C55734`, med rom6 og siste romankerpunktsposisjon
`(44,81)`. Snapshotet inneholder Amiga-kode og tilstand, ikke en C64-kjøring
eller en logg over inputen som feilet. Det lastes derfor ikke som ny spillkode.

Den gamle Amiga-motoren søkte alle mellomliggende Y-posisjoner etter et
landingspunkt. I den kontrollerte venstresekvensen stoppet den på Y79,
mens originalkoden fortsatte til Y80. Det kunne gi støtte på siden av veggen.

`$2022/$2105/$2150` avbryter et nedadgående hopp på aktuell solidkontakt
før flyttehjelperne. `$1D84-$1DBF` vurderer det nåværende kontaktpunktet
ved fritt fall; den søker ikke et mellomliggende landingspunkt. Bruce bruker
dessuten kroppsklassen `$A7` og frigjøringstelleren `$B0`, mens NPC-er har en
egen landingsgren med én sidehjelper. Tap av støtte behandles før ny input,
slik `$1DCA->$1DC4` gjør. Disse grenene erstatter nå landingssveipet.

## Kage og Yamo gjennom vegger

Det var to feil som forsterket hverandre:

1. Normal NPC-bevegelse hoppet over `$1C5B`-grenens svartkontakt og
   tilbakerulling. `$17BE-$17DB` kaller denne grenen for alle aktive aktører.
2. Kontaktkontrollen brukte Bruce-masker også for fiendene. `$29AB-$29BA`
   velger maskebank fra `$95` via `$59A5={0,140,70}`. De faktiske aktørene
   bruker Bruce0, Yamo70 og Kage140 lagt til grunnposituren. Deler av Kages
   masker og breddeflagg manglet i det tidligere datauttrekket.

Uttrekket omfatter nå maskene gjennom `$CB3F`, breddeflaggene og banktabellen.
Kontaktmaskenes pekertabeller er `$1167/$1239`; breddeflaggene følger
`$5CBF` med den komplette aktørindeksen, ikke bare grunnposituren.
Gangens maskepositurer veksler som i `$28B3-$2902`. NPC-ens faste gangfart
styres separat fra posituren, slik at nullstilling av fart ikke feilaktig
velger ståmasken før kontakt. Veggrestitusjon vises for begge fiendene.

## Hovedmeny og Shift+D

Hovedmenyen har F3 for én/to vekslende Bruce-spillere og F5 for datastyrt
eller menneskestyrt Yamo. Ild eller Return starter, Escape går til AmigaDOS.
F10 under spilling åpner menyen og lar et nytt spill startes.

To spillere får hver sin romposisjon, reservefall, lanterner, romtilstand og
poeng. `$183B-$1884` fastsetter veksling etter et mistet liv mens den andre
spilleren har forsøk igjen; `$1856-$1870` bytter `$28..$43` og gjenoppretter
lanterneoppføringer. `$16A2-$1701` velger motsatte porter ved spillerskifte.
På Amiga bruker spiller1 joystick2 og spiller2 joystick1; Yamo bruker den
andre porten når menneskestyring er valgt. I WinUAE kan
`amiga-run.ps1 -TwoJoysticks` gi tastaturjoystick på begge portene (`kbd1`
som før, `kbd2` på museporten). Dette er et separat valg fra to Bruce-spillere.
Menneskelig Yamo bruker fortsatt deler av aktøradapteren; full input-/AI-
tilstandsparitet er ikke bekreftet av menyen.

**Shift+D** i hovedmenyen åpner testvalgene:

- F1: uendelige reservefall. Dette hindrer livtrekk, men lar Bruce dø.
- F2: udødelighet mot kamp og faredød.
- F3 slår brettvalg på eller av. F9/F10 blar mellom rom 1–20 i menyen og under spilling.
- F5 tar deg tilbake til hovedmenyen. Med brettvalg på kreves Fire for å starte.
- Fire bekrefter et rom etter blaing. F8 åpner menyen når brettvalg er på.

Brettvalg fullfører nå lanterner i lavere romnumre før valgt rom lastes.
Valgt rom beholder sine lanterner; poeng og reservefall gis ikke for
cheat-innsamlingen. Se [cheat-progresjon](CHEAT_PROGRESS.md), inkludert
spillerlagring og C64s nullteller-plassholdere.

HUD viser TEST og `FALLS INF` ved uendelige fall. Alle overstyringer er av i
et normalt, nytt program. Valgene og den nye menyutformingen er uttrykkelige
test-/Amiga-funksjoner, ikke påstander om at C64 hadde disse funksjonene.

## Kontroller og avgrensning

`test-session.ps1` sammenligner160 døds-/livsteg,140 rom6-hopp-/fallsteg,
120 NPC-veggsteg og1280 maskekontakter i20 rom med faktisk6502-kode.
Den bruker kontrollerte tilstander og ekte rom-/maskedata. De utvalgte
bevegelses- og maskevektorene inngår også i det avgrensede native regresjonssettet
(`BL_SESSION_WALL_CASES=324`:64 kontaktvektorer +260 rutesteg).

Hostkontrollene dekker også Game Over, uendelige liv, udødelighet,
romvalg og uavhengige lanterner/poeng etter to spillerskifter. De beviser
ikke naturlig gjennomspilling, full kampkontakt, hele NPC-maskinen eller
alle aktørfaser. Native meny-/minne-/timingresultater registreres separat
i `reference/validation/session-walls-delivery.json`.

To6000-felts CLI-kjøringer på PAL OCS/68000/KS1.3/512+512 består
regresjonskontrollene, OS-retur og minnekravet:85408 byte sammenhengende Chip
RAM gjenstår i begge. Det er446/447 forsinkede oppdateringer og79/77 tapte
lydfelt, så streng kadens er fortsatt åpen. Den siste rettelsen av INF-teksten
er bare i vanligbygget. Autotestens kode, initialiserte data, BSS-størrelser,
relokasjoner og symboler er kontrollert identiske; ett ubrukt utfyllingsbyte
etter ELF-ens17-byte `.data` varierer ved konvertering. Sammenligneren tillater
bare de tre ubrukte justeringsbytene i dette segmentet, og bevarer råopptakets
opprinnelige kilde-/binæridentiteter.

Manuell nytest: bruk et nytt spill, Shift+D og rom6; prøv hopp mot venstre,
Kage/Yamo mot svarte vegger, faredød med lyd/stillstand og siste reservefall.
Gamle USS-filer inneholder den gamle eksekverbare koden.
