"""Check caps and live-colour emblems in an owned normal-ADF A500 boot.

Rooms are entered with the built-in room selector, not a natural playthrough.
Classic pixels are checked against live C64 data; Enhanced against the masters.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import time
from PIL import Image
from build_enhanced_art import PALETTE
from capture_paula_stream import elf_symbols,elf_hunk_index
from check_enhanced_mode import check_structure
from title_reference import reference
from winuae_ipc import command,tap_fire

ROOT=Path(__file__).resolve().parents[1]


def check(folder,pid):
    pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",(folder/'winuaebootlog.txt').read_text(errors='replace'))[-1]
    def cmd(text):return command(pipe,text,timeout=15,expected_pid=pid)
    def val(at,n=4):
        r=re.search(r'(?mi)^[0-9a-f]{8}\s+((?:[0-9a-f]{4}\s+){1,8})',cmd(f'DBG m {at:x} 1'))
        return int.from_bytes(bytes.fromhex(r[1])[:n],'big')
    def dump(name,at,n):
        p=folder/name;assert 'Wrote ' in cmd(f'DBG S {p} {at:x} {n:x}');return p.read_bytes()
    def front():
        at=int(re.search(r'COP1LC: \$([0-9a-f]+)',cmd('DBG c'),re.I)[1],16)
        w=struct.unpack('>66H',dump('copper.bin',at,132))
        if w[:2]!=(0x100,0x4200) or w[18:26:2]!=(0xe0,0xe2,0xe4,0xe6):return b''
        return dump('front.bpl',w[19]*65536+w[21],40960)
    def wait(fn,seconds=120):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            if fn():return
            time.sleep(.12)
        raise AssertionError('Timed out: '+fn.__name__)
    def key(k):cmd('EVT KEY_'+k+' 1');time.sleep(.25);cmd('EVT KEY_'+k+' 0')
    def image(label,data):
        rgb=[tuple(((pen>>shift)&15)*17 for shift in (8,4,0)) for pen in PALETTE]
        im=Image.new('RGB',(320,256))
        im.putdata([rgb[pixel(data,x,y)] for y in range(256) for x in range(320)])
        im.resize((960,768),Image.Resampling.NEAREST).save(folder/(label+'.png'))
    def pixel(data,x,y):
        return sum(((data[y*160+x//8+40*p]>>(7-x%8))&1)<<p for p in range(4))
    wait(lambda:front()==reference(),240)
    task=val(val(4)+276);cli=val(task+172)*4;node=val(cli+60)*4;hunks=[]
    while node:hunks.append(node+4);node=val(node)*4;assert len(hunks)<=8
    bss,symbols=elf_symbols(folder/'release.elf');base=hunks[elf_hunk_index(folder/'release.elf')]
    def addr(s):return base+symbols[s]-bss
    ram=addr('m')
    cmd('EVT KEY_SHIFT_LEFT 1')
    try:key('D')
    finally:cmd('EVT KEY_SHIFT_LEFT 0')
    wait(lambda:front()==reference(debug=True))
    key('F3')
    for _ in range(14):key('F10')
    key('F5')
    current=14;records=[];geometry={}
    for room,enhanced in ((14,False),(14,True),(16,True),(16,False)):
        if room!=current:
            cmd('EVT KEY_SHIFT_LEFT 1')
            try:key('D')
            finally:cmd('EVT KEY_SHIFT_LEFT 0')
            for _ in range(room-current):key('F10')
            key('F5')
            current=room
        if records and enhanced!=records[-1]['enhanced']:key('F4')
        wanted=reference(enhanced=enhanced,room_select=True,room=room)
        wait(lambda:front()[110*160:]==wanted[110*160:])
        key('RETURN');tap_fire(cmd)
        wait(lambda:val(addr('game_field_active'),1) and val(ram+0x29,1)==room and
             val(addr('source_audio_active'),1) and val(addr('actor_logic_steps'),2)>2 and bool(front()))
        key('P');wait(lambda:not val(addr('source_audio_active'),1));wait(lambda:bool(front()));time.sleep(.3)
        label=f'room{room+1:02}-'+('enhanced' if enhanced else 'classic')
        m=dump(label+'-ram.bin',ram,65536)
        bg=dump(label+'-background.bpl',val(addr('background')),40960)
        visible=front();(folder/(label+'-visible.bpl')).write_bytes(visible)
        word=lambda at:m[at]|m[at+1]<<8
        colors=word(0x480b+room*2);raster=word(0x4833+room*2)
        caps=[];white=[];gold=[];source=[];pens={};checked=0
        for row in range(3,25):
            for col in range(40):
                cell=row*40+col;code=m[0x8c00+cell];tile=code&127
                if row<=4 and tile in (0x43,0x45):kind='caps';caps.append(cell)
                elif tile in (0x2d,0x2e):
                    kind='gold' if m[0xd800+cell]&7==7 else 'white'
                    (gold if kind=='gold' else white).append(cell)
                else:continue
                source.append((cell,code,m[0xd800+cell],m[0xa800+code*8:0xa808+code*8].hex()))
                pens.setdefault(kind,set())
                for dy in range(8):
                    y=row*8+dy;bits=m[0xa800+code*8+dy];band=0
                    for edge in m[raster:raster+3]:
                        if edge==253 or y+51<edge+3:break
                        band+=1
                    for x in range(8):
                        actual=pixel(bg,col*8+x,32+y);pens[kind].add(actual)
                        if not enhanced:
                            pair=bits>>(6-2*(x//2))&3
                            expected=m[0xd800+cell]&7 if pair==3 else m[colors+band*3+pair]&15
                            assert actual==expected,(label,cell,dy,x,actual,expected)
                            checked+=1
        assert len(caps)==8 and len(white)==8,(label,len(caps),len(white))
        assert len(gold)==(8 if room==16 else 0),(label,len(gold))
        if room in geometry:assert geometry[room]==source,'Classic/Enhanced source cells differ'
        else:geometry[room]=source
        if enhanced:
            checked=check_structure(m,bg,True)
            assert 1 not in pens['caps'],'White cap survived'
            assert {0,7,10,15}<=pens.get('gold',{0,7,10,15})
            assert {0,1,3,12}<=pens['white']
            image(label,visible)
        records.append(dict(room=room+1,enhanced=enhanced,cap_halves=len(caps),white_halves=len(white),
                            gold_halves=len(gold),checked_pixels=checked,pens={k:sorted(v) for k,v in pens.items()}))
        print('PASS',label,records[-1],flush=True)
        key('F8');wait(lambda:front()==reference(enhanced=enhanced,room_select=True,room=room))
    report=dict(method=__doc__,checks=records,source_cells_attributes_and_glyphs_unchanged=True,
                tested_adf_sha256=hashlib.sha256((folder/'test.adf').read_bytes()).hexdigest())
    (folder/'result.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path);parser.add_argument('pid',type=int)
    args=parser.parse_args();check(args.folder.resolve(),args.pid)
