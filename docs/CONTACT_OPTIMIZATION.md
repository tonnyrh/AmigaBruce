# Kontakt og synlig fremdrift — 27. oktober 2026

Andre optimaliseringsrunde gjennomfører en avgrenset OP1-pilot og retter
visningssultingen funnet i OP0. [Plan](AMIGA_OPTIMIZATION_PLAN.md) og
[første VIC-pilot](AMIGA_OPTIMIZATION_REPORT.md) beholdes som historikk.
Full sanntidsakseptanse er fortsatt åpen.

## Kildegrunnlag og endring

Uendrede bytes fra `.reference/c64/work/untrained-memory.bin`, SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Utgaven er fortsatt en kandidat, ikke sertifisert urørt1984-utgave.

- `$52AD–$5309` kopierer96 maskebytes med toppforskyvning `$1C` og
  sidefase `$1B`. Fase1/2 forskyver tre kolonner2/4 bits til høyre;
  fase3 forskyver fire kolonner2 bits til venstre. De fullstendige
  forskyvningspassene er slått sammen per rad. Fremoverkopieringen beholdes
  i samme rekkefølge ved overlappende minne. Carry kommer fra rad0 i siste
  originalpass; slutt-A/X/Y/N/Z, V/D/I og SP bevares.
- `$537E–$53CE` tar tre ordnede glyph-/maskekontakter. Kolonnene er skrevet
  ut direkte, så den gamle kolonneløkkens multiplikasjoner bortfaller.
  Lesing og RAM-skriving skjer i original rekkefølge, også når en glyphpeker
  viser inn i klasseflagg skrevet av forrige kolonne. Bare virtuelle N/Z/C
  som neste CPY overskriver før observasjon, utelates.
- `$5431–$55AA` nullstiller klasseoppsummeringen, normaliserer kolonnene
  og setter fire kontaktbits i `$B6,X`. De eksakte operandene i kildens
  fire OR-kjeder brukes, inkludert gjentatt `$4EFE`. Kontrollverktøyet
  sammenligner operandlisten direkte med de frosne instruksjonsbytene.
- `$55E6/$5658/$56CA` bytter sju bytepar i hver23-bytes klassekolonne.
  Direkte C-hjelpere beholder også slutt-A/X/N/Z. Alle JSR-stackbytes
  ved `$5443/$544E/$5459` skrives, selv om SP gjenopprettes. Tilfeldigleseren
  kan observere bytes nedenfor SP senere.
- `$53E4/$5429` beholder kropp/fot-skillet og den ikke-lokale returen via
  to PLA og `$52A4`. Felt-/lydservice ved de eksisterende trygge punktene
  er uendret. Ingen kollisjonsbokser, støtteregler eller AI-regler er lagt til.

Klassereduksjonens raske inngang krever `$50<3`, altså de faktiske tre
aktørene. Andre innganger beholder den instruksjonstro banen.

## Målt effekt på kontaktkjernen

Måleparet bruker faktisk PAL-planlegging på68000/OCS/KS1.3,512KiB Chip og
512KiB slow. Rom1 har ingen joystickinput og udødelighet som uttrykkelig
testutvidelse. Hver kjøring har360 løkker/360 spillsteg. Dette er ikke
naturlig gjennomspilling eller en måling av alle20 rom.

| Måling | Før | Etter kontaktendring |
| --- | ---: | ---: |
| Profilert maskeforskyvning, gjennomsnitt |61,572 linjer |38,260 linjer |
| Profilert kontakt-radløkke, gjennomsnitt |64,110 linjer |61,977 linjer |
| Aktiv PAL-tid uten profilering |2 827 felt |2 644 felt |
| Manglende lydserviceticks |261 |168 |
| Tegnede bilder |2 |2 |

Maskeforskyvningen er omtrent38 % billigere per målt kall. Hele målebanen
brukte omtrent6,5 % kortere tid. Det er ett A/B-par med separate profilerte
kjøringer; kildefaser kan endres når faktisk kjøretid endres. Profileringens
egen kostnad regnes ikke som en gevinst. RAM-/registerutfall kontrolleres
separat mot de faktiske instruksjonene.

