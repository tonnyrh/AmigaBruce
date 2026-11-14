# Lanterner, bakgrunn og figurkontakt på PAL A500

Den frosne Remember/T64-kandidaten har SHA-256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Identiteten som urørt 1984-utgave står åpen.

* **Lanterner.** Rutinen ved `$331C–$336D` følger rompekeren fra `$4CE2`.
  Ved `$3361` nullstiller den posten for en tatt lanterne og reduserer
  telleren for rommet. Amigaen oppdaterer derfor visningens maske for det
  aktive rommet i et vanlig steg. Ved ny start, debughopp, endret rom,
  romlasting (også etter dødsfall) eller bytte av spiller leser den alle
  20 lister. Tospillerrutinene ved `$183B` og `$0FED` kan bytte ut
  innholdet i listene. Styringen av dører og poeng leser fortsatt kildedataene.
* **Maling av bakgrunnen.** Når motorens eksisterende flagg viser at
  tegn, animasjon og tegnsettbank er uendret, kan Amigaen hoppe over
  nullstilling av radmaskene, malekallet og fordelingen til de to
  skjermbufferne. Vanlig opprydding og vedlikehold av kontaktdata kjøres.
  Endringer som kom etter en delvis maling blir fortsatt liggende i kø.
* **Gjenoppretting av skjermbufferen.** Hver buffer har ett byte som sier
  om den kan ha ventende bakgrunnsarbeid. Begge køene beholder den samme
  prioriteten, startposisjonen og grensen på 5 000 byte. Etter arbeid
  kontrollerer tegneren begge køene før den merker bufferen som ajour.
  Senere bilder kan hoppe over begge søkene til det kommer nye endringer.
* **Figurkontakt.** Ved `$5380`, `$539A` og `$53B4` sammenlignes tre
  pikselkolonner i rekkefølge. Den native 68000-løkken beholder D0 innen
  0–255 mellom kolonnene. Den kan fjerne tre `MOVEQ` per rad og nå
  scratchbyten `$4E` med et fortegnet avvik fra pekeren til `$4EED`.
  Ett færre adresseregister må lagres og gjenopprettes. Leserekkefølge,
  adresseoverlapp, treffskrivinger og servicegrenser er bevart.

## Hva som er kontrollert

`check_lamps.c` sammenligner sesjonens 20 masker med en ny full avlesing
etter hvert spillsteg og hopp. Oppsettet legger inn en bestemt
lanterneplukking og dødelige treff. Det kontrollerer tre dødsfall, to
spillerbytter og 42 romhopp ved 303 kontrollpunkter. Dette er en
kontrollert prøve med den levende motoren. Vanlig rombytte med joystick
kontrolleres også i CLI-utgaven.

`check_queue.c` sammenligner de gamle og nye kopirutinenes rektangler,
rekkefølge, radpekere og gjenstående arbeid for begge skjermbufferne.
9 216 gjennomganger omfattet 6 204 budsjettstopp og 1 252 tomme passeringer.
Kontaktprøven kjører den lenkede 68000-koden mot de eksisterende
192 radvektorene. Den sammenligner hele 64 KiB og parameterblokken for
hvert tilfelle. Mikroprøven kjører gammel/ny/ny/gammel kode i samme
WinUAE-instans. Ni kombinasjoner av 1, 4 eller 8 rader og tomme,
spredte eller tette treff tok 3,6–6,7 % mindre tid i den nye løkken.

De uprofilerte kamprutene måler faktisk tid for spillsteg og faktiske
Paula-publiseringer. De separate profilprøvene tar tid rundt
bakgrunnsmalingen og bakgrunnskopieringen. Med lanterneendringen alene
brukte malingen 4 040 rasterlinjer på 180 kall. I den valgte varianten
brukte den 2 258 på 183 kall. Gjenoppretting av skjermbufferen gikk fra
4 924 linjer på 224 kall til 4 450 på 219 kall. Tidsbesparelser i enkeltrutiner
kan ikke summeres til tid spart i spillet, siden mengden venting ved
presentasjon også kan endre seg.

En pilot brukte køens radpeker for å avgjøre om det gjensto arbeid. Den
brukte 766 felt i trappen, men hadde ett tomt Paula-felt i den andre
langkampen. En annen pilot brukte egne flagg for de to køene og fikk to
tomme og to doble felt. Den leverte varianten bruker én felles indikasjon
per skjermbuffer og kontrollerer de gjenværende radmaskene etter kopiering.

I sluttbygget bestod den egne 68000-reprisen 53 motorkontroller og
1 200 løkker. Det lagrede kampbildet var identisk med forrige bygg i
alle 40 960 byte. Største ledige Chip-blokk etter lasting i testutgaven
var 52 632 byte. Den vanlige CLI-utgaven kjørte 6 024 felt etter pause
og krysset rom 1 → 2 → 1 med joystick. Diskettutgaven kjørte 6 005 felt
etter pause og ga turen til spiller 2 i rom 1 med fire liv. Begge hadde
null tapte lydtikk i målevinduet.

## Gjentakelse

Med forrige målemiljø fra [direkte figurtegning](../actor-draw-2026-11-01/README.md)
kan `build_probe.py short <ny mappe>` og `build_probe.py long <ny mappe>`
bygge de to måleutgavene. Bruk samme ruter i `op-score-2026-10-31/run.ps1`.
Vertsprogrammet for lanternene lenkes med de samme motorobjektene som
`test-source-visibility.ps1`. For køprøven trekkes `restore_source_cells`
ut fra forrige og ny `amiga/main.c` som henholdsvis `before_restore` i
`queue_before.h` og `after_restore` i `queue_after.h`. Kompiler med
disse to headerne og `core` på inkluderingsstien. Kontaktprøven og mikroprøven bruker
[`proof.c`, `vectors.bin` og `micro.c`](../op1-row-walk-2026-10-31/)
med den nye kontaktobjektfilen. `python tools/verify_op_finish.py`
kontrollerer den samlede leveransen. [Råmålinger og byggidentiteter](delivery.json).
