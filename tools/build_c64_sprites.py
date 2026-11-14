"""Rip actor components by running the frozen candidate's real sprite writer.

No image generation, quantisation, scaling or reflection. The VIC's horizontal
expansion is part of the source display. PNG alpha and the OCS mask are separate
from colour zero: opaque black must survive the conversion.
"""
from pathlib import Path
import hashlib
import json
import sys
from PIL import Image, ImageDraw
from build_fighter_dma import pack, unpack

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler

SOURCE = ROOT/'.reference/c64/work/untrained-memory.bin'
OUT = ROOT/'assets/c64/sprites-v1'
SHA = '092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
PALETTE = [0x000,0xfff,0x833,0x7cc,0x84a,0x6a4,0x338,0xcc7,
           0x852,0x541,0xb77,0x444,0x777,0xaf9,0x78c,0xbbb]
RGB = [tuple(((c >> shift)&15)*17 for shift in (8,4,0)) for c in PALETTE]
ACTORS = [('yamo',1,70), ('kage',2,140), ('bruce',0,0)]


def sha(data): return hashlib.sha256(data).hexdigest()
def artifact(path):
    return dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path.read_bytes()))


def execute(m, entry, actor=0):
    cpu = MPU(memory=m, pc=entry)
    cpu.x, cpu.sp = actor, 0xff
    cpu.stPushWord(0x02fe)
    for count in range(100000):
        if cpu.pc == 0x02ff: return count
        cpu.step()
    raise AssertionError(f'Unfinished source routine ${entry:04X}, PC=${cpu.pc:04X}')


