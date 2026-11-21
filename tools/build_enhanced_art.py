"""Compile Enhanced artwork only. No source-game collision bytes are inputs."""
from pathlib import Path
import re
from PIL import Image
from build_fighter_dma import pack, unpack
from enhanced_architecture import PAGODA_INDEX, VAULT_DETAIL_INDEX, VAULT_DETAIL_COUNT, TOWER_INDEX, VAULT_LAMP_INDEX, masonry, runtime_stamp_index, stamps
from coarse_bruce import bruce_pixels
from enhanced_fighters import BRUCE_SOURCE_POSES, BRUCE_UNDIRECTED
from enhanced_enemies import enemy_pixels, reference_pose, source_shape
from bruce_editor_data import (Asset, EDIT_DIR, ALPHA, apply_override, fighter_asset,
                               stamp_asset, stamp_bytes, planar_pixels, check_files)

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'assets/graphics/enhanced-study'
PALETTE = (0x111,0xffe,0xa43,0x9bc,0x634,0x693,0x235,0xec5,
           0xa87,0x876,0xd96,0x345,0x789,0xbd7,0x668,0xcb9)
RGB = [tuple(((c >> shift) & 15)*17 for shift in (8,4,0)) for c in PALETTE]


def nearest(rgb, choices):
    return min(choices,key=lambda i: sum((a-b)**2 for a,b in zip(rgb,RGB[i])))


def base_pixels(actor, slot, face):
    """Colors in display order on the 48x21 source canvas."""
    if actor < 2:
        return enemy_pixels(actor,reference_pose(actor,slot,face),face)
    return bruce_pixels(slot,face)


