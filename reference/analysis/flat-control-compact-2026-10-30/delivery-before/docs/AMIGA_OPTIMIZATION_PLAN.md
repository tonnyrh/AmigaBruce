# Plan: optimalisering av Bruce på Amiga 500

27. oktober 2026. OP0-målebane, OP2-pilot, OP1-kontaktpilot og en
ny målt 68000 VIC-runde er gjennomført. Visningssultingen i OP3 er rettet
ved beslutningspunktet. Se
[første leveranserapport](AMIGA_OPTIMIZATION_REPORT.md) og
[kontakt-/visningsrunden](CONTACT_OPTIMIZATION.md) og
[68000-runden](VIC_NATIVE_OPTIMIZATION.md) og
[synlighet/kontaktforberedelse](YAMO_VISIBILITY_PERFORMANCE.md) og
[lokale kontaktregistre](CONTACT_REGISTERS_OPTIMIZATION.md). Resten av planen
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

Gjeldende større native motorløft: [rutiner, målinger og kontroller](NATIVE_ENGINE_OPTIMIZATION.md).

Videreført med [kontakt-/VIC-kjerner](CONTACT_KERNEL_OPTIMIZATION.md), inkludert eksakt spillstegstopp og fortsatt åpne lyd-/tidsporter.

Videre optimalisering: [pakkede kontaktmasker, 28. oktober](PACKED_MASK_OPTIMIZATION.md).

Siste kontaktløft: [pekeroppsett, klassifisering og kildebasert fellerettelse](CONTACT_PREPARATION_OPTIMIZATION.md).

Neste målte VIC-løft: [gjenbruk av uendret pikselkontakt på 68000](VIC_REPEAT_OPTIMIZATION.md).

29. oktober: [kontaktsegment-forsøk](CONTACT_SEGMENT_OPTIMIZATION.md) ga1428/1431/1428 PAL-felt mot1428 før. Ingen av de tre variantene er innført. Neste kandidat er en større sammenhengende kontaktkjerne ved$5212-$52AC; servicepunkter og C64-resultat skal fortsatt beholdes.

29. oktober, videreføring: [native spritekopiering](SPRITE_COPY_OPTIMIZATION.md) gir23,14 % lavere kostnad per kall.53 native fixturer, full vertssammenligning og CLI/ADF består; total1428->1429 felt gir fortsatt ingen dokumentert gevinst i samlet tempo. Neste analyse følger C64s$48-venting ved$1C32 og Amigaens vertikalblank-/tegneplanlegging, med samme kildehastighet som krav.

29. oktober, skjermplanlegging: [avgrenset forsøk og avvisningsgrunn](PRESENTATION_EXPERIMENTS.md). 1429->1415 PAL-felt, men tapte lydtikker25->44. Endringen er ikke innført. Verifisert produksjonsmotor er beholdt; CPU-/Blitter-overlapp og lydpublisering er neste målepunkt.

29. oktober, OP3/OP6: [sammenhengende trappefaser og renere romoverganger](RENDER_COHERENCE.md). Kildefasen bevares; synlig tegning samles i skjult buffer. OP5-diagnostikk deles i separate kontrollbilder uten lavere minneport. Brukerens stoppregel er gjennomgang av OP0-OP6; det opprettes ikke en ny, ubegrenset liste med optimaliseringsrunder.

29. oktober, OP4-lesebane: [samlet levende lanterneinnhenting](VIEW_PROJECTION_OPTIMIZATION.md). Visningskostnad55,839->48,394 linjer/kall;1432->1426 PAL-felt for360 steg i det uprofilerte paret. Ingen progresjonscache eller kildeendring. Enkeltmaskeforsøket var tregere og er ikke innført. OP4s input-/IRQ-avlesning og gjenværende OP0/OP5/OP6-kontroller behandles videre innen den opprinnelige listen.

29. oktober, OP2/OP5: [enkeltlesing av kalde spritebytes](VIC_CACHE_OPTIMIZATION.md). To uprofilerte kjøringer gir1422 felt/360 steg mot1426 før, med9 mot17 tapte lydtikker. Ingen endret VIC-regel eller ny gjenbruk. Streng sanntid og de resterende OP-portene er fortsatt åpne.

OP6, registrert funn før retting: hovedmenyen ble tegnet i synlig buffer.
ADF-opptak ved lydstart kunne vise bare en del av tittelen. Ferdig meny
skal kreve full pikselidentitet i oppstartsprøven; skjult menypublisering
og meny->spill-overgang behandles videre innen OP6.

29. oktober, OP6: [skjult menytegning og generell startbuffer](MENU_PUBLICATION.md).74 native UI-bilder,30 endrende skjulte arbeidsbilder, uendret64KiB kilde-RAM under menyvalg og start fra begge frontposisjoner. Ingen ekstra framebuffer. Ny timing-/stack- og full akseptanse gjenstår; dette avslutter ikke OP0-OP6.

