# Bevegelig nett i rom 5

Påfølgende [rombytteoptimalisering](ROOM_LOAD_PERFORMANCE.md) beskriver
gjeldende bygg. De opprinnelige bygg-/tidsmålingene under er historiske.

25. oktober 2026. Brukerfunnet var at Bruce ble kastet mot høyre når han
hoppet inn i det midtre nettet. Feilen var at Amiga-adapteren behandlet
tegn `$62` som `stun=16`. Den vanlige treffreaksjonen flyttet ham deretter
bakover fire piksler per steg. Dette var ingen oversettelse av C64-rutinen.

Kilde: `.reference/c64/work/untrained-memory.bin`, SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Remember/T64-kandidaten er fortsatt ikke bekreftet som urørt 1984-utgave.
Originalfilen er uendret. [Disassembly](../reference/analysis/moving-net-2026-10-25/source-disassembly.txt)
er laget fra disse faktiske bytene.

## Nedovervendte spyd langs nettet i Enhanced

Rom 5 bruker åtte faste spyd rundt det bevegelige nettet. Rompekeren i
`$4B38/$4B4D` velger den pakkede kartstrømmen `$6E1B–$6F81` i
Remember/T64-kandidaten ovenfor. Kartverdi `$C0` forekommer i kolonne
16, 17, 22 og 23 på rad 0, i kolonne 17 og 22 på rad 4, og i kolonne 16
og 23 på rad 5. Kolonner og rader er nullbaserte 8×16-celler.

Romlasteren ved `$0AE3–$0AEE` og `$0B0B–$0B16` skriver tegnparet
`$40/$C0`. Øvre tegn ved `$A200` har bytene `3F 3F 2A 2A 08 08 08 08`.
Nedre tegn ved `$A600` har åtte `08`. Bitpar 2 gir hvitt fra paletten
ved `$47D1`. Bitpar 3 gir festet farge fra cellens farge-RAM. Den gamle
Enhanced-paletten for søyler malte også disse tegnene i mørke murfarger.
Standardtegningen bruker nå C64-fargene på de synlige pikslene og lar
Enhanced-muren synes gjennom bitpar 0. En egen fargeendring i
grafikkeditoren gjelder bare den halvdelen av tegnet som ble malt.

På PAL A500 i WinUAE samsvarte alle 384 synlige spydpiksler i rom 5 med
C64-kilden, både i bakgrunnsbufferen og på den viste skjermen. Samme
sammenligning i bakgrunnsbufferen dekket alle 28 spyd i rom 5, 6, 7, 9 og
10, inkludert de ulike festefargene.
[Rom 5 i WinUAE](../reference/analysis/room05-spears-2026-11-02/room-05-enhanced.png)

## Lanternene som slukker i rom 5

I den samme C64-binæren styrer `$3760–$378C` venstre lanterne og
`$37B4–$37E0` høyre. Mens tilhørende post (`$4D70` eller `$4D74`) er
aktiv, øker romrutinen dens teller. Ved `$20` tennes lanternen. Ved `$40`
slukker den og telleren nullstilles. Romstart ved `$3402` setter høyre
teller til `$1F`, så de to lanternene skifter tilstand til ulike tider.

Tegnrutinen ved `$17E2` dekoder strengene ved `$4626–$462D`. På rad 4
bruker den `$13/$93` og `$66/$E6` i kolonne 11 (tent og slukket), og
`$14/$94` og `$67/$E7` i kolonne 28. To rader i den slukkede høyre
veken får fremdeles fire mulige bitmønstre via `$4122–$412F`.
Ved innsamling gir postene hver sin tomme brakett, `$1E/$9E` og
`$1F/$9F`. Romrutinen hopper da over tenning og slukking.

Enhanced manglet begge de slukkede tegnparene og viste derfor C64-grafikk
en del av hver syklus. Nå bruker de samme form og oppheng som de tente
lanternene, med mørkere glass og veke. Grafikken velges direkte fra de
levende tegnene, også når høyre veke skifter.
[Begge tilstander fra WinUAE](../reference/analysis/room05-lanterns-2026-11-02/lantern-cycle.png)

## Regler fra maskinkoden

