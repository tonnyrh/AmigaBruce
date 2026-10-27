"""Rebuild all20 candidate rooms and compare contacts with original6502 code.

Only audit JSON is public. Original glyph pixels, cell data and derived maps
remain in ignored .reference. Does not change or launch the Amiga game.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw
from c64_room_model import ROOT, decode, validate_loader, pixels, uniform_probes, oracle_contact, model_contact
from build_room_backgrounds import authored_array, render

LOCAL = ROOT / '.reference/c64/room-reconstruction'
REPORT = ROOT / 'reference/validation/c64-room-reconstruction.json'
C64_PALETTE = [0,0,0,255,255,255,136,57,50,103,182,189,139,63,150,85,160,73,
               64,49,141,191,206,114,139,84,41,87,66,0,184,105,98,80,80,80,
               120,120,120,148,224,137,120,105,196,159,159,159]
FLAG_PALETTE = [0] * 768
for i,rgb in {0:(8,16,24),1:(239,121,69),2:(255,232,101),4:(76,202,226),8:(233,96,188)}.items():
    FLAG_PALETTE[i*3:i*3+3] = rgb


def record(path):
    path = Path(path)
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def trigger(tile, room):
    if tile in (2,3,4,5):
        return f'door{tile}: $2E89 dispatch / $30D4 conditions'
    if tile in (0x13,0x14,0x31):
        return 'lantern: pixel contact flag2 required, $2EB1/$2F04'
    if tile in (0x2d,0x2e) and room == 16:
        return 'R17-specific contact: $2EEA/$2FD6'
    if room != 18 and (tile in (0x64,0x0f,0x40,0x54,0x55,0x56,0x58,0x59,0x5a) or 0x71 <= tile < 0x7d or tile == 0x66 and room >= 10):
        return 'hazard dispatch: flag2 required, $2EC1-$2F01/$304B'
    if tile == 0x60:
        return 'stateful contact/color trigger $306B; not a simple platform'
    if tile == 0x62:
        return 'conditional actor state$17 on flag4, $310C; not generic net ID'
    return None


def main():
    LOCAL.mkdir(parents=True, exist_ok=True)
    source = ROOT / '.reference/c64/work/untrained-memory.bin'
    initial = source.read_bytes()
    registered = json.loads((ROOT / 'reference/validation/candidate-rooms.json').read_text())
    assert hashlib.sha256(initial).hexdigest() == registered['source_files'][0]['sha256']
    game = (ROOT / 'core/game.c').read_text()
    current = [dict(room=1,platforms=authored_array(game,'bl_platforms'),nets=authored_array(game,'bl_climbables')),
               dict(room=2,platforms=authored_array(game,'room2_platforms'),nets=authored_array(game,'room2_climbables'))]
    current += json.loads((ROOT / 'reference/validation/room-blockouts.json').read_text())['rooms']
    probes = uniform_probes(initial)
    results, examples, catalog = [], {}, {}
    contact_checks = 0
    for room in range(20):
        model, memory = validate_loader(initial, room)
        glyphs, flags, colors = pixels(memory, model)
        cells = []
        for i,raw in enumerate(model['cells']):
            role = trigger(raw & 127, room)
            cells.append(dict(column=i%40,row=i//40,screen_y=24+(i//40)*16,
                              tile=raw&127,color=8 if raw&128 else model['default_color'],
                              attribute_black=bool(raw&128),trigger=role))
            key=(model['bank'],raw&127)
            item=catalog.setdefault(key,dict(bank=key[0],tile=key[1],rooms=set(),colors=set(),uses=0))
            item['rooms'].add(room+1);item['colors'].add(cells[-1]['color']);item['uses']+=1
        role_counts = Counter(c['trigger'] for c in cells if c['trigger'])
        # Three preserved source contact silhouettes, all four horizontal
        # pixel-pair phases, roof/gap/net/floor positions. These are CPU-only
        # fixtures, not natural play traces or timing measurements.
        checks = 0
        for pose in (0,2,8):
            for x in (20,22,24,26,80,142,144,146,220,290):
                for y in (50,98,102,146,196):
                    actual = oracle_contact(memory,x,y,pose)
                    expected = model_contact(memory,flags,x,y,pose)
                    assert actual == expected, (room+1,pose,x,y,actual,expected)
                    checks += 1
        contact_checks += checks
        layout = current[room]
        claimed = sum(b-a for a,b,y in layout['platforms'])
        unsupported = sum(not any(0<=yy<200 and flags[yy*320+x] & 9
                                 for yy in range(y-2,y+3))
                          for a,b,y in layout['platforms'] for x in range(max(0,a),min(320,b)))
        net_area = sum((b-a)*(d-c) for a,b,c,d,_ in layout['nets'])
        no_net_pixels = sum(not flags[y*320+x]&4 for a,b,c,d,_ in layout['nets']
                            for y in range(max(0,c),min(200,d)) for x in range(max(0,a),min(320,b)))
        entry = dict(room=room+1,charset=hex(model['charset']),default_color=model['default_color'],
                     cells=440,tail_cells=len(model['tail']),loader_instructions=model['loader_instructions'],
                     semantic_pixel_counts={str(k):v for k,v in sorted(Counter(flags).items())},
                     black_attribute_cells=sum(c['attribute_black'] for c in cells),
                     trigger_cell_counts=dict(role_counts),cpu_contact_checks=checks,
                     current_platform_spans=len(layout['platforms']),current_net_rectangles=len(layout['nets']),
                     current_claimed_surface_pixels=claimed,
                     current_surface_pixels_without_class1_or8_within2px=unsupported,
                     current_net_rectangle_area=net_area,current_net_rect_pixels_without_class4=no_net_pixels,
                     init_entry=hex(int(registered['rooms'][room]['init_address'],16)+1),
                     loop_entry=hex(int(registered['rooms'][room]['loop_address'],16)+1),
                     dynamic_state_reconstructed=False)
        # Independent editor map copies must be compared, not trusted by name.
        editor = ROOT / f'.reference/upstream/bruce/map_original/level{room+1}'
        packed = initial[model['start']:model['end']]
        entry['editor_packed_stream_identical'] = editor.read_bytes() == packed
        entry['tile_stream_sha256'] = hashlib.sha256(packed).hexdigest()
        results.append(entry)
        detail=dict(model)
        detail.update(cells=cells,flags_sha256=hashlib.sha256(flags).hexdigest(),cpu_contact_checks=checks)
        local_json = LOCAL / f'room-{room+1:02}.json'
        local_json.write_text(json.dumps(detail,indent=2)+'\n')
        mask = Image.frombytes('P',(320,200),bytes(flags));mask.putpalette(FLAG_PALETTE)
        mask.save(LOCAL/f'room-{room+1:02}-contacts.png')
        visible=bytes((0,2,1,colors[i]&7)[v] for i,v in enumerate(glyphs))
        picture=Image.frombytes('P',(320,200),visible);picture.putpalette(C64_PALETTE+[0]*(768-48))
        picture.save(LOCAL/f'room-{room+1:02}-glyphs.png')
        if room in (0,1,2,5):
            planar=render(layout);raw=bytearray(320*200)
            for y in range(200):
                for x in range(320):
                    raw[y*320+x]=sum(((planar[p*10240+(y+32)*40+x//8]>>(7-(x&7)))&1)<<p for p in range(4))
            own=Image.frombytes('P',(320,200),bytes(raw))
            own.putpalette(Image.open(ROOT/'assets/graphics/v1/mountains-indexed.png').getpalette())
            examples[room]=(picture.convert('RGB'),mask.convert('RGB'),own.convert('RGB'))
        print(f'R{room+1:02}: loader exact; {checks} exact contact checks; bank{model["bank"]}; provisional spans{len(layout["platforms"])}',flush=True)
    # A separate public report contains facts and signatures, no original art.
    sources=['tools/c64_room_model.py','tools/audit_c64_room_model.py',
             '.reference/c64/work/untrained-memory.bin','.reference/upstream/bruce/decompress.go',
             '.reference/upstream/bruce/README.md','.reference/upstream/bruce/brucelee_ida_dis.txt',
             '.reference/upstream/bruce-lee/README.md','.reference/upstream/bruce-lee/src/scenes.ts',
             '.reference/upstream/bruce-lee/src/sprites/Background.ts',
             'tools/build_room_geometry.py','tools/build_room_backgrounds.py','core/game.c',
             'core/room_geometry.h','reference/validation/room-blockouts.json']
    sheet=Image.new('RGB',(3*336,4*235+42),'#081018');draw=ImageDraw.Draw(sheet)
    for col,label in enumerate(['C64 glyph layout / diagnostic colors','C64 pixel contact classes','Current Amiga blockout']):
        draw.text((col*336+8,9),label,fill='#eeeeee')
    for row,(number,images) in enumerate(examples.items()):
        for col,picture in enumerate(images):
            draw.text((col*336+8,row*235+35),f'ROOM {number+1:02}',fill='#eeeeee')
            sheet.paste(picture,(col*336+8,row*235+52))
    draw.text((8,4*235+22),'CONTACTS: orange=1, yellow=2, cyan=4, pink=8. No room init/loops or raster colors.',fill='#eeeeee')
    preview=LOCAL/'comparison.png';sheet.save(preview)
    entries=[]
    for (bank,tile),item in sorted(catalog.items()):
        base=(0xa000,0xa800,0xb000)[bank]
        raw=initial[base+tile*8:base+tile*8+8]+initial[base+(tile|128)*8:base+(tile|128)*8+8]
        entries.append(dict(id=f'tile-b{bank}-{tile:02x}',bank=bank,tile=tile,
                            width=8,height=16,rooms=sorted(item['rooms']),colors=sorted(item['colors']),
                            uses=item['uses'],source_glyph_sha256=hashlib.sha256(raw).hexdigest(),
                            graphics_status='reference_only_replacement_not_created',
                            semantic_variants_must_preserve_color_attribute=True))
    catalog_path=ROOT/'reference/validation/room-tile-catalog.json'
    catalog_path.write_text(json.dumps(dict(status='used_static_candidate_tiles',
        source=record(source),tile_count=len(entries),dynamic_mutations_included=False,
        entries=entries),indent=2)+'\n')
    result=dict(date='2026-10-24',status='passed_static_loader_and_pixel_contact_reconstruction',
                primary_edition_verified=False,native_hardware_emulated=False,amiga_runtime_changed=False,
                full_room_parity=False,room_count=20,loader_comparisons=20,
                uniform_contact_checks=len(probes),pose_contact_checks=contact_checks,
                used_static_tile_count=len(entries),tile_catalog=record(catalog_path),
                uniform_contact_probes=probes,rooms=results,
                coordinate_system='C64 active display320x200; tile field begins y24; x actor left, y actor bottom+1; Amiga adds HUD32',
                limitations=['Static room stream and source collision silhouettes only; room init/loop mutations and IRQ raster palette are not reproduced',
                             'Surface proximity and rectangle occupancy are diagnostics, not pass/fail gameplay parity',
                             'Original glyph images and full cell maps stay in ignored .reference; no new game artwork shipped',
                             'Current Amiga motor still uses authored/tile-top blockouts'],
                source_projects=[dict(path=f'.reference/upstream/{p}',commit=subprocess.check_output(['git','-C',str(ROOT/'.reference/upstream'/p),'rev-parse','HEAD'],text=True).strip()) for p in ('bruce','bruce-lee')],
                source_files=[record(ROOT/p) for p in sources],local_preview=record(preview))
    REPORT.write_text(json.dumps(result,indent=2)+'\n')
    print(f'PASS:20 loader comparisons, {len(probes)} uniform probes, {contact_checks} contact comparisons. Amiga runtime unchanged.')
    print(preview)


if __name__ == '__main__':
    main()
