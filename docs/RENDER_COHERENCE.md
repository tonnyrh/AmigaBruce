# Sammenhengende rombilder, 29. oktober 2026

Brukerfunn: rykkete trappeanimasjon i rom12 og grafikkfeil ved død/rombytte.
Dette behandles innen OP3 og OP6; det innføres ingen nye spillregler.

Frosset C64-kandidat:
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
`$2C92-$2CD6` velger bank og bevegelsesmønster; `$2CD8-$2CEF` oppdaterer
fasen i `$64` med retning fra `$65`; `$2CF1-$2D54` skriver de tre parene
med8x16-tegn, inkludert dupliserte rader og omslag etter åtte mønsterbyte.
Disassemblyen er lagret i analysemappen. Remember/T64-identiteten er fortsatt
ikke sertifisert som urørt 1984-utgave.

Rom12 har åtte cachefelt, 6528 byte per samlet fase. Bakgrunnsarbeidet var
delt i to grupper, mens kopiering til skjermbufferen hadde et budsjett på
5000 byte. En vertstest med ekte kildebaserte spillsteg viste1088 avvikende
planarbytes etter første gruppe. Den andre gruppen gjorde bakgrunnen korrekt,
men delvis oppdaterte bilder kunne allerede være vist.

Løsningen beholder den begrensede bakgrunnskøen for vanlige endringer og
legger alle gyldige cachefelt i samme kildefase direkte i den skjulte
skjermbufferen før figurene tegnes. Kun hele16-pikselord som overlappes fullt
kan tas ut av kopieringskøen. Maskerte kantord beholder vanlig kopiering av
nabografikk. Endrede tegn/farger invaliderer hele det berørte cachefeltet;
ukjent fase bruker eksisterende kildebasert tegning. Kilde-RAM røres ikke.
Dekningsmasken gjenbruker allerede konsumert renderer-metadata og krever
ingen ekstra buffer eller Chip-/slow-allokering.

To konkrete overgangsfeil rettes også:

- Etter første publisering av buffer1 var lokal bufferindeks fortsatt0.
  Neste tegning kunne derfor velge den synlige buffer1. Indeksen settes nå
  eksplisitt til den publiserte bufferen før neste skjulte buffer velges.
- Rydding av GAME OVER-feltet ved y49 med høyde8 slettet også y56,
  den første tegnede pikselraden i C64-rommet. Tekst/rydding flyttes til
  y46, innenfor HUD-området. Native kontroll fant16 slettede rompiksler
  på denne linjen før rettingen.

Vertskontrollen dekker60 rominnlastinger/gjeninnlastinger,96 kildebaserte
spillsteg i rom12, uendret kilde-RAM under presentasjon og korrekt fallback
når et cachefelt endres. Eksisterende kø-/overflytskontroller beholdes.
Native fasebilder, overgangskontroller og samlet motorakseptanse rapporteres
separat i analysemappen. En mellombuild med en ekstra100-byte tabell feilet
allokering i den store diagnosebyggen; den er arkivert og ikke godkjent.

Dette er en bildekorreksjon. Ingen forbedring i samlet tempo eller full
sanntidsakseptanse hevdes. Ny naturlig prøving av rom12, død og rombytte
står som eksplisitte brukerprøver.

Native pausebasert før/etter-kontroll: gammel versjon hadde8 av16 bilder
med blandede faser, opptil1888 feil rompiksler i trappefeltene. Ny versjon
hadde0 av16; etter kontrollert død og rom13->12 hadde den0 av12. Begge
nye prøvene hadde også null avvik i statiske rompiksler utenfor figurene.
Dødsprøven injiserer terminal aktørtilstand fra C64-motorkontrollen
(`$D1=$FF,$BF=25,$CE=1`) og kontrollerer at kildens loader-epoke øker.
Dette er en kontrollert prøve, ikke en naturlig gjennomspilling.

