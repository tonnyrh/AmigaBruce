"""Rip all candidate room glyphs with source init, attributes and raster colors.

These images are an inspectable extraction. Runtime draws the same glyph bytes
directly, including later modifications by the statically translated programs.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image,ImageDraw
from c64_room_model import room_memory, word
from verify_c64_room_runtime import invoke

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/c64/rooms-v1'
COLORS=[0x000,0xfff,0x833,0x7cc,0x84a,0x6a4,0x338,0xcc7,
        0x852,0x541,0xb77,0x444,0x777,0xaf9,0x78c,0xbbb]
RGB=[tuple(((value>>shift)&15)*17 for shift in (8,4,0)) for value in COLORS]


def indexed(width,height):
    image=Image.new('P',(width,height))
    image.putpalette([v for rgb in RGB for v in rgb]+[0]*720)
    return image


def source_room(source,room):
    initial=list(source);initial[2]=50;initial[3]=0;initial[0x100]=0
    initial[0x104]=1;initial[0x105]=0;initial[0x16]=initial[0x17]=0
    invoke(initial,0x10c5);invoke(initial,0x33ca)
    initial[0x9e]=initial[0x4bae+room];initial[0xa1]=initial[0x4bc2+room];initial[0xb6]=1;initial[0xce]=4
    m,_=room_memory(initial,room)
    for i in range(5):m[0x4e97+i]=0
    invoke(m,0x336e);invoke(m,word(m,0x4ec4+room*2)+1)
    return m


def render(m,room):
    image=indexed(320,200);pixels=image.load()
    bank={0x38:0xa000,0x3a:0xa800,0x3c:0xb000}.get(m[0xf2],0xb800)
    palette=word(m,0x480b+room*2);raster=word(m,0x4833+room*2)
    for y in range(24,200):
        band=0
        for j in range(3):
            if m[raster+j]==253:break
            if y+51>=m[raster+j]+3:band+=1
            else:break
        colors=[v&15 for v in m[palette+band*3:palette+band*3+3]]
        for column in range(40):
            cell=(y//8)*40+column;code=m[0x8c00+cell]
            values=colors+[m[0xd800+cell]&7];bits=m[bank+code*8+y%8]
            for pair in range(4):
                color=values[(bits>>(6-pair*2))&3]
                pixels[column*8+pair*2,y]=pixels[column*8+pair*2+1,y]=color
    return image


def main():
    source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
    OUT.mkdir(parents=True,exist_ok=True)
    contact=Image.new('RGB',(5*320,4*216),(0,0,0));labels=ImageDraw.Draw(contact)
    files=[]
    for room in range(20):
        image=render(source_room(source,room),room)
        path=OUT/f'room-{room+1:02}.png';image.save(path)
        assert image.mode=='P' and image.size==(320,200)
        contact.paste(image,(room%5*320,room//5*216+16))
        labels.text((room%5*320+4,room//5*216),f'ROOM {room+1:02}',fill='white')
        files.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    contact.save(OUT/'all-rooms.png')
    atlas=indexed(128,512)
    for bank in range(4):
        for tile in range(128):
            for row in range(16):
                bits=source[0xa000+bank*2048+(tile|(128 if row>=8 else 0))*8+row%8]
                for pair in range(4):
                    value=(bits>>(6-pair*2))&3
                    for dx in range(2):atlas.putpixel((tile%16*8+pair*2+dx,bank*128+tile//16*16+row),(0,1,14,5)[value])
    atlas.save(OUT/'glyph-atlas.png')
    (OUT/'graphics-validation.json').write_text(json.dumps(dict(status='passed_indexed_source_extraction',
        source_sha256=hashlib.sha256(source).hexdigest(),room_count=20,charset_banks=4,
        pixel_scaling='Each C64 multicolor pair becomes two horizontal pixels; no resampling',
        palette='16 explicit OCS12-bit entries; C64 analog RGB is represented, not certified',
        raster_source='$48EA-$49BA, color pointers$480B, raster pointers$4833; active-display origin51',
        images=files),indent=2)+'\n')
    print('Ripped20 initialized room images and512 bank-specific8x16 glyphs;16 OCS colors')


if __name__=='__main__':main()
