# Kildebasert musikk og effekter for Paula

25. oktober 2026. Temaet og de **15 gyldige effektsekvensene `$80–$8E`**
er hentet fra faktiske C64-bytes, ikke komponert eller generert med AI.
Kilde: `.reference/c64/work/untrained-memory.bin`, SHA-256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Kandidaten er fortsatt ikke bekreftet som valgt urørt 1984-utgave.

## Hva koden gjør

Tittelskjermen starter Micropearl-spilleren med `$E000/$E003` fra `$06DA`.
Tittel-IRQ `$154C` kaller `$E006` én gang per PAL-felt. Den kontrollerte
initialiseringen bruker originalens `$E314=3`, `$E870=0`, `$E871=$FF`.
Spillerens tilstand og SID-registre gjentar seg etter en ett-felts innledning
og en løkke på **1154 felt**, omtrent23 sekunder. Alle tre stemmene bruker
pulsbølge i dette temaet. Registersekvensen er lagret som differanser og RLE,
**2942 byte** med korrekt løkkepunkt.

Ved spillstart stopper originalen tittellåten (`$0724–$0729`), og spill-IRQ
`$15A8` bruker effektspillerne `$EB03`, `$EF73`, `$F073`. `$2509–$255D`
velger første ledige kø; hvis alle er opptatt, sammenlignes effekttabellens
prioritet mot kø1, deretter2 og3. Like høy prioritet kan erstatte. Det er
ingen tilfeldig variasjon eller ny mikseregel i denne oversettelsen.

Tabellen `$EBE5` har15 effektpekere. Den neste tilsynelatende «pekeren» er
allerede kommandotabell ved `$EC03`. `$8F` er derfor ikke en sekstende
dokumentert effekt; den gamle disassembly-kommentaren «80–8f» er for vid.
Kommandodataene fortsetter gjennom lanternemelodien etter `$EE19` og lagres
separat fra de uendrede originalene. Dekoderen beholder frekvens, ADSR og
pulsbredde mellom noter slik originalen gjør, og fanger gate av/på også når
begge skrives i samme felt. Bare å sammenligne siste gatebit ville mistet
slike anslag.

| ID | Datastrøm | Kildebruk / avgrensning | Sekvenslengde |
| --- | --- | --- | --- |
| `$80` | `$EC31` | `$1FC4`: spillerens gang, klatring og hoppstart. AI-gange går direkte til bevegelseshjelpere og omgår dette kallet. | 2 felt |
| `$81` | `$EC37` | `$225F`: forberedende aktørtilstand. Full utløsing av denne tilstanden gjenstår i aktørporteringen. | 33 felt |
| `$82` | `$EC47` | `$10B5`, kalt fra blant annet `$0CD5/$0DF8`: fiendeinntreden. | 13 felt |
| `$83` | `$EC7A` | Gyldig data; naturlig brukssted er ikke avklart her. Ressursen er laget uten å gjette en ny spillutløser. | 7 felt |
| `$84` | `$EC90` | `$205A/$209F`: første sparkeoppdatering ved restteller12. | 22 felt |
| `$85` | `$ECBE` | `$22D2`: stikk ved restteller12; også `$227C` i en separat aktørgren. | 7 felt |
| `$86` | `$ECD8` | `$2E29`, via slag-/spark-/fallgrenene: registrert treff. | 6 felt |
| `$87` | `$ECEC` | `$2A93`: registrert stikk-treff. | 9 felt |
| `$88` | `$ED0E` | Blant annet `$3059`: kildebasert fare-/dødsgren. Ikke lagt på alle nederlag ut fra utseendet alene. | 21 felt |
| `$89` | `$ED59` | `$404E–$407C`: kildekodens bevegelige celler. | 2 felt |
| `$8A` | `$ED60` | `$424F`: felles lydkall fra flere dynamiske romrutiner. | 80 felt |
| `$8B` | `$ED8E` | Blant annet `$3E0D`: romkode. | 15 felt |
| `$8C` | `$EDC8` | Gyldig rom-/sekvensdata; se de konkrete kallstedene før flere aktørutløsere legges til. | 15 felt |
| `$8D` | `$EE07` | Blant annet `$32D3`: objekt-/romkode. | 104 felt |
| `$8E` | `$EE19` | `$2F36`: lanternemelodi. | 27 felt |

Lengden inkluderer kildefeltet som avslutter sekvensen. ADSR kan være
videreført mellom effekter; selvstendige WAV-forhåndsvisninger starter med
den kontrollerte nulltilstanden. De er ikke naturlige C64-opptak.

## Amiga-versjonen

Etter oppstartsskriket vises **FIRE TO START**, og kildens tema går i løkke.
Ild starter spillet og stanser temaet, slik skillet mellom tittel og spill
gjøres i C64-koden. Escape går til AmigaDOS. Autotesten bruker120 tittelfelt
og trenger ingen manuell knapp. Oppstartsskriket er beholdt.

