# Plan: optimalisering av Bruce på Amiga 500

27. oktober 2026. Første OP0-målebane og OP2-pilot er implementert og målt.
Se [første leveranserapport](AMIGA_OPTIMIZATION_REPORT.md). Resten av planen
og sanntidsakseptansen står åpne; tabellen nedenfor bevarer utgangspunktet.

Målet er å få den kildebaserte motoren innenfor PAL A500 OCS / 68000 /
Kickstart 1.3 / 512 KiB Chip + 512 KiB slow, med bevart C64-oppførsel.
Først måles kostnadene pålitelig. Deretter erstattes de dyreste delene av
den instruksjonstro oversettelsen med små, kildeavstemte C-/68000-rutiner.
Spillfart, fysikk og fienderegler skal ikke justeres for å skjule treg kode.

## Utgangspunkt og mål

Gjeldende baseline er [native sluttrapport](../reference/analysis/actor-chain-2026-10-26/native-final.txt),
[normal klokkekontroll](../reference/analysis/actor-chain-2026-10-26/normal-clock.json)
og [filbundet leveranse](../reference/validation/source-world-delivery.json).

| Måling | Nåværende resultat | Betydning / mål |
| --- | --- | --- |
| Normal rom 1, kort klokkeprøve | 352 PAL-felt og 70 spillsteg mellom prøvepunktene, ca. 5 felt/steg | Tilbake til kildens ordinære 3 felt/steg, uten å hoppe over tilstander. Prøven er ikke statistikk for hele spillet. |
| Kontrollert native reprise | 1 200 ytre løkker / 400 logiske steg | Ett injisert kildefelt per løkke; dette beviser ikke normal sanntidsfart. |
| Verste registrerte presentasjonsgap, uten eksplisitt bildeopptak | 8 PAL-felt | Eksisterende strenge feltport skal bestås; den skal ikke slakkes. |
| Registrerte løkker med feltoverskridelse | 718 | Skill ytre løkker fra faktisk medgåtte PAL-felt i ny rapport. |
| Verste lydservice | 114 rasterlinjer, ca. 36 % av et registrert 313-linjers felt | Lyd er en viktig målekandidat, ikke en bekreftet forklaring på alle overskridelsene. |
| Tapte lydserviceticks i reprisen | 541; største servicegap 2 felt | Ingen manglende serviceticks i den endelige sanntidskontrollen. |
| Største ledige Chip-blokk i native testen | 52 632 byte | Behold minst eksisterende port på 49 152 byte, og mål også slow RAM, stack og fragmentering. |
| `actor_code` i normal linker-map | 145 288 byte av 187 142 byte `.text` | Stor instruksjonstro funksjon med virtuell register-/flagg- og returhåndtering. Kandidat for spesialisering; størrelse alene beviser ikke kjøretid. |
| Kildekontroller | 3 034 bytevise RAM-/registerkontroller; fem integrerte scenarier | Behold og utvid med grensetilfeller for hver endret rutine. |
| Native logikkontroller | 53/53, pluss korrekt OS-retur | Bevares etter relevante motorendringer. De godkjenner ikke rasterfase eller naturlig gjennomspilling. |

Den korte normalprøven antyder at tiden per steg må ned fra omtrent 100 til
60 ms i denne situasjonen: rundt 40 % mindre samlet tid. Dette er et
orienteringspunkt, ikke et løfte om gevinst eller en full spillmåling.

To viktige svakheter i dagens diagnose må avklares først:

- `stage0..5` er ikke komplette målinger av én og samme løkke. Når tegning
  holdes tilbake, kan senere stage-verdier stamme fra en tidligere løkke.
  Sluttrapportens `stage1=1030` og `stage2=229` kan derfor ikke brukes som
  additive kostnader eller som en sikker rangering av flaskehalser.
- `room_load_max_gap=19671` inneholder innledende test-/oppstartsarbeid og
  er ikke målt vanlig rombyttetid. Bildeopptakets 260 felt er også en egen
  diagnostisk kostnad. Profilfeltene er null i denne ikke-profilerte kjøringen.

