# Kollisjon, lanterner og romgrensene i rom 1

**Senere samme dag:** [bevegelsesgjennomgangen](C64_MOVEMENT.md) erstatter de
tidligere begrensningene for spark-/hopp-/fallmasker og enkel X-tilbakerulling.
Beskrivelsen og tallene under bevarer omfanget av den første kontaktleveransen.

Gjennomgang 25. oktober 2026. Fasit for denne avgrensede rettelsen er bytene i
`.reference/c64/work/untrained-memory.bin`, SHA-256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Dette er Remember/T64-kandidaten, fortsatt uten bekreftet identitet som valgt
urørt 1984-utgave. Kildeutsjekkinger og originalbinær er uendret.

## To forskjellige kollisjonstrinn

Hovedløkken kaller `$5212` ved `$1C0D`, deretter `$2E39` ved `$1C10`.
Kamp og aktørbevegelse kommer etterpå. Posisjon og positur fra forrige
aktøroppdatering brukes dermed av objektbehandlingen.

`$5212–$52AB` velger figurmasken gjennom `$4F4E` og pekerne `$1167/$1239`.
Den sammenholder maskens 21 synlige rader med de faktiske tegnbitene.
Bitplanene AND-es; det er ikke bare et rektangel eller en test av flis-ID.
Resultatet `$B6` gjelder hele masken, mens `$A7` utelater de nederste seks
radene. Kontaktklassene er 1 for fast piksel, 2 for supplerende piksel og
4/8 for kombinasjonen av de to planene, avhengig av fargeattributtets tre
lave biter. Klasse 4 er nett; klasse 8 er svart kontakt.

`$1C39–$1C5A` regner så om til objektceller:

- kolonne = `(råX − 12) >> 2`; rå X er halv skjerm-X pluss 12;
- rad = `(råY − 12) >> 4`; rom 14 legger først til fire, med byteomslag;
- X i Amiga-kjernen er **sprite-venstre**, Y er **bunn + 1**.

`$2E6E–$2E88` undersøker tre kolonner på denne raden og på raden under.
Dette er 8×16-celler. Det er ikke de samme fire tegnradene som brukes av
pikselkjernen. Tegnradpekerne ligger i `$4338/$434C`; for cellerad 2–12
er adressen `$8C00 + (2×rad − 1)×40 + kolonne`.

## Lanterner

`$2E55–$2EB3` starter med `$53 = $B6 & 2`. Vanlige celler forskyver dette
flagget med `ASL`; det forblir ikke-null gjennom alle seks kandidatceller.
Det er altså **ett felles flagg**, ikke et eget bekreftet pikseloverlapp for
hver lanterne. En nærliggende supplerende piksel kan gjøre en lanterne i
de seks cellene innsamlelig. Vi skal ikke erstatte dette med en strengere
Amiga-treffboks.

Lanternecelle `$13`, `$14` eller `$31` går til `$2F04`. Bare aktør 0,
Bruce, får samle. `$331C–$336D` søker rommets firebytes-records via
`$4CE2 + 2×rom`: aktivstatus, erstatningstegn, kolonne og rad. Ved treff
nullstilles status og rommets gjenstående antall dekrementeres. De to
tegnradene erstattes av recordens tegn og tegnet OR `$80`. Nytt treff på
samme lanterne avvises. `$2F2D–$2F36` gir 125 poeng og lydforespørsel `$8E`.

Amiga brukte tidligere alltid masken for høyrevendt stående Bruce. Nå bruker
objektpasset de entydige, telleruavhengige kildepositurene:

| Tilstand | C64-rutine | Maskenummer venstre / høyre |
| --- | --- | --- |
| Står stille uten nett | `$2996–$299F` | 0 / 2 |
| Bokseslag, tilstand 17 | `$282F–$2840` | 4 / 6 |
| Ligger, tilstand 26 | `$27A6–$27B7` | 64 / 66 |

Det manglende `$8E`-lydkallet er også lagt til etter vellykket innsamling.
Det gjelder ingen ny lydressurs; dette bruker den allerede porterte
kildebaserte effektsekvensen.

Stående på nett er ikke en konstant positur i `$2974–$2993`; denne grenen
beholdes i den åpne adapterdelen. Høyreståing, slag og liggemaskene har samme
raske kontaktbane. Uttrekket kontrollerer mot kildebytene at tredje kolonne er
tom og at bitparene er fulle før denne banen brukes. De forskjøvne maskene
koster 1008 ekstra byte CPU-RAM, uten nye Chip-allokeringer. Venstreståing
bruker den generelle bitplanebanen: enkelte originale 442-celles romstrømmer
skriver til `$9010/11` i maske 0 og kan lage delvise bitpar. Den utvidede
kontrollen i rom 5 fanget dette; den raske banen brukes derfor ikke for maske 0.

