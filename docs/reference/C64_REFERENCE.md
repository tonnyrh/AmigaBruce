# C64-referanse og opptaksprosedyre

Primær-ID: `c64-1984-pal-rakki-s0`. Se `reference/manifest.json` for identitet
og aktuell status. Valget er katalogbasert frem til originalen er hentet og kjørt.
Binærhenting ga HTTP 401; ingen tilgangsbegrensninger er forsøkt omgått.

## Lokal struktur

```text
.reference/
  c64/original/    urørt referansedisk, skrivebeskyttet
  c64/work/        kopier som emulatoren kan åpne
  c64/captures/    opptak, skjermbilder, input og målte spor
  c64/profiles/    emulatorinnstillinger og lokale ROM-identiteter
  upstream/bruce/ sekundært analyse-repo, låst commit
```

`tools/c64_reference.py register` godtar bare G64-signaturen for den valgte
filtypen, kopierer til original- og arbeidsbane, beregner SHA-256 og beskytter
originalkopien mot skriving. Registrering er **ikke** bekreftelse av PAL,
utgivelsesår eller uendret program; det krever egen kontroll og evidens.
Verktøyet erstatter ikke en eksisterende original eller arbeidskopi.

## Emulatorprofil før første måling

Bruk VICE x64sc. Registrer faktisk versjon og executable-hash, PAL-maskinmodell,
VIC-II og SID-modell, ROM-hasher, drive type/ROM, true-drive-innstillinger,
joystickporter og inputmetode. Lagre eksportert config lokalt og hash den.
Start fra hard reset med arbeidsdisken. Dokumenter autostart/lastesekvens,
eventuelle tastetrykk, menyvalg og spillermodus. Ingen trainer, patch eller
snapshot fra sekundærrepoet i baselinen. Dokumenter warp under lasting, og
slå det av før kontroll av lyd, timing og opptak. Ingen ROM-filer i Git.

## Første evidenspakke

1. Boot til tittel/meny, kontroller disk og utgave. Registrer faktisk skjermtekst.
2. Start valgt enspillermodus fra reset. Identifiser hvilket rom som er R01;
   koblingen til sekundærrepoets rom 1 må verifiseres eksplisitt.
3. Ta skjermbilde og et VICE-snapshot før input. Hash begge, dokumenter
   frame/cycle og aktive fiender/feller. Et snapshot er emulatorversjonsspesifikt.
4. Gjør separate opptak fra samme snapshot: ro 120 PAL-felt, venstre/høyre
   holdt 60 felt, kort retningspuls, hopp, fall fra kant og klatrestart/-stopp.
   Bekreft hopp-/kampkombinasjoner før de brukes som testinput.
5. Logg begge joystickporter og tastatur per felt, med definert samplingsfase.
   PAL-felt er en inputtidsakse, ikke en antakelse om spillets oppdateringsfrekvens.
6. Mål posisjon, fotpunkt, animasjon, tilstand og hendelser. Merk koordinatrom
   (VIC-register, logisk spillkoordinat eller skjermpiksel) og måleusikkerhet.
   Ved videomåling: ingen oppdiktet subpikselpresisjon.
7. Gjenta hver sekvens minst to ganger fra samme baseline. Hvis utfallet
   varierer, undersøk fase/RNG/input før determinisme eller toleranse fastsettes.
8. Registrer evidens og oppdater tilhørende PAR-ID. Et tomt spor er ingen test.

Mål hoppkurve, avsatspassering og stiger i tillegg til sluttposisjon.
Ved grensetilfeller gjentas input ett felt tidligere og senere. Fiender og
romhendelser må sammenlignes ved likt tids-/tilstandsutgangspunkt.

## Evidensformat

Opprett `docs/parity/evidence/<capture-id>.json` med denne formen når et
faktisk opptak foreligger. Originalfiler blir liggende lokalt; indeksen kan
versjoneres med hash og relative stier:

```json
{
  "capture_id": "CAP-0001",
  "reference_id": "c64-1984-pal-rakki-s0",
  "disk_sha256": "<actual sha256>",
  "emulator_version": "<actual version>",
  "profile_sha256": "<actual sha256>",
  "baseline_sha256": "<actual sha256>",
  "room_id": "R01",
  "mode": "<observed selection>",
  "parity_ids": ["PAR-003"],
  "input_sampling_phase": "<documented phase>",
  "measurement_method": "<memory trace or video; coordinate definition>",
  "measurement_uncertainty": "<measured resolution>",
  "artifacts": [{"path": ".reference/c64/captures/CAP-0001/input.csv", "sha256": "<actual sha256>"}],
  "result": "<actual observations and repeatability>"
}
```

Input-CSV: `pal_field,joy1_up,joy1_down,joy1_left,joy1_right,joy1_fire,joy2_up,joy2_down,joy2_left,joy2_right,joy2_fire,keyboard_event`.
Tilstandsspor: `pal_field,cycle,room,actor,x,y,state,animation,score,lives,event`.
Tomme/manglende mål holdes åpne; de fylles ikke med nullverdier som ser målte ut.

## Kandidatens validerte opptaksgrense

`capture-c64.ps1` starter en egen skjult VICE-prosess og avslutter bare den.
Porten må være ledig. Verktøyet kontrollerer PRG-, snapshot- og emulatorhash,
restorer snapshotet og setter IO Simulation på joystickport 1. Ingen spill-RAM,
spillkode eller CPU-register endres under opptaket. Den eldre debuggerbaserte
oppstarten av dette snapshotet er fortsatt en eksplisitt begrensning.

Hver observasjon skjer ved PC `$1BCE`; siste instruksjon i CPU-historikken skal
være `$1BCC`. En breakpoint på gjeldende PC deaktiveres mens én instruksjon
utføres, slik at samme stopp ikke telles to ganger. En ny RESUMED → STOPPED
kreves. CPU-historie før og etter minneavlesningen skal være identisk.

Etter åtte tomme spillsteg måles hver sekvens to ganger fra samme snapshot.
Alle rader, inklusive relativ CPU-klokke og rasterfase, skal samsvare.
Klokkeintervallene korrigeres for forskjellen i målt rasterlinje og syklus
ved de to stoppene. Resultatet skal være nøyaktig `3 * 312 * 63 = 58968`
CPU-sykluser. Ingen toleranse brukes for feltantall eller posisjon.
Opptakene dekker spillsteggrenser, ikke vilkårlige ettfelts inputpulser.

Se `reference/traces/MACHINE-0001/`, `MACHINE-0002/`, `MACHINE-0003/` og
[arbeidsleveransen](../NIGHT_HANDOFF.md). Gamle forkastede spor blir ikke
rehabilitert; de nye opptakene har egne identiteter og metoder.
