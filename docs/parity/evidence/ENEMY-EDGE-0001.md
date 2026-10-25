# Ninja ved høyre utgang — 2026-10-22

Feilen i Amiga var en manglende NPC-utgang: en fiende på den øvre høyre
plattformen beholdt retningen og ble klemt mot skjermgrensen. C64 lar ham
forlate rommet gjennom døren. Det er ikke en ny regel om å snu straks og
finne korteste vei til Bruce.

Ny måling fra det frosne, trenerfrie C64-utgangspunktet bruker bare vanlig
joystick: høyre 64 steg, nøytral 64, venstre 64, nøytral 168. To kjøringer
gir identiske 361 observasjoner, uten rombytte eller kampkontakt.

| Hendelse | C64 | Amiga vertskjerne |
| --- | --- | --- |
| Ninja kommer inn, X294/Y98 | Steg 96 | Steg 96 |
| Ninja forlater høyre dør, X302/Y98 | Steg 114 | Steg 114 |
| Ninja kommer inn igjen, X294/Y98 | Steg 274 | Steg 274 |
| Første bevegelse mot venstre etter retur, X290/Y98 | Steg 290 | Steg 290 |

Ventetiden mellom utgang og retur er 160 spillsteg, omtrent 9,6 sekunder.
C64-telleren leses som 160 ved utgangen. De fulle romavhengige tellerne er
ekstrahert fra `$131F+rom` for Ninja og `$135B+rom` for Yamo. `$2F90/$3001`
fjerner NPC-ens aktive bit ved døren; spillerens rom blir ikke byttet.

Amiga bruker nå de synlige dørene for fiendeutgang og disse ventetellerne.
Utgangen er ikke et nederlag og øker ikke poeng, rombytter eller dødsteller.
En egen vertstest kontrollerer at Ninja kommer tilbake vendt mot Bruce og
kan nå gulvet under plattformene. Solid gulvkant nederst er ikke en dør.

Dette godkjenner ikke hele navigasjonen: 156 senere/øvrige posisjonsavvik
beholdes i sammenligningsrapporten. C64 kan halvere eller variere tellere i
andre sammenhenger; her brukes den fulle tabelltelleren som ble målt for
Ninja. Andre dører er tabellbaserte, og full gjeninntreden med skadet fiende,
romspesifikk oppførsel og opprinnelig retail-utgave er fortsatt åpne punkter.

- Opptak: `reference/traces/ENEMY-EDGE-0001.json`.
- Input: `reference/scenarios/ENEMY-EDGE-0001.json`.
- Analyse: `reference/validation/enemy-room-edges.json`.
- Regresjonen kjøres av `test-parity.ps1` gjennom `compare_enemy_edges.py`.

## Oppfølging av fortsatt manuell feil

Brukeren rapporterte fortsatt fastlåsing i rom 1, øverst til høyre etter
forrige rettelse. Det regnes som en gjenåpnet feil. Emulatorvinduene var
lukket ved oppfølgingen, så den aktuelle tilstanden kunne ikke leses av.

`test-amiga.ps1 -EnemyEdgeTest` gjentar nå samme vanlige input i det
kompilerte A500-spillet. Den krever alle fire tabellhendelsene, inkludert
utgang mens Bruce står på gulvet under, uten at spillerens rom skifter.
Testen dekker selve 68000-koden og rendererens vanlige kjøring. Det er en
avgrenset regresjon, ikke bevis for at alle manuelle fastlåsinger er løst.
Rapport: `reference/validation/a500-enemy-edges.json`.

Den korte ruten bestod to påfølgende filsystemoppstarter på A500-profilen.
En tidligere 6000-felts ADF-kjøring bestod også hendelsene, men den erstattes
som sluttrapport av den korte testen. Et kort ADF-forsøk skrev ingen rapport
og feilet ved opprydding; det teller ikke som bestått.
