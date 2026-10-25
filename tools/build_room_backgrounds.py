"""Compile generated scenery and authored geometry into planar room bases.

No C64 character/sprite pixels are read. Input is semantic blockout geometry,
the project's authored palette and the two existing authored room layouts.
The 68000 only decompresses on a cache miss; lamps/HUD remain dynamic.
"""
import hashlib
import json
import re
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
WIDTH,HEIGHT,PLANE_BYTES=320,256,10240
SCENERY=ROOT/'assets/graphics/v1/mountains-indexed.png'


def rle(data):
    encoded=bytearray();index=0
    while index<len(data):
        end=index+1
        while end<len(data) and data[end]==data[index] and end-index<127:end+=1
        if end-index>=3:
            encoded.extend((end-index,data[index]));index=end
        else:
            start=index;index+=1
            while index<len(data) and index-start<127:
                if index+2<len(data) and data[index]==data[index+1]==data[index+2]:break
                index+=1
            encoded.append(128+index-start);encoded.extend(data[start:index])
    encoded.append(128)
    return bytes(encoded)


def unrle(data):
    result=bytearray();index=0
    while data[index]!=128:
        count=data[index];index+=1
        if count&128:
            count&=127;result.extend(data[index:index+count]);index+=count
        else:
            result.extend([data[index]]*count);index+=1
    return bytes(result)


def authored_array(source,name):
    match=re.search(r'\b'+name+r'\[\]\s*=\s*\{(.*?)\};',source,re.S)
    assert match,name
    return [list(map(int,row.split(','))) for row in re.findall(r'\{([0-9, ]+)\}',match[1])]


def render(room):
    pixels=bytearray(WIDTH*HEIGHT)
    scenery=Image.open(SCENERY)
    assert scenery.mode=='P' and scenery.size==(320,200)
    pixels[32*320:232*320]=scenery.tobytes()
    def rect(x,y,w,h,c):
        left=max(0,x);right=min(WIDTH,x+w);top=max(0,y);bottom=min(HEIGHT,y+h)
        if left>=right or top>=bottom:return
        for row in range(top,bottom):pixels[row*WIDTH+left:row*WIDTH+right]=bytes([c])*(right-left)
    if room['room']<3:
        for left,right,top,bottom in ((56,96,152,196),(256,288,98,144),(224,288,144,196)):
            rect(left,32+top,right-left,bottom-top,1)
            for x in range(left,right+1,6):rect(x,32+top,1,bottom-top,4)
            for y in range(top,bottom,6):rect(left,32+y,right-left,1,4)
    for x0,x1,y0,y1,_ in room['nets']:
        rect(x0,32+y0,x1-x0,y1-y0,1)
        for x in range(x0,x1+1,6):rect(x,32+y0,1,y1-y0,7)
        for y in range(y0,y1,6):rect(x0,32+y,x1-x0,1,7)
    for x0,x1,y in room['platforms']:
        rect(x0,32+y,x1-x0,4,11);rect(x0,32+y,x1-x0,1,12)
        rect(x0,32+y+4,x1-x0,1,0)
        for x in range(x0+3,x1,10):rect(x,32+y+2,1,1,4)
    planar=bytearray(PLANE_BYTES*4)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            c=pixels[y*WIDTH+x]
            for plane in range(4):
                if c&(1<<plane):planar[plane*PLANE_BYTES+y*40+x//8]|=128>>(x&7)
    return bytes(planar)


def main():
    source=(ROOT/'core/game.c').read_text(encoding='utf-8')
    rooms=[dict(room=1,platforms=authored_array(source,'bl_platforms'),nets=authored_array(source,'bl_climbables')),
           dict(room=2,platforms=authored_array(source,'room2_platforms'),nets=authored_array(source,'room2_climbables'))]
    rooms+=json.loads((ROOT/'reference/validation/room-blockouts.json').read_text())['rooms']
    header=['/* Generated AI scenery and authored blockout surfaces; build_room_backgrounds.py. */',
            '#ifndef BRUCE_ROOM_BACKGROUNDS_H','#define BRUCE_ROOM_BACKGROUNDS_H']
    common=render(dict(room=3,platforms=[],nets=[]))
    packed_common=rle(common)
    assert unrle(packed_common)==common
    header.append('static const unsigned char room_base_common[]={'+','.join(str(v) for v in packed_common)+'};')
    records=[]
    for room in rooms:
        data=render(room);delta=bytes(a^b for a,b in zip(data,common));packed=rle(delta)
        assert len(data)==40960 and bytes(a^b for a,b in zip(unrle(packed),common))==data
        number=room['room']
        header.append('static const unsigned char room_base_%d[]={%s};' %
                      (number,','.join(str(v) for v in packed)))
        records.append(dict(room=number,unpacked_bytes=len(data),packed_bytes=len(packed),
                            sha256=hashlib.sha256(data).hexdigest()))
    header.append('static const unsigned char * const room_bases[20]={'+','.join('room_base_%d'%n for n in range(1,21))+'};')
    header+=['#endif','']
    target=ROOT/'amiga/room_background_data.h';target.write_text('\n'.join(header),encoding='utf-8')
    paths=['tools/build_room_backgrounds.py','core/game.c','core/room_geometry.h','reference/validation/room-blockouts.json','assets/graphics/v1/mountains-indexed.png']
    report=dict(original_pixels_used=False,roundtrip_passed=True,
                common_packed_bytes=len(packed_common),
                total_packed_bytes=len(packed_common)+sum(r['packed_bytes'] for r in records),rooms=records,
                generated_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                source_files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths])
    (ROOT/'reference/validation/room-backgrounds.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('20 backgrounds; lossless roundtrip PASS;',report['total_packed_bytes'],'packed bytes; 819200 unpacked bytes')


if __name__=='__main__':main()
