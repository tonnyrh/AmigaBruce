# Spillbarhet og første synlige grafikkleveranse

Dette er en videre kandidat i M4 og første del av M5, ikke fullført M4/M5.
Feller, dynamiske dører og naturlig gjennomspilling mangler fortsatt. De 20
rommene er fortsatt tilgjengelige som inspeksjon med F1/F2.

## Endringer

Bruce, Ninja og Yamo har 21 nye AI-genererte positurer totalt. Bilder med
løpesteg, slag, spark, liggestilling og klatring erstatter de rektangulære
prototypefigurene i det vanlige spillet. Bruce står i ro når han står stille.
Venstrevendte bilder speiles om samme anker som høyrevendte. Klatrebilder
bytter med vist klatreavstand som før, ikke bare etter en animasjonsteller.

Ny AI-generert fjellbakgrunn er konvertert til samme 16 OCS-farger og brukes
under plattformer/nett. Yamo har fått en egen mørkegrønn palettfarge. Denne
bakgrunnen er første stilkandidat og deles foreløpig av alle rom. Plattformene
og nettene er fortsatt de eksisterende skissene, ikke ferdige nye tiles.

Kildebilder og prompts finnes i `assets/graphics/v1/`. Verktøyet var innebygd
image_gen; seed var ikke tilgjengelig. Format og palett er validert med
Amiga-grafikk-skillens deterministiske verktøy. Originalens skjermbilde ble
brukt som identitets-/miljøreferanse. Dette erstatter ikke den planlagte
ressurs-for-ressurs-oversettelsen av C64-tiles og sammensatte animasjonsbilder.
Ingen eksakt C64-komposisjon eller godkjent grafisk paritet påstås.

`tools/build_fighter_art.py` beholder faste utsnitt og anker (16,25) i 32x26
piksler, pakker to fargeindekser per byte, og skriver Amiga-headeren. 8736
byte er CPU-side kildekunst; eksisterende stamp-/maskestørrelser og Chip DMA-
arbeidsområde gjenbrukes.

Stamp-/maskelagringen er flyttet fra en stor statisk BSS-del til to separate
CPU-allokeringer. Dette reduserer kravet til ett sammenhengende minneområde
ved programlasting; eventuell bruk av Chip RAM for CPU-data måles eksplisitt
som `cpu_stamp_chip_bytes`. Bakgrunnene bruker nå 117554 pakkede byte,
fortsatt med to utpakkede rombuffere.

Tegneren bruker et generert radintervall for hver positur. Tomme topp-/bunn-
rader kopieres ikke til DMA-arbeidsområdet og blittes ikke, mens fotankeret
beholdes. Dette er nødvendig: den første versjonen som alltid tegnet 26 rader
mistet ett felt på frame 5145 i 6000-felts kamptesten (318 arbeidsrasterlinjer).
Den testen ble stoppet og teller som mislykket; optimalisert kode må gjennom
hele ruten på nytt. Ingen timinggrense er lempet for å skjule feilen.

T06 har en kandidatrettelse: støtte/landing bruker kroppsbredde rundt midten,
seks piksler på hver side, i stedet for midtpunkt alene. Dette gjelder også
eksisterende NPC-bevegelse og må vurderes mot C64. Ingen hopp etter faktisk
gulvavgang er innført. Verdien er et eksplisitt testforslag fra den manuelle
observasjonen, ikke en målt original pikselmaske.

T10-NET har en avgrenset kandidatrettelse: et pågående hopp inn i et nett
griper ved ren sideinput, uten at opp holdes. Grepet beholdes mens kroppen
overlapper nettet. Etter slipp gjelder fortsatt fritt fall med låst X.
Opp/ned prioriteres fortsatt foran sideinput under klatring. Den første,
bredere autogrepvarianten påvirket en frossen fiendesekvens og ble forkastet;
den skal ikke regnes som en godkjent implementasjon.

## Avgrensning og test

T02/T03 og resten av de åpne kampreglene er ikke løst med ny kunst. Nye
figurer endrer ikke kampens treffbokser. Eksakte fot-/håndankre mot C64 og
alle romtemaer må fortsatt gjennomgås. Bruk `docs/ACTIVE_TESTS.md` for retest;
tidligere godkjente tester er ikke satt tilbake til åpne.

Kjernetestene inkluderer kantlanding fra begge sider, sats fra ytterste
støtte, autogrep uten opp og rett fall etter nettutgang. Kandidatens faktiske
native resultater føres i `reference/validation/visual-candidate.json` etter
kjøring. Eldre milepælrapporter har sine opprinnelige kildesignaturer; ikke
tolk et gammelt pass som validering av nye kilder.

Første 900-felts romtest bestod med null tapte felt og `cpu_stamp_chip_bytes=0`.
Eksplisitt Chip-allokering var 170948 byte og største frie Chip-blokk 268352
byte. Det native bildet finnes i `docs/images/m4-rooms.png`.

Oppstart på vertsmaskinen viste seg å kunne ta over 90 sekunder før emulator-
vinduet ble opprettet. To tidlige forsøk rakk derfor ikke å levere rapport og
regnes ikke som bestått. Testens vertstidsfrist ble økt til 240 sekunder pluss
kjøretid; kravene til emulert PAL-timing ble beholdt. Den separate endringen
i CPU-allokering er en minneforbedring, ikke dokumentert rotårsak til disse
tidsavbruddene. Windows-vindusverktøyet kunne ikke brukes til visuell normal-
kontroll fordi det returnerte tilgang nektet. Native framebuffer-eksport
brukes derfor som visuell evidens.

Etter radoptimaliseringen bestod hele 6000-felts kampruten. Toppbelastningen
på samme frame 5145 var 276 rasterlinjer, null tapte felt. Alle 69 lyder fikk
stillhetsomlasting og ingen ble droppet. Kamputfall: 11 fiendespawn, 65 treff,
5 beseirede fiender, 2 spiller-dødsfall og 2 nye liv, lik kjernetesten.
900-felts romrute bestod også etter optimaliseringen. Gjentatt oppstart av
selve kamprendereren skal i tillegg kontrollere de nye CPU-allokeringene.

Den gamle 360-felts CLI-ruten fullførte uten felttap, men nådde ikke helt ut
av nettet med den nye gripebredden. Den feilet derfor sitt krav om registrert
fritt fall. Kravet er beholdt: en lengre 900-felts rute brukes for ny dekning
av fall, klatring, slag, spark og liggestilling. Dette er endret testlengde,
ikke et fravik fra fallregelen. Den gamle rapporten er historisk, ikke ny
godkjenning. En ekstra 900-felts kampfixture med ett oppvarmingssteg kjøres
to ganger fra CLI for å kontrollere figur-/maskeminne ved gjentatt oppstart.

Sluttkontroll: 7200-felts romtur besøkte alle20 rom, med19 lastinghendelser,
null tapte spillefelt og maksimalt26 felt ved en eksplisitt romlasting.
Både900-felts bevegelsesrute og900-felts kamprenderer bestod to påfølgende
CLI-oppstarter, med lik tilgjengelig Chip-/utvidelses-RAM før hver kjøring.
Den nye validatoren kontrollerer både ressursdata og ferske kildesignaturer.

Testverktøyet brukte samme bildefilnavn for6000-felts kamp og senere
debug-/repetisjonstest. Det senere bildet er bevart separat som
`docs/images/m3-repeat.png`. Den eldre bildesignaturen er beholdt som
historisk post, mens dens nå overskrevne fil ikke påstås bevart. Runtime-
resultatene er uendret. Ferske visuelle bevis er rombildene og repetisjonsbildet.
