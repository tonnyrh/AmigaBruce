# Øvre sprang og liggende stilling

## Spranget til høyre

MACHINE-0004 bekrefter at spranget er mulig i C64-kandidaten: ved sats fra
`x198,y101` ender forløpet på høyre avsats ved `x250,y98`. Vår høyre avsats
hadde ståhøyde y96 og var dermed to piksler for høy. Ståhøyden og den tilhørende
dekorveggen er korrigert til y98; hoppets fart og kurve er beholdt.

Host-testen starter på den målte satsposisjonen og krever landing ved x250,y98.
De komplette native-input-forløpene rapporteres også. De viser fortsatt det
kjente inputfaseavviket rundt oppstart av gange/sats; disse delene erklæres ikke
som full paritet. Den senere satsprøven i C64 viser dessuten at kanttimingen
har betydning. Eksakte fotmasker langs plattformkanten er fortsatt åpne.

I spilleren: slipp opp og land først hvis Bruce allerede hopper rett opp.
Trykk så opp+høyre samtidig nær kanten. Retningen velges ved sats; høyre
underveis i et allerede startet stående hopp gjør det ikke til et løpshopp.

## Ligge ned

Ned på fast underlag velger liggende stilling. Figuren beholder fotpunktet,
blir liggende i ro også med en horisontal retning holdt inne, og vises med en
egen lav, vannrett skissefigur. Slipp ned for å reise deg, eller velg opp for å
hoppe. Kandidatens ett ventesteg i den liggende tilstanden er bevart.

Ned mens Bruce allerede henger på nettet er fortsatt klatring ned. Ned på
plattformen over nettet gir liggende stilling, som observert i kandidaten.
Ned i luften gjør ikke figuren liggende. Kamp-/prosjektilmasker er ikke ferdige;
den nye skissefigurens grafiske høyde er ikke sertifisert som original treffmaske.

Tre målte forløp dekker hold/slipp, ned+høyre og liggende → hopp. Alle posisjoner
og den logiske målstillingen samsvarer. Målstilling sammenlignes med C64s
`next_state == 26`; dette er ikke en sertifisering av spriteanimasjonens fase.
Amiga-testene krever nå at liggende stilling faktisk har vært aktiv.

Nye referanseopptak kan kjøres med:

```powershell
.\capture-c64.ps1 -CaptureId MACHINE-0004 -ScenarioFile reference/scenarios/MACHINE-0004.json
```
