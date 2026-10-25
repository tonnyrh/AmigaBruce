# M4 — første spillbare del: lanterner og R01 ↔ R02

2026-10-21. **M4 er påbegynt, ikke fullført.** Denne kandidaten har to spillbare
rom. De øvrige atten rommene, feller, bevegelige broer, spillermoduser og
sluttsekvens gjenstår. M2/M3s åpne paritetsavvik er fortsatt åpne.

## Spill

Bygg med `.\amiga-build.ps1`, start med `.\amiga-run.ps1`.
Samle de gule lanternene ved å hoppe borti dem. En tatt lanterne forblir borte
ved retur til rommet i samme spilløkt. Tilstanden lagres foreløpig bare i RAM.
Kjernen fører 125 poeng per lanterne; poengtavle og originalens poeng-/livregler
er ikke ferdige.

Bruk det midtre nettet i første rom, gå til plattformkanten og hopp til øvre
høyre avsats. Gå videre mot høyre for å komme til rom 2. Fra venstre kant på
øvre plattform i rom 2 kan du gå tilbake. Skjermen viser romnummer.
Overganger videre til rom 3–20 er stengt inntil geometri og romregler er klare.

Rom 1 beholder den målte bevegelseskjernen. Rom 2 har en foreløpig strukturell
skisse: plattformer og et nett, ikke originale pikselmasker eller bro-/fellekode.
Fiender kommer tilbake med kandidatens romlokale spawnregler; originalens
forfølgelse mellom rom og nøyaktige pauser ved inntreden er ikke implementert.

## Referansegrunnlag

`tools/analyze_c64_rooms.py` leser romtabeller fra den hash-låste kandidatens
minnedump. Ingen editorstandarder brukes som fasit. Alle 20 romstrømmer er
dekodet og lanterneregnskapet kontrollert. Eksporten inneholder koordinater,
antall, ankomstposisjoner og dørkoblinger; ingen original grafikk eller 6502-kode.
`valid` i dørdata betyr at en dør finnes i den statiske romstrømmen og har en
ankomst. Dynamisk opprettede dører kan mangle der, selv om koblingen finnes.

Tre nye opptak er skilt fra de eldre, fryste bevegelsesopptakene:

- ROOM-0001: forsøk uten hopp tok ingen lanterner og nådde ikke romutgangen.
- ROOM-0002: den fullførte lanterneruten viser første innsamling ved steg 13,
  x=16/y=184. Det andre forsøket støtte på romlasting med endret spillrytme;
  bare det ferdige, dobbelt gjentatte lanterneforløpet brukes som evidens.
- ROOM-0003: komplett tur-retur, gjentatt identisk to ganger. Rom 1→2 ved
  steg 171 gir x=6/y=98; retur ved steg 194 gir x=298/y=98.

Vertsreplayet treffer første lanterne på steg 13 og går inn i rom 2 på steg 171
med samme ankomstposisjon. Returen skjer på steg 198, fire steg for sent.
Alle senere posisjons- og innsamlingstelleravvik beholdes i
`reference/validation/candidate-room-routes.json`. Første lanterne og riktige
ankomstpunkter er regresjonskrav; hele rutene har ikke godkjent paritet.

Lanternefeltet undersøkes før bevegelse, som i `$1C10` før `$1C29`. Søkets
tre kolonner og to rader følger `$1C39/$2E6E`. C64s supplerende piksel-/
kollisjonsflagg er ennå ikke gjenskapt, og dette er en dokumentert begrensning.

## A500-validering

`.\test-amiga.ps1 -RoomsTest` kjører 900 tegnede bilder med vanlig
joystick-input: én lanterne samles, Bruce går til rom 2 og returnerer. Ingen
teleportering eller endring av spillminne brukes. Samme input kjøres i
vertskjernen, og rombytter, innsamling, poeng og sluttilstand sammenlignes.