Tre Paula-kanaler spiller korte, uforanderlige bølgeformer med kildens
frekvenser, pulsbredder, gate-signaler og ADSR-parametre. Bølgeformbanken
tar **2260 byte Chip RAM**, mot4004 byte for de tidligere kamplydene:
1744 byte mindre. Musikkdata, effekttabeller og avspillerkode ligger i
CPU-tilgjengelig minne. En liten bølgeformbank sparer RAM sammenlignet med
å lagre hele temaet som PCM. Kanalene følger Paulas faste stereofordeling.

Dette er en **Amiga-ekvivalent**, ikke en analog eller syklusnøyaktig SID:

- Puls, trekant, sagtann og kombinasjonen trekant/puls bruker8/16/32 prøver
  per periode. Paula-perioden og pulsbredde blir kvantisert.
- Støy bruker en deterministisk1024-byte ressurs. Det er ikke hele SIDens
  kontinuerlige støyoscillator. Støyhastigheten begrenses av OCS-DMA.
- ADSR bruker en uttrykkelig50Hz-tilnærming med faste heltall og MOS-tabellens
  tider. Analog respons og SIDens digitale ADSR-særtilfeller emuleres ikke.
- De kontrollerte kildesekvensene ruter ikke stemmer gjennom SID-filteret;
  uttrekket avviser nye filter-/sync-/ringtilfeller fremfor å overse dem.
- Hvert kildefelt beholdes. A500s og C64s PAL-feltklokker er litt ulike;
  den tidligere dokumenterte langtidsforskjellen er fortsatt åpen.

Frekvensomregningen følger [MOS6581-databladet](https://myoldcomputer.nl/Files/mos_6581_sid.pdf).
Paulas perioder og DMA-grense følger [Commodores maskinvaremanual](https://oldcrap.org/wp-content/uploads/2023/04/amiga-all-hw-ref-manual.pdf).
Minste periode er satt til124. Ingen nye kampregler fastsettes av lydavspillingen;
aktørutløsere følger fortsatt den avgrensede spilladapteren. Full naturlig
utløsing av alle C64-aktørtilstander gjenstår sammen med aktørporteringen.

## Ressurser og verifikasjon

- `tools/build_c64_audio.py`: leser den låste binæren, utfører lydrutinene
  og lager data med kildeadresser/hash. Originalfilene endres ikke.
- `test-source-audio.ps1`: sammenligner native C med de faktiske6502-rutinene
  gjennom7540 felt, alle15 effekter og opptatte/prioriterte køer; sammenligner
  også temaet over to gjennomløp og lager WAV-forhåndsvisninger fra samme
  parameteravspiller som brukes av Amiga.
- `test-core.ps1`: rom-/aktørregresjon samt signaturer av6000 felts faktiske
  Paula-parametre og120 tittelfelt. Dette er ikke en ny C64-spillparitetsgodkjenning.
- Native A500-resultater må være bundet til de nye kildene. Gamle
  `sfx_variant_mask` og engangs-PCM-avbrudd gjelder den pensjonerte avspilleren;
  kontinuerlig bølgeform-DMA har et annet testgrunnlag.

[Manifest](../assets/audio/c64-equivalent-v1/manifest.json),
[kilderegisterspor](../assets/audio/c64-equivalent-v1/source-registers.json),
[vertskontroll](../reference/validation/source-audio-host.json).

[Tema som Amiga-forhåndsvisning](../assets/audio/c64-equivalent-v1/title-amiga.wav)
og [effektutvalg](../assets/audio/c64-equivalent-v1/effects-amiga.wav).

## Native resultat

To CLI-kjøringer av bygget med rippede C64-sprites på PAL A500 OCS/68000/Kickstart1.3/
512+512 fullfører 6000 spillfelt og120 tittelfelt hver. Hashene for faktisk
skrevne Paula-parametre matcher verten: spill1264196226 og tittel2708371906.
Endringen i spillsignatur følger de korrigerte aktørfasene og utløserne;
selve kildens effekt-/temadata er uendret. Alle tre stemmer brukes, alle15
ID-er forespørres av testsekvensen, og lyddekoder/parameteravspiller har0 feil.
Hver start består også324 positur-,70 bevegelses- og29 objektkontroller. OS gjenopprettes.
Dette er kontrollert parameter-/runtimeavspilling, ikke et mikrofonopptak
eller en naturlig gjennomspilling av alle rom.

Chip-reserven består nå:88480 byte sammenhengende mot49152-målet i
testutgaven. De nye kjøringene har257 forsinkede felt per6000 og maksimalt
2 PAL-perioder mellom oppdateringer. Den strenge tidsporten er fortsatt åpen.
Spritebanken er73680 byte Chip/12852 pakket. Rapportens tilgjengelige
utvidelsesminne før runtimeallokering er44560 byte i begge kjøringer.
Normalbyggets ledige minne og feltkadens er ikke målt i denne testen.
Testutgaven har ekstra framebufferkopi og signaturmåling. Resultatene er
diagnose og kilde-/runtimekontroll, ikke en samlet bestått A500-port.
[Leveranserapport](../reference/validation/source-audio-delivery.json).
