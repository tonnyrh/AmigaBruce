# Pakkede kontaktmasker, 28. oktober 2026

Denne runden fortsetter fra `c77404b` på `optimize/native-amiga-engine`.
Spillregler, input, venting, grafikk og lyddatasett er uendret.

## Kildekontrakt og implementasjon

Frosset kandidat: `.reference/c64/work/untrained-memory.bin`, SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Kandidaten er fortsatt ikke sertifisert som urørt 1984-utgave.

Rutinen `$52AD–$5309` klargjør kontaktmasken:

- `$52AD–$52C8` nuller den vertikale prefiksen fra `$1C`; fase tre
  legger til 32 nullbytes. Dette skjer før lesing fra maskepekeren.
- `$52C9–$52D5` kopierer 96 bytes framover fra den selvmodifiserte
  operanden `$52CC/$52CD` til `$CAE0+Y`.
- Fase null returnerer uten skift. Fase én/to kjører to/fire hele
  høyreskift over tre 32-byte baner (`$52E3–$52F0`). Fase tre kjører
  to venstreskift over fire baner (`$52F3–$5307`). Exit-carry er siste
  bit fra rad null, ikke den siste native løkkeinstruksjonens carry.

`amiga/contact_align.s` behandler fire uavhengige rader i hvert langtord.
Masker hindrer bitflyt mellom nabobytes. Det er ingen serviceobservatør
inne i den eksisterende kopierings-/skiftbanen. Alle bufferbytes og
slutt-A/X/Y/C/N/Z/V/D/SP blir som før; SP øker to fra kilde-RTS.

Hurtigbanen krever fase 0–3, offset 0–7 og maskepeker høyst `$FFA0`.
Andre innganger bruker den beholdte C-rutinen, med 16-bits adresseomslag.
Langtordkopi brukes bare på partallsadresser uten farlig framover-overlapp.
Odde adresser og overlapp med mål etter kilde kopieres bytevis i original
rekkefølge. Fase-tre-prefiksen nulles bytevis ved odde mål.

ABI er fire 32-bits argumenter, også fra `-mshort`-modulen. D2–D7 og
A2–A4 bevares. D0 returnerer kilde-carry; wrapperen publiserer øvrige
virtuelle registre. Ingen nye allokeringer eller Chip-buffere opprettes.

## Kontroller

Kontaktpakken har 4 209 kontroller mot faktiske C64-bytes, 2 314 995
utførte kildeinstruksjoner og uendret 489 service-registerforløp.
256 nye tilfeller dekker alle faser/offset, odde adresser, overlapp på
begge sider, prefiksalias og lesing gjennom `$FFFF`.

256 direkte native sammenligninger kontrollerer maskebuffer, canaries
og virtuelle exit-registre mot C-banen. Samlet kjernekontroll er nå
454 (256 maskeforberedelser, 128 pikselradforløp, 70 klassesammendrag).
Dette kommer i tillegg til de 53 komplette native RAM-/registerfixturene.

Den første kandidaten ble avbrutt før rapport: statisk gjennomgang fant
en fase-tre-nulling med langtord på odde adresser. Bare den eide test-
emulatoren ble stoppet. Korrigeringen er kontrollert i alle faser/offset;
den avbrutte kjøringen er uttrykkelig utelatt som måleresultat.

## Måling

Samme faktiske PAL-planlegger og 360 spillsteg som i forrige rapport,
rom 1 med stillestående testudødelig Bruce og begge fiender. 1 200 ytre
løkker er sikkerhetsgrense. Profilering og normal tidsmåling er separate.
Arkivene ligger i `reference/analysis/optimization-2026-10-27/`.

| Trinn | PAL-felt | Tapte lydserviceticks |
| --- | ---: | ---: |
| Forrige leveranse, `contact-class-groups-fixed-timing` | 1 614 | 29 |
| Pakket maske, `align4-compact-controls-final-timing` | 1 530 | 21 |

Dette er cirka **5,20 % kortere målt kjøretid** i denne scenen. Det er
ikke et gjennomsnitt for alle rom eller en fysisk A500-måling. Profilen
inneholder ekstra instrumenteringskostnad og endret faktisk IRQ-fase.

Profilert maskeforberedelse går fra 34,404 til 14,337 rasterlinjer per
kall, omtrent 58,3 % mindre. Det er 738 kall i begge profiler. Øvrige
rutiner kan få andre IRQ-/spillfaser når faktisk kjøretid endres; deres
kostnader eller utfall tilskrives ikke automatisk denne maskekjernen.

Lyd-/sanntidskravet er fortsatt åpent. Færre tapte ticks i denne enkelt-
målingen er ingen godkjenning av lyd. Feltport, minstekrav til Chip-reserve,
alle tre stemmer og tre-felts kildeventer er uendret. Naturlig gjennomspilling,
original rasterfase, alle rom og fysisk A500 gjenstår som egne akseptanser.

## Normalbygg og minne

EXE er 342 416 byte mot 341 744 før, en økning på 672 byte.
`.text` er 193 090 byte (`$2F242`), opp 546; `.rodata` 78 940,
`.data` 9 og BSS 171 088 er uendret. Forskjellen mellom Hunk- og
tekststørrelse inkluderer relokasjons-/filmetadata. Ingen nye
Chip-allokeringer eller permanente arbeidsbuffere er lagt til.

