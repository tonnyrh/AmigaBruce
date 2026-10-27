# Milepælgjennomgang og samlet kildeport

27. oktober 2026. Den delvise aktøradapteren er erstattet i vanlig spill med
statisk oversatt C64-kode: native C-grener og funksjonskall, uten kjørende
6502-opkodedekoding. Den gamle adapteren beholdes kun for historiske tester.

## Avklaringer fra faktisk maskinkode

| Område | Kilde og betingelser | Implementering |
| --- | --- | --- |
| Hovedrekkefølge | `$1BC2–$1C32`: tjenester, rom, kontakt, objekter, kamp, aktører, sprites og opprydding | Hele kjeden bruker samme kilde-RAM. Kamp skjer før aktøroppdatering. |
| Alle aktørtilstander | `$1C5B–$2508`: venting, dispatch, historikk og kontakt | Alle28 tilstander, støtte/landing, nett, fall, retrett og restitusjon. |
| Positur og kontakt | `$2780–$29C2`, `$5212–$56FF`, tabeller `$1167/$1239` | Faktisk kildepositur, hel-/kroppskontakt og bevegelseshistorikk. Tegningen velger ikke fysikkmasken. |
| Samtidig kamp | `$29C3–$2C23`: samle alle treffflagg før skade brukes | Ingen sekvensiell prototype eller generell Yamo-prioritet. Falltreff krever tilstand14, VIC-gate og kildens høyde-/kvote-/offerkrav. |
| Fallkvote | `$15BD–$15CD`: null i `$4EEC` fyller alle kvoter til2, så dekrementeres telleren | Kildens IRQ-fase, ikke en tre-stegs opplading. |
| AI og inntreden | `$40BC`, `$0CD5/$0DF8`, `$2D7C`, `$179E` | Hele tilstandsmaskinen, med kildeventing, klokke, retrett, angrep, inntreden og objektpass. |
| Faredød | `$304B/$407D` setter tilstand25/teller16 | Helse settes ikke kunstig negativ ved første farekontakt. Tilstandsmaskinen fullfører livet senere; lyd følger kildens kallsteder. |
| Liv og turbytte | `$1818–$188B`, `$0763`, `$0FED` | Faktisk livtrekk, helse, romreset og bytte av per-spillerdata/lanterner. Fire reservefall, ni med menneskelig motstander. |
| Poeng og bonus | `$312C/$3175/$3184`, konvertering `$32DC` | Binært24-bits tall i `$41–$43`, bonusliv og rekord. `$4392/$4395` er bonusgrenser, ikke poeng. Native HUD viser poeng. |
| Nytt spill | `$0743→$0F72→$0763→$09BC` | Første tur starter riktig også med to spillere. Oppstart bruker ikke døds-/turbytteadapteren. |
| Game Over | `$1964–$1981` |254 felt, eventuelt annen spiller, ellers64 felt til før menyen. |
| Rom/progresjon | `$2E39`, `$2F8E/$2F9A`, `$09BC`, `$331C/$336E`, alle20 init-/løprutiner | Faktisk laster, lanterner, dynamikk, dører og sluttgrener. Startrom/F1/F2 er eksplisitte testutvidelser. |

Kilde: `.reference/c64/work/untrained-memory.bin`, SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Remember/T64-kandidaten er ikke bekreftet som valgt urørt1984-utgave.
[Oversettelsesmanifest og adresset disassembly](../reference/analysis/actor-chain-2026-10-26/translation.json)
følger de faktiske bytene. Originalen og kildeutsjekkingene er uendret.

## Kontroller og begrensninger

`test-c64-actors.ps1` sammenligner3 034 forløp med faktisk6502-kjøring:
alle64KiB RAM, registre, flagg, stack og kontrollgrenser. Dette inkluderer
2 037 aktør-/oppstartstilfeller,517 kamptilfeller og480 rom-/hovedsteg.

`python tools/audit_c64_world.py` kontrollerer den integrerte kjeden i alle
fire kombinasjoner av én/to spillere og automatisk/menneskestyrt Yamo.
720 felter per kombinasjon omfatter to injiserte livstap og turbytte.
En femte sekvens kontrollerer siste liv, begge Game Over-ventere og retur til
meny. Totalt7 055 873 kildeinstruksjoner kontrolleres ved felt-/hovedgrenser.
Dette er kontrollerte innganger, ikke naturlig gjennomspilling.

`tools/build_source_actor_fixture.py` lager53 kompakte68000-kontroller fra
faktisk kilde-CPU-kjøring. De kontrollerer hele RAM med32-bits FNV og alle
registre etter aktørtilstander, kamp og hovedsteg i20 rom. Hashene er en
regresjonskontroll; de erstatter ikke den bytevise vertskontrollen.

Maskinvaregrenser som fortsatt trenger akseptanse:

