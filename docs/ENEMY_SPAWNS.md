# Kage og Yamo: inngang, plassering og tid

Gjennomgang 26. oktober 2026. Reglene under er fulgt i den frosne
Remember/T64-kandidatens faktiske 6502-bytes. Kandidaten er fortsatt ikke
bekreftet som en urørt 1984-utgave.

Kilde: `.reference/c64/work/untrained-memory.bin`, SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Originalfilen er uendret. [Disassembly og kontroller](../reference/analysis/spawn-audit-2026-10-26/)
er separate analyseprodukter.

## Kilderegler og rettelser

| Kildeadresse | Betingelse og effekt | Amiga |
| --- | --- | --- |
| `$0A2A–$0A69`, `$130B/$1347`, `$4C9E` | Romlast nullstiller bevegelsesrecordene og klokken. Separate første tellere for Kage/Yamo; senere runde gir3, menneskelig Yamo gir8. `$7A!=0` sperrer tjenesten. | Romtabeller erstatter felles/snapshot-avledede96/232. Rom 1 starter104/240. Dødsreload laster kilden før tellere kopieres. |
| `$1BEE–$1C13`, `$0DA4`, `$0D0F`, `$0DB1` | Først ambientrutinen, så begge tellere ned, Yamo, Kage, romrutine og objektpass. Tellere løper også mens fienden er aktiv. | Tjenesten flyttet foran rom/kollisjon/aktøroppdatering. Ingen ekstra oppdatering før en født fiende kan treffe en bombe. |
| `$0DB1–$0DD6` | Kage på teller0 kan utsettes16 oppdateringer når Yamo er aktiv, runde0, automatisk Yamo, klokkehi<25 og minneavlesning>=25. | Den faktiske grenen kjøres, også når Kage allerede er aktiv. |
| `$0B8E–$0CE6`, `$0DF8–$0E2D`, `$4BAE/$4BC2/$4BD6/$4BEA` | Rommets standard/alternative koordinater, kildegater og eventuell engangs lagret ankomst med helse. Helse begrenses til20/7. | Hele spawn-tjenesten kjører fra oversatte originalinstruksjoner. Gjenbruker tidligere koordinat-/veggrecord innen rommet slik koden gjør. |
| `$1159–$1165` | Valget leser levende RAM via pekeren`$16/$17` og Y. Det er ingen uniform tilfeldig generator. | CPU-registere bevares mellom de tre tjenestekallene. `$1166` er en arbeidsbyte etter RTS, ikke en opcode. |
| `$2235–$2269`, `$24F4`, `$2780` | Yamo fødes BF16/CE10, vender først mot Bruce ved CE1 og går til BF18/CE16. Kage fødes BF0/CE16 og vender straks. Lik X vender mot venstre. | Egne inngangsfaser og positurer. Første grunnbevegelse er oppdatering28 for Yamo,17 for Kage; første oppdatering skjer i fødselsrunden. |
| `$0CD5/$0DF8`, `$4F4E` | Første objektmasker er108 for Yamo og130 for Kage. De er forskjellige fra neste ordinære positurmaske. | Fødselsmasken beholdes frem til første aktøroppdatering; viktig ved eksplosjoner og nett. |
| `$2E39`, `$2F90–$2F97`, `$30D4–$310B` | Faktisk dynamisk dørcelle2..5 og bevegelsesrecord/grense må tillate utgang. Rom 12 har egen gate. NPC fjernes uten å bytte Bruces rom. | Statisk horisontal dørtest erstattet med objektpassets celler og original gate. Oppdatert før neste aktørbevegelse. |
| `$3001–$304A`, `$0D42–$0DA3`, `$131F/$135B` | Fjerning bruker rommets returteller. Før hi25: full base i runde0, ellers3. Hi25..31: halv base, også senere runde. Fra32:3. Menneskelig Yamo har base48. | Kampdød, fare og dør bruker samme kildebaserte fjerning/teller. Faste96-returer er fjernet fra disse banene. |
| `$1614–$1626` | Klokken`$87/$88` går per felt når`$104` er aktiv og`$105` ikke er negativ; hi mettes ved128. | Logisk feltklokke videreført. Dette sertifiserer ikke faktisk veggklokketid når native rendering forsinkes. |

[Alle 20 roms koordinater og tellere](../reference/analysis/spawn-audit-2026-10-26/room-table.md)
viser begge tabellplasseringer. Tilstedeværende NPC ved rombytte kan ankomme
ved Bruces destinasjon med bevart helse; det er ikke et tredje tilfeldig
spawn-punkt. `$0BFA` bruker og tømmer den lagrede ankomsten én gang.
Kages fortegnsgren ved `$0C38` leser Yamos `$136F`-tabell; denne særheten er beholdt.

