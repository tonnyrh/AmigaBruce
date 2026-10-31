# OP4. Lydtikkene som forsvinner ved falltreff på Kage

To nye referansekjøringer gjentok **12 tapte lydtikker på 985 PAL-felt**.
Bruce løp og hoppet i rom 1 med Kage og Yamo aktive. Et privat bygg lot
eksisterende felt- og lydservice kjøre på nytt i Kages skadeløkke. Begge
prøvene fikk **null tapte tikker på 989 felt**. Normalbygget beholder
OP2-koden inntil håndteringen av det nye avbruddspunktet er integrert.

## Fra en sen lydsjekk til kildeinstruksjonene

Alle ruter hadde 240 oppvarmingssteg og 240 målte steg på PAL A500 OCS med
68000, Kickstart 1.3, 512 KiB Chip og 512 KiB slow i WinUAE. I bevegelsesruten
var Bruce i lufta i 96 steg. Lydtap telles når det har gått mer enn ett
PAL-felt siden forrige betjente lydtikk. Målingen sier ikke hvordan et
bestemt lydkort eller en høyttaler gjengir tapet.

| Bygg og rute | PAL-felt | Tapte lydtikker |
| --- | ---: | ---: |
| Referanse med bevegelse, to kjøringer | 985 / 985 | 12 / 12 |
| Merking av kallsteder og arbeidsområder | 1102 | 13 |
| Tidsstempling mellom lydsjekker, to kjøringer | 1297 / 1284 | 15 / 13 |
| Samme tidsstempling, stillestående Bruce | 1236 | 0 |
| Egen måling av kamp og poengberegning | 988 | 14 |
| Privat serviceprøve med bevegelse, to kjøringer | 989 / 989 | 0 / 0 |
| Privat serviceprøve med stillestående Bruce | 964 | 0 |

I begge detaljerte kjøringer kom de store forsinkelsene ved steg **168 og
207** i måleperioden. Siste sjekk lå ved kontaktradene i `$5380`. Neste
var ved spriteoppdateringen i `$2586`. Mellom dem tok kampkallet ved
`$1C23 → $29C3` henholdsvis 2 024 og 2 038 rasterlinjer i begge
kjøringene. Detaljert sporing ga i tillegg én eller tre enkelttap ved
tegning av poengtallet. De store kampoppholdene var også synlige med
bare kallstedsmerking. Probesummen brukes ikke som ordinær spilletid.

I et separat bygg ble poengkallene tidfestet direkte. De 53 kallene brukte
2 076 av kampens 2 262 rasterlinjer ved første treff og 2 073 av 2 274
ved andre. Selve desimalkonverteringen utgjorde bare 480 og 484 linjer
av poengtiden. Disse vinduene er nøstet.

## Hvorfor originalen går rundt igjen

To kontrollerte opptak fra Amiga-bygget bevarer inngangsminne og registre
ved `$29C3` og utdata ved retur til `$1C26`. I hvert opptak ble videre
service holdt tilbake under det ene kallet. Py65 kjørte de faktiske bytene
i den frosne Remember/T64-kandidaten fra samme inngang. Hele 64 KiB og
A/X/Y/SP/C/Z/N/V/D/I stemte ved retur. Kjøring både med og uten testens
udødelighetsinngrep ga samme utfall. Identiteten som urørt 1984-utgave
og naturlig rasterfase er åpne. Kildehash er
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.

- `$2BF9–$2C0A` finner bit 4 og bit 7 i `$BC+X`. Ved de to treffene
  er X = 2 og flaggbyten `$90`. Bruce får 50 poeng via `$3175`.
- `$2C0C–$2C13` trekker 5 fra Kages åttebiters helse. Negativt resultat
  tar grenen til `$2C24`. For Kage gir `$2C40–$2C44` ytterligere 200 poeng.
