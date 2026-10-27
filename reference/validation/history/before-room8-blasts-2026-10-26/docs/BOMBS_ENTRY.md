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

`$2E39–$2E6D` behandler Kage, Yamo og Bruce i den rekkefølgen; bare
dødstilstand25 utelates. Den globale objektkontaktbiten `$B6&2` gjelder de
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