Kildekontrollen av første ordinære AI-steg viste dessuten at statisk
nettbevegelse kaller sidehjelperen to ganger i AI-grenen `$2352/$236C`.
Amiga gjorde bare ett kall. AI bruker nå fire skjermpiksler der koden gjør
det, mens menneskelig Yamos manuelle nettsteg fortsatt bruker to.

## Kontroller og avgrensning

`test-spawn.ps1` kompilerer den faktiske spillkoden og sammenligner med
originalinstruksjoner: 80 rominitialiseringer, 4320 tjenester, 960 fjerninger,
60 klokketilfeller og 908 inngangsoppdateringer. Et separat hovedløkkeforsøk
sammenligner 123 oppdateringer frem til Kages høyreutgang i rom 1.
30 fødsel/eksplosjonstilfeller dekker begge fiender, alle fem bomber i rom 8
og tre eksplosjonsfaser. Alle disse 30 fjerner fienden med rommets returteller.

`tests/spawn_fixture.h` velger 223 kontroller fra disse kildekjøringene:
80 initialiseringer, 60 tjenester, 40 returer, 8 inngangssekvenser, 5 kantpunkter
og 30 eksplosjonsfødsler. Samme fixture inngår i vertens og 68000s session-test.
Byggidentiteter binder DLL, kildefiler og native resultater til leveransen.

Dette er kontrollerte starttilstander med injisert RAM, kontaktfelt og
registergrenser. Rom 1-målet står inaktivt ved X302 for å isolere NPC-ruten.
Det er ingen naturlig gjennomspilling. Minneavlesningens naturlige fordeling
kan ikke sertifiseres før hele aktør-/IRQ-konteksten er portert. Vanlig
AI-venting, retrettstøtte, samlet treffbehandling og deler av aktørmaskinen
har fortsatt avvik beskrevet i [AI-auditen](C64_AI.md).
Den ordinære adapterens konvertering av fall-/reaksjonstilstand til
dørportens BF-verdi er også del av den ufullstendige aktørporten. Den
kontrollerte rom1-ruten sertifiserer ikke alle gjenopprettings- og
vertikale dørkombinasjoner.

Menneskelig Yamo er koblet til `$42CA` for riktige tellere og kildegater.
Full input-/inaktivitetsstyring for den modusen er fortsatt åpen.
Logiske tellere er hovedløkkesteg/felt, ikke målte sekunder eller bevis på
stabil 50 Hz. Native måling og byggidentiteter lagres i
`reference/validation/spawn-delivery.json` etter fullført kontroll.

## Maskinkontroll og bygg

To komplette A500-løp med samme binær er godkjent: 223 utvalgte
spawn-kontroller per løp og deretter 6000 felt i kampreplayen. Begge matcher
vertens sju resultater: 55 treff, 6 nedleggelser, 9 fiendeinnganger,
2 Bruce-dødsfall, 2 tilbakestillinger og sluttposisjon 8/196.
Alle fixture-feilkoder er null, bildekontrollen er tapsfri, og AmigaOS
gjenopprettes begge ganger. Største ledige Chip-blokk er 52 632 byte.

De lange kildefixturene kjører før maskinvareovertakelsen. Løpene ble
avsluttet separat fordi samlet oppstartstid overskred to-løpskommandoens
ventebudsjett. Første komplette rårapport er bevart og kontrollert med
hele den uendrede `test-amiga.ps1`-porten; kilde- og binæridentitetene er
like i begge løp. Ingen funksjons- eller minneport ble senket.

869/883 felt er forsinket, med maksimal avstand 3 perioder utenom
bildeopptaket. Stabil feltkadens er fortsatt åpen. Dette er kontrollerte
replayer med fast leseside `$17=$68`, ikke naturlig C64-spill.

En tidligere maskinkjøring ble avvist: eldre stack-fixtures initialiserte
ikke det nye inngangsfeltet, og testbygget manglet den fastsatte
minnereserven. Hele fixture-figurene initialiseres nå. Testfunksjonene før
maskinvareovertakelsen er størrelsesoptimalisert, og rom1s tapsfrie
kontrollbilde har 16 KiB buffer; bildet bruker 9896 byte og beholder
full dekodet hashkontroll. Avviste data er bevart separat.

Normal EXE/ADF er bygget, og AmigaDOS-kommandoen `start` er oppdatert.
Gjeldende byggidentiteter og maskinrapporter finnes i leveranseregisteret.
