# Lydavspilling 25. oktober 2026

Denne siden beskriver opptakene før den senere DMA-/PAL-service-rettelsen.
Se [den nye avspillingsbanen](PAULA_STREAM.md). Opptak og kildeidentiteter
under er historiske og beholdes som grunnlag for stereofeilsøkingen.

Brukerfunn: WAV-forhåndsvisninger hørtes riktige ut, mens spilling manglet
toner/effekter og muligens hadde feil tempo. Etter et første forsøk med mono
meldte brukeren at effektene var til stede, men at enkelte klanger var rare
og en musikkstemme fortsatt kunne mangle. Endelig lyttegodkjenning av den
korrigerte tokanalsprofilen er fortsatt åpen.

## Rettelse i startoppsettet

Forhåndsvisningene summerer de tre stemmene til mono. WinUAEs arvede
standardinnstillinger hadde full stereoseparasjon: Paula0 til høyre og
Paula1/2 til venstre. Den aktive brukerinstansen hadde dette oppsettet.
I en isolert test på samme maskin avviste WASAPI-driveren en mono-enhet og
WinUAE valgte deretter åtte kanaler. Dette er dokumentert i testloggen;
den samme fallbacken ble ikke målt i brukerinstansen.

Prosjektets startskript angir derfor nå uttrykkelig:

```ini
sound_output=exact
sound_channels=stereo
sound_stereo_separation=0
sound_stereo_mixing_delay=0
sound_frequency=48000
```

Dette samler de tre stemmene på begge utganger med en vanlig tokanals
lydenhet. Ingen instrumenter, melodidata, tempo eller spillregler er endret.
Et nytt `-ConfigOnly`-valg lager oppsett uten å starte en emulator eller
slette eksisterende autotestresultater.

Kjør `./amiga-run.ps1` for vanlig spilling, eller lag en ADF-profil med
`./amiga-run.ps1 -Disk -ConfigOnly`. Den leverte kopien
`amiga/out/bruce-a500.uae` kan lastes i brukerens vanlige WinUAE. Den peker
på prosjektets gjeldende ADF og lokale Kickstart1.3. Ingen globale WinUAE-
innstillinger er lagret. En allerede kjørende instans får ikke innstillingene
fra en ny fil før profilen lastes.

## Musikkstemmene

Kilden er fortsatt kandidaten med SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Musikken er hentet fra de faktiske rutinene `$E000/$E003/$E006`, kalt av
`$06DA/$154C`. Kandidatens utgaveidentitet er ikke sertifisert.

Alle stemmene spiller ikke fra begynnelsen. Den eksisterende avspilleren
og de kildeuttrukne registrene gir følgende over1155 felt, inkludert
innledningsfeltet før1154-feltsløkken:

| SID-stemme / Paula | Første aktive felt | Tid ved50Hz | Felt med volum og ikke-null PCM |
| --- | --- | --- | --- |
| 1 / 0 | 1 | 0,02s | 970 |
| 2 / 1 | 385 | 7,70s | 338 |
| 3 / 2 | 129 | 2,58s | 610 |

Den gamle native parameterprøven av temaet dekker bare120 felt, altså
2,4 sekunder, og beviser derfor ikke at de to senere stemmene høres.
Den testen beholdes som en avgrenset regresjon, ikke en full musikktest.

Nye opptak kjører det vanlige, uendrede spillprogrammet i WinUAE6.0.3 med
PAL OCS/68000/Kickstart1.3/512KiB Chip+512KiB slow. Debuggerens lydmaske
isolerer hver Paula-stemme i den eide testinstansen; en fjerde kjøring
tar opp hele miksen. Hvert opptak dekker mer enn1154 PAL-felt.
Alle tre har ikke-null lyd, og venstre/høyre utgang er identiske.
Dette er faktisk native PCM, men med diagnostisk demping av øvrige stemmer,
ikke en naturlig gjennomspilling eller en SID-innspilling.

Disse opptakene ble gjort før den senere NPC-rekylrettelsen. Programmet og
tilhørende hovedkilde er bevart under
`reference/validation/history/before-npc-recoil-2026-10-25/`, og opptaksrapporten
peker nå på dette arkiverte bygget. Opptakene relabeles ikke som en ny
lydkjøring av det senere spillbygget. Selve mikseroppsettet og lydressursene
er uendret; nye parameterregresjoner følger den aktuelle spillleveransen.

Musikktelleren i normalprogrammet økte1444 felt over28,9705 sekunder målt
med Windows' monotone klokke, omtrent49,84 oppdateringer/sekund. Det gir
ikke grunnlag for en generell endring av musikktempo. Korte opphold ved
tung tegning/romlasting og langtidsforskjellen mellom PAL-klokkene gjenstår.

## Opptaks- og testavgrensninger

WinUAEs IPC-opptak bruker GUI-ens `workprefs` som formatbeskrivelse. Uten
å åpne GUI var den mono44100, selv om den aktive lydenheten var stereo48000.
De første konverterte AVI-opptakene fikk derfor feil tids-/formatgrunnlag
og er forkastet som lytte- og tempobevis.

De endelige opptakene bruker ukonvertert PCM-passthrough. Byteinnholdet
blir pakket om til WAV med den aktive lydenhetens stereo48000-format.
Kontrollen krever både tokanals48000 i driverloggen og3844/3848 PCM-byte
per PAL-pakke; den avviser surround-fallback og feil format. Ingen
tonehøydejustering eller strekk av lyden brukes. Kode, konfigurasjon,
emulator, originalopptak og WAV-filer bindes med hash i rapporten.

`tools/audit_audio_playback.py` kontrollerer stemmene mot kildeuttrekket,
ikke-null bølgeformer og faktisk avspilt PCM. De vanlige to6000-felts
A500-regresjonene kontrollerer fortsatt parameterhash, gjenoppretting,
minne og tidsavvik hver for seg.

SID-klang er fortsatt en tilnærming med8/16/32-prøvers bølgeformer,
1024-byte støy og50Hz ADSR. Paula laster dessuten LC/LEN ved slutten av
en pågående DMA-blokk; parameterhash alene beviser ikke presist tidspunkt
for alle bølgeformbytter. Disse grensene er ikke skjult av mikserettelsen,
og rare enkelteffekter er ikke erklært løst.

[Maskinvaremanualen, kapittel5](https://www.theflatnet.de/pub/cbm/amiga/AmigaDevDocs/hard_5.html)
dokumenterer kanaltilkobling og DMA-gjenlasting.
[WinUAEs lydopptakskode](https://github.com/tonioni/WinUAE/blob/master/od-win32/avioutput.cpp)
viser formatvalget fra `workprefs`.

[Maskinlesbar rapport](../reference/analysis/audio-playback-2026-10-25/report.json)
og [hele native miksen](../reference/analysis/audio-playback-2026-10-25/title-native-mixed.wav).
