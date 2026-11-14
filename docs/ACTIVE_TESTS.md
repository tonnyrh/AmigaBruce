# Aktive tester — samlet kildeport, 27. oktober

Vanlig spill bruker nå hele C64-kjeden. [Kildegrunnlag, adresser og porter](MILESTONE_COMPLETION.md).
Start et nytt spill; gamle USS-filer inneholder gammel kode.

## Maskinkontroll før endelig godkjenning

- **RC2 Enhanced combat audio (14 November).** Listen on physical Amiga to the imported Bruce shout (one-in-three chance on punches while no shout is playing), both Kage weapon swishes and Kage Kick Variant 2. Check that long clips finish cleanly and that Classic keeps its source audio. Host probability/source-state checks and the normal-ADF WinUAE playback checks pass; physical listening acceptance remains open. [RC2 evidence](../reference/analysis/release-rc2-2026-11-14/report.json). The RC1 lethal-punch-only cry has been replaced.

- **Enhanced death and Yamo impacts (12 November).** On physical Amiga, verify that bomb death holds Bruce's stiff pose in both facing directions and that Yamo's two new impact samples are audible and comfortable in combat. The four controlled WinUAE death cases and host audio checks pass. [Death evidence](../reference/analysis/enhanced-death-2026-11-12/report.json) · [Audio evidence](../reference/analysis/yamo-impact-2026-11-12/report.json).

- **Felt og styring.** Avlesingen ved `$169D` er kontrollert både før og
  etter en retningsendring. Det som gjenstår er nøyaktig tidspunkt for
  synlig respons i naturlig spill, særlig når et langt treff avbryter
  bevegelsen. [Målegrunnlag](FIELD_WORK.md).

- I rom 1 er falltreffene på Kage og Yamo kontrollert mot C64-koden.
  I siste leveranse har to lange kampruter én Paula-publisering i alle
  12 000 felt. Den bevegelige ruten bruker 14,96–15,04 s for 240 steg,
  mot målet på 14,40 s. Kontroller også trappetempoet i rom 12.
  Følg opp kampfarten mot målet på tre felt per steg ved naturlig spilling.
  [Målinger for de to rutene](OP_A500_ACCEPTANCE.md).

- A500-TIME: feltkadens og input-/lydhendelsestiming gjennom alle rom og kamp.
  Native samlekjøring samler tidsavvik; den er ikke et sanntidspass.
  Første [optimaliseringsmåling](AMIGA_OPTIMIZATION_REPORT.md) fant langvarig
  hold av nye figurtilstander. [Neste runde](CONTACT_OPTIMIZATION.md) gir
  360/360 synlige bilder i samme belastningsscene. Fortsatt mangler full
  feltkadens og lydservice; [68000-runden](VIC_NATIVE_OPTIMIZATION.md) og
  [kontaktforberedelsen](YAMO_VISIBILITY_PERFORMANCE.md) og
  [lokale kontaktregistre](CONTACT_REGISTERS_OPTIMIZATION.md) reduserer målt tid.
  [Native kontakt-/objekt-/poengløft](NATIVE_ENGINE_OPTIMIZATION.md) fortsetter
  fra den pushede milepælen med nye helrutinekontroller og målinger.
  [Kontakt-/VIC-kjerner](CONTACT_KERNEL_OPTIMIZATION.md) gir videre CPU-gevinst;
  lydtick-/feltporten står fortsatt åpen.
  [Pakkede kontaktmasker](PACKED_MASK_OPTIMIZATION.md) reduserer målt tid videre
  med 5,2 %; 454 native kjernekontroller supplerer kilde-/motorfixturene.
  [Resten av kontaktløpet](CONTACT_PREPARATION_OPTIMIZATION.md) gir ytterligere
  4,18 % kortere målt tid; 1046 native kjernekontroller kjøres separat.
  [VIC-hurtigbanen](VIC_REPEAT_OPTIMIZATION.md) viderefører målt CPU-arbeid
  uten å endre kollisjonslås eller spritepiksler.
  Normal klokkeprøve er fortsatt tregere enn tre felt per steg. Kontroller
  synlig framdrift også under naturlig spilling.
- VIC-PHASE: kontroller naturlige samtidige treff og spritekontakt ved kanter.
  Den nye låsen bruker faktiske kildepiksler, men er feltbasert.
- ROOM-ALL/LINKS: fullfør hele spillet naturlig, inkludert dynamiske åpninger,
  feller og ny runde. Brettvalg og startrom bekrefter kun inspeksjon.
- M0: bekreft valgt urørt1984-utgave. Remember/T64-kandidaten er hash-låst,
  men er fortsatt ikke sertifisert som denne utgaven.

