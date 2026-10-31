# Tittelbilde, pause og nytt liv

**P** holder det gjeldende spillbildet og viser «PAUSED» i fotlinjen.
Samme tast fortsetter spillet. F10 åpner menyen og Esc går til AmigaDOS,
også fra pause. Spillet demper Paula og stanser oppdateringene av kamp,
rom og lyd. Ved fortsettelse forankres feltklokkene på nytt. En tast som
holdes inne teller som ett trykk.

Fjellscenen på lasteskjermen og i menyen er tegnet for Bruces 16-fargers
OCS-palett. Figuren er den rippede C64-posituren `$0C`, vendt mot høyre.
Landskapet og det latinske penselalfabetet er tegnet i
`tools/build_title_art.py`. Den samme 4 484 byte store illustrasjonen
pakkes ut i en eksisterende skjermbuffer på begge skjermene. Menyen
publiseres etter at bildet er ferdig, og rommet får tilbake spillpaletten.

## Skjermskift ved død

Kildegrunnlaget er den frosne Remember/T64-kandidaten med SHA-256
`092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8`.

* Når Bruce mister et liv, går `$184B` til `$0EA7`. Lagringen ved
  `$0EAD` slår av VIC-bildet. Fra `$0EC1` fyller rutinen skjermminnet
  med `$DC` før den skriver spillermeldingen. Ved `$0F21` velger den
  et annet tegnsett. Amiga-tegneren brukte fortsatt rommets tegnsett
  under meldingsventingen ved `$0F47`.
* Ved siste liv slår `$189A` av VIC-bildet før Game Over-meldingen.
  Venting og eventuell turveksling går fortsatt gjennom `$1968/$197D`.
* Amiga slukker begge Copper-listene og bitplanene ved disse to
  lagringene. Så viser den et ferdig meldingsbilde med spillernummer eller
  «GAME OVER». Den ordinære romlasteren ved `$09BC` slukker igjen før nytt
  rombilde publiseres. Kildens feltklokke går under meldingsventingen.
  Dødsskriket og den siste posituren kommer før denne overgangen.

Den interaktive kontrollen i `tools/check_pause_respawn.py` bruker
WinUAE-tastaturhendelser og leser de viste bitplanene. Den framprovoserer
dødsfall ved å sette offerets dødstilstand og teller i testinstansen.
I det ordinære bygget stemte hele skjermbildet for «PLAYER 1», «PLAYER 2»
og «GAME OVER» med forventet bilde. Lasteskjermen og menyen ble også
sammenlignet piksel for piksel i WinUAE. [Kontrollresultat](../reference/analysis/title-pause-respawn-2026-10-31/result.json)
