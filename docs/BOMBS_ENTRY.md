# Fiendeinnganger og bomber

26. oktober2026. Frossen kilde er Remember/T64-kandidaten
`.reference/c64/work/untrained-memory.bin`, SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Den er ikke sertifisert som urørt1984-utgave. Originalene er uendret.

## Fiendene har flere inngangspunkter

`$0BFA–$0C4B` velger mellom standardpunktet `$4BAE/$4BC2`, alternativet
`$4BD6/$4BEA` og lagrede koordinater/helse `$8A/$8C/$8E+aktør`.
Yamo tester `$136F`; Kage tester `$1333`, men fortegnsvalget ved `$0C38`
leser faktisk `$136F`. Det er beholdt. `$1159` leser kilde-RAM; ingen ny
myntkastregel eller uniform fordeling er lagt til.

Rom6 har standard `(44,81)` og alternativ `(56,194)`. Begge fiender kan
bruke punktet oppe ved Bruce. Rom7 har `(244,179)` og `(234,114)`, og rom8
har `(32,68)` og `(38,116)`. Valg finnes også i de øvrige rommenes tabeller;
en tabelloppføring betyr ikke at fiender naturlig er aktivert i alle rom.

Porten kjører nå den statisk oversatte `$0BFA`-rutinen, inkludert de
opprinnelige minneavlesningene. Det ekstra, faste NPC-punktet som tidligere
overskrev den valgte plasseringen på slutten av Amiga-stegene er fjernet.
Ved vanlig rombytte lagres aktive fienders helse og Bruces destinasjon
slik `$2FA5–$2FBD` gjør. Lagret inngang brukes én gang og tømmes av kildekoden.
Helse begrenses deretter som i `$0D04/$0E0D`.
Etter overlevd livstap nullstilles de lagrede X-flaggene`$8B/$8C`, slik
`$1832–$1836` gjør; dette kontrolleres også i dødsfixturene.

Full IRQ, minneavlesningsrekkefølge, inngangsanimasjoner og ordinær
spawn-/ventetjeneste er fortsatt delvise adaptere. Dette er ikke en påstand
om identisk naturlig valgfordeling eller full NPC-paritet.

## Fiender utløser bomber

### Rom 11 når Yamo går over bomben

Kontrollert 31. oktober 2026 mot kandidaten med SHA-256 øverst i dokumentet.
Rom 11 har sju bomber. Kolonne og objektrad er henholdsvis (19, 6), (24, 6),
(21, 9), (34, 9), (9, 12), (21, 12) og (34, 12). Romrutinen hopper fra
`$3CBD` til `$3228` før figurenes kontakt beregnes ved `$1C0D → $5212`.
En aktiv Yamo i gangtilstand kan tenne en bombe. Objektpasset velger aktør
1, leser kontaktbiten fra `$B7` og undersøker cellene under kroppsmasken.
Ved treff på `$60` går det til `$306B`. En allerede tent bombe eller tre
opptatte tidsregistre gir ingen ny tenning.

Det synlige signalet kommer først ved eksplosjonen. I rom 11 er øverste
bombetegn `$60` i tegnsettet ved `$A800`. Radene er
`82 82 69 69 55 55 55 55`. Ingen av pikselparene bruker individuell
tegnfarge (bitpar 11). Tenning skriver `$FD` over `$F8` for dette ene
tegnet ved `$30CA`. Nedre tegn `$E0` beholder fargen. Bombens piksler
forblir dermed identiske mens Yamo går videre. Åtte spillsteg etter tenning
tegner `$323D–$325A` første eksplosjon. Ved gammel teller 20 setter
`$328A–$32B5` grafikk og farge tilbake.

