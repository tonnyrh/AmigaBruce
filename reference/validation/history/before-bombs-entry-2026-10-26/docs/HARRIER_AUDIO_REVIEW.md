# Lydgjennomgang mot Harrier Attack

25. oktober 2026. Brukeren ba om å sammenligne med
`C:/vscode/_EXT/harrierattackreloaded`. Gjennomgangen gjelder lokal kildekode
ved commit `79989f690d43aa3539a2c5f575517cee1ddbcd5a`, med ren arbeidskopi.
Dette er en kodegjennomgang og beregning fra eksisterende lydparametre.
Den endrer ingen spillkode, lydressurser, emulatorinnstillinger eller bygg.

## Hva Harrier gjør

| Område | Harrier-kode i `amiga/main.c` | Betydning for Bruce |
| --- | --- | --- |
| Effektstart | `stopSfxChannel`, `playSfxAtTuned`, `startPendingSfxChannel`, ca. linje 3503, 3842 og 4084 | Stopp setter volum til null og slår av DMA. Ny sample startes etter en serviceforsinkelse; registrene overskrives ikke straks med stillhet. |
| Engangssample | `sfxChannelSilenceQueueDelay`, ca. linje 4120 og 4152 | Etter innlasting legges en stille løkke inn som neste blokk, slik at starten av effekten ikke gjentas. Bevisste alarm-/drønneløkker unntas. |
| MOD-noter | `modBeginRetrigger`, `modCompletePendingRetriggers`, ca. linje 4441–4492 | DMA av, ny sample ved neste service, deretter repeatområde eller stillhet. Dette er PCM-noter med egen start, ikke en SID-oscillator. |
| Kanalbruk | `playSfxAtTuned`, `startModTrack`, `modStopChannels` | Menymusikk eier alle fire Paula-kanalene. Effekter avvises mens MOD spiller, og overgangene rydder ventende starter. |
| Klokke | `WaitVbl` og `serviceModMusicToCurrentVbl`, ca. linje 3454 og 4608 | Servicen behandler høyst én tick når telleren har endret seg. Den spiller ikke tapte ticks i en tett CPU-burst. |
| Minne | `startModTrack`, ca. linje 4631–4660 | Pakket musikk og mønstre trenger CPU-minne; bare aktive instrumentprøver kopieres til Chip RAM. Bruce bruker allerede samme minneskille for registerdata og bølgeformer. |

Viktig presisering om klokken: I **nåværende** Harrier-kode økes
`frameCounter` i den pollede `WaitVbl`. Kommentarer rundt MOD-servicen nevner
en VBlank-teller, men dette er ikke en uavhengig CPU-avbruddsklokke. Om tegning
overskrider et felt uten et nytt ventekall, teller denne variabelen ikke alle
faktiske hardwarefelt. Harrier er dermed ikke bevis på at vi kan løse Bruces
tempo ved å kopiere denne telleren.

## Den relevante forskjellen i Bruce

`amiga/source_audio.h` starter tre DMA-kanaler én gang og skriver deretter
`AUDxLC/LEN/PER/VOL` for hvert lydfelt. Den ønsker kontinuerlige bølgeformer,
ikke en ny PCM-sample for hvert anslag. Nye LC/LEN-verdier er derfor neste
DMA-blokk, mens den aktive blokken kan fortsette med en ny periode og et nytt
volum. Parameterhashene i autotestene forteller hva CPU skrev; de beviser
ikke når Paula tok i bruk den nye blokken.

[Commodores maskinvaremanual, kapittel 5](https://www.theflatnet.de/pub/cbm/amiga/AmigaDevDocs/hard_5.html)
beskriver egne arbeidskopier av adresse og lengde, naturlig gjenlasting og
lydavbrudd. Den advarer også om at et svært kort DMA-stopp, under to
sampleperioder, kan fortsette i gammel posisjon. Dette støtter Harriers
fasedelte samplehåndtering; det fastsetter ikke at én hel ramme med opphold
er riktig for Bruces kildebaserte oscillatorer.

Bruces forhåndsvisning i `tools/verify_source_audio.py` bruker den samme
parameterberegningen, men bytter bølgeform straks. Den gjengir ikke Paulas
aktive blokk, innlastingsøyeblikk eller korte mellomtilstander ved separate
registerskrivinger. Det finnes derfor en reell forskjell mellom hva testen
beregner og hva den faktiske DMA-kanalen kan spille.

`tools/compare_harrier_audio.py` beregner varigheten av blokker som den
eksisterende parameteravspilleren foreslår, med uendret periode gjennom hele
blokken: `byteantall × periode / 3546895` sekunder. Dette er **ikke målt
bytteforsinkelse**. Den aktive gamle blokken, gjenstående prøver og senere
periodeendringer må også være kjent for å måle forsinkelsen.

| Kildesekvens, kontrollert start | Eksempel på beregnet blokklengde |
| --- | --- |
| Tittel, lengste aktive foreslåtte bølge | 32 byte × periode 934: 8,427 ms |
| Effekt `$80`, første felt | 1024 byte støy × periode 220: 63,515 ms |
| Effekt `$85`, andre felt | 1024 byte støy × periode 524: 151,280 ms |
| Effekt `$8D`, siste aktive felt | 1024 byte støy × periode 2965: 856,005 ms |

Enkelte kildefrekvenser klippes dessuten til Paula-periode 65535 i den
eksisterende oversettelsen. Kombinert med 1024-byte støy gir det 18,92 sekunder
ved konstante parametre. Det betyr **ikke** at en effekt er målt å vente så
lenge; etterfølgende periode-/volumendringer påvirker avspillingen. Det viser
at vi mangler en kort, garantert grense for et naturlig blokkbytte.

Dette er et konkret feilsøkingspunkt for rare eller tapte anslag under
spilling. Det er ikke bekreftet som årsaken til brukerens opplevde manglende
musikkstemme; de tidligere separate native opptakene inneholder alle tre.
Tittellåten bruker korte pulsbølger, og har ikke samme lange støyblokker.

## Hva vi bør bruke videre

1. Skill ønskede registerverdier fra den faktisk innlastede DMA-blokken.
   Kontroller bølgeformbytter med native lydopptak og hardwarestatus, særlig
   overgang fra støy til melodi på samme kanal. Et parameterhash er ikke nok.
2. Bruk eksplisitt eierskap og en dokumentert start-/stoppsekvens for Paula.
   Bruces oppstartsskrik har allerede latch-kontroll før stille reload;
   kontinuerlige spillstemmer trenger en løsning tilpasset deres bølgeformer.
3. Mål lydfelt mot den faktiske PAL-klokken under tung tegning. En ordnet
   service mellom tegnebolker kan være nyttig, men løser ikke i seg selv
   manglende tid. Behold kildens feltsekvens og mål både lyden og spilltakten.
4. Behold C64-kandidatens tre køer, prioritet, noter og gate-/ADSR-data.
   Harriers retriggervern, tilfeldige effektvarianter, firekanals MOD og
   tempojustering er andre spillregler og skal ikke erstatte disse.

Den frosne C64-kandidatens SHA256 er fortsatt
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Utgaven er ikke sertifisert som valgt, urørt 1984-utgave. Denne gjennomgangen
gir ingen ny godkjenning av lyd, full SID-klang eller C64-spillparitet.

Maskinlesbare funn, kildehasher og alle 16 sekvenser:
`reference/analysis/harrier-audio-2026-10-25/report.json`.
Gjenskap beregningen med `python tools/compare_harrier_audio.py`.