## Fast kontrakt gjennom arbeidet

Referansen er de uendrede bytene i `.reference/c64/work/untrained-memory.bin`,
SHA256 `092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Remember/T64-kandidaten er fortsatt ikke bekreftet som valgt urørt 1984-utgave.

- Bevar rekkefølgen `$1BC2–$1C32`: rom, kontakt, objekter, kamp,
  aktøroppdatering, spritebygging og opprydding med tilhørende tjenester.
- Bevar tellere, byteoverløp, treffinnsamling før skade, SEI/CLI og
  kilde-RAMs mellomresultater. Scratch- og stackskriving kan påvirke senere
  lesing, blant annet `$1159`; de kan ikke fjernes som «ubrukte» uten bevis.
- Bevar selvmodifiserte operander og ikke-lokale returforløp. En vanlig
  native C-retur er ikke automatisk ekvivalent med kildens stackbehandling.
- Mellomlagring kan spare beregninger, men skal ikke bestemme nye
  kollisjoner, færre AI-oppdateringer, andre angrepsvinduer eller nye hoppregler.
- Ikke øk maskinkravet, bruk 68020-instruksjoner, slå av syklusnøyaktighet
  eller kreve mer Chip RAM for å få et bedre måleresultat.

Den frosne maskinkoden og dens disassembly er fasit. Eksisterende native
kode er en implementasjon som skal kontrolleres, ikke en ny fasit.

## Prioritert arbeidsrekkefølge

### OP0 — Frys baseline og få pålitelig profilering

**Første arbeidsøkt.** Lag en separat baseline med kilde-/byggidentiteter,
rårapporter og inputruter. Eksisterende bygg og godkjente rapporter beholdes.

Instrumenter den faktiske kildebanen i `amiga/main.c` og `core/c64_rooms.c`:

- felt/IRQ, VIC-lås, input og innhenting av medgåtte felt;
- romløp, `$5212` kontakt, `$2E39` objekter, `$29C3` kamp;
- `$179E/$1C5B` aktører og `$2584/$25E2` spritebygging/registerpublisering;
- lyddekoder, tone-/bølgeoppslag, DMA-bufferskriving og Paula-publisering;
- projeksjonen i `core/session.c`, bakgrunnsendringer, restaurering av
  gamle figurer, ny figurtegning, blitterventing og venting på VBlank;
- romlaster, palett-/tegncache og animasjonscache, målt separat fra testkontroll.

Bruk gjeldende løkke-ID, gyldighetsmaske, antall kall og individuelle
start/sluttstempler. Rapporter både inkluderende og ekskluderende tid:
en lyd-/feltservice inne i kontakt må ikke telles dobbelt i totalen.
Skill arbeid, venting, oppstart, lasting, testfixtures og opptak.
Mål profileringens egen kostnad; endelig akseptanse kjøres uten profilering.

Samle median, p95, p99 og absolutt topp, med rom, aktørtilstander, kilde-PC/
rutine og antall endrede celler. Tidslinjen må forklare innholdet i
`held_image_fields`, også den registrerte sammenhengende rekken på 483
løkker. Skill et korrekt uendret bilde fra et nytt bilde som aldri blir vist.
Avklar også `canvas_residue_bytes=87`: det kan ikke godkjennes som null
figurrest bare fordi bakgrunnskontrollen gir null avvik.

**Leveranse:** en konsistent kostnadsrangering og reproduserbare ruter på
normal planlegging og kontrollert reprise. Den dyreste målte komponenten
velges som neste pilot; nedenstående rekkefølge er utgangspunktet.

### OP1 — Reduser kostnaden i den instruksjonstro motoren

Filer: `tools/build_c64_rooms.py`, `tools/build_c64_actors.py`,
generert `core/c64_actor_programs.h` og kontrollerte hjelpere i `core/c64_rooms.c`.

1. Velg én ofte kalt, kostbar rutine fra OP0. Oversett den til en liten
   direkte C-rutine med identiske RAM-/register-/stackeffekter. Start med
   kontakt-/sprite-/klassehjelpere dersom de dominerer; ikke skriv om hele
   aktørmaskinen på én gang.
2. Spesialiser sikre bladkall slik at hvert lite JSR ikke trenger ny
   inngangsdispatch i den store `actor_code`-funksjonen. Behold den virtuelle
   stackens observerbare skrivinger og original retursemantikk.
3. Slå sammen korte, dokumenterte instruksjonssekvenser. Analyser når
   virtuelle flagg faktisk leses før neste overskriving. Alle eksterne
   kontrollpunkter, ukjente kall, PHP/PLP og relevante I/O-grenser behandles
   konservativt som observerbare. Ikke fjern flagg bare fordi en demo fungerer.
4. Vurder deling i mindre native funksjoner når måling og disassembly viser
   færre registerspill og dispatchkostnader. Ikke-lokale returer får fortsatt
   eksplisitt håndtering.

`$1159/$199F/$478D/$4794` er allerede spesialisert i generatoren.
`$26A0/$52AD/$537E` har allerede raske løkker. Ny gevinst må måles mot
dagens utgave; disse tidligere endringene skal ikke telles som nytt arbeid.

**Port:** alle relevante kildegrener gir samme RAM, registre og kontrollgrense;
rutinen er målbart raskere på 68000 uten uakseptabel kodevekst.

### OP2 — Gjør arbeid som skjer hvert PAL-felt billig

**VIC-lås og felt/IRQ:**

- Profilér `source_actor_field`, `source_vic_latch` og `source_vic_cache`
  hver for seg. Radcache, bytekontroll én gang per sprite/felt og skift i
  stedet for deling med 1/2 er allerede på plass.
- Vurder å gjenbruke forrige kollisjonsresultat når alle effektive registre,
  posisjoner og bitmapinnhold er identiske. Det gjenbrukte resultatet skal
  fortsatt akkumuleres i låsen, også etter at en tidligere lesing har tømt den.
- Vurder endringsversjoner fremfor gjentatt lesing av 63 bitmapbytes, men
  bare når alle skrivebaner er dekket: spritekopiering, rom-/prosjektilkode,
  init, bank-/pekerbytte og reset. Manglende invalidering er en feil, ikke en gevinst.
- Behold alle åtte sprites, kildepiksler, ekspansjon og global latchsemantikk.
  Ikke erstatt dette med figurbokser eller en antatt matrise av aktørpar.

**Lyd:** `core/source_audio.c`, `core/source_dma.c`, `amiga/source_audio.h`.

- Mellomlagre frekvens- og bølgeoppslag med full nøkkel når parametrene er
  uendret. ADSR-/gatebehandling skal fortsatt gå hvert påkrevd felt.
- Mål 32-bits delinger/multiplikasjoner i generert 68000-kode. Bruk små
  eksakte tabeller eller dokumentert heltallsaritmetikk der det lønner seg.
- Faste DMA-buffere, gjenbruk av uendret bølge og hopping over bufferkopi
  for stille stemmer er allerede implementert. Mål resterende kostnad.
- Ingen nye lange samples, færre stemmer, endret pitch, kortere toner eller
  endret effektprioritet. Bevar de eksisterende kildebaserte parameterforløpene.

**Port:** samme latchresultat og RAM-effekter; samme lydregistre/parametre og
DMA-bilder i kontrollerte sekvenser, med redusert feltkostnad.

### OP3 — Vis endringene uten unødvendig kopiering eller sulting

- Behold statisk bakgrunn og eksisterende buffere. Kopier bare faktisk
  endrede celler/ord/figurgrenser. Ikke legg til en ny full Chip-bakgrunn.
- Mål og fjern dobbel restaurering/kopiering. Prøv rettet 68000-kopiering
  mot blitter for små og store områder, med reell OCS-/Paula-DMA aktiv.
- Gjør venting på blitter nyttig ved å betjene trygge felt-/lydoppgaver,
  uten reentrant aktør-/kampkjøring eller lesing av uferdig buffer.
- Den eksisterende roterende køen og prioriteten for feller beholdes.
  `hold_image` får en dokumentert grense for nye synlige endringer; det
  skal ikke kunne holde dem tilbake på ubestemt tid.
- Mål fra publisert kildetilstand til synlige piksler. Elektriske feller,
  bomber og angrepspositurer må ikke bli synlig forsinket for å spare CPU.

**Port:** samme kildebilde og korrekte overlegg, ingen uforklarte rester,
stabile VBlank-publiseringer og ingen sulting av nye tilstander.

### OP4 — Stram inn planlegging, input og avlesning til visningen

- Profilér normal `source_game_service` med faktisk PAL-tid. En rask
  kontrollert reprise erstatter ikke normalmodusens innhenting av felt.
- Behold kildens tre-felts spillrytme og feltbaserte tellere. Ikke nullstill
  et etterslep eller hopp over IRQ-/spillsteg for å pynte på rapporten.
- Dokumenter joystickens avlesningspunkt. Mål korte ildtrykk, holdt opp og
  retningsskifte ved landing. Ikke legg inn OR-låsing eller nye inputvinduer.
- Kartlegg IRQ-avhengigheter før arbeid eventuelt fordeles i flere bolker.
  Bevar SEI/CLI, rekkefølge og synlige mellomtilstander; ikke del kamp eller
  AI vilkårlig mellom felter.
- Reduser unødvendig projeksjon i `source_session_view`: les bare det
  visningen trenger, og oppdater lanterne-/progresjonsvisningen ved faktiske
  mutasjoner. Inkluder død, turbytte, ny runde og testhopp i invalideringen.
  Kilde-RAM forblir autoritativ, uten en ny konkurrerende spilltilstand.

**Port:** korrekt input-/hendelsesrekkefølge, ingen tapte feltellere og
ordinær tre-felts kadens i normalmodus i de kontrollerte aktive scenene.

### OP5 — Bruk 68000, kompilator og minne målrettet

- Undersøk disassembly for faktiske varme løkker. Prøv `-O2` på utvalgte
  små funksjoner mot dagens `-Os`; ikke øk hele motoren ukritisk til `-O3`.
- Bruk 68000-assembly bare der en målt varm løkke fortsatt er for dyr i C.
  Aktuelle kandidater er bitmasker, planar-konvertering og korte kopieringer.
- Behold 16-/32-bits typer og dagens eksplisitte ABI mellom `-mshort`-
  modulen og øvrig kode. Global endring til `-mshort` inngår ikke i planen.
- Mål kode, rodata, BSS, stack og begge RAM-typene. CPU-kode/tabeller hører
  hjemme i slow RAM så langt det er mulig; DMA-kilder må ligge i Chip.
  Kontroller faktisk plassering og fallback, ikke bare total ledig RAM.
- Vurder størrelsen på eksisterende tabell-/tegncacher ut fra treffrate.
  Eksempelvis bruker tegncachen 40 KiB CPU-RAM. En mindre cache kan frigjøre
  plass til raskere kode, men godtas bare ved bedre samlet tid i alle relevante rom.
- Verifiser hva linkerens seksjonsopprydding allerede fjerner. Ikke anta
  at sletting av gamle adapterfunksjoner gir mer fart eller mye mindre EXE.

**Port:** netto tidsgevinst med uendret maskinkrav og dokumentert minnemargin.

### OP6 — Rombytte og oppstart, etter den løpende spillkostnaden

- Mål original laster/init, tegn-/palettarbeid, bakgrunn og animasjonscache
  separat fra opptak, sammenligning og native fixtures.
- Behold tidligere renderer-gjenbruk bare ved gyldig innholdsnøkkel.
  Kildens init, dør-/lanterneendringer og NPC-/livseffekter må fortsatt kjøres.
- Undersøk gjentatt førstegangsoppsett i intro/meny/start, uten å gjenbruke
  feil spilltilstand eller omgå `$0743/$0F72` etter at spillervalg er gjort.
- Bruk eksisterende buffersett. Målet for rombytte bestemmes fra ren måling
  og kandidatens kode/forløp, ikke den misvisende oppstartstelleren.

**Port:** raskere, korrekt rombytte og oppstart med uendrede rommutasjoner.

## Tidsbudsjett og endelig akseptanse

Et PAL-felt er omtrent 20 ms; mål mot den faktiske målte feltlengden.
Følgende er et foreløpig arbeidsbudsjett for et travelt felt, ikke nye
spillregler eller en lovet ytelse. OP0 må vise hva som kreves for å nå det.

| Arbeid | Mål i et travelt felt |
| --- | ---: |
| Felt/IRQ, input og VIC-lås | opptil ca. 2 ms |
| Alle tre lydstemmer og publisering | opptil ca. 3 ms |
| Spillsteg når det forfaller | opptil ca. 7 ms |
| Opptegning/kopiering | opptil ca. 5 ms |
| Reserve | ca. 3 ms |

Gjennomsnitt over tre felt kan skjule en overskridelse i ett felt. Derfor
kontrolleres både samlet spillsteg, travleste felt, lydservice, input og
tid til synlig oppdatering. Budsjettet er et optimaliseringsmål; den
eksisterende akseptanseporten skal ikke flyttes for å godta en treg utgave.

Arbeidet avsluttes med:

1. Relevante rutinekontroller mot de faktiske C64-bytene, deretter hele
   `test-parity.ps1` ved samlede motorendringer. Behold alle 3 034 kontroller,
   fem liv-/spillermodusscenarier, lyd- og DMA-kontrollene.
2. Native kontroll av berørte rutiner og de 53 motorfixturene. Test på
   68000/OCS/KS1.3, både CLI og ADF. Ingen ekstra RAM eller endret CPU-fart.
3. En testpakke som uttrykkelig bruker **den nye kildebanen** i alle 20 rom.
   Gamle romturer eller adaptertester kan ikke godkjenne denne motoren.
   Ta med rom 1 med begge fiender, kanter/hopp/nett i rom 5–6, alle bomber
   i rom 8, nederste felle og nett i rom 10, prosjektiler/sluttrom i 19–20,
   turbytte, faredød og ny runde.
4. To uavhengige, minst 6 000 felter lange sanntidskjøringer i normal
   planlegging, uten profilering eller opptak i det målte området. Oppstart,
   romlasting og opptak merkes og får egne tall. Ingen tapte lydserviceticks,
   ubegrenset innhenting eller uventet tregere spillsteg godtas.
5. Bestått eksisterende strenge feltport, korrekt VBlank-publisering,
   uendrede kildeutfall og minst 49 152 byte sammenhengende Chip-reserve
   gjennom avtalte belastningsscener. Oppgi også største slow-blokk og stackmargin.
6. Naturlig sammenligning og fysisk A500-kontroll som egne akseptanser.
   Kodetester gir ikke sertifisert originalutgave eller rasterparitet.

Hver optimalisering leveres som en liten, reverserbar endring med kildeadresser,
før/etter-tid, kode-/RAM-kostnad og kontrollresultat. En patch uten målt
nettogevinst tas ikke inn i ytelsesbanen. Full referanseimplementasjon og
diagnostikk beholdes i testbygg/vertsverktøy uten å doble produksjonsmotoren
i det begrensede A500-minnet.

## Første konkrete leveranse

Gjennomfør OP0 og én målt pilot fra OP1 eller OP2. Lever profilrapport,
uendret kildeutfall, dokumentert faktisk gevinst og ny prioritering.
Deretter tas neste største kostnad. Ingen bred omskriving eller ny kunst/
lydproduksjon starter før denne arbeidsmåten har vist at den virker.
