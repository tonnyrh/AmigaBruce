# Plan: optimalisering av Bruce på Amiga 500

Gjeldende prioritering: **31. oktober 2026**. Planen ble opprettet 27. oktober.
Status og neste arbeidsrekkefølge nedenfor gjelder nå. Den opprinnelige
baselinetabellen og leveranseloggen lenger ned beholdes som historikk;
gamle tall skal ikke brukes som målinger av dagens normalbygg.

Målet er å få den kildebaserte motoren innenfor PAL A500 OCS / 68000 /
Kickstart 1.3 / 512 KiB Chip + 512 KiB slow, med bevart C64-oppførsel.
Først måles kostnadene pålitelig. Deretter erstattes de dyreste delene av
den instruksjonstro oversettelsen med små, kildeavstemte C-/68000-rutiner.
Spillfart, fysikk og fienderegler skal ikke justeres for å skjule treg kode.

## Sluttkontroll i WinUAE

Den samlede leveransen og de målte akseptansegrensene er beskrevet i
[OP-kontrollen for PAL A500](OP_A500_ACCEPTANCE.md). Den erstatter
arbeidsrekkefølgen nedenfor. WinUAE er valgt sluttplattform i denne runden.

## Status før den samlede kontrollen

Etter OP2-dekoderen fikk normalbygget ny meny og korrigert dødssekvens.
OP2-målingen nedenfor bruker nettopp denne versjonen som utgangspunkt.
[Bygg og testruter](../reference/analysis/op2-vic-pairs-2026-10-31/measurements.json)
binder før- og etterresultatene til byggene. PAL-budsjettet, original
rasterfase, naturlig gjennomspilling og fysisk A500 står fortsatt åpne.

| Del | Faktisk status | Videre beslutning |
| --- | --- | --- |
| OP0 – måling | Lett diagnose av bygget før OP2 er gjennomført med gjentakelse og måling av instrumenteringens kostnad. | Bruk den samme OP0-ruten uten detaljsporing for videre sammenligning. |
| OP1 – motor | Kontaktbudsjettet er målt, og Kages første serviceintervall er prøvd med reell kontroll av inndata. Rom 1 gikk fra 964 til 965 og fra 964 til 964 PAL-felt. Med Bruce i bevegelse gikk tiden fra 985 til 994 felt. | Piloten er avsluttet. Behold gjeldende motor. [Kage-forsøket](OP1_KAGE_PREFIX.md) |
| OP2 – felt og lyd | Maskedekoderen er levert. Neste endring flytter valg av horisontal pikseljustering ut av radløkken når to sprites overlapper. Rom 1 med begge fiender gikk fra 1004 til 963 PAL-felt i begge par. Tapte lydtikker gikk fra 3 til 0. | Behold rutinen. Bruk 963 felt som referanse for denne ruten. [Målemetode og kontroller](OP2_VIC_PAIR_OVERLAP.md) |
| OP3 – visning | Synlighet, trappefaser og flere overgangsfeil er behandlet. Tre figurer med maskinvaresprites er et isolert forsøk, ikke normalbygg. | Behold normal renderer. Spriteforsøket gir ca. 1,1–1,4 % samlet gevinst og ingen godkjent hardware-kollisjonserstatning. Ikke bruk mer tid på multiplexing nå. |
| OP4 – felt, lyd og input | Integrert feltservice ved `$2C51` bestod to komplette kampforløp med 18 kontrollerte IRQ-returer. Under begge lange falltreff falt tomme Paula-felt fra 15 til 3–4. Samme bevegelsesrute tok 1012–1013 felt mot 998 med lik utgangsmåling. | Behold feltservicen fra OP2. Den kortere poengvisningen er målt separat nedenfor. [OP4-feltprøven](OP4_FIELD_OWNER.md) |
| OP5 – kode/minne | Mindre kallkontroll og lokale 68000-kjerner er levert. De siste 13 CPU-sammenligningene er ikke valgt. | Behold minneportene og mål stack. Faste globale registre og mer generell caching legges til side. |
| OP6 – lasting | Menypublisering og romoverganger er behandlet; separat endelig tidsakseptanse mangler. | Etter løpende spillkostnad: mål ren rombyttetid og kontroller CLI/ADF, død og turbytte. |

