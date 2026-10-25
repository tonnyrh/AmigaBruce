"""Extract local analysis artwork; never put original pixels in shipped assets.

Room charset selection: candidate $0A9B-$0AAD/$15D0-$15EC.
Sprite component templates: $2719, tables $59BD/$5A8F/$5B61/$5CBF.
Components are not automatically final composite actor frames.
"""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def room_cells(memory, room):
    pointer = memory[0x4b34+room] + 256*memory[0x4b49+room]
    cells = []
    while memory[pointer] != 128:
        count = memory[pointer]
        pointer += 1
        if count & 128:
            count &= 127
            cells.extend(memory[pointer:pointer+count])
            pointer += count
        else:
            assert count
            cells.extend([memory[pointer]]*count)
            pointer += 1
        assert len(cells) <= 442
    assert 440 <= len(cells) <= 442
    return cells[:440]


def tile_rows(memory, bank, tile):
    base = (0xa000, 0xa800, 0xb000)[bank]
    return memory[base+tile*8:base+tile*8+8] + memory[base+(tile+128)*8:base+(tile+128)*8+8]


def main():
    source = ROOT/'.reference/c64/work/untrained-memory.bin'
    memory = source.read_bytes()
    assert len(memory) == 65536
    output = ROOT/'.reference/c64/art-extracted'
    output.mkdir(parents=True, exist_ok=True)
    records = []
    palette = [0,0,0, 221,85,51, 238,238,221, 68,102,170] + [0]*756
    for bank in range(3):
        atlas = Image.new('RGB', (16*40, 8*48), '#333333')
        draw = ImageDraw.Draw(atlas)
        for tile in range(128):
            raw = tile_rows(memory, bank, tile)
            pixels = bytearray()
            for value in raw:
                for shift in (6,4,2,0):
                    pixels.extend([(value >> shift)&3]*2)
            picture = Image.frombytes('P', (8,16), bytes(pixels))
            picture.putpalette(palette)
            name = f'tile-b{bank}-{tile:02x}'
            picture.save(output/(name+'.png'))
            left, top = tile%16*40, tile//16*48
            atlas.paste(picture.resize((24,32), Image.Resampling.NEAREST).convert('RGB'), (left,top))
            draw.text((left,top+33), f'{tile:02x}', fill='white')
            records.append(dict(id=name, kind='tile', width=8, height=16,
                                source_sha256=digest(raw), reference=name+'.png',
                                status='reference_only_not_amiga_art'))
        atlas.save(output/f'tiles-bank{bank}.png')
    for index in range(210):
        pointer = memory[0x59bd+index]+256*memory[0x5a8f+index]
        rows = memory[0x5b61+index]+1
        columns = 2 if memory[0x5cbf+index] else 1
        assert 1 <= rows <= 22, (index, rows)
        raw = memory[pointer:pointer+rows*columns]
        # Retain the complete template, including six 22-row source entries;
        # the C64's 21-row destination clipping is a separate composition step.
        height = max(21, rows)
        picture = Image.new('P', (24,height), 0)
        picture.putpalette(palette)
        for y in range(rows):
            for column in range(columns):
                value = raw[y*columns+column]
                for bit in range(8):
                    if value & (128 >> bit):
                        picture.putpixel((column*8+bit,y), 2)
        name = f'component-{index:03}'
        picture.save(output/(name+'.png'))
        records.append(dict(id=name, kind='sprite_component', width=24, height=height,
                            source_address=hex(pointer), row_count=rows,
                            byte_columns=columns, source_sha256=digest(raw),
                            reference=name+'.png',
                            status='component_requires_actor_composition_and_anchor_review'))
    report = dict(source=str(source.relative_to(ROOT)), source_sha256=digest(memory),
                  extraction_script_sha256=digest(Path(__file__).read_bytes()),
                  original_assets_are_local_only=True,
                  production_art_generated=False, records=records)
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'Extracted {len(records)} local reference components; production art not generated')


if __name__ == '__main__':
    main()