- `$2C47–$2C51` gjenoppretter X, setter tilstand og teller, og hopper til
  `$2BF9`. Fallflagget står fremdeles. Etter 26 slike returer blir neste
  helseresultat positivt i åttebiters aritmetikk og løkken avsluttes.
  26 × (50 + 200) + 50 gir 6 550 poeng ved hvert av disse treffene.

| Steg | Kages helse før / etter | Poeng før / etter | 6502-instruksjoner | CPU-sykluser i kildeprøven |
| ---: | ---: | ---: | ---: | ---: |
| 168 | 2 / 123 | 425 / 6 975 | 40 381 | 151 018 |
| 207 | 3 / 124 | 6 975 / 13 525 | 40 426 | 151 164 |

Dette er enkeltkall fra opptak, ikke en C64-gjennomspilling med naturlige
avbrudd. Spillregelen og poengføringen er bevart i serviceforsøket.

## Avbruddspunktet og beslutningen for normalbygget

I kildeprøvene var I-flagget klart gjennom begge kampkall. På returen ved
`$2C51` var også desimalmodus av. Den private prøven betjente eksisterende
service her bare for Kage med fallflagget satt og helse på minst 133, når
en ny subtraksjon fortsatt kan gi negativt resultat. Målingen inkluderer
kostnaden for disse sjekkene.

I seks avgrensede kontroller ble et spill-IRQ injisert ved 1., 13. og
25. passering fra hvert opptak, med eksplisitte CIA-pinner og rasterverdi.
Originalvektoren går til `$1103`, spillhandleren til `$48C1`, og
`$4915` kaller `$15A8`. Kilden kjører de tre SID-driverne før
sprite-/feltarbeidet og inngangsavlesningen ved `$169D`. RTI ga nøyaktig
retur til `$2C51` og gjenopprettet registrene.

Dagens native felt- og lydservice ga samme registre, sluttpoeng og helse
i disse fortsettelsene. Etter det injiserte feltet avvek likevel **38
minnebyte** i hver kontroll. Det gjaldt 12 palettebyte, 12 øvrige byte i
stack-siden, fire pekerbyte, seks byte i rasterplanen og fire modellerte
maskinvareregistre. Den allerede separate, mer komplette IRQ-kandidaten
stemte med originalen i hele minnet, registrene, retur-PC og stigende
SID-gatekanter. Alle seks prøver bestod også som kompilert 68000-kode
i WinUAE. Dette kontrollerer ett eksplisitt IRQ i hver situasjon. Det
avgjør ikke når alle raster-IRQ-ene skal kjøres i det vanlige spillet.

Oppfølgingen knyttet forfalte PAL-felt til IRQ-banen ved `$2C51`.
Den sammenlignet stack, inngang, registerstrøm og retur gjennom neste
spillfelt og målte de faktiske Paula-publiseringene. [Resultater fra
feltprøven](OP4_FIELD_OWNER.md). Et kortere kampkall som kutter de
opprinnelige poenghendelsene ville endre resultatet i C64-koden.

## Gjenta målingene

I analysemappen bygger `probe.py reference` referansen og `probe.py sites`
og `probe.py timed` måleprogrammene. `focus.py`, `trial.py` og
`capture.py` bygger de avgrensede variantene. `run.ps1` bruker nytt
etikettnavn per kjøring. Rom/fiendemaske/inputrute er 1/3/2 ved bevegelse
og 1/3/0 når Bruce står stille. Opptakene bruker 408 og 447 oppvarmingssteg.
`audit_combat.py` sammenligner opptaket med originalinstruksjonene.
`build_irq.ps1`, `irq.py` og `proof.py` lager de eksplisitte
IRQ-kontrollene. De kjøres med `run.ps1 proof` og nytt etikettargument.
`verify.py` leser tilbake alle rapportene og gjentar kildekontrollen
når private opptak finnes. Ingen originale minnedumper ligger i
Git-registeret.

[Målerapport, hendelser og byggidentiteter](../reference/analysis/op4-moving-audio-2026-10-31/result.json).