[CPU-forsøkene](NATIVE_CPU_EXPERIMENTS.md) og
[spriteforsøket](HARDWARE_ACTORS_PROBE.md) er dokumenterte undersøkelser,
ikke leverte hastighetsforbedringer. Prosent fra ulike tidspar skal ikke
summeres. Kontrollert reprise, stillestående mikrotest, romtur og naturlig
spilling er forskjellige bevis og skal rapporteres hver for seg.

## Tidligere arbeid innen OP0–OP6

**Poengvisningen er målt.** Sifferparene fra `$315D` skrives nå med en
avgrenset 68000-rutine. Bevegelsesruten gikk fra 992 og 993 til 984
PAL-felt, med omtrent 40 ms kortere tid for det lengste spillsteget.
Begge falltreffene beholder sine 53 poengtildelinger.
[Poengmålingen](OP_SCORE_DISPLAY.md).

**Desimalkonverteringen er målt.** I to kjøringer gikk det lengste
spillsteget fra 3130 til 2817 rasterlinjer. Bevegelsesruten gikk fra
984 felt til henholdsvis 980 og 982 felt. [Måling og C64-kontroll](OP_SCORE_DECIMAL.md).

**Spriteoppdateringen er målt.** På vanlige steg uten poengtildeling i
rom 1 gikk `$2584` fra 49,9 rasterlinjer per steg med Bruce alene til
158,7 med begge fiender. Det forklarer anslagsvis 22 % av det målte
merarbeidet. De to gjentakelsene uten detaljmåling tok 720 felt alene
og 961 med begge. [Måling og C64-kontroll](OP_SPRITE_COST.md).

**Aktørmålingen er gjennomført.** Kallet `$1C29 → $179E` er målt på
de fire rom 1-rutene. Intervallene skiller `$2D7C` fra `$1C5B` og
`$2780` for Bruce, Yamo og Kage. En egen prøve bruker to
tidsavlesinger rundt hele aktørkallet. Tallene, de valgte rutinene og
de åpne akseptansegrensene står i
[OP-kontrollen](OP_A500_ACCEPTANCE.md).

### 1. OP0: lett diagnose gjennomført

[Måling og valgt mål](OP0_LIGHT_MEASUREMENTS.md): Rom 1 bruker 720 felt
med Bruce alene, 810 med Yamo og 1030/1031 med begge, per 240 målte steg.
Kontroll med færre tidsstempler gir 1017 felt med begge. Profilert total
skal ikke brukes som normaltempo. Rader, kontaktens egen tid og justering
utgjør samlet 374,4 eksklusive profilerte linjer per steg. OP1s radbehandling
og batchoppsett er valgt som neste avgrensede pilot; ingen ny normalmotor
er levert i OP0-runden. Metoden og begrensningene følger nedenfor.

Bruk det identifiserte normalbygget som referanse. Lag et separat målebygg
med samme motor, renderer og lyd, med få tidsstempler og tellere. Utelat
testfixtures, RAM-/lydhashing og bildeopptak i den målte perioden. Oppgi
avvik i instrumentering; ikke kall et instrumentert bygg identisk normal-EXE.

Mål rom 1 med Bruce alene, med Kage, med Yamo og med begge. Skill faste
testtilstander fra naturlig ankomst og kamp. Ta også med rom 12 for
trappeoppdateringer og rom 13 med Yamo ved første avsats. Registrer faktisk
forløpt PAL-tid, kildefelt, spillsteg, servicegap og tid til synlig bilde.
Ikke bruk antall ytre løkker eller emulatorens FPS som spillhastighet.