def frame_bounds(data):
    points=[(i%48,i//48) for i,c in enumerate(data) if c!=15]
    left,top=min(x for x,y in points),min(y for x,y in points)
    width=max(x for x,y in points)+1-left
    height=max(y for x,y in points)+1-top
    return left,top,width,height


def encode_frame(data, box=None):
    left,top,width,height=box or frame_bounds(data)
    assert width<=48 and height<=21,(width,height)
    packed=bytearray()
    for y in range(top,top+height):
        for x in range(left,left+width,2):
            pair=data[y*48+x]<<4
            packed.append(pair|(data[y*48+x+1] if x+1<left+width else 15))
    return (left,top,width,height),packed


def tiles(image, choices):
    w,h=image.size
    image=image.convert('RGB')
    pixels=[nearest(image.getpixel((x,y)),choices) for y in range(h) for x in range(w)]
    return planar_tiles(w,h,pixels)


def planar_tiles(w,h,pixels):
    result=bytearray()
    for ty in range(0,h,8):
        for tx in range(0,w,8):
            for plane in range(4):
                for y in range(8):
                    result.append(sum(((pixels[(ty+y)*w+tx+x]>>plane)&1)<<(7-x) for x in range(8)))
    return result


def array(name, data):
    return ('static const unsigned char '+name+'[] ENHANCED_STORAGE={\n'+
            '\n'.join(','.join(str(x) for x in data[i:i+24])+',' for i in range(0,len(data),24))+'\n};\n')


def display_pixels(actor,slot,face,edits):
    base = base_pixels(actor,slot,face)
    if edits is None:
        return base
    values = apply_override(fighter_asset(actor,slot,face,base),edits)
    return [15 if p==ALPHA else p for p in values]


def table(kind,name,rows,flat=False):
    lines = [','.join(map(str,row)) for row in rows]
    if not flat:
        lines = ['{'+line+'}' for line in lines]
    return 'static const '+kind+' '+name+'[]={\n'+',\n'.join(lines)+'\n};\n'


def base_scenery():
    source=Image.open(ART/'tiles-source.png').convert('RGB')
    mid=source.width//2
    mountain=source.crop((0,source.height//5,mid,source.height*3//5)).resize((320,64),Image.Resampling.BOX)
    sky=tiles(mountain,(3,6,8,9,10,11,12,14,15))
    walls=[planar_tiles(64,32,[masonry(x,y,warm) for y in range(32) for x in range(64)]) for warm in (False,True)]
    return (('sky','Mountains and sky',320,64,sky),
            ('wall-cool','Slate wall',64,32,walls[0]),('wall-warm','Brick wall',64,32,walls[1]))


def compile_art(edits=EDIT_DIR):
    if edits is not None:check_files(edits)
    pixels = bytearray()
    blocks, offsets, views = [], {}, []
    used = 0
    def store_frame(colors):
        nonlocal used
        (x,y,w,h),data = encode_frame(colors)
        key = (w,h,bytes(data))
        if key not in offsets:
            offsets[key] = used//2
            blocks.append((len(pixels), used//2, w, h))
            pixels.extend(data)
            # Four interleaved mask/data pairs, with one shifter guard word.
            used += h*(32 if w<=16 else 48)
        return (offsets[key],x,y,w,h)

    edited = {}
    preview=Image.new('RGBA',(len(BRUCE_SOURCE_POSES)*48,3*21))
    for actor in range(3):
        for slot in range(len(BRUCE_SOURCE_POSES) if actor==2 else 13):
            for face in (0,1):
                effective_face = 1 if slot in (BRUCE_UNDIRECTED if actor==2 else (5,6)) else face
                effective_slot = slot-2 if actor==2 and slot in (3,4) else slot
                colors = display_pixels(actor,effective_slot,effective_face,edits)
                if actor<2:
                    edited[actor,slot,face] = colors
                else:
                    views.append(store_frame(colors))
                if face:
                    frame=Image.new('RGBA',(48,21))
                    frame.putdata([(*RGB[c],255) if c!=15 else (0,0,0,0) for c in colors])
                    preview.paste(frame,(slot*48,actor*21))

    # $2584/$25E2 can display a latched pose with the other facing. Give
    # every native pair its own lookup; share cropped DMA pixels by content.
    npc_words, alternate_run = [], []
    for actor in range(2):
        exact = {}
        shared = {}
        for slot in range(13):
            if slot in (3,4):continue
            for face in (0,1):
                if slot in (5,6) and not face:continue
                pose = reference_pose(actor,slot,face)
                words = store_frame(edited[actor,slot,face])[0]
                exact.setdefault((pose,face),words)
                box,mask=source_shape(actor,pose,face)
                shared.setdefault((box[2]-box[0],mask),words)
        for face in (0,1):
            for pose in range(0,70,2):
                # Many unlisted source states reuse the very same cropped
                # mask at another anchor. Carry the artist's edit with it.
                box,mask=source_shape(actor,pose,face)
                shape_key=(box[2]-box[0],mask)
                if shape_key not in shared:
                    shared[shape_key]=store_frame(enemy_pixels(actor,pose,face))[0]
                words = exact.get((pose,face),shared[shape_key])
                npc_words.append(words)
                if 0x0e<=pose<=0x14:
                    run_slot = 3 if pose in (0x10,0x12) else 4
                    if pose==reference_pose(actor,run_slot,face):
                        words=store_frame(edited[actor,run_slot,face])[0]
                    alternate_run.append(words)
    limit=int(re.search(r'BL_FIGHTER_CACHE_BYTES (\d+)',(ROOT/'amiga/c64_sprite_data.h').read_text())[1])
    scenery_parts=[]
    for key,label,w,h,data in base_scenery():
        if edits is not None:
            asset=Asset(key,label,'Backgrounds',w,h,tuple(planar_pixels(w,h,data)))
            data=planar_tiles(w,h,apply_override(asset,edits))
        scenery_parts.append(data)
    sky,wall,warm_wall=scenery_parts
    lookup,architecture=stamps((ROOT/'assets/c64/rooms-v1/charsets.bin').read_bytes())
    repainted=set()
    if edits is not None:
        edited_stamps=bytearray()
        for i in range(0,len(architecture),48):
            stamp=architecture[i:i+48];asset=stamp_asset(i//48+1,stamp)
            pens=apply_override(asset,edits)
            if tuple(pens)!=asset.pixels:
                repainted.add(i//48+1)
            edited_stamps.extend(stamp_bytes(asset,stamp,pens))
        architecture=edited_stamps
    assert len(lookup)==VAULT_DETAIL_INDEX+VAULT_DETAIL_COUNT and len(architecture)==48*max(lookup)
    lookup=runtime_stamp_index(lookup,repainted)
    trap_codes=(0x64,0x65,0x66,0x67,0xe4,0xe5,0xe6,0xe7)
    source_traps=not any(lookup[512+code] for code in trap_codes)
    # Four pairs of scanlines per stamp. Store repeated pairs only once in
    # the executable, including their source signature, mask and four planes.
    pairs={}
    pair_offsets=[]
    for start in range(0,len(architecture),48):
        for y in range(0,8,2):
            pair=b''.join(architecture[start+p*8+y:start+p*8+y+2] for p in range(6))
            pair_offsets.append(pairs.setdefault(pair,len(pairs)*12))
    # The CPU paints the repeating masonry. Index its 8x8 tiles in program
    # memory so independent artist edits need no more Chip RAM for walls.
    wall_tiles = {}
    wall_map = bytearray()
    for texture in (wall,warm_wall):
        for at in range(0,len(texture),32):
            tile = bytes(texture[at:at+32])
            wall_map.append(wall_tiles.setdefault(tile,len(wall_tiles)))
    scenery=sky
    raw=pixels+scenery
    if len(raw)>40960 or used+len(scenery)>limit:
        raise ValueError(f'Enhanced graphics need {len(raw)}/40960 unpacking bytes and {used+len(scenery)}/{limit} Chip buffer bytes.')
    encoded=pack(raw,compact=True);assert bytes(unpack(encoded))==raw
    header=('/* Generated by tools/build_enhanced_art.py. */\n'
            'static const UWORD enhanced_palette[16]={'+','.join(hex(c) for c in PALETTE)+'};\n'+
            table('EnhancedBlock','enhanced_blocks',blocks)+
            table('EnhancedView','enhanced_bruce_views',views)+
            table('UWORD','enhanced_npc_words',[npc_words],flat=True)+
            table('UWORD','enhanced_alt_run_words',[alternate_run],flat=True)+
            f'#define ENHANCED_NIBBLES {len(pixels)}\n#define ENHANCED_TILE_BASE {used}\n'+
            '#define ENHANCED_LAMP_INDEX 768\n'+
            f'#define ENHANCED_SOURCE_TRAPS {int(source_traps)}\n'+
            f'#define ENHANCED_TOWER_INDEX {TOWER_INDEX}\n'+
            f'#define ENHANCED_VAULT_LAMP_INDEX {VAULT_LAMP_INDEX}\n'+
            f'#define ENHANCED_SKY_BYTES {len(sky)}\n#define ENHANCED_WALL_BYTES {len(wall)}\n#define ENHANCED_TILE_BYTES {len(scenery)}\n'+
            array('enhanced_wall_map',wall_map)+array('enhanced_wall_tiles',b''.join(wall_tiles))+
            array('enhanced_arch_index',bytes(lookup[:PAGODA_INDEX]))+
            table('UWORD','enhanced_pagoda_index',[lookup[PAGODA_INDEX:VAULT_DETAIL_INDEX]],flat=True)+
            table('UWORD','enhanced_vault_detail_index',[lookup[VAULT_DETAIL_INDEX:]],flat=True)+
            table('UWORD','enhanced_pair_offsets',[pair_offsets],flat=True)+
            array('enhanced_arch_pairs',b''.join(pairs))+
            array('enhanced_packed',encoded))
    return header,preview,dict(frames=26+len(views)//2,npc_source_views=len(npc_words),actor_bytes=used,packed_bytes=len(encoded),tile_bytes=len(scenery))


def main():
    header,preview,report=compile_art()
    (ROOT/'amiga/enhanced_art.h').write_text(header,encoding='ascii')
    preview.save(ART/'fighters-ocs.png')
    print('Enhanced:',report)


if __name__=='__main__':
    main()
