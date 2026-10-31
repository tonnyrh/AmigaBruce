"""Inspect actual published sprite DMA descriptors in an owned normal probe.

The PNG is a software reconstruction from live bitplanes plus sprite DMA;
it is not an emulator-video screenshot. Device appearance is checked separately.
"""
import argparse,hashlib,json,re,struct,time
from pathlib import Path
from PIL import Image
from winuae_ipc import command
from capture_paula_stream import elf_symbols
from audit_vic_native_kernels import sections
from audit_native_menu_publication import reference
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/hardware-bruce-2026-10-31'
def main():
    p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--version',default='v5');p.add_argument('--start',action='store_true');p.add_argument('--room',type=int,default=12);p.add_argument('--samples',type=int,default=5);p.add_argument('--right',action='store_true');p.add_argument('--fire',action='store_true');p.add_argument('--label',default='native-display');a=p.parse_args()
    runtime=ROOT/f'.tmp/hardware-bruce-{a.version}-ui';out=BASE/a.version/a.label;out.mkdir(exist_ok=True)
    log=runtime/'winuaebootlog.txt'
    if not log.exists():log=ROOT/'.tmp/session-ui/winuaebootlog.txt'
    # WinUAE may keep its boot log beside the executable. Every command
    # still verifies the pipe's server PID before reading or sending input.
    pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",log.read_text(errors='replace'))[-1]
    def cmd(q):return command(pipe,q,expected_pid=a.pid)
    def read(at,n):
        if n>16:
            path=runtime/f'read-{at:x}-{n:x}.bin';assert 'Wrote ' in cmd(f'DBG S {path} {at:x} {n:x}');return path.read_bytes()
        reply=cmd(f'DBG m {at:x} {(n+15)//16:x}');data=bytearray()
        for line in reply.splitlines():
            m=re.match(r'^[0-9A-Fa-f]{8}\s+((?:[0-9A-Fa-f]{4}\s+){1,8})',line)
            if m:data.extend(bytes.fromhex(m[1]))
        assert len(data)>=n,(at,n,reply);return bytes(data[:n])
    def word(at):return int.from_bytes(read(at,2),'big')
    def long(at):return int.from_bytes(read(at,4),'big')
    elf=BASE/a.version/'sprite/out/bruce_amiga.elf';_,ss=sections(elf);_,syms=elf_symbols(elf);seg=[dict(ss)[n] for n in ['.text','.rodata','.data','.bss']]
    def modules():
        task=long(long(4)+276);node=long(long(task+172)*4+60)*4;hunks=[]
        while node and len(hunks)<5:hunks.append(node+4);node=long(node)*4
        assert len(hunks)==4;return hunks
    def copper():
        q=cmd('DBG c');return int(re.search(r'COP1LC: \$([0-9a-fA-F]+)',q)[1],16)
    def registers(raw):
        ws=struct.unpack('>'+str(len(raw)//2)+'H',raw);regs={}
        for i in range(0,len(ws)-1,2):
            if ws[i:i+2]==(65535,65534):return regs,(i+2)*2
            regs[ws[i]]=ws[i+1]
        raise AssertionError('Copper list has no terminator')
    hunks=[];deadline=time.monotonic()+180
    while time.monotonic()<deadline:
        try:
            hunks=modules();cp=copper();regs,_=registers(read(cp,512));front=(regs[0xe0]<<16)|regs[0xe2]
            if read(front,40960)==reference():break
            if not a.start:break
        except (AssertionError,KeyError,IndexError):pass
        time.sleep(1)
    else:raise AssertionError('Complete normal menu did not appear')
    def addr(name):
        v=syms[name];i=next(i for i,s in enumerate(seg) if s[3]<=v<s[3]+s[5]);return hunks[i]+v-seg[i][3]
    def key(k):cmd('EVT KEY_'+k+' 1');time.sleep(.35);cmd('EVT KEY_'+k+' 0');time.sleep(.35)
    if a.start:
        cmd('EVT KEY_SHIFT_LEFT 1');key('D');cmd('EVT KEY_SHIFT_LEFT 0')
        for k in ['F1','F2']+['F4']*(a.room-1)+['RETURN']:key(k)
        time.sleep(10)
    manifest=json.loads((ROOT/'assets/c64/sprites-v1/manifest.json').read_text());frames=manifest['frames']
    palette=[0x000,0xfff,0x833,0x7cc,0x84a,0x6a4,0x338,0xcc7,0x852,0x541,0xb77,0x444,0x777,0xaf9,0x78c,0xbbb]
    def rgb(v):return tuple(((v>>k)&15)*17 for k in [8,4,0])
    samples=[];pause_checks=[]
    try:
        if a.right:cmd('EVT JOY2_RIGHT 1')
        if a.fire:cmd('EVT JOY2_FIRE_BUTTON 1')
        for sample in range(a.samples):
            paused=False
            try:
                cmd('EVT SPC_PAUSE 1');cmd('EVT SPC_PAUSE 0');paused=True;time.sleep(.06)
                cpu=cmd('DBG r');time.sleep(.05);assert cmd('DBG r')==cpu;pause_checks.append(True)
                assert read(addr('bruce_hw_game'),1)==b'\1' and not read(addr('game_field_loading'),1)[0]
                custom=cmd('DBG c')
                dma=int(re.search(r'DMACON: \$([0-9a-fA-F]+)',custom)[1],16)
                assert word(addr('source_fault'))==0 and dma&0x20
                cp=copper();cps=struct.unpack('>2I',read(addr('copper'),8));buffer=cps.index(cp)
                raw=read(cp,1024);regs,list_bytes=registers(raw[:512]);assert list_bytes<=512
                assert regs[0x104]&0x38==0x20,'Normal playfield must be behind all sprite pairs'
                ptrs=[(regs[0x120+ch*4]<<16)|regs[0x122+ch*4] for ch in range(8)]
                null=cp+256+8*92;assert raw[992:996]==b'\0'*4
                assert list_bytes==252 and regs[0x098]==0xf000
                actors=[];errors=0
                for kind,first,count in [(0,3,3),(1,6,2),(2,0,3)]:
                    active=[ch for ch in range(count) if ptrs[first+ch]!=null]
                    if not active:continue
                    key_index=word(addr('bruce_hw_key')+buffer*6+kind*2)
                    assert kind*70<=key_index<(kind+1)*70
                    f=frames[key_index];left,top,right,bottom=f['bounds'];height=bottom-top;columns=(right-left+15)//16
                    assert active==list(range(columns))
                    expected=Image.open(ROOT/'assets/c64/sprites-v1'/f['file']).convert('RGBA')
                    decoded=Image.new('RGBA',(48,height));positions=[];actor_errors=0
                    for ch in range(count):
                        channel=first+ch
                        assert ptrs[channel]==(cp+256+channel*92 if ch<columns else null)
                        if ch>=columns:continue
                        sp=struct.unpack('>46H',raw[256+channel*92:256+(channel+1)*92]);pos,ctl=sp[:2]
                        x=(((pos&255)<<1)|(ctl&1))-128;y=((pos>>8)|((ctl&4)<<6))-44
                        stop=(ctl>>8)|((ctl&2)<<7)
                        assert not ctl&128 and stop==y+44+height and sp[2+height*2:4+height*2]==(0,0)
                        if ch:assert (x,y)==(positions[0][0]+ch*16,positions[0][1])
                        positions.append((x,y))
                        for row in range(height):
                            for bit in range(16):
                                pen=(1 if sp[2+row*2]&(0x8000>>bit) else 0)|(2 if sp[3+row*2]&(0x8000>>bit) else 0)
                                if pen:decoded.putpixel((ch*16+bit,row),(*rgb(regs[0x180+2*(17+(channel//2)*4+pen-1)]),255))
                    for row in range(height):
                        for col in range(48):
                            want=expected.getpixel((left+col,top+row)) if left+col<48 else (0,0,0,0)
                            actor_errors+=decoded.getpixel((col,row))!=want
                    assert actor_errors==0,(kind,key_index,actor_errors)
                    errors+=actor_errors
                    actors.append(dict(kind=kind,actor=f['actor'],frame_index=key_index,source_pose=f['base_pose'],facing=f['facing'],columns=columns,position=positions[0],pixel_errors=actor_errors,decoded=decoded))
                front=(regs[0xe0]<<16)|regs[0xe2];bitmap=read(front,40960);pal=list(palette);pal[15]=regs[0x19e]
                image=Image.new('RGB',(320,256))
                for y in range(256):
                    for x in range(320):
                        color=sum(1<<plane for plane in range(4) if bitmap[y*160+plane*40+x//8]&(128>>(x&7)))
                        image.putpixel((x,y),rgb(pal[color]))
                for actor in sorted(actors,key=lambda q:{1:0,0:1,2:2}[q['kind']]):
                    image.paste(actor['decoded'],actor['position'],actor['decoded'])
                prefix=out/f'sample{sample}';(prefix.with_suffix('.copper')).write_bytes(raw);prefix.with_suffix('.bpl').write_bytes(bitmap);image.resize((640,512),Image.Resampling.NEAREST).save(prefix.with_suffix('.png'))
                samples.append(dict(source_latch_ram=read(addr('m')+0xd01e,1)[0],source_latch_phase='Paused publication snapshot, not the source read/clear phase',buffer=buffer,actors=[{k:v for k,v in q.items() if k!='decoded'} for q in actors],pixel_errors=errors,dma_enabled=True,copper_list_bytes=list_bytes,game_room=read(addr('m')+0x29,1)[0]+1,custom=custom,cpu=cpu))
            finally:
                if paused:cmd('EVT SPC_PAUSE 1');cmd('EVT SPC_PAUSE 0')
            time.sleep(.15)
    finally:
        if a.right:cmd('EVT JOY2_RIGHT 0')
        if a.fire:cmd('EVT JOY2_FIRE_BUTTON 0')
    def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    r=dict(status='passed_all_actor_native_sprite_dma_descriptors',elf=item(elf),samples=samples,pause_stability_checks=pause_checks,joystick_right=a.right,joystick_fire=a.fire,source_rule_changed=False,natural_playthrough=False,original_raster_certified=False,
      method='Owned normal hardware-sprite probe; paused Copper pointers, actual Chip DMA words and active DMA flag; pixel comparison with original ripped PNG; software composited preview, device screenshot separate',artifacts=[item(p) for p in out.iterdir() if p.is_file() and p.name!='report.json'])
    (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS live published DMA sprite data:',len(samples),'samples, zero pixel errors')
if __name__=='__main__':main()
