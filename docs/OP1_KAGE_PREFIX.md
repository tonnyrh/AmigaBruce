# OP1. Gjenbruk av Kages første kontaktintervall

**Beslutning.** Kage-piloten er prøvd i et separat bygg og lagt til side.
Den traff 221 av 240 ganger i den særskilte tellerkjøringen. De øvrige 19
gangene ble bufferen fylt. I to før/etter-par i rom 1 ga dette henholdsvis
ett ekstra og null sparte PAL-felt. Den ordinære OP2-utgaven beholdes.

| Kontroll, 240 spillsteg | PAL-felt før | Etter | Tapte lydtikker før / etter |
| --- | ---: | ---: | ---: |
| Rom 1, stillestående Bruce, første par | 964 | 965 | 0 / 0 |
| Rom 1, stillestående Bruce, omvendt kjørerekkefølge | 964 | 964 | 0 / 0 |
| Rom 1, Bruce løper og hopper | 985 | 994 | 12 / 12 |
| Rom 13, Yamo aktiv | 724 | 724 | 0 / 0 |
| Rom 12, trapper, ingen aktive fiender | 818 | 812 | 0 / 0 |

Den stasjonære referansen var 964 felt med denne utgaven av ruteprogrammet
og 963 i forrige OP2-måling. Innenfor første par gikk det registrerte
arbeidsvinduet ned fra 259 153 til 255 987 rasterlinjer. I andre par var
tallene 258 754 og 257 241. De kortere arbeidsvinduene ga ingen tilsvarende
reduksjon i forløpt PAL-tid. Forskjellen i rom 12 kan ikke tilskrives
gjenbruk for Kage fordi ingen figurer utenom Bruce var aktive.
Største ledige slow-blokk i rom 1 var 9 216 byte i referansen og 7 392
i piloten. Tidsbyggene var innenfor minstekravet til Chip RAM.

**Oppfølging.** OP4 sporet de 12 tapte lydtikkene til to langvarige
falltreff på Kage og prøvde service ved kildens faktiske løkkegrense.
[OP4-målingen](OP4_MOVING_AUDIO.md)

## Kildegrunnlag

I den frosne Remember/T64-kandidaten kaller `$1C0D` kontaktrutinen ved
`$5212`. Kage behandles først, med X = 2 ved `$5214`. Når `$97 & 1`
er satt, hentes posisjonen fra `$A0/$A3` og posituren fra `$4F50`.
Tabellene ved `$1167/$1239` gir adressen til figurens 96 maskebyte.
`$52AD–$5309` justerer disse for posisjonen. `$55AB–$55C4` nuller
72 kontaktbyte og `$530A–$537D` setter opp de tre kolonnene for første
radgruppe. Tabellen ved `$50E7/$50FF/$5117` gir radadressene.
Ved `$5380`, Y = 0, når Amiga-motoren neste servicepunkt.
Begge rom 1-opptak fra forrige runde brukte 1 509 kildeinstruksjoner i
dette intervallet. Kildehash er
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Identiteten som urørt 1984-utgave og nøyaktig IRQ-fase er fortsatt åpne.

## Hva piloten gjenbrukte

Ãƒâ€°n privat buffer holder Kages sist beregnede forberedelse. På en aktuell
gjentakelse sammenligner 68000-koden rom, posisjon, positur, figurpeker,
tegnsettbank, radadresser, tre tegnkoder, tre attributtbyte og alle
96 maskebyte. Den bruker vanlig beregning når noe er endret. Manglende
tredjekolonne, mulige adressealiaser, odde figurpekere og adresser utenfor
de valgte områdene går også gjennom den vanlige banen. Bruce og Yamo
beregnes som før.

Ved gjenbruk gjenskapes de justerte maskene, klasseflaggene, pekerne,
de selvmodifiserte operandene, stackbytene og registrene som kan leses
ved første radservice. Selve rompikslene leses etter dette punktet.
Testen lot et romtegn endres akkurat i servicekallet. Kages kropps- og
fotmasker gikk da fra 0/2 til 4/6, slik de gjorde i C64-instruksjonene.

## Kontroller

Kontrollene bruker 218 eksplisitte tilstander, blant annet alle 96 enkelte
maskebyte, kombinasjonene av fire horisontale og åtte vertikale faser,
stackomslag, alternative pekere, aktivering, stige, dynamiske tegn og
rombytte. Originalinstruksjonene kjøres fra de forberedte tilstandene.
En separat vertskontroll sjekker om kandidaten gjenbruker, fyller eller
avviser oppføringen som forventet. Det sammenlignes 65 536 minnebyte og
registre ved andre servicekall og ved retur til `$1C10`. På den aktive
Kage-banen er det andre kallet første pikselrad. Både vertsprøven og den native
68000-prøven bestod alle 218 tilfeller med null avvik. Referansen utførte
1 824 753 instruksjoner fra C64-kandidaten. Maskinkoden og relokasjonsmålene
for Kages forberedelse, driveren og radløkken er like i tidsbygget og
det native kontrollbygget. Dette er avgrensede
kontroller og dekker ikke en naturlig gjennomspilling av alle rom.

Hver tidsprøve bruker PAL OCS, 68000, Kickstart 1.3, 512 KiB Chip og
512 KiB slow med 240 oppvarmingssteg og 240 målte spillsteg. Før/etter
har samme kode for prøveruten og ordinær feltplanlegging, tegning og lyd.
De to rom 1-parene prøver motsatt rekkefølge. Bevegelsesruten veksler
mellom løping og skråhopp i blokker på 20 steg. Begge fiender var aktive
i alle målte løkker i rom 1, og Bruce var i luften i 96 målte steg på
begge kjøringer med bevegelse. Den ekstra telleren for gjenbruk kjøres i
en egen binær og inngår ikke i før/etter-parene.

## Etterprøving

På Windows med prosjektets toolchain og WinUAE-oppsett brukes skriptene
i [analysemappen](../reference/analysis/op1-kage-prefix-2026-10-31).
`build_pilot.py reference` bygger de felles objektene. Bygg deretter
`candidate` og `observed` med samme skript. `run.ps1` tar variant,
ny prøveetikett, rom, fiendemaske og inputrute. Rute 0 er stillestående,
rute 1 klatrer og rute 2 løper og hopper. `build_controls.ps1` bygger
vitneprogrammene og genererer de lokale kontrolltilstandene. Det bruker
de to private C64-minneopptakene fra kontaktmålingen og romtestens DLL.
`run.ps1 proof` med ny etikett kjører kontrollene på Amiga. Rått C64-minne
og den store lokale prøvefilen ligger utenfor Git.

[Målinger og byggidentiteter](../reference/analysis/op1-kage-prefix-2026-10-31/result.json).
