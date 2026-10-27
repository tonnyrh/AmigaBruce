# NPC-rekyl og uventet romstart i rom2

Brukerfunn 25. oktober2026: Bruce sparket Yamo gjennom høyre vegg på
mellomnivået i rom2, og rommet startet deretter på nytt.

## Årsak og rettelse

Den gamle NPC-rekylen skrev bare en ny X-posisjon og klemte den til4–314.
Den gikk utenom bevegelsesrecordene som Bruces rekyl allerede brukte.
Også vanlig NPC-gange gikk utenom historikkprefiksen. Når en truffet NPC
senere fikk svart kontakt, hadde restitusjonen ingen riktig forflytning
å reversere. Den kunne dermed gå til kildens nødgren for romgjeninntreden.

I tillegg fortsatte NPC-rekylen etter en veggtilbakerulling. Bare Bruce
var beskyttet mot et ekstra rekylsteg mens tilstand24 eide koordinatene.
Etter at trefftelleren gikk ut, manglet vanlig NPC-oppdatering også grenen
som avslutter denne veggrestitusjonen.

Rettelsen bruker nå samme registrerte X-forflytning for alle tre aktører,
bevarer NPC-gangens historikk og lar restitusjonen eie koordinatene til den
er ferdig. Rå-X-grensene12–163 gir skjerm-X0–302. Den delte historikkprefiksen
er tatt ut i `bl_source_wall_age`; den er ikke en ny beregnet veggregel.
Den ordinære NPC-bevegelsens resterende kontakt-/AI-adapter er beholdt.

## Faktiske C64-bytes

Kilde: Remember/T64-kandidaten med SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Dette er ikke en sertifisering av valgt, urørt1984-utgave.

- `$241F/$242E/$247E/$24A1`: reaksjoner kaller de samme X-hjelperne,
  med aktør i X. De går ikke utenom historikken for Yamo eller Kage.
- `$1E86/$1EC4`: grensekontroll før hvert rå-X-steg; vellykket bevegelse
  øker henholdsvis `$4F5D,X` eller `$4F60,X`. Hver enhet er to skjermpiksler.
- `$1C6B–$1C9A`: historikken ages bare når gjeldende record er ikke-null;
  deretter nulles gjeldende record. Records er flettet med tre aktørbytes.
- `$1CC7–$1D6E`: svart kontakt reverserer den lagrede forflytningen og
  setter tilstand24/teller64. Dette skjer før handlingens egen forflytning.
- `$24B7–$24EA`: ved fortsatt svart kontakt og tom historikk setter koden
  uttrykkelig `$51=0`, leser rommets standardankomst og går til `$2F8E`.
  Dette kan skje også når det opprinnelig var en NPC som var fast.
  Amiga skal derfor bevare denne kildens nødgren, ikke bare ignorere
  alle romstarter fra en NPC.

Instruksjonsutskrift og kodekontroller ligger i
`reference/analysis/npc-recoil-2026-10-25/`.

## Kontroller

Før rettelsen gjenskapte en kontrollert R02-sekvens feilen: spark med Yamo
på Y146 og X276–288 lot NPC-en skli inn i svart kontakt, og romgjeninntreden
fulgte etter3–6 oppdateringer. Ytterligere injiserte startpunkter X290–304
var allerede inne i hindringen uten tidligere historikk. Slike tilstander
kan fortsatt nå den legitime C64-nødgrenen og brukes ikke som et krav om
at alle romgjeninntredener må fjernes.

De nye spillregresjonene dekker24 tilfeller: Yamo/Kage, overlevd/dødelig
spark, fire innløpsposisjoner mot mellomnivåets høyre vegg, den åpne øvre
utgangen og vanlig NPC-gange før treffet. Bruce flyttes bort etter det
kontrollerte treffet for å isolere reaksjonen. Testene kontrollerer beholdt
historikk, ingen ekstra rekyl i restitusjon, kildegrenser, avsluttet
veggrestitusjon og uendret rom-/spillerstatus. Dette er injiserte
testtilstander, ikke en registrert naturlig gjennomspilling.

192 tilfeller kjører den opprinnelige reaksjonskoden for aktør0/1/2 og
sammenligner X, retning og registrerte helpersteg med Amiga-hjelperen,
inkludert Kages ekstra rekyl ved teller10 og begge X-grenser.
1000 ekstra tilfeller sammenligner begge NPC-aktørenes vegg-/historikk-
forløp byte for byte med den faktiske6502-koden. Kildens nødgren beholdes.

Den komplette NPC-aktørmaskinen, korrekte NPC-kontaktpositurer i alle faser,
ordinær svart-kontakt-dispatch, kampens VIC-kontakt og AI-/livsforløp er
fortsatt delvise. Rettelsen er ikke en erklæring om full vegg-/kamp-paritet.
Den nye A500-rapporten binder24 regresjoner per start til kildekontrollene;
den strenge feltkadensen rapporteres separat.

To nye A500-CLI-kjøringer fullfører 6000 spillfelt hver, med 24 beståtte
rekylkontroller per start og gjenopprettet OS. Største ledige Chip-blokk er
88480 byte, over kravet på 49152. Kjøringene har 262/261 forsinkede felt og
maksimalt to PAL-perioder mellom oppdateringer uten framebufferkopien;
den strenge tidsporten består derfor fortsatt ikke. Rapportbufferen bruker
den frakoblede skjermbufferen etter OS-gjenoppretting, slik at testens
ekstra rapporttekst ikke tar varig plass i det begrensede minnet.

Start det nye programmet fra disk/CLI før manuell retest. En gammel USS
gjenoppretter også den gamle programkoden og tester ikke rettelsen.

[Leveranserapport](../reference/validation/npc-recoil-delivery.json),
[kildefixture-resultater](../reference/analysis/npc-recoil-2026-10-25/source-controls.json).
