# Bruce: bevegelse, spark og veggkontakt

25. oktober 2026. Kilde er den frosne Remember/T64-kandidatens faktiske bytes,
SHA-256 `092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Kandidaten er fortsatt ikke bekreftet som valgt urørt 1984-utgave. Originaler
og kildeutsjekkinger er uendret. Atari-/nettleserrekonstruksjonen brukes ikke.

## Feilen som lot Bruce sparke gjennom vegger

Amiga-koden flyttet sparket og returnerte før den tidligere X-veggsjekken.
Denne sjekken brukte dessuten alltid ståmaske 2 og angret bare én X-endring.

C64 gjør dette i en annen rekkefølge: `$5212` beregner poseavhengig
pikselkontakt, deretter behandler `$1C5B` venting, bevegelseshistorikk og
svart kontakt **før** hopp-/spark-/retningskoden. Objekt- og kampbehandlingen
kommer før aktøroppdateringen i hovedløkken. Vi har beholdt denne rekkefølgen.

Kontaktene er bitklasser fra tegn-/figurplanene. Klasse 8 gir svart hindring;
klasse 4 er nett. Klasse 1 er ikke en generell sidevegg, og klasse 2 er ikke
automatisk solid. Det er ikke innført nye veggrektangler eller en regel om
at alle synlige grafikkpiksler stopper Bruce.

## Portert veggrutine

`core/source_wall.c` dekoder `$1C68–$1D6E` og `$24B7–$24EA` direkte:

- `$4F57–$4FDA` rommer nåværende forflytning og ti eldre records. Hver record
  teller opp, ned, venstre og høyre. Y-enheten er én piksel; X-enheten er to.
- Historikken flyttes bare når nåværende bevegelsestellere er ikke-null.
  Aktørens handlingsventing kommer før denne operasjonen.
- Svart kontakt reverserer en record gjennom de originale retningshjelpernes
  grenser. Den behandler opp/ned/venstre/høyre i kildeorden. Dette er ikke
  bare å sette X tilbake til én lagret koordinat.
- Nedoverhistorikk har en annen retry-gren enn oppover/sideveis historikk.
  Opptil ni gjennomganger og det betingede ekstra sidesteget er beholdt.
  Kontaktflagget beregnes **ikke** på nytt inne i denne sløyfen.
- Resultatet er tilstand 24/teller 64. Klar kontakt gir først teller 0;
  ordinær handling kan deretter fortsette. Ved fortsatt svart kontakt og tom
  historikk bruker koden rommets standardankomst via `$4BAE/$4BC2`, akkurat
  som `$24DB–$24EA`. Dette er ikke en ny vilkårlig respawnposisjon.
- `$4FDB`-positurlåsen og tilstand 24s valg av figurmaske er beholdt.
  `$27C1–$27D7` bruker tidligere positur og de to spritebreddene fra `$5CBF`.
  Disse 70 metadatabytene er tatt ut fra samme binær.

Den integrerte historikkbroen registrerer Amiga-aktørens faktiske
forflytninger og Bruces rekyl i kildeenheter. Den dekodede rutinen er
kontrollert mot 500 kjøringer av de opprinnelige 6502-bytene: posisjon,
retning, tilstand, tellere, venting, positurlås og alle 44 historikkbytes.
Historikkbroen gjør ikke resten av den foreløpige aktørmotoren kildeidentisk;
spesielt kan en forenklet bevegelse ha et annet hjelperforløp enn C64.

## Spark

Venstre/høyre er tilstand 12/13. `$204C/$2091` avviser nett/svart kontakt
med masken `$0C`. Svart kontakt har allerede vært gjennom veggrutinen.

| Restteller før handling | Kildens forflytning |
| --- | --- |
| 12, 11, 10 | én Y opp, én X-hjelper i sparkretning (to skjermpiksler) |
| 9 til 3 | én X-hjelper, ingen Y-forflytning |
| 2, 1 | slutt ved helmaskens faste kontakt; ellers én Y ned og én X-hjelper |
| 0 | ordinær støtte-/handlingsgren; ingen ekstra skriptet Y-forflytning |

`$288B–$28B2` velger maske 22/26 ved teller 12–10 og 24/28 ved teller 9–0.
Det tidligere ekstra nedsteget og den stående kontaktmasken under spark er
fjernet. Effekt `$84` forespørres ved teller 12 hvis sparket faktisk kjøres.
Nett/fast kontakt avslutter i kildegrenen; vi viderefører ikke spark gjennom
nettet eller bruker en vilkårlig tilbakesprett.

480 kontroller i alle 20 rom kjører faktisk `$2780 → $5212 → $1C5B` med
forskjellige sparkfaser og retninger. Native resultat sammenlignes med
posisjon, retning, sparkstatus, veggtilstand, fase, historikk og aktive
spark-/restitusjonsmasker. Koordinatene er injiserte; dette er ikke en
naturlig gjennomspilling eller en VIC-/IRQ-emulering.

## Hopp og grenser

Hoppets fasevektorer er kontrollert mot de faktiske hjelperkallene i
`$2008–$2047/$20D2–$216A`. En detalj er at `CPY #6` ved `$2111/$215C`
ser Y fra den horisontale hjelperen, ikke den opprinnelige resttelleren.
Begge nedoverkallene utføres. Grenene er ikke tolket som en antatt kurve.
Det sidelengse hoppets siste forflytning var tidligere feilaktig null.