## Målrettede nytester med den nye motoren

| ID | Utfør og observer |
| --- | --- |
| VIS-R02 | Start nytt spill i ny EXE. La Yamo forsvinne ved død/fjerning, bytt rom1↔2 og vent på ny inntreden. Ingen figur skal bli stående når kildeflaggets bit0 er null. Gamle USS-filer kjører gammel kode. |
| T02/T03/T07 | Rett fall og skrått hopp mot begge; hold slag mot Kage/Yamo; hopp foran stikk. Falltreff krever faktisk tilstand14. Samtidige treff følger kildeflaggene; ingen generell Yamo-prioritet. |
| T06/SRC-EDGE | Stå ytterst, sats og land begge veier. Hele støtte-/landingsgrenen og posemasken er nå portert. Ikke bruk bakerste tegnede fot som egen kollisjonsregel. |
| T08/T09/T11 | Veggpress, gjentatte hopp ved holdt opp, liggestilling og oppreisning. Retning låses i pågående hopp; liggestilling er kampbeskyttet etter kildens offerfilter. |
| T10/R05-MOVING-NET | Hopp inn fra begge sider, slipp input, prøv ren opp/ned/side og alle diagonaler. Nett23 har egen transport/venting. Ingen kunstig treffreaksjon ved nettgrep. |
| R06-JUMP/NPC/KAGE-WALL | Hopp venstre fra inngangsavsatsen. Prøv begge fiender mot svarte vegger og stikk fra begge sider. Ingen ny generell vegg som skjold; kildehistorikk og spritegate avgjør. |
| AI/SPAWN | Stå nede mens Kage kommer oppe til høyre i rom1. Prøv venting, retrett, retur, lagret helse og alternativ inngang i rom6–8. Hele AI-/aktørkjeden er nå aktiv. |
| NPC-RECOIL-R02 | Spark Yamo mot høyre vegg på mellomnivå, også dødelig. Kontroller retning, restitusjon og at Bruce/rommet blir stående. |
| BOMBS/R08-BLAST | La begge fiender gå over alle fem bomber, også ved ankomst og under reaksjon. Prøv Bruce uten udødelighet: kildeeffekt, positur8, teller16 og senere livtrekk. |
| R11-YAMO-BOMBE | Retest on physical Amiga: user-approved bomb-only contact margin, one pixel up/left/right, now enabled in normal Classic/Enhanced. All 54 formerly paired-height walks arm with the policy enabled; 8,424 pixel controls cover Bruce, Yamo and Kage. Try both directions, running and landing, especially room 11's middle platform. Three simultaneous source timers remain the limit. Also check the flatter, embedded Enhanced charges. [Policy and evidence](BOMBS_ENTRY.md#explicit-amiga-bomb-margin-user-decision-9-november-2026). |
| R19-BLINK | Start rom 19 i det nye bygget og utløs monsterets nederlag. Kontroller blink, lyd og åpning. Mål fra nederlaget til åpningen. Kontrollert A500-reprise er fortsatt langsommere enn PAL-C64. [Kilder og tidsmålinger](R19_WIZARD_FLASH.md). |
| T14/DEATH/2P | Mist liv etter kamp, fare og innsamling. Se etter rent skifte fra dødsposituren til spillernummeret eller Game Over, også ved turbytte. Kontroller reservefall00. Samle ulike lanterner med to spillere og kontroller rom, poeng og fall for hver tur. [Skjermskift ved død](TITLE_PAUSE_RESPAWN.md). |
| SCORE/BONUS | Kontroller poeng for lanterner/kamp og bonusliv. HUD viser kilde-RAMs binære24-bits poeng; ingen egen Amiga-poengregel. |
| CHEAT-PROGRESS | Velg rom 10 med Shift+D og F9/F10. Først ved Fire skal rom 1–9 markeres fullført. Prøv også andre spillers skyteknapp etter turbytte. I rom 13 skal Kage og Yamo komme inn etter bekreftelse. |
| GEO-R02/ROOM-LOAD | Midtforbindelsen i rom2, retur1↔2 og5↔6, samme rom ved død. Kontroller geometri, palett, lanterner og nett. |
| R06-TRAP-REPAINT | Ny EXE/ADF: observer øvre venstre felle over en hel syklus. Kildens lange pause beholdes, men gammel hvit rest skal ikke bli stående etter at tegnet er fjernet. Se USS-analysen og de nye køkontrollene. |
| R10-ELECTRIC | Følg nederste elektriske felle mens nettene ruller. Meld synlig forsinkelse separat fra kildefellens tilstand. |
| AUDIO/SPRITES | Lytt gjennom tittellåten og naturlige døds-/kampforløp. Kontroller kildepositurer i begge retninger, også Kages stav. Originalt motorvalg styrer nå posen direkte. |

