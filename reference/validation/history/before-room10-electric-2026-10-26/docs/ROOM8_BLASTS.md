# Rom8: eksplosjoner mot skadde fiender

26. oktober2026. Brukeren meldte at fiender overlevde eksplosjoner i rom8.
Den tidligere fulle treffkjeden var bare kontrollert i rom7; rom8 hadde
inngangs-/faregren-kontroller. Denne gjennomgangen dekker alle fem bomber
i rom8, ikke bare det delte dødsrutinekallet.

Kilde: `.reference/c64/work/untrained-memory.bin`, SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Dette er den frosne Remember/T64-kandidaten, ikke en sertifisert urørt1984-utgave.
Originalen er uendret.

## Feilen og regelen i kilden

Fiendene ble tegnet med skade-/nedslåttpositur, men objektpasset brukte
`BlGame`-kroppens stå-/liggemaske. Det er ulike pikselmasker. Ved samme
eksplosjon kunne dette både hindre et riktig treff og gi et feilaktig treff.

| Kode | Betydning |
| --- | --- |
| `$2780–$29C2` | Velger aktuell positur og maskebank `$4F4E`. Tilstand18 gir44/46; tilstand19 gir56/60 ved teller minst10 og58/62 senere, avhengig av retning. Dette er ikke liggestilling26 med64/66. |
| `$5212–$52AC` | Tester den valgte kollisjonsmaskens bitpar mot aktuelle tegn og attributter. `$7C` må være valgt av IRQ/romkonteksten; loaderen alene gjør ikke det. |
| `$2E39–$2F01` | Alle aktive aktører unntatt tilstand25 skannes. `$B6&2` er objektkontaktbetingelsen; det finnes ingen generell eksplosjonsimmunitet i skade-/nedslåttilstand18/19. |
| `$304B–$3068` | Fare i dette rommet ber om lyd`$8C`; NPC-er går til `$3001` for fjerning og returventing. |
| `$3228–$32CB` | Eksplosjonens former/farlige tegn kommer fra de opprinnelige bombefasene. |

NPC-objektpasset bruker nå `bl_combat_object_pose`, som inkluderer de
representerte fighter-reaksjonene. Den samme projeksjonen brukes allerede
for stikkets spritekontakt og beholdes felles. Alle maskebytes og
eksplosjonsfaser er uendret. Ingen større eksplosjonsboks er lagt til.

Dette retter den innkommende objektkontaktmasken. Hele aktørmaskinen,
positurlåser, venting, recoil-fysikk og naturlige spillforløp er fortsatt
delvis rekonstruert. Spillergrafikkens øvrige kontaktadaptere er en egen sak.

## Kildekontroller

`test-room8-blasts.ps1` kjører2160 kontroller over bombecellene `(7,4)`,
`(29,4)`, `(3,7)`, `(17,7)` og `(21,7)`, begge fiender/retninger, tre
eksplosjonsfaser og tolv representerte positur-/tellertilstander.
Originalinstruksjonene velger først positur ved `$2780`, beregner så
kontakt ved `$5212` og behandler objektet ved `$2E39`. Faktisk fjerning
og returventing sammenlignes med den kompilerte Amiga-implementasjonen.

Før rettelsen hadde den første matrisen40 forskjeller, i tilstand18/19.
Etter rettelsen har den utvidede matrisen0 forskjeller. Seksti utvalgte
tilfeller kjører også i session-fixturen på68000: de40 opprinnelige
avvikene og20 kontroller for normal og sen nedslåttpositur.

Den tidligere rom7-kontrollens loader-kontekst er også presisert til
aktivt tegnsett før originalens kontaktkode kjøres. Ingen instruksjoner
eller originaldata er endret av testene.

En synlig flammeoverlapp er ikke alene bevis på C64-treff. Maskens faktiske
bitpar og objektkontaktbiten avgjør. Kontroller med uteblitt treff beholdes
derfor som regresjonskrav sammen med dem der fienden skal fjernes.

Dette er kontrollerte, injiserte tilstander og ny kjøring av maskinkoden,
ikke opptak av naturlig C64-spilling. Brukerens situasjon må prøves på nytt
med det oppdaterte bygget.

[Alle kildekontrollene](../reference/analysis/room8-blasts-2026-10-26/report.json).
Gjeldende bygg og native resultater er bundet i
`reference/validation/room8-blasts-delivery.json`.

## Maskinkontroll og levering

Hele host-regresjonen består. To CLI-oppstarter på PAL A500, 68000, OCS,
Kickstart1.3 og512KiB Chip+512KiB slow gjennomfører hver6000 felt og de
60 nye eksplosjonskontrollene. Alle fixture-, rom-, tegne-, DMA- og
lydfeiltellere er0; AmigaOS gjenopprettes i begge løp. Største ledige
Chip-blokk etter lasting er60832 byte.

Den kontrollerte kampreplayen stemmer med host:62 treff,6 beseirede
fiender,10 fiendeinnganger,2 spillerdødsfall og2 respawns. Den bruker
den eksplisitte, låste lesesiden104 som beskrevet i BOMBS_ENTRY.md;
dette beviser ikke det naturlige spillets tilfeldighetsfordeling.

Jevn50Hz er fortsatt åpent: løpene registrerte1000/1004 tapte felt og
største mellomrom3 perioder uten skjermfangsten. Dette er funksjonelle
kontroller, ikke bestått sanntidskrav eller full spillparitet.

Vanlig spill er bygd som223264-byte EXE og901120-byte ADF. AmigaDOS-
kommandoen `start` er oppdatert med samme EXE. En allerede kjørende
spillinstans må startes på nytt for å bruke rettelsen.