Restteller 0 har nå en egen fase, skilt fra fritt fall 14. Første ustøttede
fallsteg er én Y-piksel, mens fortsatt åpent fall bruker to. Den ekstra
Amiga-ventingen før nytt stående hopp er fjernet. Faser for hopp, spark,
fall og veggrespons velger nå kildemasker i objekt-/vegg-/nettdeteksjonen.

54 sekvensielle original-CPU-steg sammenlignes med venstre, stående og
høyre hopp, inkludert overgang til fall og forsøk på motsatt retning.
Testen bruker et eksplisitt tomt arbeidsfelt for å isolere bevegelseskoden;
den fastsetter ikke kollisjon med gulv eller naturlig romprogresjon.

Kontaktberegningen mellomlagrer forskjøvede figurmasker for å spare 68000-tid.
Maskens faktiske, gjeldende bytes må først ha hele tofargede par og tom tredje
kolonne. Delvise par og bredere masker går gjennom den generelle pikselrutinen.
Dette gjelder blant annet masken som romkode kan endre; skriving til
maskeminnet ugyldiggjør mellomlageret. Optimaliseringen skal ikke endre
kontaktklassene. For validerte hele bitpar pakkes de fire kontaktklassene
i fire nibbler i stedet for fire byte. Det halverer disse tabellene og
sparer 17 536 byte CPU-tilgjengelig minne. Delvise masker beholder den
generelle rutinen. Bare den forespurte X-forskyvningen bygges i maskelageret.
Alle 35 Bruce-masker prøves mot den opprinnelige `$5212`
i alle 20 rom, inkludert høyrekanten og rom 5s endrede maskebytes.

Hjelperne tester grensene før endringen. X kan bli 0–302, Y kan bli 45–199.
Bruces gang/spark/klatring/fall og reaksjonsrekyl bruker disse grensene.
Ninja/Yamos separate AI-/reaksjonsadapter er ikke fullportert her.

## Det som fortsatt er åpent

- Den komplette `$1C5B`-aktørmaskinen er ikke portert. Tilstand, venting og
  historikk er fortsatt koblet til en delvis Amiga-aktørmodell.
- Gang-/klatre-/reaksjonspositurenes hele sekvens og ventelås gjenstår.
  Disse tilfellene har fortsatt eksplisitte maskeadaptere. Ny kunst er ikke
  fasit for kollisjon.
- Landing bruker fortsatt en posisjonssveip-adapter. Hele `$1D99`-grenen med
  kroppskontakt og sideforsøk, og alle støtte-/avbruddsgrener under hopp,
  må porteres før full gulv-/kantparitet godkjennes.
- Kampen bruker fortsatt foreløpige aktørbokser og sekvensiell parbehandling;
  full VIC-spritekontakt, samtidige treff og livsforløp er egne åpne porter.
  Eksisterende reaksjons-/livstimer får fortsatt avslutte også ved veggrespons,
  slik at adapteren ikke låser en Bruce med negativ helse som aktiv for alltid.
- Naturlig gjennomspilling og brukerens konkrete veggsituasjon er ikke godkjent
  av disse injiserte kontrollene. Ingen bestemte rom eller vegger ble oppgitt.
- Tidligere A500-målinger gjenbrukes ikke som native godkjenning av denne byggen.
  Strenge Chip-/feltkrav rapporteres separat fra kode-/CPU-samsvar.

Kjør `test-source-movement.ps1`, `test-core.ps1` og `test-c64-rooms.ps1`.
[Resultater](../reference/analysis/movement-audit-2026-10-25/wall-report.json) og
[adresset disassembly](../reference/analysis/movement-audit-2026-10-25/source-disassembly.txt).
Autotesten kjører også 70 små, kildeavstemte kontroller på 68000 før lydstart.

## Leveransen før spriteskiftet (historikk)

Målingene under gjelder bevegelsesbygget før C64-sprites ble standard.
Gjeldende figurdata og nye native resultater er dokumentert i
[spriteleveransen](C64_SPRITES.md). De gamle tallene gjenbrukes ikke som
ytelses-/minnegodkjenning for det nye bygget.

Vanlig EXE er219 252 byte og ADF901 120 byte. CLI-kommandoen `start`
oppdateres til dette normalbygget. Ingen interaktiv emulator er startet på
nytt som del av leveransen.

To nye6000-felts kjøringer på PAL A500 OCS/68000/Kickstart1.3/512+512
består70 bevegelses- og29 objektkontroller hver. Spill-/Paula-signaturer
matcher de kildebundne vertstestene; rom-, lyd-, tegnkontroll og
runtime-aritmetikk har0 feil. Begge gjenoppretter OS. Dette er ikke naturlig
veggtesting eller ny native gjennomspilling av alle20 rom.

Den strenge tids-/minneporten står fortsatt åpen: 225 og 224 forsinkede felt,
opp til 2 PAL-perioder mellom oppdateringer, og29 968 byte største
sammenhengende Chip-blokk mot49 152-målet. Romlasting måles separat og tar
opptil100 felt i disse løpene. Normalbyggets tids-/minnereserve er ikke målt.
CPU-kontaktdataene er redusert med17 536 byte; testens
`expansion_available_before` er18 392 byte. Feilfri fixturekjøring omdefinerer
ikke de strenge grensene. Eldre native resultater er arkivert separat.

[Gjeldende kildebundne leveranserapport](../reference/validation/movement-delivery.json).