Råbygg og rapporter ligger under
`reference/analysis/optimization-2026-10-27/contact-{before,after}-{profile,timing}/`.
`contact-baseline/` bevarer første leveranses kilde, bygg og bevis.

## Rettet visningsgrense

Den gamle regelen kunne avvise ny tegning hver gang CPU-arbeidet hadde
overskredet140/220 linjer. Da ble det aldri tegnet igjen i en vedvarende
tung scene. Nå sjekkes tiden siden sist faktisk publiserte bilde: etter
tre PAL-felt skal neste visningsbeslutning tegne. Tersklene og den
roterende kopieringskøen beholdes; kilden får ingen færre steg eller IRQ-er.

Dette er en frist ved beslutningspunktet, ikke en garanti om tre felt mellom
bilder. Et langt udelelig spillsteg kan fortsatt overskride fristen.

Med denne rettelsen tegnes360 av360 bilder i samme belastningsscene,
mot2 tidligere. Aktiv tid er2 857 felt, mot2 644 med kontaktendringen alene
og2 827 før denne runden. Mer tegning har en reell kostnad: den samlede
banen er omtrent1 % tregere enn før runden, samtidig som synlig fremdrift
opprettholdes. Vi rapporterer ikke6,5 % som samlet gevinst for sluttbygget.
Lydservice mangler210 ticks i denne scenen, og sanntidsporten er ikke bestått.

`present-after-timing/` inneholder denne separate målingen. Før/etter
kontaktkjernen endrer bare motoren og den genererte aktørheaderen; den
etterfølgende visningsendringen endrer bare `amiga/main.c` og `core/scene_copy.h`.

## Verifikasjon og videre arbeid

`./test-source-contact.ps1` kontrollerer2 248 injiserte tilfeller med alle
64KiB RAM, prosessorregistre og returadresse mot706 112 faktiske C64-
instruksjoner. De dekker alle side-/toppfaser, kopieringsalias, enkeltstående
klasseflagg med alle kolonnebytter, vilkårlige flaggverdier, glyph/klasse-alias
og ikke-lokal retur. Før endringen bestod den første1696-tilfellers pakken;
enkeltflaggtilfellene ble lagt til etterpå.

3 034 eksisterende kildekontroller og fem integrerte liv-/turbytteforløp
bestod etter kontaktendringen. Kopierings-/visningskontrollen omfatter nå
vedvarende CPU-overlast og klokkeomslag.

Ny native 68000-kjøring bestod53/53 kildenære RAM-/registerkontroller og
1 200 PAL-felt/400 logiske steg på OCS/KS1.3 med512+512KiB. Ingen kilde-,
lyd-, DMA-, gjengivelses- eller aritmetikkfeil ble rapportert; retur til
AmigaOS ble kontrollert. Største ledige Chip-blokk var52 632 byte.
1 061 nye bilder ble tegnet og139 holdt, med største holderekke2 felt.
Lydservice manglet241 ticks. Restkontrollen fant42 HUD-bytes,0 bytes i
ventende kopiering og33 uforklarte scenebytes. Dette er fortsatt en åpen
bildediagnose, ikke et godkjent rent overlegg.

Normalbygget åpnet rom1 med fire reservefall og aktiv kildemusikk. Et
faktisk bitplanebilde er lagret som
[oppstartskontroll](images/session-contact-running.png). Tre påfølgende
måleintervaller viste119/117/119 kildefelt mot PAL-klokkens intervaller;
ingen kildefeil. EXE-en er336 676 byte, SHA256
`bd9a9b61741c7258a6ce72928e69417e21fa40449991a96ca2b55e65b2cd71e4`.
Mot forrige bygg økte kode med914 byte og konstante data med8 byte; BSS er
uendret. ADF-en er901 120 byte. Målingene dokumenterer ikke naturlig
gjennomspilling eller kontinuerlig sanntidskadens.

Fortsett med den faktiske kostnaden i kildens hovedsteg, resterende
kontaktarbeid og tegning av figurer/bakgrunn. Bildets restkontroll skiller
HUD, ventende bakgrunnskopiering og uforklarte scenebytes; ingen avvik
godkjennes ved å kalle hele scenen «ren». Rasterfase, naturlig gjennomspilling,
alle rom, to6000-felts tester og fysisk A500 står fortsatt åpne.
