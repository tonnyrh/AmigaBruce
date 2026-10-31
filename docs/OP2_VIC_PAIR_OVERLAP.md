# OP2. Pikseloverlapp mellom to sprites

Rom 1 er målt med samme Bruce-, Kage- og Yamo-rute før og etter endringen.
Begge par sparte 41 PAL-felt per 240 spillsteg, omtrent 0,82 sekunder ved
50 Hz. Det gjenstår 243 felt til målet på 720. Tidsforskjellen gjelder hele
spillsekvensen med lyd og tegning.

| Rute | PAL-felt før | Etter | Tapte lydtikker før → etter |
| --- | ---: | ---: | ---: |
| Rom 1, begge fiender, første par | 1004 | 963 | 3 → 0 |
| Rom 1, begge fiender, omvendt kjørerekkefølge | 1004 | 963 | 3 → 0 |
| Rom 12, trapp, 240 klatresteg | 816 | 810 | 0 → 0 |
| Rom 13, Yamo | 736 | 724 | 0 → 0 |

Hver kjøring startet et nytt PAL A500-miljø i WinUAE med syklusnøyaktig
68000, OCS, Kickstart 1.3, 512 KiB Chip og 512 KiB slow. OP0-programmet
varmet opp i 240 spillsteg og målte de neste 240. Det brukte vanlig
feltklokke, renderer, lyd og spillmotor, med skriptet inngang og udødelig
Bruce. Begge fiender var aktive i alle målte løkker i rom 1. I rom 12 var
fiender tillatt og ingen ble aktive i måleintervallet. Rom 13 brukte
fiendemaske 1. Telleren for lydtap registrerer forsinket betjening av Paula.
Hørbar lyd og naturlig gjennomspilling må vurderes separat.

## Kilde og implementasjon

Oppstarten ved `$07EA–$07FA` setter vertikal dobling til null og
horisontal dobling til `$FF`. Kampkoden leser `$D01E` ved `$29CE`
og returnerer ved null. Ved `$3D20` leses låsen igjen, og `AND #$03`
tester de to laveste sprite-bitene. Opphavet er den frosne
Remember/T64-binæren med SHA256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Identiteten som urørt 1984-utgave og den nøyaktige VIC-rasterfasen er åpne.

Amigaen sammenligner de dekodede, synlige pikslene som danner disse bitene.
For par uten vertikal dobling velges venstre og høyre figur én gang.
Forskyvningen bestemmer hvilke ord som kan overlappe. Fra 16 pikslers
forskjell er det høyst 32 piksler igjen å sammenligne per rad, og fra 32 er
det høyst 16. Radpekerne går deretter direkte fram til treff eller siste
felles rad. Par med vertikal dobling bruker den eksisterende radberegningen.
Låsen akkumulerer fortsatt treff mellom kildekodens avlesninger.

110 592 enkeltpikselprøver dekker alle 48 horisontale forskyvninger og
alle 48 × 48 par av pikselposisjoner. Ytterligere 8 741 vertskontroller
dekker blant annet doble størrelser, pikselformater, endrede spritedata
og tømming av låsen. De fem integrerte kildeforløpene omfatter 7 055 873
utførte kildeinstruksjoner. Den nye rutinen har 282 byte 68000-kode.
Verifikasjonen kontrollerer både koden og de fire adresseoperandene i
målebygget, det vanlige spillet og det native testbygget.

Normalprogrammet vokste fra 325 640 til 326 156 byte. Rutinen bruker de
eksisterende maskebufferne. I rom 1-målingen var største ledige Chip-blokk
85 440 byte i begge bygg. Største ledige slow-blokk gikk fra 9 728 til
9 272 byte etter lasting.

Det native testbygget bestod 53 kontroller og 1 200 løkker. Største ledige
Chip-blokk var 52 632 byte mot minstekravet på 49 152. Normalbygget viste
komplett meny fra AmigaDOS og fra skrivebeskyttet ADF. På ADF gikk rom 1
fra steg 9 til 47 uten registrert motorfeil. Sanntidskravet for spillet
som helhet står åpent.

[Målinger, rute og byggidentitet](../reference/analysis/op2-vic-pairs-2026-10-31/measurements.json).