| Adresse | Betingelse | Effekt |
| --- | --- | --- |
| `$2E39–$2E68`, `$2E6E–$2EE9` | Aktiv aktør, ikke dødtilstand25 | Skanner tre celler på to rader. Forrige tilstand23 nullstilles via `$2E10` før ny objektkontakt. |
| `$2EA5`, `$310C–$3127` | Skanningen finner tegn `$62`, og pikselkontakt `$B6 & 4` | Setter tilstand23, teller `$CE=$10`, venting `$0106=0`, `$AA=0`. Dette er grep på bevegelig nett, ikke skade eller rekyl. |
| `$2187–$218B` | Tilstand23, men ingen nettkontakt | Går til tomgang via `$2504`; ingen sideveis utkasting. |
| `$218D–$21EB` | Tilstand23 med nettkontakt | `$AA=1` beholder posituren. `$AD` teller ned. Når den er null, gir ren opp/ned to Y-piksler, ren venstre/høyre fire X-piksler og setter `$AD=4`, `$AA=0`. Diagonaler eller sluppet input gir ingen egen bevegelse. Ild starter ikke slag/spark i denne grenen. |
| `$2191–$21A7` | Datastyrt medaktør, `$42CA=0` | Velger sideretning fra aktørens ståretning før samme nettgren. Full øvrig AI er fortsatt en separat åpen portering. |
| `$21EE–$2204`, `$2C70–$2D54` | Nettfasen `$60==1` etter romoppdateringen | Nettet bærer aktøren to Y-piksler: opp når `$65=0`, ned ellers. Tegnrullingen og fasedataene kommer fra den oversatte romrutinen. |
| `$2207–$2234`, `$24F4` | Etter egen bevegelse og eventuell transport | Beholder tilstand23/telleren, nuller input og ild for denne oppdateringen og motregner opp/ned-historikk. |
| `$2974–$2993` | Ny positur skal velges | Transport alene beholder posituren; egen bevegelse veksler nettpositur10/12. Grep beholder den tidligere posituren fram til en slik veksling. |

Det bevegelige nettet har altså en annen rytme enn vanlige klatrefelt.
To piksler vertikalt/fire sidelengs hver femte logikkoppdatering skal ikke
erstattes med den raskere statiske nettgrenen. Nettets egen transport kommer
i tillegg og kan motvirke spillerens bevegelse.

Amiga bruker nå denne grenen og egne `$AD/$AA`-felt. Kontakt med `$62`
går også utenom den vanlige kampreaksjonen. Slipp beholder kontaktposituren,
og svart kontakt bruker fortsatt kildens historikk/tilbakerulling. To
følgefunn ble rettet: tomgang etter fall på nett bruker samme oppdaterings
kontaktflagg, og utgang fra veggrestitusjon bruker eksisterende `$B6` før
første fallsteg, i stedet for å søke støtte med en ny fallmaske.

## Kontroller og begrensninger

`test-moving-net.ps1` sammenligner 12 800 kontrollerte innstillinger med
faktisk 6502-kjøring av `$2187`: alle retninger/diagonaler, ventefaser,
transportretninger, tap av kontakt og bevegelsesgrenser. Sju sekvenser
sammenligner 310 steg med originale rom5-løp, objektpass, aktørgren og
positurvalg. De dekker grep fra begge sider, opp/ned, sluppet/skrå input,
utgang begge veier og svart kontakt ved kanten. Ingen falsk skade/rekyl
godtas. [Rapport](../reference/analysis/moving-net-2026-10-25/report.json).

430 av disse kontrollene er også generert som faste Amiga-fixtures.
Aktørstartene/inputene er kontrollerte testtilstander. Dette er ikke en
naturlig gjennomspilling i VICE eller en godkjenning av hele aktørmotoren.
Brukerens konkrete hopp skal fortsatt prøves i den nye spillbyggen.

## Amiga-kjøring

To kjøringer fra CLI på PAL 68000/OCS, Kickstart1.3, 512 KiB Chip +
512 KiB slow, er fullført med 6000 PAL-felt hver. Alle 430 nettkontroller
og de tidligere bevegelses-/vegg-/livs-/sprite-/lydkontrollene passerer.
Største ledige Chip-blokk etter lasting er 60 832 byte i begge kjøringer.
Normalutgaven er 206 008 byte; de nye fixturtabellene ligger i testutgaven.

Det strenge ytelseskravet er **ikke bestått**: 627/630 tapte oppdateringer
og største målte oppdateringsgap3 felt. Dette gjelder den generelle
kampreplayen, ikke en naturlig gjennomspilling av rom5. Kildefunksjonene
er kontrollert per logikksteg; full tidstro spilloppførsel krever fortsatt
at ytelsesavvikene løses. [Gjeldende bygg og målinger](../reference/validation/moving-net-delivery.json).