Normal CLI starter nytt spill og bytter til rom 2; Yamos synlig/skjult/
tilbake-forløp består i begge bildebuffere. Rom-1-bildet ved spillstart er
byteidentisk med før. Korte klokkeprøver med begge fiender varierer med
kampfasen: den tidlige prøven har 121–125 kildefelt per 29–30 spillsteg
(cirka 4,2–4,3 felt per steg); den endelige prøven har 125–126 felt per
25–26 steg (cirka 4,8–5,0). Ingen kildefeil registreres. Disse korte prøvene
er ikke kontrollerte A/B-par eller et sanntidspass. Tre-feltsmålet er
fremdeles ikke nådd med begge fiender. `start` er samme EXE som bygget.

Neste prioritet fra den nye profilen er kontaktoppsettet utenom selve
maskeforskyvningen (162,872 rasterlinjer eksklusivt per spillsteg),
deretter gjenværende arbeid i hovedkjeden og spritepubliseringen.
VIC har fortsatt sjeldne topper; lydservicetap må avklares mot disse
serviceintervallene. Dette er målekandidater, ingen vedtatt endring av
C64-regler eller flytting av IRQ-observasjonspunkter.

## Minnet i det større kontrollprogrammet

Første komplette native kontrollbygg stoppet før spillstart med
`allocation_failed=1`. En separat diagnostisk kopi med bevisst feil første
forventningshash ble brukt for å nå allokeringene raskt. Denne kopien er
ikke en paritetskontroll og kan aldri godkjennes som 53 beståtte tilfeller.
Etter cleanup viste den eide instansens RAM maskinens BSS i Chip RAM,
manglende lyd-/visningsbuffere og null kjernekontrollfeil. Originale
kildedata og det umodifiserte testbygget ble beholdt.

Det tidligere fullbygget hadde bare 1 472 byte slow RAM ledig før de
uttrykkelige spillallokeringene. Derfor pakkes nå testenes skriveoppføringer
som adresse-høy/adresse-lav/verdi, tre byte i stedet for en firebytes
struktur med padding. Ingen odde ordlesninger innføres på 68000.
Samtlige 53 sett med innganger, kilde-RAM-hasher og registerforventninger
er identiske med før. Registeravlesning i de nye kjernekontrollene bruker
den eksisterende 13-registerkontrollen framfor nye enkeltvise lesninger.
Dette er lagrings-/kodebesparelse i testhjelperne, ingen flytting av
minneporten eller fjerning av kontroller. Diagnostikken er bevart under
`align4-native-allocation-rejected`; rå minnedumper holdes lokalt i `.tmp`.

Den pakkede diagnostiske kopien fullfører 1 200 løkker med 52 632 byte
sammenhengende Chip-reserve og 454/454 kjernekontroller. Den rapporterer
med hensikt fixturefeil 1 for den endrede forventningshashen. Dette er en
negativ kontroll og dokumentasjon av allokering, aldri full paritetsaksept.
Den umodifiserte 53-fixturkjøringen rapporteres separat nedenfor.

Synlighetshjelperen publiserer nå aktivbit først etter at en inaktiv aktørs
posisjon, tilstand og komponenter er satt opp. De separate IPC-skrivingene
spenner over reelle kildefelt; den tidligere aktive-først-innsprøytingen
kunne gi AI-en en halvferdig tilstand og en legitim tidlig fjerning. Selve
spillkoden er uendret av denne korreksjonen i den manipulerte testoppsettingen.

## Endelig umodifisert native kontroll

53/53 originale komplette RAM-/registerfixturer og 454/454 kjernekontroller
består. Reprisen fullfører 1 200 løkker / 400 kildespillsteg og returnerer
til AmigaOS. Kilde-, lyddekoder-, DMA-, aritmetikk-, render-, opptaks- og
VIC-kontrollene rapporterer null feil.

Største Chip-blokk er 52 632 byte, uendret fra forrige leveranse og over
49 152-byteporten. Slow RAM før spillallokeringene er 1 064 byte i dette
større kontrollbygget; normalutgaven har færre diagnosefunksjoner/data.
Den native kontrollutgaven er 368 104 byte mot tidligere 367 472. De 629
skriveoppføringene bruker 1 887 byte framfor 2 516, uten endret innhold.

Reprisen viser 992 nye og 208 kort holdte bilder, største holdrekke ett
felt. Maksimalt gap er fortsatt fem felt og 81 lydserviceticks mangler;
den strenge sanntidsporten er **ikke bestått**. Bildediagnosen har fortsatt
42 HUD-bytes, 33 uforklarte scenebytes og ingen ventende kopier. Dette er
de samme åpne verdiene som forrige kontrollerte reprise, et annet forløp
enn den faste tidsmålingen med 21 tapte ticks. Ingen porter er slakket.

Alle vertskontrollene for aktørkjeden, fem integrerte liv-/spillermoduser,
kontakt, objekter, poeng, synlighet, VIC, lyd/DMA og tegnekø består.
Leveranse- og optimaliseringsverifikasjon binder disse rapportene og
normal CLI-/ADF-opptak til de endelige kilde-/byggidentitetene.
