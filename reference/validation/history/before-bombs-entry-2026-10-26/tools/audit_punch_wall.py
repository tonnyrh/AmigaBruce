"""R06 wall/fire turns: frozen6502 bytes vs the current host actor adapter.

Controlled starts and joystick sequences, static source room glyphs. No
natural playthrough, room-loop/IRQ or VIC sprite-sprite contact claim.
Run test-session.ps1 first if its source-bound host DLL is absent/stale.
"""
import ctypes,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'.reference/tools/python')]
from verify_source_movement import invoke,SHA
from verify_source_climb import raw_input
from c64_room_model import oracle_contact
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler

def artifact(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def trace(d,source,label,inputs):
    d.bl_audit_prepare(5,60,196,0,0)
    m=[d.bl_c64_read(i) for i in range(65536)]
    m[0x500:0x4300]=source[0x500:0x4300];m[0x5000:0x5800]=source[0x5000:0x5800]
    m[0x95:0x98]=[1,0,0];m[0x9e]=42;m[0xa1]=196;m[0xa4]=0;m[0x7c]=0xa0
    for v in (0xbf,0xce,0xc2,0xcb,0x106,0x4fdb,0xc8,0x4f48,0x4f4e):m[v]=0
    for i in range(132):m[0x4f57+i]=0
    rows=[]
    for step,input in enumerate(inputs):
        pose=m[0x4f4e];px=m[0x9e]*2-24;py=m[0xa1]
        flags,body=oracle_contact(m,px,py,pose)
        m[0xb6]=flags;m[0xa7]=body;m[0x98]=raw_input(input);m[0x9b]=0 if input&16 else 1
        m[0xd4]=source[0x5cbf+pose];m[0xd7]=source[0x5cc0+pose];m[0xdc00]=255
        before=[px,py,m[0xa4],m[0xbf],m[0xce],pose]
        cpu=invoke(m,0x1c5b,(0xffff,0x2f8e))
        assert cpu.pc==0xffff,(label,step,'unexpected source room re-entry')
        invoke(m,0x2780);d.bl_audit_step(input,0)
        a=[d.bl_audit_read(i) for i in range(9)]
        expected=[m[0x9e]*2-24,m[0xa1],m[0xa4],m[0x4f4e]]
        actual=[a[0],a[1],a[2],a[5]]
        assert actual==expected,(label,step,input,flags,actual,expected)
        assert a[8]==flags,(label,step,'contact',a[8],flags)
        assert a[6]==(24 if m[0xbf]==24 else 0),(label,step,'wall state')
        if m[0xbf]==24:assert a[7]==m[0xce],(label,step,'wall counter')
        rows.append(dict(step=step,input=input,contact=flags,before=before,
            source_after=[*expected,m[0xbf],m[0xce]],amiga_after=actual,
            turned=before[2]!=m[0xa4]))
    return dict(label=label,room=6,start=[60,196],facing=0,steps=rows)

def main():
    source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
    assert hashlib.sha256(source).hexdigest()==SHA
    previous=json.loads((ROOT/'reference/analysis/session-walls-2026-10-25/report.json').read_text(encoding='utf-8-sig'))
    for x in previous['source_files']:assert artifact(x['path'])['sha256']==x['sha256'],f"Run test-session.ps1: stale {x['path']}"
    d=ctypes.CDLL(str(ROOT/'.tmp/session-test/session.dll'))
    d.bl_audit_prepare.argtypes=[ctypes.c_long]*5;d.bl_audit_step.argtypes=[ctypes.c_long]*2
    d.bl_audit_read.argtypes=[ctypes.c_long];d.bl_audit_read.restype=ctypes.c_long
    d.bl_c64_read.argtypes=[ctypes.c_long];d.bl_c64_read.restype=ctypes.c_ubyte
    cases=[trace(d,source,*s) for s in [
        ('fire-immediately-at-wall',[1]*12+[16]*16+[0]*8),
        ('release-immediately-at-wall',[1]*12+[0]*24),
        ('punch-before-wall',[1]*11+[0]*4+[16]*12+[0]*8),
        ('punch-clear-of-wall',[1]*9+[0]*4+[16]*12+[0]*8)]]
    fire=cases[0]['steps'][12];release=cases[1]['steps'][12]
    assert fire['turned'] and release['turned']
    assert fire['before'][:3]==[2,196,0] and fire['source_after'][:3]==[8,196,1]
    assert fire['contact']&8 and fire['source_after'][4]==24
    assert fire['source_after']==release['source_after']
    for case in cases[2:]:assert not any(s['turned'] for s in case['steps'])
    out=ROOT/'reference/analysis/punch-wall-2026-10-26';out.mkdir(parents=True,exist_ok=True)
    dis=Disassembler(MPU(memory=list(source)));lines=[]
    for a,end in [(0x1c5b,0x1d6f),(0x1e86,0x1e9a),(0x1ec4,0x1ed8),(0x1f76,0x1fc4),(0x226a,0x22bd)]:
        while a<end:
            n,t=dis.instruction_at(a);lines.append(f'{a:04X} {source[a:a+n].hex(" "):8} {t}');a+=n
    (out/'source-disassembly.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    files=['core/game.c','core/game.h','core/source_wall.c','core/source_wall.h',
        'core/c64_rooms.c','core/c64_rooms.h','core/c64_room_data.h','core/c64_room_programs.h',
        'tests/session_bridge.c','tools/audit_punch_wall.py','tools/c64_room_model.py',
        '.tmp/session-test/session.dll']
    r=dict(status='passed_source_wall_fire_turn_controls',source_sha256=SHA,
        edition_verified=False,natural_playthrough=False,implementation_changed=False,
        source_files=[artifact(p) for p in files],cases=cases,
        limits=['Controlled start; source room geometry already checked by room audit',
            'No source room loops, IRQ or VIC sprite-sprite fight in this actor check',
            'Checks position/facing/pose/contact/recovery; not complete actor-state parity'])
    (out/'report.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print('PASS '+str(sum(len(c['steps']) for c in cases))+' source/Amiga actor steps: fire/release at R06 wall turn identically; clear punches retain facing')
if __name__=='__main__':main()