`python tools/audit_r11_yamo_walk.py` kjøres etter `./test-c64-actors.ps1 -CompileOnly`.
Kontrollen bruker styrte startplasseringer, går fra begge sider på alle
sju bomber og kjører både med AI og med Yamos joystick. I 28 av 28 forsøk
reserverte aktør 1 tidsregisteret, og eksplosjonstegnene dukket opp 24
modellerte PAL-felt senere. Hele kilde-RAM stemte med vertsbygget av
spillmotoren etter hvert felt og hvert hovedsteg. Dette er kontrollert
kjøring av kandidatens maskinkode med modellert VIC-kontakt og feltgrense.

I det ordinære WinUAE-bygget (EXE SHA-256
`88dc94012e801d56e80fcaed767a5d158bab451ed10b6902ca97ae9df0d31528`)
ble rommet åpnet med testmenyen. Bruce stod stille på mellomnivået mens
Yamo kom fra høyre på øverste avsats og passerte bomben i kolonne 24.
Ingen figurposisjoner eller tidsregistre ble skrevet av testen. Ved
spillsteg 417 var telleren 6 og bomben så ut som før. Ved steg 423 og
426 viste den aktive skjermbufferen begge eksplosjonsformene. Alle 768
piksler i utsnittet på 24 × 32 piksler stemte med kildebildet ved hvert
av de tre stegene. Den gule markøren under utsnittet viser bombens plass.

![Yamo passerer bomben på øverste avsats i WinUAE](../reference/analysis/r11-yamo-walk-2026-10-31/winuae-room11.png)

Brukerens konkrete passering der eksplosjonen uteble står åpen i
[testlisten](ACTIVE_TESTS.md). Et lagringspunkt før kontakt kan vise om
bomben var ledig, om Yamo fikk kontakt, og hva som faktisk ble tegnet.

### Felles rutiner

`$2E39–$2E6D` behandler Kage, Yamo og Bruce i den rekkefølgen; bare
dødstilstand25 og inaktive aktører utelates. Objektkontaktbiten `$B6,X & 2` gjelder de
seks skannede cellene. Bombetegn`$60` går via `$2EF7` til `$306B`, uten
en test som begrenser utløsning til Bruce.

`$306B–$30D3` krever fargeklasse ulik5, reserverer den første ledige av tre
poster `$4FDE..$4FE0`, lagrer kolonne/rad minus1 og setter attributt`$FD`.
Amiga sjekket tidligere bare dette for Bruce. NPC-passet gjør nå også dette.

`$3228–$32CB` bruker gammel tellerverdi ved fasevalget:8 gir eksplosjon og
effekt`$8D`,12 bytter form,16 går tilbake til første form,20 rydder bildet
og24 frigjør posten. Tegn`$71..$7C` er farlige under eksplosjonen.
Utløsning alene er altså ikke umiddelbar skade.

`$304B` sender farerammede NPC-er til `$3001`, fjerner dem og velger ny
returventing via `$0D42`. Native kode bruker nå denne faktiske grenen,
inkludert de selvmodifiserte tabelloperandene ved `$0D55/$0D85`.
En lokal tellekompensasjon hindrer Amiga-adapteren i å trekke den nye
returventingen allerede i samme steg som eksplosjonen fjerner fienden.

## Bruce skriker, står stille og mister et liv

`$3057` ber om effekt`$8C`; `$3068 → $407D` velger tilstand25/teller16.
`$216B–$217A` lar posisjonen stå stille og går til livsgrenen `$1818`
på siste aktøroppdatering. `$27B8` velger positur8. Lyden er den eksisterende
kildebaserte Paula-utgaven av denne effekten; ingen ny lyd er generert.
Portens livsadapter bruker fortsatt negativ helse som intern dødsmarkør;
kildevalget som sammenlignes her er BF25/CE16, positur og stillstand.
Dette erklærer ikke full helse-/HUD-paritet under dødssekvensen.

Grunnforløpet fantes allerede. To Amiga-avvik er rettet:

