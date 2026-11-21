"""Check room 12 ceiling spear pixels in an owned normal-ADF WinUAE boot."""
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
    for _ in range(11):key('F10')
    wanted=reference(debug=True,room_select=True,room=11)
    wait(lambda:front()[110*160:]==wanted[110*160:])
    records=[];geometry=[]
    for enhanced in (False,True):
        if enhanced:key('F4')
        key('RETURN');tap_fire(cmd)
        wait(lambda:val(addr('game_field_active'),1) and val(ram+0x29,1)==11 and val(addr('actor_logic_steps'),2)>2)
        key('P');wait(lambda:not val(addr('source_audio_active'),1))
        time.sleep(.3)
        label='enhanced' if enhanced else 'classic'
        m=dump(label+'-ram.bin',ram,65536)
        bg=dump(label+'-background.bpl',val(addr('background')),40960)
        visible=front();(folder/(label+'-visible.bpl')).write_bytes(visible)
        word=lambda at:m[at]|m[at+1]<<8
        colors=word(0x480b+22);raster=word(0x4833+22)
        pixels=0;cells=[];pens=set()
        for row in (3,4):
            for col in range(40):
                cell=row*40+col;code=m[0x8c00+cell]
                if code&127!=0x40:continue
                cells.append(cell)
                for dy in range(8):
                    y=row*8+dy;bits=m[0xa800+code*8+dy]
                    band=0
                    for edge in m[raster:raster+3]:
                        if edge==253 or y+51<edge+3:break
                        band+=1
                    for x in range(8):
                        pair=bits>>(6-2*(x//2))&3
                        if not pair:continue
                        expected=m[0xd800+cell]&7 if pair==3 else m[colors+band*3+pair]&15
                        if enhanced and pair==2:expected=1
                        at=(32+y)*160+col
                        actual=sum(((bg[at+40*p]>>(7-x))&1)<<p for p in range(4))
                        assert actual==expected,(label,cell,dy,x,pair,actual,expected)
                        if pair==2:pens.add(actual);pixels+=1
        assert len(cells)==58 and pixels==1044,(len(cells),pixels)
        geometry.append(bytes(m[0x8c78:0x8cc8]+m[0xd878:0xd8c8]+m[0xaa00:0xaa08]+m[0xae00:0xae08]))
        checked=check_structure(m,bg,True) if enhanced else pixels
        records.append(dict(look=label,ceiling_cells=len(cells),blade_pixels=pixels,blade_inks=sorted(pens),structure_pixels=checked))
        if enhanced:
            rgb=[tuple(((pen>>shift)&15)*17 for shift in (8,4,0)) for pen in PALETTE]
            image=Image.new('RGB',(320,256))
            image.putdata([rgb[sum(((visible[y*160+x//8+40*p]>>(7-x%8))&1)<<p for p in range(4))] for y in range(256) for x in range(320)])
            image.resize((960,768),Image.Resampling.NEAREST).save(folder/'room12-enhanced.png')
        key('F8');wait(lambda:front()==reference(enhanced=enhanced,room_select=True,room=11))
        print('PASS room 12',label,records[-1],flush=True)
    assert geometry[0]==geometry[1]
    report=dict(method=__doc__,checks=records,source_ceiling_geometry_and_attributes_unchanged=True,
                tested_adf_sha256=hashlib.sha256((folder/'test.adf').read_bytes()).hexdigest())
    (folder/'result.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path);parser.add_argument('pid',type=int)
    args=parser.parse_args();check(args.folder.resolve(),args.pid)
