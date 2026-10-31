# Skjult menytegning, 29. oktober 2026

OP6: menyen ble tømt og tegnet direkte i buffer0 selv når Copper viste
bufferen. Et faktisk ADF-opptak viste bare en del av tittelen. Lydstart
var derfor utilstrekkelig som bevis for at hele menyen var ferdig.

Menyen tegnes nå i den andre av de to eksisterende skjermbufferne. Hele
menyen ferdigstilles før Copper-publisering ved VBlank. En ekstra feltgrense
sikrer at Copper har overtatt den nye bufferen før den gamle kan gjenbrukes.
Ved F10-retur lar første feltgrense en eventuell spillpublisering bli latchet.
Den eksisterende lokale `back`-variabelen følger den faktiske fronten; ingen
ny Chip-buffer eller persistent visningstabell allokeres.

Spillstart fyller først bufferen som ikke viser menyen. Den eksisterende,
blokkerende OCS-kopirutinen kopierer hele40960-byte-bildet, med lydservice
mens Blitter arbeider. Etter publisering og feltgrense fylles den andre
bufferen. Det forrige faste valget av buffer1 var ikke gyldig etter et
vilkårlig antall menyvalg. Den overflødige synlige FIRE TO START-tegningen
beholdes bare i diagnosebanen. Den gamle ubrukte CPU-kopihjelperen fjernes.

Dette endrer Amiga-presentasjon. Menytekst, valg, tastetolkning og kallene
som starter spillet beholdes. C64-starten er fortsatt
`bl_session_source_start` -> `bl_c64_world_start`, som setter `$42C9-$42CC`
og kjører `$0743`; spillets eksisterende kilde-/IRQ-kjede er ikke endret.
Tittelens lydtjeneste beholdes. Ingen ny spillregel utledes fra menyprøven.
Den frosne Remember/T64-kandidaten er fortsatt ikke sertifisert urørt1984:
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.

Native UI-kontroll:74 pausebaserte front-/bakbilder,37 ufullstendige skjulte
arbeidsbilder, hvorav30 faktisk endret seg mellom prøvene mens frontbildet
var komplett. Alle synlige menyer samsvarer med før-/etterbilder rekonstruert
fra den frosne forrige fonten og menyteksten. Testen dekker spillervalg,
Yamo-valg, Shift+D, testflagg, romvalg, retur til vanlig meny, F10-retur og
spillstart med både buffer1 og buffer0 som menyfront.
Hele64KiB C64-RAM er identisk før og etter de ti menyendringene før start.
Dette er kontrollerte UI-prøver, ikke en naturlig C64-gjennomspilling.

`verify_menu_publication.py` kontrollerer de faktiske råbildene og
RAM-dumpene, bindes til den nye normal-ELF-en og verifiserer at motorfilene
og spilløkkens kildetekst er identiske med baseline. Seksjonsstørrelser
registreres i samme rapport; BSS er uendret. Normal EXE er343104 byte,
88 byte mer enn forrige leveranse. Statisk main-/kallkjedestack og fysisk
A500-kontroll er fortsatt egne OP5-/akseptansepunkter.

Den nye bakgrunnskopieringen bruker en eksisterende verifisert Blitterbane;
det fremsettes foreløpig ingen ren tidsgevinst for hele oppstarten. Tidligere
spill-/VIC-målinger er historiske målinger av den frosne forrige main-filen;
de skal ikke fremstilles som nye timingkjøringer av menybygget. Streng
sanntid, input-/IRQ-avlesning og resten av de opprinnelige OP0-OP6-portene
står fortsatt åpne.

F10-returen har ogs� to delvis tegnede bakbilder mens det samme komplette
spillbildet vises, med en faktisk endring mellom pr�vene. Det beholdte
rombildet sammenlignes med kilde-RAMs tegn/palett:54280 statiske piksler,
null avvik. Figurflater og utpekte animerte tegn er eksplisitt utelatt.

V3-motoren er kontrollert med76 egne `color-final`-menybilder,34 faktisk endrende skjulte arbeidsbilder, begge startbufferposisjoner og uendret kilde-RAM under menyvalg. Den senere motorendringen tillates kun gjennom den eksakte fargeskriver-/metadatavakt-kontrollen; alle andre motorfiler og spilløkkens tekst kontrolleres fortsatt.