- Negativ kamphelse blokkerer ikke lenger objektpasset. C64 utelater
  tilstand25, ikke alle med negativ helse; en eksplosjon kan erstatte en
  pågående kampdød med tilstand25. Livstap telles bare én gang.
- En gammel veggretting24 får ikke overstyre dødsposituren. Dødsgrenen
  erstatter den, mens de fysiske koordinatene beholdes gjennom stillstanden.

Udødelighet i testmenyen undertrykker fortsatt død med hensikt. For vanlig
lytte-/dødstest må denne være av; uendelige liv lar dødssekvensen gå normalt.

## Kontroller

`test-bombs-entry.ps1` sammenligner640 inngangsvalg over20 rom med faktiske
6502-instruksjoner, inkludert minnegrensene191/192, begge utfall og lagrede
innganger. Tre aktørkontakter med en ekte bombe i rom7 sammenlignes med
`$2E39`; begge NPC-er kontrolleres også mot eksplosjonsfjerning.
Tre tidligere Bruce-tilstander sammenlignes gjennom16 dødsoppdateringer
hver.42 NPC-farekontroller dekker aktuelle bomberom og tid0/25/32.

44 utvalgte inngangs-, bombe-, døds- og integrasjonskontroller inngår også
i session-fixturen på verten og68000. Starttilstander og minneavlesningsdata
er injisert og merket; dette er ikke naturlig C64-gjennomspilling.

[Kildekontroller og disassembly](../reference/analysis/bombs-entry-2026-10-26/report.json).
Gjeldende bygg og native resultat bindes i
`reference/validation/bombs-entry-delivery.json` etter maskinkontrollen.

**Historisk måling for BOMBS-ENTRY-bygget.** Gjeldende kode, spawn-rekkefølge
og nye maskinkontroller beskrives i [spawn-leveransen](ENEMY_SPAWNS.md).

Maskinkontrollen er fullført: to A500-CLI-løp på6000 felt hver består
funksjonsportene, inkludert44 nye kontroller per løp og de tidligere
session-/vegg-/bevegelses-/nett-/lydkontrollene. Begge matcher vertens
kontrollerte kampresultat:62 treff,6 nedleggelser,10 fiendeinntredener og
2 Bruce-dødsfall/tilbakestillinger. OS gjenopprettes begge ganger.
Største sammenhengende Chip-blokk er60832 byte.967/963 felt er forsinket,
med maksimal avstand3 perioder; stabil feltkadens er fortsatt åpen.
Normal EXE er223036 byte, ADF901120, og `C:start` peker på normalbygget.

### Kontrollerte langtidskjøringer

Første to native løp bestod situasjonskontrollene, men den samlede
kampreplayen hadde62 treff mot vertens64. De ble avvist av sammenligningen;
rådata og EXE er bevart under `uncontrolled-read-diagnostic/` i analyseområdet.
Ingen forventning eller sammenligningsport ble senket for å godta dette.

Etter at `$0BFA` ble koblet inn, leser `$1159` også levende RAM som SID-
driveren endrer, blant annet`$F6..$FB`. Verten avspiller én lydoppdatering per
kontrollfelt, mens native avspilling følger faktiske maskinfelt og innhenter
forsinkelser. Disse er forskjellige inngangsdata til en minnebasert velger.

Den ordinære kampreplayen injiserer derfor nå samme høye lesebyte`$17=$68`
på begge plattformer, før replayen starter. Leseren bruker da kandidatens
uendrede spritebytes i`$6800`-området. Selve velgerkoden og den lave
pekertelleren kjøres fortsatt normalt. Rapporten oppgir`source_reader_page=104`,
og testporten krever denne verdien i tillegg til identiske kampresultater.
Dette gjelder bare kontrollreplayen; normalspill og rom-/dørinspeksjon får
ingen slik overstyring. De640 separate kildevalgene er fortsatt primærkontrollen
av inngangsreglene. Langtidsreplayen fastsetter ikke naturlig C64-valgfordeling.
