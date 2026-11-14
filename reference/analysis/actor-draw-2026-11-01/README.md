# Direkte tegning av Bruce, Kage og Yamo

Det forrige bygget tegnet figurene på koordinatene fra C64-motoren.
Samtidig beregnet det tre separate sett med interpolerte koordinater
som tegneren aldri leste. På en profilert kamprute ble mellomposisjonene
oppdatert 768 ganger. Den nye løkken leser posisjon og positur fra samme
figurtilstand som før, og slipper å kopiere tre `BlGame`-strukturer til
stakken for hver tegning.

## Hva langkampen viste

Direkte tegning uten flere lydsjekker ga 763 og 767 PAL-felt i to korte
prøver. I begge langprøvene manglet tre publiseringer. En ekstern måler
så telleren øke ved steg 1 489, 1 649 og 1 809 på den samme kjørbare
filen. I en særskilt sporingsutgave ble en forsinkelse på to felt oppdaget
ved steg 1 808. Returadressen i 68000-stakken lå ved lydsjekken i den
oversatte `$2586`-rutinen. Dette identifiserer hvor spillet oppdaget
forsinkelsen. Tidsmålingene for sluttbygget bruker en separat utgave uten
stakksporing.

Den frosne Remember/T64-kandidaten har SHA-256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Det er fortsatt uavklart om den er den urørte 1984-utgaven.

| C64-adresse | Bytes | Operasjon ved lydsjekken på Amiga |
| --- | --- | --- |
| `$1C23` | `20 C3 29` | Før `JSR $29C3` når kontaktgrenen sender aktørene til kampbehandling. |
| `$1C29` | `20 9E 17` | Før `JSR $179E` oppdaterer aktørene. |
| `$25AE` | `A6 51 E0 02` | Før `LDX $51; CPX #2` avgjør om en sekundær sprite kan bygges. Den primære komponenten er behandlet. |

De tre punktene gir Paula anledning til å betjene et forfalt felt. De
kaller kun lydservicen. Joystick og spillsteg beholder sine egne grenser.
På verts-PC ble en tellende funksjon kalt 3 468 ganger over 2 880 felt og
960 spillsteg. Alle 65 536 byte, 13 register-/tilstandsverdier og
returgrensen stemte i parvise kjøringer med og uten telleren. Denne
kontrollen av funksjonskallet er separat fra sammenligningene med
C64-instruksjonene og de faktiske Paula-skrivingene i WinUAE.

## Sluttkontroll på PAL A500

WinUAE kjørte med sykluseksakt 68000, OCS, Kickstart 1.3 og
512 KiB Chip + 512 KiB utvidelse. Den faste reprisen bestod alle
53 motorkontroller og 1 200 løkker. Det lagrede kampbildet var identisk
i alle 40 960 byte med forrige leveranse. Største ledige Chip-blokk
i denne testutgaven var 52 632 byte. CLI-utgaven kjørte 6 016 felt
etter pause og krysset rom 1 → 2 → 1 med joystick. ADF-utgaven kjørte
6 024 felt etter pause, og spiller 2 overtok med fire liv i rom 1.
Begge hadde null tapte lydtikk i dette målevinduet. De to lange
kamprutene målte også de fysiske Paula-skrivingene i hvert felt.

## Gjentakelse

Bygg de tidligere måleutgavene som beskrevet i
[feltarbeidet](../field-work-2026-11-01/README.md). `build_trial.py release <ny-mappe>`
og `build_trial.py long-release <ny-mappe>` legger produksjonsendringen
inn i de samme korte og lange måleprogrammene. Bruk `run.ps1` fra
`op-score-2026-10-31` med den samme rom-, fiende- og rutekoden som
før. Den korte kampruten bruker rom 1, fiendemaske 3 og rute 2.

`check_audio_seams.py <DLL> <rapport.json>` bruker vertsobjektene fra
`test-c64-actors.ps1`. Ved lenking av kontroll-DLL-en trengs også eksport
av `bl_c64_set_audio_poll`. Skriptet laster to uavhengige kopier og
sammenligner dem etter hver felt- og stegrutine i fire oppsett.

[Leveransen](delivery.json) binder råmålingene, vanlig CLI- og diskettoppstart,
bildetestene og motorprøvene til versjonen som ble kjørt. Kjør
`python tools/verify_op_finish.py` for å kontrollere dem.