**Avgrensning:** Gang, hopp, klatring og reaksjoner bruker fortsatt den
tidligere ståmaskeadapteren i objektpasset. Der må kildeaktørens tilstand,
faseteller, tidligere positur og `$4FDB`-lås porteres samlet. Støtte-/landings-
adapteren bruker også fortsatt maske 2. Kunstens animasjonsnummer brukes
ikke som erstatning for C64-posituren. Retningen og masken for disse fasene
er fortsatt åpne; denne rettelsen er ikke full kollisjonsparitet.

## Høyre utgang fra rom 1

Originaldata har utgangscellene i **kolonne 39**. Utgang `$05` er på rad 5,
utgang `$02` på rad 8. Cellene er utløsere, og dørbehandlingen hopper over
kravet om supplerende pikselkontakt.

Begge må passere `$30D4–$310B`. For disse høyreutgangene kreves:

- rå X **større enn `$A1`**, altså minst 162 = **skjerm-X 300**;
- høyrebevegelse i `$4F60` må være ikke-null;
- utgangscellen må finnes i de seks undersøkte cellene.

| Forbindelse | Mulig Y-bånd ved objektpasset | Ankomst i rom 2 | Retur til rom 1 |
| --- | --- | --- | --- |
| Øvre, celle 39/5 | 76–107 | X=6, Y=98 | X=298, Y=98 |
| Nedre, celle 39/8 | 124–155 | X=8, Y=146 | X=296, Y=146 |

Båndene følger celleregningen, ikke en ny høydejustering. Vanlig gulvnivå
ved de to forbindelsene er Y=98 og Y=146. Ankomsten ved en forbindelse
skal ikke erstattes av rom 2s separate standardstart X=24, Y=98.
Destinasjonene kommer fra `$4B5E/$4B9A`, X fra `$4BFE/$4C76` og Y fra
`$4C12/$4C8A`; retur bruker de tilsvarende slot-tabellene.

**X=296 og 298 avvises. X=300 uten høyrebevegelse avvises også.** X=300 og
302 med høyrebevegelse godtas i riktig høydebånd. Venstre retur krever
rå X under 16: skjerm-X=6 godtas, X=8 avvises. Ingen ekstra margin, krav om
hele figuren utenfor bildet eller knapp for rombytte er innført.

Dette bekrefter at bytte før hele figuren er ute av skjermen finnes i
kandidatens kode. Den opplevde visuelle timingen i brukerens kjøring er
ikke målt her; vi fastslår ikke en ny årsak ut fra opplevelsen alene.
Romgrafikken og dens plassering er beholdt fra dekodet romstrøm og tegnsett.

## Kontroller

Kjør `test-c64-rooms.ps1 -ObjectsOnly` for de 29 målrettede tilfellene.
Her velger den **faktiske** `$2780`-rutinen positur, `$5212` beregner
pikselkontakt, og `$2E39` utfører objektsøket. Vi stopper ved `$2F8E` før
originalens IRQ-overtakelse og stack-nullstilling. Native integrasjon
sammenlignes med resultater, lanternerecords, endrede tegn, antall, poeng
og lydkø. Gjentatt kontakt skal ikke samle eller score på nytt.

`test-c64-rooms.ps1` kjører dessuten alle 35 Bruce-maskene i 20 rom,
inkludert X=300 og 302, i tillegg til init-/løp-/animasjonskontrollene.
`test-core.ps1` og Amiga-autotesten kjører de samme 29 integrasjonstilfellene.
Native resultat oppgir `contact_fixture_cases=29` og feilindeks, der 0 betyr
ingen feil. Testforberedelsen ligger før lydstart og maskinvareovertakelse.

Se [kildefixtures og resultater](../reference/analysis/contact-audit-2026-10-25/report.json)
og [adresset disassembly](../reference/analysis/contact-audit-2026-10-25/source-disassembly.txt).
Dette er kontrollerte CPU-/integrasjonstilstander, ikke naturlig
gjennomspilling. Native tids- og minnekrav rapporteres separat.

## Kontaktleveransen før bevegelsesrettelsen

Følgende målinger gjelder den arkiverte kontaktbyggen før endringene i
[bevegelsesgjennomgangen](C64_MOVEMENT.md), ikke gjeldende EXE.
29 objektkontroller og24 860 pikselkontroller bestod. To A500-CLI-starter
fullfører29 kontaktkontroller og6000 spillfelt hver, uten kontakt-, rom-,
lyd- eller runtime-aritmetikkfeil; lyd-/spilltilstand matcher verten. Vanlig
EXE er212 864 byte, ADF901 120 byte. `start` oppdateres til normalbygget.

Den strenge testporten feiler fortsatt:29 968 byte største sammenhengende
Chip-blokk mot49 152-målet,14 forsinkede felt per6000 og maksimal avstand
to PAL-perioder. Testbygget har ekstra framebuffer-/signaturmåling; vanlig
byggets ledige minne og feltkadens er ikke målt her. Ingen20-roms native
gjennomspilling er gjennomført i denne revisjonen.
