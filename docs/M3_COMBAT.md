# M3 – kampadapter og kildeavklaringer

Oppdatert 25. oktober 2026. **Spillbar adapter; full C64-kamp er ikke portert.**
[Gjennomgangen av T01–T18](TEST_AUDIT_2026-10-25.md) erstatter tidligere
påstander om treff, prioritet, restitusjon og nederlag.
Den tidligere teksten og målingene er bevart i
[historikken](history/M3_COMBAT_BEFORE_TEST_AUDIT.md).

Kildereferanse: fryst `untrained-memory.bin`, SHA-256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Kandidatens identitet som urørt 1984-utgave er fortsatt uavklart.

| Tema | Kodebasert regel | Status i Amiga |
| --- | --- | --- |
| Treffgrunnlag | `$29C3` leser VICs globale spritekollisjonslås og aktørmapping `$4F40` | Foreløpige bokser; kilde-spritekontakt gjenstår |
| Samtidighet | Samle treffflagg før skade; offer2,1,0; ingen generell slag-/sparkprioritet | Sekvensielle par er fortsatt et kjent avvik |
| Slag | Tilstand17, retningsgrense6 i kilde-X og Y-forskjell<22; ingen egen tellergate | Fire prototypefaser, foreløpig rekkevidde |
| Spark | Tilstand12/13, restteller<10 og retningsgrense6, etter VIC-gate | Bevegelse/treffvindu ikke fullstendig avstemt |
| Stikk | Tilstand22, restteller<8 og retningsgrense4, etter VIC-gate | Prototypen bruker også egne boks-/høydegrenser |
| Koordinater | X er kildens aktøranker, omregnet fra halvpiksler; ikke figurens sentrum | Kommentaren rettet til sprite-venstre/bunn+1 |
| Fall | Tilstand14, høyde-/kvote-/offertilstand og VIC-gate | Manglende/feil falltreff er fortsatt åpent; ikke gjør alle synkende hopp skadelige |
| Kvoteforbruk | `$2B06–$2B2A` bruker kvote før flere avvisningsgrener | Prototypens senere kvoteforbruk og «ingen angrep»-test avviker |
| Skade | Ordinære grener trekker stikk2/slag3/spark7/fall5 | Verdier finnes i adapteren; terminal fallgren har en dokumentert kandidatanomali |
| Skadereaksjon | Tilordne teller3/4/12/8 uten flytting i resolveren; aktøroppdatering etterpå i samme gjennomgang | Rettet: kamp før bevegelse og ett første rekylsteg i bevegelsen |
| Aktørrekkefølge | `$17BC–$17DF`: Ninja, Yamo, Bruce | Rettet fra spiller-først til kilderekkefølge |
| Ligge | Offer i tilstand26 avvises av kamprutinen | Beskyttelse finnes; input/opp-reisning og farekontakt ikke samlet godkjent |
| Vellykket treff | Angriperen får egen venting/restitusjon; `$10D0` bruker tidsbyte `$88` | Full portering gjenstår; åtte-stegs måling uten treff er ikke universell kampkadens |
| Død | Eget livs-/reset-/romlastingsforløp | Rom/NPC-er lastes på nytt, men liv/Game Over og full original timing mangler |

Yamo har både slag og spark. Ninja bruker et eget stikkangrep.
Starthelse36/20/7 og de målte første inntredentidene gjelder det dokumenterte
kandidatutgangspunktet; de er ikke en universell initialisering for alle rom.
Reaksjonsbevegelse, fiende-AI og respawn er fortsatt delvis prototypekode.
Den separate [AI-verifikasjonen](C64_AI.md) dokumenterer nå alle relevante
avstands-/tilstandsgrener, venting og inntredentabeller mot originalbytene.
588 ordinære beslutningsvalg samsvarer; dette godkjenner ikke hele AI-en.

`python tools/audit_c64_tests.py` kontrollerer kodegrenene ved å utføre
faktiske kildebytes med eksplisitte injiserte innganger. `test-core.ps1`
kontrollerer den nåværende rom-/aktøradapteren separat. Gamle
`-LegacyBlockout`-forventninger er pensjonert. Testene er ikke bevis på full
originalparitet. Native målinger må være knyttet til kildene som ble bygget;
eldre M3- og rommålinger er historiske etter aktørendringer.

Kontroller: ild uten sideretning gir slag; gange + retning/ild kan gi
flyvende spark. Escape går til AmigaDOS; `start` starter siste klargjorte bygg.
Bygg med `amiga-build.ps1`, start med `amiga-run.ps1`.
