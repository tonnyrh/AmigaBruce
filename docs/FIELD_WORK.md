# Feltarbeid på PAL A500

## Målt i WinUAE

På den faste kampruten i rom 1 tok 240 steg 796 og 794 PAL-felt på to
kjøringer med Kage og Yamo til stede hele tiden. Forrige bygg brukte
812 og 812. Med 50 felt i sekundet gikk tiden fra 16,24 s til 15,92 og
15,88 s. Målet på tre felt per steg er 14,40 s. Alle fire kjøringene
hadde én Paula-publisering per felt.

Med Bruce stående og begge fiender aktive falt tiden for de samme 240
stegene fra 783/766 til 743/743 felt. Det er 14,86 s i begge de nye
prøvene. I de to langkampene rakk bygget 1 854 steg på 6 001 felt og
1 874 steg på 6 000 felt. Forrige bygg rakk 1 842 og 1 846. Paula fikk
én publisering i hvert av de 12 001 feltene i de nye prøvene. Tidligere
hadde de to prøvene til sammen fem felt uten publisering og ett med to.

Trapperuten i rom 12 gikk fra 778 til 769 felt. Ruten med Yamo i rom
13 brukte 720 felt for 240 steg i begge bygg.

Joystickprøven i CLI-utgaven gikk fra rom 1 til 2 og tilbake. De 36
bildene fra trappene i rom 12 og de 12 fra død og retur til rommet hadde
sammenhengende tegnoppdateringer og uendrede statiske piksler.

Vanlig CLI og oppstart fra skrivebeskyttet ADF kjørte henholdsvis 6 018
og 6 006 felt etter pause med null tapte lydtikk. På ADF overtok spiller 2
etter dødsfall. Den separate 68000-testen bestod alle 53 kontroller og
1 200 løkker på Kickstart 1.3 med PAL OCS og 512 + 512 KiB. Største ledige
blokk Chip RAM etter lasting var 52 632 byte i denne testutgaven.
[Byggidentitet og råmålinger](../reference/analysis/field-work-2026-11-01/delivery.json).

## Joystick

På C64 går spillavbruddet fra `$48C1` via `$4915` til `$15A8`.
Etter lyd, spritevisning og tidstellere kommer avlesingen ved `$169D–$1702`.
Når `$0104` er null, fortsetter programmet ved `$1703` med de gamle
verdiene i `$98/$9B` og `$99/$9C`. Ellers velger `$03` porten til
aktiv spiller. `$1383+X` velger om retningen skal gå gjennom tabellen
ved `$4A85`. `$42CA` bestemmer om den andre spilleren styrer Yamo.

I vanlig Amiga-spill leser nå selve feltrutinen joystickregistrene når
den passerer denne grensen. For standard enspillermodus kan 68000 skrive
de to bufferne og sluttflaggene direkte. De andre modusene følger alle
relevante grener, også PHA/PHP-skrivingene til stakken. Kontrollerte
repriser kan fremdeles levere inndata gjennom motorens eksisterende API.

Vi startet fra et frosset VICE-snapshot og nådde stående og hoppende Bruce
med joystick. Høyre før avlesingen ga retningene 7, 7, 7. Høyre etter
avlesingen ga 15, 7, 7. I de to situasjonene gikk det 20 009 og 19 877
C64-sykluser mellom de første observerte returene til `$1703` i
etter-prøven. WinUAE-prøven bruker den vanlige Amiga-portleseren og tolv
kontrollerte felt med samme portverdier. Verten avtaler når kanten kommer
i forhold til avlesingen. Dette måler rekkefølgen mellom inndata og felt.
Absolutt forsinkelse fra fysisk kontroller til synlig bevegelse og hele
C64-avbruddets naturlige rasterfase står åpne.

## Tegning med fiendene til stede

Blitteren gjenoppretter bakgrunnen bak figurene og tegner maskerte sprites.
Tidligere ventet CPU-en både på slutten av hvert oppdrag og før den kunne
programmere det neste. CPU-en kan nå beregne neste rektangel mens blitteren
arbeider. Ved hvert nytt oppdrag venter CPU-en før den skriver
blitterregistrene, og den venter før egen pikseltegning, inkludert
prosjektilene i rom 19. Under spillets maskinovertakelse får CPU og blitter
dele bussen. Bildepresentasjonen beholder sine egne eierskapsgrenser.

Er bildet klart før linje 44, kan det meldes til Copper fra linje 44 i
samme felt. Det blir synlig ved neste Copper-omstart. CPU-en fortsetter
å betjene lyden mens den venter. Et sent bilde følger den eksisterende
presentasjonsveien.

Hver tegnrad har de samme 20 ordmaskene. De to oppdateringskøene deler nå
én kolonnemaske per ord. Det frigjør 3 920 byte. I en kopi av det store
testprogrammet målte vi at DOS tidligere lastet BSS i Chip RAM og at begge
skjermbufferne og lydbufferen manglet. Etter endringen lastes BSS i
utvidelsesminnet og alle tre bufferne får plass i Chip RAM.

## Lyd og lange falltreff

Paula beholder tre DMA-kanaler med fast adresse og lengde. Ved bølgebytte
fyller 68000 kanalens 1 024 byte i grupper på 32 byte. En kort bølge
leses inn i registrene én gang. Perioder, volum, kanalvalg og kildeeffekter
følger samme datastrøm. Når lydservicen er ajour, kan spill- og lydservice
bruke samme klokkeavlesing. Når lydkoden faktisk kjører, leses klokken
igjen før neste spillfelt behandles.

Et falltreff på Yamo ved steg 728 tok 1 392 rasterlinjer i en instrumentert
langtest, omtrent 89 ms. Helsens byte gikk fra 3 til 124. Ved `$2C03`
tildeles 50 poeng. Yamos gren setter A og X til 1 ved `$2C30`, slik at
`$317F` skriver i midtre poengbyte og gir 256 poeng. `$2C36` gir deretter
194 poeng i lav byte. Det gir 500 per negativt omløp, mot 250 for Kage.
68000 kontrollerer den opprinnelige ekstralivsterskelen etter **hver**
tildeling. Siste ordinære omløp kjøres ferdig gjennom kilderutinen, slik
at stakk, desimalarbeidsområde, HUD og flagg får kildeverdiene.

Kildegrunnlaget er Remember/T64-kandidaten med SHA-256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Identiteten som urørt 1984-utgave er fortsatt uavklart.