Levende debuggeravlesning kunne selv treffe flere bufferbytter og ga ett
misvisende blandet etter-bilde. Sluttkontrollen pauser emulatoren mens
kilde-RAM og skjermbildet leses. WinUAE-hendelsen er dokumentert i
[offisiell inputevent-kilde](https://github.com/tonioni/WinUAE/blob/master/inputevents.def).
Bilder fra den levende metoden er bevart som uavklarte/måleutsatte,
men brukes ikke til godkjenning av pikselkoherens.

OP5/diagnostikk:53 motorfixturer og454 ekstra kontaktreferanser passer ikke
lenger samlet i den store diagnosebyggen. De kjøres separat:53 fixturer og
1200 løkker i motorbygget,454 kontaktkontroller pluss256 spritevarianter
(710 totalt) i referansebygget. Ingen kontroller eller minneporter fjernes.
De8 kontaktprimitivene bindes bytevis mellom normal-, motor-, referanse-
og tidligere1046-kontrollbygg. Diagnostikkens nye preprosessorguard endrer
bare én debug-symbolbyte i normal EXE; CODE/DATA/BSS og relokeringer er
uendret. Sluttkontrollen binder det testede lastebildet med en HUNK-signatur
som utelater SYMBOL/DEBUG, men beholder alle lastede byte, minnekrav og
relokeringer.

Sluttkontroller:53 native fixturer og1200 løkker består i motorbygget;
710 kontroller består i den separate kjernekjøringen. Største ledige
Chip-blokk er fortsatt52632 byte (port49152); diagnosebygget har2192 byte
ledig expansion-RAM før de eksplisitte grafikkallokeringene. Opptaket har
null rester i selve scenen og null uforklarte rester;42 HUD-bytes er
forventet dynamisk status. CLI/ADF-oppstart, rom1-6, synlighet og den negative
fellefasen i rom6 består. Normal EXE er343028 byte,812 mer enn før.
Det hevdes fortsatt ikke at PAL-sanntidsporten er bestått.

Etter OP4-optimaliseringen av visningsdata er samme kontroll gjentatt med
den nye normalbyggen:12 bilder i rom12 og12 etter kontrollert død og
rombytte, alle med null avvik i animerte og statiske rompiksler.
Den nye ELF-identiteten bindes direkte i render-coherence.json.

OP2/OP5s nye VIC-cache beholder samme renderer. Den nye normalbyggen
kontrolleres med egne `vic-cache-native`-opptak, direkte bundet til ELF.

OP6-menybygget er kontrollert separat som `menu-native` og
`menu-native-death`:12+12 bilder, null animasjons- og statiske avvik.

V3-fargeskriveren er kontrollert med egne `color-native`/`color-native-death`-opptak fra den nye normal-ELF-en:12+12 bilder, null animasjons- og statiske avvik. Den aktive metadatakroppen beholder opprinnelig maskinkode og relokeringer.


30. oktober: en ny prøve fant fire piksler som den gamle kontrollen feilaktig
kalte statiske. De tilhører tegn $93: originalens $40D0/$40D3 skriver
$AC9A/$AC9B med samme AND-$30-resultat. Bildet viste et komplett lovlig
eldre flimmerpar $00/$00, mens kilde-RAM allerede hadde $20/$20. Dette er
fakkel-/flimmeranimasjon, ikke trappenes $61-$63-faser. Feilprøven og den
eldre kontrollkoden er bevart. Ny kontroll skiller bare ut de dokumenterte
radene 2/3 for $93/$94/$B1 i den valgte banken og kontrollerer dem mot hele
lovlige bytepar fra originalkoden og originalinit. Uendrede rader må fortsatt
stemme eksakt. Blandede par, ugyldige mønstre og vilkårlige enkeltpiksler
avvises i 88 positive/negative kontroller; ingen pikseltoleranse innføres.
Det registreres også om synlig flimmer faktisk skifter når kilde-RAM viser
flere komplette tilstander. Denne bildeanalysen beviser ikke sanntidsporten.


30. oktober, sluttbygg: observer-native og observer-native-death har12+12
pausebaserte bilder, null blandede trappefaser, null statiske avvik og null
ulovlige flimmerpar. Synlig tegn $93 viste tre ulike lovlige par, som også
kilde-RAM gjorde. Originalinit i flimmerkontrollen kjøres gjennom faktiske
6502-bytes: $10C5, $33CA, loader $0A9B-$0B30, $336E og rommets initpeker;
Python-verktøyets decode-modell fastsetter ikke de initierte tegnbytene.
Menytesten har78 bilder, hvor33 viser endring i skjult buffer mens den
synlige forblir komplett. Alle opptak er kontrollerte emulatorprøver.
Normal EXE er nå343388 byte; sanntid og naturlig brukerprøve er fortsatt åpne.
