# Grafikkflyt for tiles og figurer

**1. november 2026.** Classic bruker [rippede C64-sprites](C64_SPRITES.md)
og C64-romtegn. Nye grafikkforsøk for Enhanced lagres separat med prompt og
opprinnelse. [Prosjektplanen](PROJECT_PLAN.md) beskriver figurprøven, det
foreslåtte menyvalget og kontrollene mot Classic.

Brukerens beslutning 24. oktober: hver grafikkdel skal kunne spores fra
C64-referansen gjennom en lagret AI-prompt til validert Amiga-grafikk.
Kollisjon, fotpunkt, romgeometri og tidsforløp endres ikke av ny kunst.

## Lokal uttrekking

Kjør `python tools/extract_c64_art.py`. Originalpiksler, kontaktark og
manifest blir liggende i Git-ignorert `.reference/c64/art-extracted/`.
Det trekkes ut tre tegnsett med 128 sammensatte 8 × 16-tiles og 210
spritekomponenter fra kandidatens tabeller. Spritekomponenter må settes
sammen og merkes per figur, tilstand, retning og animasjonsfase før de kan
behandles som komplette Bruce-/Ninja-/Yamo-bilder. Ikke gjett anker fra
bounding box eller bruk et ufullstendig komponentbilde som ferdig figur.

## Gjenbrukbar prompt

Lagre en ferdig utfylt kopi per ressurs og behold referansehash, modell,
parametre, dato og versjon sammen med resultatet:

```text
Asset ID: {asset_id}
Role: {tile_or_actor_state_and_frame}
Reference: {local_reference_id_and_hash}
Target: Amiga 500 OCS, 320x256 scene, shared 16-colour palette.
Canvas: {width} x {height} pixels. Anchor: {anchor_x},{anchor_y}.
Create a refined side-view pixel-art replacement for this exact component.
Preserve its identity, facing, readable silhouette and animation phase.
For tiles preserve matching edges, surface placement and room readability.
For actors preserve the supplied foot/hand anchors and weapon direction.
Use consistent lighting and a coherent martial-arts adventure style.
No text, framing, extra limbs, camera rotation, blur or antialiasing.
Do not infer collision from the artwork or move the gameplay anchor.
Palette: {shared_ocs_palette}. Transparency index: 0 where applicable.
```

## Produksjon og integrasjon

1. Lag inventar over hver unik tile og hver sammensatt figur/animasjonsfase.
2. Velg én felles stil og palett på representative tiles og alle tre figurer.
3. Generer varianter med lagret prompt og seed der leverandøren støtter det.
4. Konverter deterministisk til indeksert PNG, 12-bit OCS-palett, riktige
   dimensjoner og masker. BOB-er trenger ikke være hardware-sprites på 16 piksler.
5. Krev valideringsrapport med hash og godkjent format. Inspiser hele
   animasjonssekvensen og tilstøtende tiles; filformat alene godkjenner ikke kunst.
6. Pakk bitplan/masker i byggverktøyet. Originale referansebilder skal ikke
   automatisk kopieres til spillbygget. Hold minneforbruk og DMA-data målbare.
7. Test figuranker, fotkontakt, grep, slag/spark og romlesbarhet på A500-profilen.

AI-produksjon av hele biblioteket er et eget arbeidstrinn. At uttrekking og
prompt finnes, betyr ikke at alle bildene er forbedret eller implementert.

## Første implementerte stilkandidat, 24. oktober

`assets/graphics/v1/` inneholder nå innebygd image_gen-kildekunst, lagret
prompt, 21 OCS-validerte figurpositurer med faste ankre og en fjellbakgrunn.
Dette er identitets-/stilarbeid basert på referanseskjermbildet, ikke en
ferdig oversettelse av alle ekstraherte C64-komponenter. Originalens
komposisjonstabeller og komplette tile-inventar må fortsatt knyttes til
hver endelig erstatning. Se `docs/NEXT_CANDIDATE_2026-10-24.md`.

## Utvidet Amiga-animasjon

Brukeren tillater friere bevegelsesmønstre i Amiga-grafikken. Den aktive
v2-kunsten har 16 bildeplasser per figur, fire klatrefaser og en bambusstav
til Ninja. Kildene og alle prompter er lagret i `assets/graphics/v2/`.
Se [animasjon og åpninger](ANIMATION_AND_OPENINGS_2026-10-24.md) for
ankre, visningstransformasjoner, minne og uendrede spillregler.

Yamo har en egen korrigert kildevariant, `yamo-green-source-v3.png`, med
grønn hud og kraftigere kropp. Prompt og visuell referanserolle er lagret
separat, og den eldre brune huden/grønne drakten beholdes som tidligere
kildekunst. Fargereduksjonen prioriterer grønntoner for huden og bruker
spredte høylys innenfor den samme OCS-paletten. Se [Yamo og HUD](YAMO_AND_HEALTH_HUD.md).