def source_frame(initial, actor, base, facing, bank=0):
    m = list(initial)
    m[0x95:0x98] = [0,0,0]
    m[0x95+actor] = (1,0x81,0x41)[actor]
    m[0x9e+actor], m[0xa1+actor], m[0xa4+actor] = 80,150,facing
    m[0x4f48+actor], m[0x4f4b+actor] = base,base+1
    offset = (0,70,140)[actor]
    m[0x4f4e+actor], m[0x4f51+actor] = offset+base,offset+base+1
    m[0x277d], m[0x277e] = bank,0
    m[0xd015] = (3,12,16)[actor]
    # Actual game setup $07EF-$07FA: hires, normal Y, doubled X, in front.
    m[0xd017] = m[0xd01b] = m[0xd01c] = m[0xd010] = 0
    m[0xd01d] = 255
    execute(m,0x2584)
    execute(m,0x25e2)
    # VIC bank $8000, screen $8C00, source visible origin (24,51).
    # Canvas anchor: source actor X minus16, actor baseline Y minus22.
    origin_x, origin_y = 80*2-24-16,150-22
    pixels = [None]*(48*21)
    components = []
    for sprite in reversed(range(5)):
        if not m[0xd015] & (1<<sprite): continue
        pointer = 0x8000 + m[0x8ff8+sprite]*64
        bits = bytes(m[pointer:pointer+63])
        x = m[0xd000+sprite*2]+(256 if m[0xd010]&(1<<sprite) else 0)-24
        y = m[0xd001+sprite*2]-51
        color = m[0xd027+sprite]&15
        components.append(dict(vic_sprite=sprite,buffer_address=f'${pointer:04X}',
                               x_offset=x-(origin_x+16),y_offset=y-150,
                               color=color,bits=bits.hex()))
        for row in range(21):
            for column in range(24):
                if bits[row*3+column//8] & (128>>(column&7)):
                    for dx in range(2):
                        px,py = x+column*2+dx-origin_x,y+row-origin_y
                        assert 0 <= px < 48 and 0 <= py < 21,(actor,base,facing,px,py)
                        pixels[py*48+px] = color
    return pixels,components


def picture(pixels):
    image = Image.new('RGBA',(48,21))
    image.putdata([(*RGB[p],255) if p is not None else (0,0,0,0) for p in pixels])
    return image


def dma_frame(pixels):
    occupied = [(i%48,i//48) for i,p in enumerate(pixels) if p is not None]
    if not occupied: return bytes(),[0,0,0,0]
    left,top = min(x for x,y in occupied),min(y for x,y in occupied)
    right,bottom = max(x for x,y in occupied)+1,max(y for x,y in occupied)+1
    # Crop X as well as Y; the original's two source sprites can use different
    # anchors. Six-byte lanes retain the existing OCS barrel-shifter guard.
    raw = bytearray()
    for y in range(top,bottom):
        mask = bytearray(6);planes = [bytearray(6) for _ in range(4)]
        for x in range(left,right):
            color = pixels[y*48+x]
            if color is None: continue
            at,bit = (x-left)//8,128>>((x-left)&7)
            mask[at] |= bit
            for p in range(4):
                if color & (1<<p): planes[p][at] |= bit
        for plane in planes: raw.extend(mask);raw.extend(plane)
    # Decode every pixel, including transparent/opaque black and guard bytes.
    for y in range(bottom-top):
        for x in range(48):
            at=y*48+x//8;bit=128>>(x&7)
            color=sum(1<<p for p in range(4) if raw[at+p*12+6]&bit)
            expected=pixels[(y+top)*48+x+left] if x+left<right else None
            assert bool(raw[at]&bit)==(expected is not None)
            assert color==(0 if expected is None else expected)
    return bytes(raw),[left,top,right,bottom]


def main():
    if not SOURCE.exists():
        report=json.loads((OUT/'manifest.json').read_text())
        for item in report['outputs']: assert sha((ROOT/item['path']).read_bytes())==item['sha256'],item['path']
        print('Verified extracted C64 sprites; immutable local candidate not installed')
        return
    m=SOURCE.read_bytes();assert len(m)==65536 and sha(m)==SHA
    OUT.mkdir(parents=True,exist_ok=True)
    components=[];component_data=bytearray()
    for i in range(210):
        pointer=m[0x59bd+i]+256*m[0x5a8f+i]
        wide=bool(m[0x5cbf+i]);counter=m[0x5b61+i]
        size=2*counter if wide else counter+1
        data=m[pointer:pointer+size];component_data.extend(data)
        components.append(dict(index=i,address=f'${pointer:04X}',copy_counter=counter,
                               wide=wide,color=None if i>=140 else m[0x5c33+i]&15,
                               bytes=size,sha256=sha(data)))
    (OUT/'components.bin').write_bytes(component_data)
    frames=[];raw=bytearray();unique={};offsets=[];bounds=[]
    atlas=Image.new('RGBA',(35*48,6*21))
    preview=Image.new('RGB',(35*96,6*62),'#223344');draw=ImageDraw.Draw(preview)
    for kind,(name,actor,offset) in enumerate(ACTORS):
        for facing in range(2):
            for base in range(0,70,2):
                pixels,parts=source_frame(m,actor,base,facing)
                other,_=source_frame(m,actor,base,facing,1)
                assert pixels==other,'Source double buffers must display identical pixels'
                frame=picture(pixels)
                path=OUT/f'{name}-{base:02x}-f{facing}.png';frame.save(path)
                atlas.paste(frame,(base//2*48,(kind*2+facing)*21))
                preview.paste(frame.resize((96,42),Image.Resampling.NEAREST),
                              (base//2*96,(kind*2+facing)*62),
                              frame.resize((96,42),Image.Resampling.NEAREST))
                draw.text((base//2*96,(kind*2+facing)*62+43),f'{name} {base:02X} {facing}',fill='white')
                data,bbox=dma_frame(pixels)
                if data not in unique: unique[data]=len(raw);raw.extend(data)
                offsets.append(unique[data]);bounds.append(bbox)
                frames.append(dict(actor=name,source_actor=actor,base_pose=base,facing=facing,
                                   components=parts,rgba_sha256=sha(frame.tobytes()),bounds=bbox,
                                   dma_offset=unique[data],dma_bytes=len(data),file=path.name))
    atlas.save(OUT/'actors.png');preview.save(OUT/'preview.png')
    (OUT/'ocs-palette.txt').write_text('\n'.join(f'#{p:03X}' for p in PALETTE)+'\n')
    packed=pack(raw,compact=True);assert unpack(packed)==raw
    (OUT/'actors.dma').write_bytes(raw)
    (OUT/'actors.packed').write_bytes(packed)
    fnv=2166136261
    for byte in raw:fnv=((fnv^byte)*16777619)&0xffffffff
    header=ROOT/'amiga/c64_sprite_data.h'
    pose_header=ROOT/'core/c64_sprite_pose_data.h'
    pose_header.write_text('/* Source $5CBF width flags, actor atlas order. */\n'+
        'static const unsigned char c64_sprite_width[3][70]={'+
        ','.join('{'+','.join(str(x) for x in m[0x5cbf+offset:0x5cbf+offset+70])+'}' for name,actor,offset in ACTORS)+'};\n')
    lines=['/* GENERATED from frozen C64 bytes; build_c64_sprites.py. */',
           '#define BL_C64_SPRITE_FRAMES 210',
           f'#define BL_FIGHTER_CACHE_BYTES {len(raw)}UL',
           '#define BL_FIGHTER_CLIP_BYTES 1344UL',
           f'#define BL_FIGHTER_CACHE_FNV {fnv}UL',
           'static const unsigned long fighter_dma_offsets[210]={'+','.join(str(x) for x in offsets)+'};',
           'static const unsigned char c64_sprite_bounds[210][4]={'+','.join('{'+','.join(str(n) for n in b)+'}' for b in bounds)+'};',
           'static const unsigned char fighter_dma_packed[]={']
    lines += [','.join(str(x) for x in packed[i:i+32])+',' for i in range(0,len(packed),32)]
    lines += ['};',''];header.write_text('\n'.join(lines),encoding='ascii')
    disassembler=Disassembler(MPU(memory=list(m)));disassembly=[]
    for start,end in ((0x07ea,0x07fd),(0x2584,0x274f),(0x2780,0x29c3)):
        pc=start
        while pc<end:
            length,text=disassembler.instruction_at(pc)
            disassembly.append(f'${pc:04X} {m[pc:pc+length].hex(" "):8} {text}');pc+=length
    (OUT/'source-disassembly.txt').write_text('\n'.join(disassembly)+'\n')
    outputs=[artifact(p) for p in sorted(OUT.iterdir()) if p.name!='manifest.json']+[artifact(header),artifact(pose_header)]
    report=dict(status='extracted_by_actual6502_sprite_copy_and_position',source=dict(path=SOURCE.relative_to(ROOT).as_posix(),sha256=SHA),
                edition_verified=False,full_actor_fsm_ported=False,components=components,frames=frames,
                source_pose_count=35,frame_count=210,unique_dma_frames=len(unique),
                source_routines=['$2584-$274E','$25E2-$269F','$2780-$29C2'],
                source_tables=['$59BD/$5A8F','$5B61','$5C33','$5CBF','$274F-$277C'],
                vic=dict(multicolor=False,x_expansion=2,y_expansion=1,screen_origin=[24,51],sprite_priority='lower VIC number in front'),
                ocs_palette=PALETTE,canvas=[48,21],anchor=[16,22],
                cache_bytes=len(raw),packed_bytes=len(packed),clip_scratch_bytes=1344,native_fnv=fnv,
                raw_sha256=sha(raw),generator=artifact(Path(__file__)),
                dependencies=[artifact(ROOT/'tools/build_fighter_dma.py')],outputs=outputs,
                original_c64_actor_pixels=True,new_art_generated=False,
                limitations=['Frozen Remember/T64 candidate is not certified pristine1984 edition',
                             'Component PNG colours map C64 indices to existing OCS12-bit palette',
                             'Ported actor state bridge is separate from these exact source pixels'])
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'Ripped210 components,210 source pose/facing composites, {len(unique)} unique DMA frames; {len(raw)} Chip bytes, {len(packed)} packed')


if __name__=='__main__':main()
