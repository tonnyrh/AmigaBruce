"""Pack existing actor pixels into immutable OCS blitter poses, both facings.

No art generation. Reproduces the former prepare_fighters bit conversion and
its anchor reflection exactly, with the current C64 room-palette mapping.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'assets/graphics/v2'
COLORS=[0,6,11,12,12,3,1,3,6,6,12,8,7,7,5,9]


def pack(data):
    result=bytearray();at=0;positions={};literal=bytearray()
    def remember(start,end):
        for pos in range(start,end):
            key=bytes(data[pos:pos+3]);items=positions.setdefault(key,[]);items.append(pos)
            if len(items)>16:del items[0]
    def flush():
        if literal:result.append(128+len(literal));result.extend(literal);literal.clear()
    while at<len(data):
        run=1
        while run<127 and at+run<len(data) and data[at+run]==data[at]:run+=1
        length=0;distance=0
        if run<3:
            for prior in reversed(positions.get(bytes(data[at:at+3]),[])):
                if at-prior>65535:continue
                count=0
                while count<255 and at+count<len(data) and data[prior+count]==data[at+count]:count+=1
                if count>length:length=count;distance=at-prior
        if run>=3:
            flush();result.extend((run,data[at]));remember(at,at+run);at+=run
        elif length>=5:
            flush();result.extend((0,distance>>8,distance&255,length));remember(at,at+length);at+=length
        else:
            literal.append(data[at]);remember(at,at+1);at+=1
            if len(literal)==127:flush()
    flush();result.append(128);return result


def unpack(data):
    result=bytearray();at=0
    while data[at]!=128:
        n=data[at];at+=1
        if not n:
            distance=data[at]*256+data[at+1];length=data[at+2];at+=3
            assert 0<distance<=len(result) and length>=5
            for _ in range(length):result.append(result[-distance])
        elif n&128:n&=127;result.extend(data[at:at+n]);at+=n
        else:result.extend([data[at]]*n);at+=1
    return result


def main():
    source=ART/'fighters-indexed.png';image=Image.open(source)
    assert image.size==(768,78) and image.mode=='P'
    raw=bytearray();offsets=[];heights=[]
    for actor in range(3):
        for face in range(2):
            for pose in range(16):
                frame=image.crop((pose*48,actor*26,(pose+1)*48,(actor+1)*26));bbox=frame.getbbox()
                top,bottom=bbox[1],bbox[3];height=bottom-top
                offsets.append(len(raw));heights.append(height)
                planes=[bytearray(height*6) for _ in range(5)]
                for row in range(height):
                    for column in range(48):
                        sx=column if face else 48-column
                        if sx>=48:continue
                        old=frame.getpixel((sx,top+row));color=COLORS[old]
                        if not old:continue
                        mask=128>>(column&7);at=row*6+column//8
                        planes[0][at]|=mask
                        for plane in range(4):
                            if color&(1<<plane):planes[plane+1][at]|=mask
                # A/B pairs for four interleaved destination planes. The mask
                # is repeated so one OCS blit draws the complete actor.
                start=len(raw)
                for row in range(height):
                    for plane in range(4):
                        raw.extend(planes[0][row*6:row*6+6]);raw.extend(planes[plane+1][row*6:row*6+6])
                # Reconstruct every source pixel from the packed DMA layout.
                for row in range(height):
                    for column in range(48):
                        at=start+row*48+(column//8);bit=128>>(column&7)
                        visible=bool(raw[at]&bit)
                        color=sum(1<<p for p in range(4) if raw[at+p*12+6]&bit)
                        sx=column if face else 48-column
                        old=frame.getpixel((sx,top+row)) if sx<48 else 0
                        assert visible==bool(old) and color==COLORS[old]
    packed=pack(raw);assert unpack(packed)==raw
    fnv=2166136261
    for byte in raw:fnv=((fnv^byte)*16777619)&0xffffffff
    lines=['/* Existing actor art, converted offline; build_fighter_dma.py. */',
           f'#define BL_FIGHTER_CACHE_BYTES {len(raw)}UL',
           '#define BL_FIGHTER_CLIP_BYTES 1664UL',
           f'#define BL_FIGHTER_CACHE_FNV {fnv}UL',
           'static const unsigned long fighter_dma_offsets[96]={'+','.join(str(x) for x in offsets)+'};',
           'static const unsigned char fighter_dma_packed[]={']
    lines += [','.join(str(x) for x in packed[i:i+32])+',' for i in range(0,len(packed),32)]
    lines+=['};','']
    header=ROOT/'amiga/fighter_dma_data.h';header.write_text('\n'.join(lines),encoding='ascii')
    report=dict(status='passed_exact_pixel_conversion_and_pack_roundtrip',
        source=dict(path=source.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(source.read_bytes()).hexdigest()),
        faces=96,palette_map=COLORS,cache_bytes=len(raw),packed_bytes=len(packed),clip_scratch_bytes=1664,
        compression='byte-run literals/repeats plus bounded16-bit backwards matches',
        layout='six-byte A/B pairs; mask repeated for four interleaved planes; one cookie-cut blit',
        native_fnv=fnv,raw_sha256=hashlib.sha256(raw).hexdigest(),header_sha256=hashlib.sha256(header.read_bytes()).hexdigest(),
        original_c64_actor_pixels=False,new_art_generated=False)
    (ART/'fighter-dma-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'Prepared96 immutable blitter poses:{len(raw)} Chip bytes,{len(packed)} packed bytes')


if __name__=='__main__':main()