Tidligere manuelt godkjente T01, T05, T12, T13, T15 og T16 beholdes som
bestått i [historikken](history/MANUAL_TEST_2026-10-24.md). T04 er mekanisk
akseptert i de testede situasjonene. De skal ikke tas på nytt som en ny full
sjekkliste. En målrettet regresjon kan bli nødvendig ved et konkret nytt funn.

Den [tidligere kodegjennomgangen](TEST_AUDIT_2026-10-25.md) er historikk for
adapteravvik. Der den sier at støtte, samtidighet eller full AI mangler,
er implementasjonsstatus erstattet av den samlede kildeporten. Naturlig
akseptanse er fortsatt separat fra injiserte RAM-/CPU-kontroller.

## Kildeavklart observasjon, 28. oktober

Takspissen i rom6 har svart kontaktklasse også etter at lanternen er tatt.
[Adresser, faktisk kollisjonsgren og kontrollerte hoppforløp](CEILING_R06.md).
Ingen ny geometri-/bevegelsesregel legges til. Naturlig spilling og generell
rasterparitet står fortsatt under de åpne portene over.

29. oktober: [tre radløkke-forsøk](CONTACT_SEGMENT_OPTIMIZATION.md) er målt og forkastet uten samlet gevinst. Motor og tidligere validerte spillbygg er gjenopprettet; ingen nye manuelle spilltester kreves for disse forsøkene.

Native spritekopiering er [kilde-/maskinverifisert](SPRITE_COPY_OPTIMIZATION.md), med23,14 % lavere kopieringskostnad i profilen. Totalmålingen og sanntidsporten er ikke forbedret til godkjent nivå; A500-TIME og lydservice står fortsatt åpne.

- OP3-R12: kontroller jevn trappefase i rom12 ved stillstand og klatring.
- OP3-REDRAW: kontroller ny spillstart, død/gjenoppståing og rombytte uten blandede rombilder eller avkuttet øverste pikselrad. [Arbeid og kildegrunnlag](RENDER_COHERENCE.md).

- OP1-R20-COLOR: ved neste naturlige spilling, kontroller blinkefeltet og slutt-timeren i rom20 med den nye EXE/ADF-en.232 kildefargelagringer per steg beholdes. R10-tid og R01-lydservice forblir under A500-TIME; ikke omtal hele spillet som13 % raskere. [Målinger og avgrensninger](FINAL_COLOR_OPTIMIZATION.md).


30. oktober: [bufferpublisering](BUFFER_PUBLICATION.md) og samlet
trappefase er rettet i ny EXE/ADF.12+12 kontrollerte rom12-/døds-/rombyttebilder
har null fase- eller statiske grafikkavvik; menyens78 bilder består også.
Ny naturlig prøve av OP3-R12 og OP3-REDRAW står åpen. Samlet A500-tempo er
fortsatt under målet; ingen full sanntids- eller originalparitet hevdes.

- R06/LOAD-DISPLAY: Start ny EXE/ADF og mist liv i rom6, deretter rombytte
  og død i rom12. Kort blank skjerm under innlasting er forventet som i
  kildekodens DEN-av-gren. Mursteinsmønster eller delvis tegnet rom skal ikke
  vises under innlastingen. Ikke gjenopprett 30.10.2026.uss for å teste ny kode.
  Se [kildespor og native-kontroll](LOADER_DISPLAY_BLANK.md).

- RUN-UNEVEN: Brukerens konkrete rom/avsats og retning må stedfestes.
  [Ny kildekontroll](FLOOR_WALK_AUDIT.md) finner ingen hovedløkkeavvik i
  2271 kontrollerte innganger. Kilden har korte fall-/landingsstopp.
  Dagens normalbygg måles til 3,338 felt/steg i en stasjonær rom12-scene;
  tre-feltsmålet står åpent. Skill flere kontaktstopp fra lengre pauser i tid.
  Ingen gulvregel er endret av denne undersøkelsen.

- R13-SPAWN: Brukeren presiserer 31. oktober at det gjelder mest Yamo ved
  første avsats. Ankomst kontra retur etter nederlag er fortsatt uavklart.
  [Rom13-kontrollen](R13_SPAWN_RATE.md) finner samme
  grunnverdier 4/32 i C64 og porten; Kage kan utsettes når Yamo er aktiv.
  3697 RAM-/registersammenligninger og 60 feltkontroller består.
  Naturlig kampforløp, RAM-leserfordeling og faktisk trykk på brukerens
  konkrete rute står åpent; tellere og spillregler er ikke endret.