29. oktober, OP0/OP5: 512-plassers tegncache med VIC-oppslag er målt i en sammenhengende, kontrollert 20-romstur (120 kildesteg per rom). Samlet arbeid falt2846304->2839756 HSYNC-linjer, men rom15 økte12890 linjer og lydtap består. Kandidaten er arkivert og de fire kilde-/byggfilene er gjenopprettet til den validerte meny-/renderbyggen; normal EXE/ADF er uendret. [Beslutning og identiteter](../reference/analysis/cache-sizing-2026-10-29/decision.json). Turen bærer kildehistorikk mellom rom og er ikke naturlig progresjon eller et isolert rutinebevis. Den eldre korte elapsed-telleren inkluderer tittel og spill; bruk [avklart tellerscope](../reference/analysis/cache-sizing-2026-10-29/counter-scope.json), ikke ren spilltid, ved tolkning av gamle tall. Rom20 har flest tapte lydtikker og er neste profilerte belastning. OP0-OP6 og sanntidsportene er fortsatt åpne.

30. oktober, OP1/OP5-kandidat: [direkte kildefargeskriving i rom20](FINAL_COLOR_OPTIMIZATION.md).7424 originalbyte-kontroller og192 sammenligninger av renderer-tilstand består. Første R20-par gir660->574 målte totalfelt/120 kildesteg og178->82 tapte lydtikker. Normalbygget er ikke erstattet mens allroms-/leveransekontroll pågår.53 native motorfixturer og1200 repriseløkker består med52632 byte største Chip-blokk; sanntidsporten bestås fortsatt ikke. Det separate 20-roms målebygget fjerner bare en ubrukt diagnoseopptaksallokering, beholder49152-byte-porten og endrer ikke produksjonsallokering eller normal main.

30. oktober, OP1/OP5 leveranse: V3 av [fargeskriveren](FINAL_COLOR_OPTIMIZATION.md) er bygd og kontrollert i normal EXE/ADF. V1/V2s R15-regresjon er arkivert. V3 gir13,236 % kortere R20-intervall og1,275 % mindre samlet arbeid over20 rom; enkelte intervaller, spesielt R10+1,117 %, øker. Alle20 diagnoseintervaller beholder minst69016 byte Chip; ordinære53-fixturer har52632. To R01-prøver gir1425 felt/11 lydtap, mot historisk1430/9; lokal lydservice er fortsatt uavklart. Ingen strenge tids-/IRQ-/stack-/maskinporter lukkes på dette grunnlaget. Ingen ekstra produksjons-BSS; ny .text+92 byte.


30. oktober, OP3/OP6: [kontrollert Copper-publisering](BUFFER_PUBLICATION.md)
er levert i normalbyggen. Normal kildekode og binær er beholdt gjennom
påfølgende separate forsøk. Alle 20 rom har sikre publiseringsprøver;
rom-12-/dødsbildene er koherente. Dette er en stabilitetsretting, ikke en
påstått gevinst i tempo. Tidligere samlede binærbindinger må oppdateres før
de kan brukes som akseptanse av den nye renderer-versjonen.

30. oktober, OP0/OP5: [to lydoppslagsforsøk](AUDIO_LOOKUP_EXPERIMENTS.md)
er forkastet. Begge består omfattende utdata-/tilstandskontroller, men gir
flere tapte lydtikker over 20-romsruten. Ingen av dem er i produksjon.
Ny R20-profil peker mot romarbeid fremfor bølgeoppslaget. En [isolert
fargeobservatør-kandidat](COLOR_OBSERVER_OPTIMIZATION.md) kontrolleres videre;
det opprinnelige antallet OP-oppgaver utvides ikke.

30. oktober, OP0/OP4: [lange normalmålinger](NORMAL_RUNTIME_BASELINE.md)
uten profilering eller opptak i selve intervallet: rom 1 gir 6877 felt,
1647 kildesteg og 235 lydtap; rom 12 gir 6943 felt, 2088 steg og null lydtap.
Begge tre-feltskrav står åpne. En passert lydprøve er ikke full sanntid.
[Den nye CIA-/IRQ-kontrollen](IRQ_INPUT_AUDIT.md) avdekker manglende
aktivitetsgate og alternativ retningstransformasjon i dagens native input,
samt eksplisitte RAM-avvik i full original IRQ-prolog/stack. De står åpne;
gamle tester som satte ferdig dekodede inputbytes beviser ikke denne delen.


Fargeobservatør-kandidaten har nå to komplette 20-romspar og separat
53-fixtur-/1200-løkkekontroll: R20-arbeid faller 4,48 % og 6,51 %, samlet
arbeid 0,62 % og 0,82 %, og samlet lydtap faller i begge par. Største Chip-blokk
i fixturbygget er fortsatt 52632. Kandidaten er integrert i produksjonskoden etter fersk standardkontroll
med53 fixturer/1200 løkker og710 separate kontakt-/spritekontroller.
Samlet leveransebinding dokumenteres i source-world-delivery.json. Den løser ikke de målte normal-
kadens-/IRQ-/input-/stack- eller fysiske A500-portene alene.


