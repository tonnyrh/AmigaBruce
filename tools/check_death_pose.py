"""Check source-driven bomb death poses in a dedicated normal-ADF WinUAE.

Usage: python tools/check_death_pose.py FOLDER PID
FOLDER contains release.elf and the owned emulator's winuaebootlog.txt.
Starts are injected; bomb arming, explosion, death and respawn run normally.
"""
import argparse
import hashlib
import json
import re
import struct
import time
from pathlib import Path

from PIL import Image
from build_c64_sprites import SOURCE, SHA, source_frame
from build_enhanced_art import display_pixels, EDIT_DIR, RGB
from capture_paula_stream import elf_symbols
from title_reference import reference
from winuae_ipc import command, tap_fire


def check(folder, pid):
    pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",(folder/'winuaebootlog.txt').read_text(errors='replace'))[-1]
    def cmd(s): return command(pipe,s,timeout=10,expected_pid=pid)
    def val(at,n=4):
        match=re.search(r'(?mi)^[0-9a-f]{8}\s+((?:[0-9a-f]{4}\s+){1,8})',cmd(f'DBG m {at:x} 1'))
        return int.from_bytes(bytes.fromhex(match[1])[:n],'big')
    def dump(name,at,size):
        p=folder/name
        assert 'Wrote ' in cmd(f'DBG S {p} {at:x} {size:x}')
        return p.read_bytes()
    def front():
        at=int(re.search(r'COP1LC: \$([0-9a-f]+)',cmd('DBG c'),re.I)[1],16)
        w=struct.unpack('>66H',dump('copper.bin',at,132))
        if w[0:2]!=(0x100,0x4200) or w[18:26:2]!=(0xe0,0xe2,0xe4,0xe6):return b''
        return dump('front.bpl',w[19]*65536+w[21],40960)
    def wait(fn,seconds=120):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            if fn():return
            time.sleep(.1)
        raise AssertionError('Timed out: '+fn.__name__)
    def key(k):
        cmd('EVT KEY_'+k+' 1');time.sleep(.2);cmd('EVT KEY_'+k+' 0')
    def pause():
        cmd('EVT SPC_PAUSE 1');cmd('EVT SPC_PAUSE 0');time.sleep(.03)
    def pixel(data,x,y):
        return sum(((data[y*160+x//8+p*40]>>(7-x%8))&1)<<p for p in range(4))

    raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SHA
    assert raw[0x27b8:0x27c1]==bytes.fromhex('c919d005a0084ca129')
    wait(lambda:front()==reference(),240)
    task=val(val(4)+276);cli=val(task+172)*4;node=val(cli+60)*4;hunks=[]
    while node:
        hunks.append(node+4);node=val(node)*4;assert len(hunks)<=4
    bss,symbols=elf_symbols(folder/'release.elf')
    def addr(name):return hunks[3]+symbols[name]-bss
    ram=addr('m')
    def put(at,value):cmd(f'DBG W {ram+at:x} {value:02x}')
    cmd('EVT KEY_SHIFT_LEFT 1');key('D');cmd('EVT KEY_SHIFT_LEFT 0')
    wait(lambda:front()==reference(debug=True))
    for room in range(1,11):
        key('F10')
        expected=reference(debug=True,room_select=True,room=room)
        wait(lambda:front()[110*160:]==expected[110*160:])
    tap_fire(cmd)
    wait(lambda:val(addr('game_field_active'),1) and val(ram+0x29,1)==10)
    records=[]
    for enhanced in (False,True):
        if enhanced:
            key('F8');wait(lambda:front()==reference(room_select=True))
            key('F4');wait(lambda:front()==reference(enhanced=True,room_select=True))
            tap_fire(cmd);wait(lambda:val(addr('game_field_active'),1) and val(ram+0x29,1)==10)
        assert bool(val(addr('enhanced_active'),1))==enhanced
        for face in (0,1):
            wait(lambda:not any(val(ram+0x4fde+i,1) for i in range(3)))
            pause()
            try:
                m=dump('before.bin',ram,65536)
                assert m[0x29]==10 and m[0xbf]!=25
                lives=m[0x28]
                for at,value in {0x95:1,0x96:0,0x97:0,0x5d:255,0x5e:255,
                                 0x9e:96,0xa1:140,0xa4:face,0xbf:0,0xce:0,
                                 0x4f48:face*2,0x4f4e:face*2,0xd1:36}.items():put(at,value)
            finally:pause()
            label=('enhanced' if enhanced else 'classic')+f'-face-{face}'
            art=display_pixels(2,14,face,EDIT_DIR) if enhanced else [15 if c is None else c for c in source_frame(raw,0,8,face)[0]]
            dots=[(i%48,i//48,c) for i,c in enumerate(art) if c!=15]
            seen=False;painted=False;armed=False;blast=False;events=[];positions=set();end=time.monotonic()+120
            while time.monotonic()<end:
                pause()
                try:
                    m=dump('ram.bin',ram,65536)
                    assert not val(addr('source_fault'),2)
                    state,pose,count=m[0xbf],m[0x4f48],m[0xce]
                    events.append(dict(step=val(addr('actor_logic_steps'),2),state=state,pose=pose,counter=count,
                                       x=m[0x9e],y=m[0xa1],lives=m[0x28],timers=list(m[0x4fde:0x4fe1])))
                    armed|=any(m[0x4fde:0x4fe1])
                    blast|=0x71<=m[0x8c00+17*40+21]<=0x7c
                    if state==25:
                        seen=True;positions.add((m[0x9e],m[0xa1]))
                        if pose==8 and not painted:
                            data=front();left=m[0x9e]*2-40;top=m[0xa1]+10
                            if data and all(pixel(data,left+x,top+y)==c for x,y,c in dots):
                                painted=True
                                (folder/(label+'.bpl')).write_bytes(data)
                                (folder/(label+'.bin')).write_bytes(m)
                                if enhanced:
                                    image=Image.new('RGB',(64,40))
                                    image.putdata([RGB[pixel(data,left-8+x,top-8+y)] for y in range(40) for x in range(64)])
                                    image.resize((384,240),Image.Resampling.NEAREST).save(folder/(label+'.png'))
                finally:pause()
                if seen and m[0x28]!=lives:break
                # Allow real execution between debugger snapshots. Repeated
                # pause/read/resume alone can starve disk-driven respawn work.
                time.sleep(.15)
            else:raise AssertionError(('Death did not finish',label,events))
            assert armed and blast and seen and painted and len(positions)==1,(label,armed,blast,seen,painted,positions)
            assert m[0x28]==lives-1,(label,lives,m[0x28])
            wait(lambda:val(ram+0xbf,1)!=25 and val(addr('game_field_active'),1))
            record=dict(look=label,armed=armed,blast=blast,visible_pose=8,opaque_pixels=len(dots),
                        stationary=True,lives_before=lives,lives_after=m[0x28],events=events)
            records.append(record)
            (folder/'result.json').write_text(json.dumps(dict(source_sha256=SHA,edition_verified=False,
                method='Controlled starting placement; actual bomb arming and explosion; no injected death state, contact mask or bomb timer. Published actor pixels checked during source state 25.',checks=records),indent=2)+'\n')
            print('PASS',label,': stiff pose $08 visible, fixed position, one life lost.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path);parser.add_argument('pid',type=int)
    args=parser.parse_args();check(args.folder.resolve(),args.pid)
