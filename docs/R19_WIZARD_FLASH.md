# Monsteret i rom 19

Lagringsfilen `31.10.2026.uss` har SHA-256
`56e12d941ff94ad461cd533925bf4bd180f9937d3b0c4fdf4a5825c14da26d9f`.
Kilde-RAM ligger i BRAM ved offset `$60C94`. Romindeksen `$29` er 18,
monsterflagget `$4E97` og telleren `$4E98` er null, og tegnsettet
`$F2` er `$3E`. Sekvensen var ferdig da bildet ble lagret. Uttrekket
ble gjort uten å endre USS-filen.

## Forløp i den frosne C64-kandidaten

Kilden er Remember/T64 med SHA-256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.
Utgaven er ikke sertifisert som urørt 1984-original.

* `$3CDC–$3D1A` tester `$4E97` og `$4E86`. Når det siste flagget blir
  null mens monsteret fortsatt er aktivt, deaktiveres monsteret og
  prosjektilene. Koden setter telleren til `$50`.
* `$3DAF–$3DF5` velger fargen gjennom `$1159`, skriver den til fire
  rader à 18 tegn og seks rader à 12 tegn, og trekker fra ett spillsteg.
  Siste steg bruker farge null. Påfølgende romoppdatering går til
  `$3D9B`, som tegner åpningen.
* `$3DF8–$3E09` velger normalt tegnsett `$3E`. Når den gamle telleren
  er minst 17, kan et minneoppslag under `$10` velge `$3C` i stedet.
  `$3E0B–$3E49` ber om lyd `$8B`, veksler positurbiten og skriver fire
  tegnstrenger. Fargen kan gjentas på påfølgende steg.

## Synlig tid på PAL

| Måling fra teller 80 til 0 | PAL-felt | Tid |
| --- | ---: | ---: |
| C64-kandidat i VICE, 4 717 784 CPU-sykluser | 240,02 | ca. 4,8 s |
| Tidligere A500-bygg, kontrollert reprise | 1 371 | ca. 27,4 s |
| Rettet A500-bygg, samme rute | 537 | ca. 10,7 s |

VICE kjørte den opprinnelige hovedløkken og rasteravbruddene. Testen
startet fra prosjektets C64-snapshot, valgte rommet gjennom `$2F9A`
og satte `$4E86` til null. VICEs syklusteller ble lest ved `$3DAF`.
Amiga-prøvene kjørte vanlig spill-, lyd- og tegnekode i sykluseksakt
WinUAE med 68000, OCS og 512 + 512 KiB. En diagnoseinngang startet
rommet, lot Bruce stå stille og satte det samme flagget etter 24 steg.
Felttid og fargen på et punkt på monsteret ble registrert ved publisering
av skjermbildet. Ingen av tidene er en avspilling av brukerens USS.

Det gamle bygget lastet hele bakgrunnen på nytt 15 ganger under
blinkingen. Det nye håndterte 19 tegnsettbytter med null fulltegninger.
De to kjøringene fikk litt ulike farge- og bankvalg fra kildens
minneleser. Det lengste observerte spillsteget falt fra 54 til 14 felt.
Tidsparitet med C64 står fortsatt åpen.

## Endring og kontroll

Ved første samlede fargeskriving bindes de 144 tegnenes individuelle
forgrunnsfarge til Amiga-palettregister 15. Før nederlaget er dette
registeret tilgjengelig for de levende prosjektilene. Kildens farge-RAM,
kontaktklasser, teller, tegnstrenger og lydrekkefølge følger fortsatt
originalrutinen. Ved et tegnsettbytte sammenligner tegneren glyfbytene
og køer cellene som får nytt innhold. HUD og de øvrige cellene beholder
bildet sitt.

Kjør `./test-c64-rooms.ps1 -WizardOnly` for den målrettede kontrollen.
Den sammenligner 82 romtilstander og hele den synlige spilleflaten mot
kjøring av de frosne 6502-bytene. Begge tegnsett inngår. Det ferdige
diskbildet ble også startet i WinUAE og kjørt fra testmenyen gjennom
blinkingen til teller null. Tre individuelle farger ble bekreftet på
monsteret i den viste skjermbufferen, ved spillefeltposisjon (134, 46).
[Måledata](../reference/analysis/r19-flash-2026-10-31/)
