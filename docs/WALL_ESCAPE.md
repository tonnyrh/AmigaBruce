# Flukt fra venstre hjørne — WALL-0001

2026-10-20. Fire naturlige inputforløp, hvert gjentatt identisk to ganger i
VICE fra samme fryste C64-kandidat. Ingen endring av spillminne eller PC.
320 steg uten input presser Bruce til x=8; deretter prøves 90 steg med flukt.

Originalkandidaten kan komme unna: både gange mot høyre og høyrehopp lykkes.
Det bekrefter ingen generell garanti mot å bli fanget av andre fiendefaser.

| Input etter steg 320 | C64 til x≥64 | Oppdatert Amiga-kjerne til x≥64 |
| --- | --- | --- |
| Ingen input | Ingen flukt | Ingen flukt |
| Hold opp + høyre | 15 steg, ca. 0,90 s | 24 steg, ca. 1,44 s |
| Ned i 16 steg, så opp + høyre | 35 steg, ca. 2,09 s totalt | 34 steg, ca. 2,04 s totalt |
| Hold høyre | 12 steg, ca. 0,72 s | 21 steg, ca. 1,26 s |

Tidene bruker tre PAL-felt per spillsteg og nominelle maskinklokker.
Amiga-tidene er omregning av vertskjernens steg, ikke en ny CIA-måling av
akkurat denne ruten på A500. Samme inputprefiks gir foreløpig forskjellig
helse og fiendeposisjoner: Bruce har 32 helse i C64 og 22 i Amiga ved steg 320.
Denne sammenligningen sertifiserer derfor ikke lik kampoppførsel.

En konkret feil er rettet: `$2A7B–$2A80` tillater sai-treff bare når den
gjenstående angrepstelleren er under åtte. Kandidaten traff tidligere ved
18–12; den bruker nå 7–1. Oppvarmingen 19–8 gir ingen sai-skade. Testene
kontrollerer spesielt grensen 8/7. Ingen ekstra flukt-immunitet er innført.

Resterende for høyt skadepress, treffgeometri, kollisjonsrekkefølge og
restitusjonsforløp står åpne under PAR-014/PAR-016. Andre vegger og faser
må måles separat. Den primære 1984-utgaveidentiteten er fortsatt ubekreftet.

Kjør `capture-c64-wall.ps1`, deretter `test-parity.ps1` for å bygge vertskjernen
og `python tools/compare_wall_escape.py .tmp/core-trace/combat-trace.exe`.
Råopptak: `reference/traces/WALL-0001.json`. Sammenligning med kildehasher:
`reference/validation/candidate-wall-escape.json`.