- CIA-lesing erstattes av avlest Amiga-joystick. Spillogikken utenfor denne
  grensen bruker kildekoden.
- VIC-låsen bygges fra faktiske spritepekere, bitmapbytes, ekspansjon og
  flerpikselflagg. Den akkumulerer og tømmes ved lesing. Beregningen er
  feltbasert; rasterfase, grenseområde og IRQ-stackfase er ikke sertifisert.
  Ingen nye angrepsbokser eller veggstråler brukes.
- Annonsering og Game Over bruker kildens feltventere. Fasen i samtidig
  CPU-forsinkelsesløkke og tilfeldigleserens naturlige fordeling er åpne.
- PAL-feltkadens er en egen port. Bestått logikk og korrekt bilde godkjenner
  ikke en treg A500-kjøring. Tidsavvik rapporteres som avvik.

Vanlig spill lar kildens IRQ-/ventetellere følge faktisk PAL-tid, også når
tegning mister et felt. SEI/CLI og romlasting avgrenser dette. Den kontrollerte
native reprisen gir eksplisitt ett felt per løkke, og markerer tidsoverskridelser
som en åpen port. Den godkjenner ikke vanlig input-/rasterfase.
VIC-radene mellomlagres bare når layout og alle63 bitmapbytes er like.
Første [optimaliseringspilot](AMIGA_OPTIMIZATION_REPORT.md) gjenbruker også
overlappresultatet ved identiske effektive piksler og registre. Latchbittene
akkumuleres hvert felt, også etter tømming; nye kontakter beregnes på nytt.

Samlekontroll: `./test-source-world.ps1`. Native rapport ligger i
`reference/validation/source-world-native.json`; samlet filbundet status
opprettes med `python tools/verify_source_world_delivery.py --record`.

De optimaliserte løkkene `$26A0/$52AD/$537E` bevarer scratch-RAM, stack,
selvmodifiserte operander og sluttflagg. Originale kontaktklassehjelpere og
ikke-lokal retur beholdes. Samme kildekontroller gjelder etter optimalisering.

Siste native kjøring:53/53 RAM-/registerkontroller bestått,1 200
repriseløkker/400 logiske steg, ingen kilde-, lyd-, DMA-, bilde- eller
aritmetikkfeil, og korrekt tilbakeføring til AmigaOS. Største ledige
Chip-blokk er52 632 byte. Dette er en 68000/OCS/KS1.3-kjøring med512+512KiB.
Normalbyggets klokke er kontrollert separat mot faktisk PAL-tid.
Etter første optimaliseringspilot er587 løkker med holdt nytt spillsteg
registrert, største rekke29, og275 lydserviceticks mangler. Bildets
restkontroll har42 HUD-bytes og33 uforklarte scenebytes; null avvik i
bakgrunnskontrollen godkjenner ikke disse scenebytene som et rent overlegg.
Den strenge feltporten er fortsatt **ikke bestått**; rapporten bevarer
overskridelsene. Kildeporten avslutter dermed ikke M1 eller full M4-akseptanse.

## Milepælstatus

| Milepæl | Kodeleveranse | Gjenstående akseptanse |
| --- | --- | --- |
| M0 | Kandidat, hash, disassembly og regelregister | Bekrefte valgt urørt1984-utgave. |
| M1 | Native motor, bygg og A500-testspor | Stabil feltkadens, timingfase og reserve gjennom hele spillet. |
| M2 | Hele aktørmaskinen, kontakt, støtte/landing og positur | Naturlige kant-/nettforløp og timing med denne motoren. |
| M3 | Hele kamp-/AI-/objektkjeden, samtidighet, reaksjon og liv | Naturlig kamp og VIC-/IRQ-fase. |
| M4 |20 rom, poeng/bonus, liv, spillermoduser og sluttgrener i felles RAM | Hel gjennomspilling, forbindelser/feller og ny runde. |
| M5 | Rippede tegn/sprites og kildebasert lyd | Naturlig lyd-/visningsfase, annonsering og Game Over-overgang. Enhanced er utsatt. |
| M6 | Lokale EXE-/ADF-bygg | Sluttpakke, fysisk A500 og publiseringsgrunnlag. |

Før endringen er131 filer fra spawn-leveransen bevart i
`reference/validation/history/before-milestone-completion-2026-10-26/`.
Eldre rapporter gjelder adapteren de ble laget med. Tidligere manuelt
bekreftede tester forblir historisk bestått.

En konkret presentasjonsrest er Game Over-IRQen `$152C/$154C`, som kaller
musikkrutinen `$E006`. Den nye feltgrensen håndterer ventingen, mens native
lyd-/visningsovergangen må avstemmes samlet med denne rasterkjeden. Dette
er en kjent M5-rest, ikke en uavklart kamp- eller livsregel.
