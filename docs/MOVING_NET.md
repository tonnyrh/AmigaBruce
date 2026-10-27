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
