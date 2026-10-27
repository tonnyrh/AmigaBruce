"""Compare the native pose selector with actual frozen6502 instructions.

These are injected actor states, not a natural gameplay/timing measurement.
Also binds the extracted pixels, DMA bytes and source component metadata.
"""
from pathlib import Path
import ctypes
import hashlib
import itertools
import json
from build_c64_sprites import ROOT,OUT,SOURCE,SHA,execute,source_frame,picture,artifact
from build_fighter_dma import unpack

FIELDS=('state','counter','facing','contact','previous','width','second_width','aa','locked')
class Pose(ctypes.Structure):
    _fields_=[(key,ctypes.c_ubyte) for key in FIELDS]


def main():
    m=SOURCE.read_bytes();assert hashlib.sha256(m).hexdigest()==SHA
    manifest=json.loads((OUT/'manifest.json').read_text())
    for item in manifest['outputs']+[manifest['generator']]+manifest['dependencies']:
        assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
    raw=(OUT/'actors.dma').read_bytes();assert unpack((OUT/'actors.packed').read_bytes())==raw
    cases=[(*p,0,0,0,0) for p in itertools.product(range(28),(0,1,2,3,4,9,10,11,12,15,16,255),(0,1),(0,4,8,12),(0,10,12,14,18,68))]
    cases += [(s,c,f,b,old,w,w2,aa,lock)
              for s,c,f,b,old,w,w2,aa,lock in itertools.product((0,23,24),(0,255),(0,1),(0,4),(0,10,68),(0,1),(0,1),(0,1),(0,1))]
    dll=ctypes.CDLL(str(ROOT/'.tmp/c64-sprites-test/sprites.dll'))
    dll.bl_source_pose.argtypes=[ctypes.POINTER(Pose)];dll.bl_source_pose.restype=ctypes.c_ubyte
    fixture=[];fixture_keys=set();count=0
    for i,case in enumerate(cases):
        p=Pose(*case);source=list(m);actor=i%3
        for field,address in [('state',0xbf),('counter',0xce),('facing',0xa4),('contact',0xb6),('previous',0x4f48),('width',0xd4),('second_width',0xd7),('aa',0xaa),('locked',0x4fdb)]:
            source[address+actor]=getattr(p,field)
        source[0x95+actor]=(1,0x81,0x41)[actor]
        execute(source,0x2780,actor)
        expected=source[0x4f48+actor]
        actual=dll.bl_source_pose(ctypes.byref(p))
        assert actual==expected,(dict(zip(FIELDS,case)),actual,expected)
        count+=1
        if (p.counter in (0,10,11) and p.previous==10 and p.contact==0 and not(p.width or p.second_width or p.aa or p.locked)) or (
            p.state in (0,1,2,3,4,20,21) and not p.counter and p.previous in (10,12) and p.contact==4 and not(p.width or p.second_width or p.aa or p.locked)) or (
            p.state in (23,24) and not p.counter and p.previous in (0,68) and p.contact==0):
            if case not in fixture_keys:fixture_keys.add(case);fixture.append((case,expected))
    # Independent file reread versus fresh source executions, both directions
    # and both double buffers. These pixels never use the native pose adapter.
    from PIL import Image
    pixel_checks=0
    for f in manifest['frames']:
        frame,parts=source_frame(m,f['source_actor'],f['base_pose'],f['facing'])
        assert parts==f['components']
        image=Image.open(OUT/f['file']).convert('RGBA')
        assert image.tobytes()==picture(frame).tobytes()
        left,top,right,bottom=f['bounds'];offset=f['dma_offset']
        for y in range(21):
            for x in range(48):
                color=None
                if left<=x<right and top<=y<bottom:
                    at=offset+(y-top)*48+(x-left)//8;bit=128>>((x-left)&7)
                    if raw[at]&bit:color=sum(1<<p for p in range(4) if raw[at+p*12+6]&bit)
                assert color==frame[y*48+x],(f['file'],x,y,color,frame[y*48+x])
                pixel_checks+=1
    header=ROOT/'tests/sprite_fixture.h'
    header.write_text('/* Actual frozen6502 $2780 outputs; injected state, not playthrough. */\n'+
        f'#define BL_SPRITE_FIXTURE_CASES {len(fixture)}\n'+
        'static const unsigned char sprite_fixture[][10]={\n'+
        '\n'.join('{'+','.join(str(v) for v in case+(expected,))+'},' for case,expected in fixture)+'\n};\n'+
        'static unsigned short sprite_fixture_check(void){\n'+
        'unsigned short i;BlSourcePose p;for(i=0;i<BL_SPRITE_FIXTURE_CASES;i++){\n'+
        ''.join(f'p.{field}=sprite_fixture[i][{j}];' for j,field in enumerate(FIELDS))+'\n'+
        'if(bl_source_pose(&p)!=sprite_fixture[i][9])return i+1;}return 0;}\n')
    report=dict(status='passed_actual6502_pose_and_ripped_pixel_controls',source_sha256=SHA,
                edition_verified=False,full_actor_fsm_ported=False,natural_playthrough=False,
                selector_cases=count,native_fixture_cases=len(fixture),pixel_checks=pixel_checks,
                frames=210,components=210,cache_bytes=manifest['cache_bytes'],
                inputs='Injected source state/counter/previous/contact/width/lock; unmodified source instructions',
                source_files=[artifact(ROOT/p) for p in ('core/c64_sprites.c','core/c64_sprites.h','core/c64_sprite_pose_data.h','core/game.h','core/combat.h','core/source_wall.h','tools/build_c64_sprites.py','tools/build_fighter_dma.py','tools/verify_c64_sprites.py','test-c64-sprites.ps1','assets/c64/sprites-v1/manifest.json')],
                native_fixture=artifact(header),host_library=artifact(ROOT/'.tmp/c64-sprites-test/sprites.dll'))
    path=ROOT/'reference/validation/c64-sprites-host.json';path.write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {count} source pose cases, {pixel_checks} source/DMA pixel checks, {len(fixture)} native fixtures')


if __name__=='__main__':main()
