# Aktive tester — samlet kildeport, 27. oktober

Vanlig spill bruker nå hele C64-kjeden. [Kildegrunnlag, adresser og porter](MILESTONE_COMPLETION.md).
Start et nytt spill; gamle USS-filer inneholder gammel kode.

## Maskinkontroll før endelig godkjenning

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
  Normal klokkeprøve er fortsatt tregere enn tre felt per steg. Kontroller
  synlig framdrift også under naturlig spilling.
- VIC-PHASE: kontroller naturlige samtidige treff og spritekontakt ved kanter.
  Den nye låsen bruker faktiske kildepiksler, men er feltbasert.
- ROOM-ALL/LINKS: fullfør hele spillet naturlig, inkludert dynamiske åpninger,
  feller og ny runde. F1/F2 og startrom bekrefter kun inspeksjon.
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
| T14/DEATH/2P | Mist liv etter kamp, fare og innsamling. Kontroller reservefall00, Game Over, annonseventing og turbytte. Samle ulike lanterner med to spillere; rom, poeng og fall skal følge riktig tur. |
| SCORE/BONUS | Kontroller poeng for lanterner/kamp og bonusliv. HUD viser kilde-RAMs binære24-bits poeng; ingen egen Amiga-poengregel. |
| CHEAT-PROGRESS | Start i rom10 via Shift+D: rom1–9 fullført, målrom bevart. Prøv to spillere og F1/F2. Romhopp gir ingen poeng/bonus. |
| GEO-R02/ROOM-LOAD | Midtforbindelsen i rom2, retur1↔2 og5↔6, samme rom ved død. Kontroller geometri, palett, lanterner og nett. |
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
