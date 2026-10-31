# OP1. Kontakt mellom figur og rom ved `$5212`

## Hva målingen skiller

På den vanlige OP0-ruten i rom 1 står Bruce stille mens Kage og Yamo er
aktive. Hver oppstart bruker 240 oppvarmingssteg og 240 målte spillsteg
på PAL A500 OCS med 68000, Kickstart 1.3 og 512 KiB Chip + 512 KiB slow.
Den ordinære ruten i forrige leveranse tok 963 PAL-felt i begge kjøringer.

Det private målebygget tar tiden ved inngang og retur fra den native
kontaktrutinen, ved starten på hver figur og før og etter hver radservice.
De to vinduene for felt- og lydarbeid telles separat. Etter ruten,
mens spillet ennå eier maskinen, måles 256 tomme par med tidsstempler.
Kalibreringen gir et anslag på observatørens bidrag til kontaktvinduet.
En separat kjøring måler hvert åttende kall. Et kontrollbygg kjører samme
observerbare spillbane med tidsstemplingen avslått. Disse diagnosebyggene
har ekstra kall og brukes ikke som ny normalreferanse.

## Kildekontroll og avgrenset avspilling

Kildegrunnlaget er Remember/T64-kandidaten med SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Identiteten som urørt 1984-utgave er åpen. Spillets hovedløkke kaller
`$5212` og fortsetter ved `$1C10`. Før hver figur er Amigaens servicepunkt
knyttet til `$5214`. Inne i radløkken brukes `$5380` når Y er delelig på
åtte. Originalen behandler figur 2, 1 og 0 i den rekkefølgen, med
aktivbiten i `$95+X`. Posisjon, positur, tegn, attributter og pikselmasker
påvirker resultatet. Kroppskontakt går til `$A7+X` og sluttmasken til
`$B6+X`.

I to separate WinUAE-kjøringer hentet vi én inngangstilstand fra vanlig
feltplanlegging etter henholdsvis 240 og 400 steg. Bare under det utvalgte
kallet ble ny IRQ- og lydservice holdt tilbake. Vi registrerte hele
inngangsminnet og alle endrede byte, registre og flagg ved hvert
servicepunkt og ved retur. Py65 kjørte deretter C64-instruksjonene fra samme
inngang. Kontrollene krever likhet i alle 65 536 byte, A/X/Y, SP og
C/Z/N/V/D/I. Kjørt kode sammenlignes med den frosne binæren. De åtte
selvmodifiserte adressebytene ved `$52CC`, `$5381`, `$539B` og `$53B5`
kontrolleres gjennom samme minneforløp. Dette er kontrollerte enkeltkall.

På Amigaen sammenlignes så den vanlige kontaktrutinen med avspilling av
de registrerte endringene ved de samme servicepunktene. Hvert tilfelle
gjentas 64 ganger per variant, vekselvis A/B/B/A, med samme inngang og
nullarbeid i servicefunksjonen. Klargjøring av inngangsminnet er utenfor
tidsvinduet. Begge varianter kontrolleres også med full minnesammenligning
på Amigaen. Detaljene i C64-stacken og de selvmodifiserte operandene er med.
Avspilleren kjenner inndata og resultat på forhånd. Et vanlig spill må også
finne eller beregne riktig resultat når figurer, tegn eller attributter endres.

## Hvilken figur er det verdt å prøve først?

I en egen rom 1-kjøring på 963 felt ble alle tre figurer behandlet 240
ganger. Posisjon og positur var lik forrige steg 239 ganger for Bruce,
221 for Kage og 103 for Yamo. Bruce hadde én kombinasjon på denne ruten,
Kage fire og Yamo 136. Registreringen kostet ingen observerte lydtikker.
Like kombinasjoner ga like kropps- og fotmasker i akkurat dette materialet.
Tegn, attributter, maskebyte, stack og mellomtilstander ved servicepunktene
kan likevel endres selv når figuren står stille.

Oppfølgingen prøvde gjenbruk for Kage fram til første radservice.
Hurtigbanen traff 221 av 240 ganger, og begge tidspar endte uten
gjentakbar gevinst. [Målinger fra Kage-piloten](OP1_KAGE_PREFIX.md)

## Gjenta forsøket

Kjør `build.py` i analysemappen og bruk `run.ps1` med en ny etikett for
hver kjøring. `control`, `timed` og `sparse` bruker 240 oppvarmingssteg.
For `capture` ble 240 og 400 brukt. `audit.py` tar opptakets mappe og lager
en kontrollert avspilling. Bygg med `build_replay.py` og bruk `replay` med
samme oppvarming og `-Fixture` satt til den genererte `replay.bin`.
`build_keys.py` og `keys` lager den separate posisjonskontrollen.
Skriptene bruker prosjektets lokale WinUAE-, ROM- og OP0-oppsett.
Råopptak med C64-minne er bevart lokalt under
`.reference/c64/work/op1-contact-budget-2026-10-31`. Git-registeret
inneholder hasher og observerte resultater. Kjør `check.py` for å
kontrollere de arkiverte kjøringene og gjenta sammenligningen mot
originalinstruksjonene når de lokale råopptakene finnes.

[Måleresultat og byggidentiteter](../reference/analysis/op1-contact-budget-2026-10-31/result.json).
