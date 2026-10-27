# Historisk M4-status, før C64-rekonstruksjonen 25. oktober

## Nåværende leveranse — første M4-kandidat

Spillet heter nå **Bruce**. [Oppstarten](BRUCE_STARTUP.md) får et kort
karateskrik og en lasteflate; brukerens illustrasjon avventer bildevedlegget.

Nyeste arbeid 24. oktober: [flere animasjonsfaser og dynamiske åpninger](ANIMATION_AND_OPENINGS_2026-10-24.md).
Brukeren tillater friere Amiga-animasjon. V2 har vekslende klatresider,
flere kamp-/løpefaser og Ninjas bambusstav. C64-kildene styrer de første
dynamiske åpningene fra rom 2 via rom 6/7 og tilbake til rom 3.
Yamos hud og kroppsform er deretter korrigert, og helsefeltene har fått
navnene KAGE, YAMO og BRUCE; se [den visuelle rettelsen](YAMO_AND_HEALTH_HUD.md).
Den [første grafikk- og spillbarhetskandidaten](NEXT_CANDIDATE_2026-10-24.md) beholdes som historikk.
Dette viderefører M4 og starter M5 med nye figurer/bakgrunn; ingen av de to
milepælene er godkjent som fullført. M4s krav om naturlig gjennomspilling og
M5s krav om ferdig presentasjon gjelder fortsatt.

Oppdatert 24. oktober: Se [20-romsutgaven](M4_ROOM_EXPLORER.md). Alle 20 rom
har nå inspeksjon med egen blokkgeometri og to bakgrunnsslots, mens naturlig
progresjon, øvrige dynamiske dører og feller fortsatt gjenstår. Denne utvidelsen
erstatter ikke M4s ferdigkrav. [Aktive tester](ACTIVE_TESTS.md) erstatter den
gamle komplette manuelle listen. [Grafikkflyten](AMIGA_ART_PIPELINE.md)
beskriver uttrekking, lagret prompt og formatkontroll for senere AI-kunst.

Den første leveransen nedenfor er beholdt som historikk:

To rom er spillbare, lanterner kan samles og innsamlingen beholdes ved retur.
Koordinater og koblingstabeller for alle20 rom er ekstrahert fra C64-kandidaten.
Se [M4-kandidaten](M4_ROOMS.md) for rute, tester, avvik og ressursmålinger.

M4 er ikke fullført. Resterende rom, nøyaktig geometri, bro-/fellelogikk,
spillermoduser og full gjennomspilling gjenstår. M3s kampforløp og M2s tidligere
kollisjonsavvik er fortsatt åpne; denne leveransen godkjenner dem ikke.