Bruk en kort profilert kjøring til rangering; bekreft totalen i uprofilert
målebygg. Summer bare gyldige eksklusive tidsblokker fra samme løkke.
Vis samlet kostnad per spillsteg, antall kall og verste felt, slik at mange
små kall ikke overses. Gamle profilgjennomsnitt alene bestemmer ikke valget.

**Resultat:** ruten er gjentatt med forklarlig tidsfordeling og dokumentert
målekostnad. Kontaktens radbehandling er valgt ut fra profilen. Denne
diagnoserunden gjenåpnes ved nye kodeendringer eller uavklarte måleavvik;
de opprinnelige sluttakseptansene beholdes.

### 2. Resultat av OP1 og OP2

OP1 prøvde å beregne første radadresse én gang og deretter øke pekerne i
`bl_contact_rows8`. Den isolerte løkken brukte 7,8–24,7 % færre rasterlinjer.
I de to rom 1-parene ble forskjellen henholdsvis 11 færre og 7 flere PAL-felt.
Gjentakelseskravet ble ikke oppfylt. [OP1-forsøket](OP1_CONTACT_ROW_WALK.md)

OP2 fant alle de observerte forsinkelsene etter felt med ny maskebygging.
Den nye rutinen reduserte tiden for 185 maskebygginger fra 8957 til 1730
rasterlinjer i den detaljerte ruten. Den senere parvise pikseltesten
fjernet de tre målte lydtapene i rom 1. OP4 skal fortsatt avklare
IRQ-/inputfase og tillatte servicegrenser i andre forløp.
[Maskedekoding](OP2_FIELD_AUDIO.md) og [pikseloverlapp](OP2_VIC_PAIR_OVERLAP.md)

30. oktober, stillestående fiender: [kostnaden er nå målt separat](ENEMY_COST.md).
Kontaktberegningen bruker omtrent tre ganger så lang tid med alle figurer som
med Bruce alene; spritebyggingen bruker over dobbelt så lang tid. En isolert
bildebygger halverer nesten spritekostnaden, men gir bare rundt 3 % lavere
samlet tidsbruk og flere tapte lydticks i testen. Den er ikke integrert.
Neste avgrensede mål er kontaktberegningen, med bevarte C64-resultater og
servicegrenser. Normalbygget er uendret i denne undersøkelsen.

31. oktober: [faste kopier i kontaktmaskene](CONTACT_UNROLL_OPTIMIZATION.md)
er utbrettet i 68000-kjernen. Den valgte varianten bruker 296 ekstra CODE-byte
uten nye buffere. Den faste prøven med begge fiender gir 3,6 % kortere
kontaktberegning; det avgrensede PAL-paret gir 1423->1410 felt og fortsatt
0 tapte lydticks. Dette er omtrent 0,9 % samlet gevinst i denne prøven.
Alle 710 native kontakt-/kopikontroller og den ferske 53-fixtur-/1200-
løkketesten består; sistnevnte beholder 52632 byte i største Chip-blokk.
Dette lukker bare dette lille kopieringssteget. Full PAL-kadens, naturlig
gjennomspilling/IRQ-fase og fysisk A500 er fortsatt åpne krav.

31. oktober: [13 isolerte CPU-sammenligninger](NATIVE_CPU_EXPERIMENTS.md)
er gjennomført med tomhetsbaner, kontaktmaskecacher, native aritmetikk og
faste 68000-registre for virtuell A og kilde-RAM-base. Kontrollene består,
men samlet gevinst er liten eller ytelsen regresserer ved overlapp.
Ingen av disse forsøkene er integrert. Normal motor og EXE/ADF beholdes.
Dette lukker undersøkelsen av disse variantene, ikke OP1/OP5 eller
sanntidskravet. Videre arbeid prioriterer en avgrenset varm kontaktrutine
fremfor flere generelle cacher eller globale registerbindinger.
