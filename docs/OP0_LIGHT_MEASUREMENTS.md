# OP0: lett måling av dagens spillbane

31. oktober 2026. OP0-diagnosen er gjennomført. **Normalspillet er ikke
endret eller gjort raskere i denne leveransen.** Neste avgrensede CPU-mål
er radbehandlingen i kontaktkjeden, OP1.

## Resultat uten autotesthashing

PAL A500 OCS, MC68000, Kickstart 1.3, 512 KiB Chip + 512 KiB slow.
Hver rute varmes opp i 240 kildeoppdateringer og måles i 240 nye.
Oppstart, lasting, musikkintro og rapportskriving ligger utenfor perioden.

| Rute | PAL-felt | Felt per spillsteg | Tapte lydserviceticks |
| --- | ---: | ---: | ---: |
| Rom 1, Bruce alene | 720 | 3,00 | 0 |
| Rom 1, Kage | 724 | 3,02 | 0 |
| Rom 1, Yamo | 810 | 3,38 | 0 |
| Rom 1, begge | 1030 | 4,29 | 19 |
| Rom 1, begge, gjentatt | 1031 | 4,30 | 19 |
| Rom 12, opp/ned på klatreområdet | 814 | 3,39 | 0 |
| Rom 13, Yamo | 736 | 3,07 | 0 |

Aktørtellingene bekrefter de angitte figurene gjennom hele den målte
perioden. Rom 12 har ingen aktive fiender i denne ruten; Bruce er i
klatretilstand ved alle 240 målte steg. Ruten forblir i rom 12. Rom 13-ruten
forblir i rom 13 med Yamo aktiv, men tester ikke naturlig retur etter nederlag.

Rom 1 med begge bruker 278487 linjer på arbeid og 42340 på venting i den
første lette prøven. Resterende 1539 linjer ligger mellom målegrensene og i
tellere/bokføring. Verste målte arbeidsblokk er 1636 linjer. Dette er ikke
gjennomsnittlig emulator-FPS; kildeoppdateringene går faktisk tregere enn
den ordinære tre-feltsrytmen i denne ruten.

Største ledige Chip-blokk er 85440 byte i det lette bygget, største slow-
blokk 17384 byte. Målebyggets minnebruk er forskjellig fra det større
fixturbygget med 52632 byte Chip-reserve; tallene må ikke blandes.

## Målingens egen kostnad

Alle lette prøver kompileres med **BL_AUTOTEST=0**. Dermed kjøres ingen
autotestfixturer, RAM-/lydhashing eller bildeopptak. Normal renderer og
lyd-/DMA-bane beholdes. Alle 18 øvrige objektfiler, inkludert motor, lyd,
DMA og session, er byteidentiske med normalbyggets; bare main er endret.
De lenkede programmene har forskjellige adresser og er ikke samme EXE.

En egen kontroll fjerner de nye tidsstemplene per løkke og spillsteg,
men beholder avgrenset rute og start-/sluttmåling. Den gir **1017 felt og
17 tapte lydticks** mot 1030/19 med flere tidsstempler. Forskjellen er
omtrent 1,3 %. Den lette målingen har altså fortsatt en synlig kostnad;
også den minimale kontrollen er instrumentert. Begge viser over fire
felt per steg med begge fiendene.

Det profilerte bygget bruker 1270 felt og har 24 tapte lydticks. Det er
omtrent 23 % mer tid enn den lette prøven. Profilen brukes til å finne
kostnader, aldri som normalbyggets tempo. Flere felt gir dessuten flere
felt-/VIC-/lydkall og kan endre faser i det kontrollerte forløpet.

## Valgt neste mål: OP1 kontaktens radbehandling

Profilens eksklusive kostnader, linjer per kildeoppdatering:

| Blokk | Linjer/steg i profil | Kommentar |
| --- | ---: | --- |
| Kontakt, egen tid | 156,4 | Uten profilerte barn; inkluderer ikke-oppsplittede native hjelpere |
| Kontaktrader | 181,1 | 2839 kall; største delblokk i kontaktkjeden |
| Maskejustering | 37,0 | 720 kall |
| VIC | 192,7 | 1270 feltkall; ikke samme antall som uprofilert rute |
| Spritebygging, egen tid | 104,0 | Uten separat kopiprimitiv |
| Spritekopiprimitiv | 56,2 | 1200 kall |
| Objekter | 91,7 | 240 kall |

Kontaktens tre første blokker gir til sammen **374,4 profilerte linjer per
steg**, uten å telle felt-/lydservice inne i kontakten dobbelt. Dette er
et rangeringsgrunnlag, ikke en lovet gevinst eller en beregning av hvor
mye normalspillet kan akselereres.

Neste pilot avgrenses til `$537E–$53E3`: `source_contact_scan` og
`bl_contact_rows8`, innen kjeden `$5212–$55AA`. Det finnes allerede native
68000-kode her. Undersøk den gjenværende kostnaden i batchoppsett,
register-/klasseoverføring og den ordnede radløkken før ny kode velges.
Behold lane-rekkefølge, aliaser, byteoverløp og de eksisterende
åtte-raders servicegrensene. Ikke legg til en ny generell maske-cache eller
gjenta de avviste tomhetsbanene uten en ny, konkret begrunnelse.

Frossen kildehash:
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Remember/T64-kandidaten er fortsatt ikke sertifisert som urørt 1984-utgave.
Denne OP0-runden endrer ingen kildebasert spillregel.

## Reproduksjon og begrensninger

Innganger og rådata ligger i `reference/analysis/op0-light-2026-10-31/`.
`identity.json` binder kildefiler, måleprogram, rom, fiendemaske og rute.
`a500.uae` dokumenterer målmaskinen. Kjør
`python tools/verify_light_op0.py` for kontroll av rapporten.

Dette er diagnostiske ruter med udødelighet, uendelige liv, automatisk
start/romvalg og eventuell eksplisitt fjerning av utelatte fiender.
Fiendefjerningen har også CPU-kostnad. Testinngrepene bestemmer ikke
originalens oppførsel. Korte målinger erstatter ikke to 6000-felts
sluttkjøringer, naturlig C64-spilling, korrekt original raster-/inputfase,
stackmargin eller fysisk A500. Rom 13-funnet om Yamo står fortsatt åpent.

Den første emulatoroppstarten ble stoppet av Windows-sandkassens DLL-feil;
målingene ble deretter kjørt med godkjent oppstart utenfor sandkassen.
Den gamle ADF-pakkeren feilet også i sandkassen. OP0 bruker derfor den
private CLI-utgaven og hevder ingen ny ADF-akseptanse. Normal EXE/ADF er urørt.