Begge bakgrunnene tegnes ved oppstart og ligger i Chip RAM. Rombytte bruker
en OCS-blitterkopi av den ferdige bakgrunnen; hver skjermbuffer oppdateres én
gang. Lanternenes gamle bakgrunn gjenopprettes uten å tegne hele rommet.
To 40 KiB rombilder, to skjermbuffere, Copper og arbeidsområder gir 166 944 byte
eksplisitt Chip-allokering i instrumentert bygg. Største ledige Chip-blokk etter
lasting er 271 240 byte i den siste målte romprofilen.

Romtesten har to lastinger og totalt åtte PAL-felt over fire oppdateringer av
skjermbuffere; største enkeltintervall er to felt. Disse fire eksplisitte
romkopiene måles separat. Vanlige spillbilder beholder kravet om ett felt;
romtesten mistet ingen vanlige spillbilder. Dette sertifiserer ikke lik
lastetid som C64: referansen har også særskilte gap ved rombytte.

Den første løsningen tegnet rommet på nytt under bytte og brukte opptil 112
felt per intervall. Det er erstattet av de ferdige rombildene. En tidlig
kampprøve fant også en feltoverskridelse; overflødige lanterne-/dørsøk er fjernet
fra vanlig bakkekamp. Bare den endelige kildehash-låste prøven brukes som
leveransegrunnlag.

Ingen fysisk A500 eller iPhone-nettemulator er testet i denne leveransen.

## Rettelse av gulv ved rombytte (2026-10-22)

Den nedre returen fra R02 har ankomst Y146 i kandidatens dørdata, mens
R01-blokkutgavens høyre gulv opprinnelig lå på Y144. Bruce ble derfor plassert
to piksler under gulvet og falt gjennom det. Første rettelse flyttet føttene
til nærmeste gulv ved ankomst, men lot det synlige trinnet mellom rommene stå.
Den løsningen er erstattet: R01s nedre høyre gulv ligger nå på Y146, likt R02s
venstre gulv og kandidatens dørankomster. Gulvgrafikk og kollisjon bruker samme
geometri. Ingen høydejustering utføres ved romankomst; rå dørdata beholdes.
Øvre forbindelse er Y98 på begge sider. R01s separate venstre plattform på
Y101 er fortsatt en annen plattform, ikke denne romforbindelsen.

Vertstesten krever like gulvhøyder på begge sider av alle spillbare dører,
krysser øvre og nedre forbindelse begge veier og kjører åtte logikksteg etter
hver ankomst for å kontrollere at Bruce blir stående uten høydeendring.
Skjermdumpene fra Amiga-romtesten (R02) og bevegelsestesten (R01) er også
kontrollert: nedre gulvkant ved R01s høyre kant og R02s venstre kant tegnes
begge på framebuffer-rad 178, altså spillfelt-Y146 pluss skjermoffset 32.
Den eksisterende A500-romruten dekker øvre forbindelse; nedre retur er
regresjonstestet i vertskjernen, ikke i et nytt C64-opptak.

## Kant-hopp og visuell forsinkelse (2026-10-22)

Gåbevegelsen tegnes jevnt over tre PAL-felt, mens logikken allerede har flyttet
Bruce fire eller seks piksler. Ved en kant kan tegningen derfor ligge etter
logikkens fotpunkt. Det tidligere ekstra hoppvinduet på ett logikksteg er nå
fjernet etter beslutningen om å følge C64-logikken. Hopp krever støtte ved
sats. Vertstestene dekker sats før kanten, avvist sats etter kanten og låst X
under påfølgende fritt fall. Visuell utjevning endrer ikke dette vilkåret.

Gulvkontakten før bevegelse beregnes én gang og gjenbrukes av valg av
liggestilling, angrep og hopp; kontakten etter bevegelse undersøkes separat.
Denne optimaliseringen beholdes for A500s feltbudsjett.

Den siste romrapporten gjelder to filsystemoppstarter. Et kort ADF-romforsøk
skrev ingen rapport innen tidsgrensen og regnes ikke som bestått.
Standard ADF-oppstart og lang ADF-kampkjøring er testet separat.