30. oktober: [bufferpublisering](BUFFER_PUBLICATION.md) og samlet
trappefase er rettet i ny EXE/ADF.12+12 kontrollerte rom12-/døds-/rombyttebilder
har null fase- eller statiske grafikkavvik; menyens78 bilder består også.
Ny naturlig prøve av OP3-R12 og OP3-REDRAW står åpen. Samlet A500-tempo er
fortsatt under målet; ingen full sanntids- eller originalparitet hevdes.


30. oktober, OP0/OP1/OP4: [ny rom1-profil, kontakt-inline-forsøk og inputkandidat](OP_FOLLOWUP_2026_10_30.md).
Profilen bekrefter kontaktpasset som en stor CPU-kostnad. Standardprofilen
feilet diagnoseallokering; separat profil uten ubrukt opptaksbuffer er
uttrykkelig merket og godkjenner ikke produksjonsminne eller sanntid.
To uprofilerte par med710 native kontroller gir1433/1430->1425 felt,
men8->11 tapte lydservicetikk i begge par og1216 flere lenkede kodebyte.
Inline-kandidaten forkastes; normalbygget er uendret. Input-slot-kandidaten
består99072 hele-RAM-/registerkontroller mot3803993 originalinstruksjoner,
men er ikke integrert før full IRQ-/stack-/palettkontekst er avklart.
Dette behandler de eksisterende OP-punktene; ingen nye optimaliseringsmål
eller svakere akseptanseporter opprettes. Maskinlesbar kontroll:
reference/validation/op-followup.json, tools/verify_op_followup.py.


30. oktober, OP4/OP5: [parameterisert native IRQ-kontekst](IRQ_CONTEXT_CANDIDATE.md)
bevarer nå originalens stack-/palett-/raster-/SID-skrivinger i3 352
kontrollerte tilfeller mot479 308 faktiske C64-instruksjoner. Hele RAM,
registre, retur-PC og alle tre SID-gateflanker sammenlignes. Fem IRQ-handlere
er dekket, inkludert spillerannonseringen.68000-kompilering og lokale
stackrammer er målt separat; dette er ikke native kjøring eller full
call-chain-margin. Kandidaten er fortsatt isolert. Normal PC-/IRQ-planlegging,
$152C/tittelmusikk, maskert/ventende IRQ og de tidligere sanntids-/maskinportene
står åpne. Originalkildene og normal EXE/ADF er uendret. Dette er videreføring
av de eksisterende OP4/OP5-punktene, ingen ny optimaliseringsliste.

30. oktober, OP1/OP5: [spritepublisering og registerplassering](SPRITE_PUBLICATION_EXPERIMENTS.md)
er undersøkt i isolerte kandidater.21 504 kildekontroller og53 native
fixturer består for publiseringshjelperen, men første20-romspar gir bare
8980->8973 felt, og rom12 blir ikke raskere. Den er ikke integrert.
Direkte bladkall ved $15BA består ytterligere640 hele-RAM-/registerprøver
mot81 112 faktiske kildeinstruksjoner; første R01-prøve gir1420 felt med
710 native kontroller. Første fullromsmåling gir8980->8905 felt og131->121 lydtap, med
uendret68136-byte Chip-reserve. Gjentakelsen gir9044->8981 felt og131->131 lydtap. Ingen
integrering er gjort mens den større kallkontroll-kandidaten vurderes.
En separat layoutprøve gir1366 færre objektkodebyte uten mer BSS/data,
og består3034 kildekontroller samt5 integrerte moduser mot7055873
originalinstruksjoner. Native funksjons-/ytelsesakseptanse står åpen. Produksjonsbygget og
alle opprinnelige OP-/sanntids-/minneporter beholdes.


30. oktober, OP1/OP5: [kompakt native kallkontroll](NATIVE_CONTINUATION_EXPERIMENT.md)
beholder alle gjestestackskrivinger og erstatter444 vanlige C-rekursive
JSR-wrappere med native fortsettelser, med original rekursiv fallback.
To varianter består hver3034 kildekontroller og5 integrerte moduser;
standardvarianten består også3352 komplette kontrollerte IRQ-tilfeller.
Objektkode/tabeller faller netto13196 byte, BSS/data er uendret.
Første native R01-pilot gir1433->1413 felt,8->6 lydtap og69016->85408
byte i største Chip-blokk, med710 kontroller. Full53-fixtur-/1200-løkketest
består med52632-byte Chip-reserve. Første20-romsrute gir9044->8965
felt og131->126 lydtap. Største ledige slow-blokk øker2504->15752 byte,
men rom12 blir ikke raskere i dette paret. Nytt fullromspar kjører; normal integrering og de tidligere sanntids-/stack-/
maskinportene er fortsatt åpne. Dette er eksisterende OP1/OP5-arbeid.
