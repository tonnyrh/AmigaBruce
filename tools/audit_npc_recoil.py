"""Controlled original6502 NPC recoil/history controls; no natural-play claim."""
from pathlib import Path
import ctypes
import hashlib
import json

from verify_source_movement import Actor, Wall, FIELDS, MPU, Disassembler, ROOT, SHA

OUT=ROOT/'reference/analysis/npc-recoil-2026-10-25'


def item(path):
    return dict(path=path,sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest())


def execute(memory,entry,actor,accumulator=0,counter=0,stops=(0x02ff,)):
    cpu=MPU(memory=memory,pc=entry);cpu.x=actor;cpu.a=accumulator;cpu.y=counter
    cpu.sp=255;cpu.stPushWord(0x02fe)
    for n in range(100000):
        if cpu.pc in stops:return cpu,n
        cpu.step()
    raise AssertionError(f'Unfinished source at ${cpu.pc:04X}')


def main():
    source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
    assert hashlib.sha256(source).hexdigest()==SHA
    lib=ctypes.CDLL(str(ROOT/'.tmp/source-movement-test/movement.dll'))
    lib.bl_recoil_prepare.argtypes=[ctypes.c_long]*2
    lib.bl_recoil_run.argtypes=[ctypes.c_long]
    lib.bl_move_read.argtypes=[ctypes.c_long];lib.bl_move_read.restype=ctypes.c_long
    lib.bl_source_wall_step.argtypes=[ctypes.POINTER(Wall),ctypes.POINTER(Actor),ctypes.c_long]
    lib.bl_source_wall_step.restype=ctypes.c_long
    helpers=[]
    for actor in range(3):
        for state in (15,19):
            for counter in (3,10):
                for facing in (0,1):
                    for raw_x in (12,13,14,50,150,161,162,163):
                        m=list(source)
                        for i in range(132):m[0x4f57+i]=0
                        m[0x9e+actor]=raw_x;m[0xa1+actor]=150;m[0xa4+actor]=facing
                        m[0xc2+actor]=state;m[0xb6+actor]=1;m[0xc8+actor]=0
                        m[0xd1+actor]=20;m[0x52]=counter
                        cpu,n=execute(m,0x240e,actor,state,counter)
                        pixels=4+(16 if facing else 8) if actor==2 and state==19 and counter==10 else 4
                        lib.bl_recoil_prepare(raw_x*2-24,facing);lib.bl_recoil_run(pixels)
                        after=[lib.bl_move_read(0),lib.bl_move_read(2)]+[lib.bl_move_read(8+d) for d in range(4)]
                        expected=[m[0x9e+actor]*2-24,m[0xa4+actor]]+[m[0x4f57+actor+d*3] for d in range(4)]
                        assert after==expected,(actor,state,counter,facing,raw_x,after,expected)
                        helpers.append(dict(actor=actor,state=state,counter=counter,facing=facing,
                            raw_x=raw_x,pixels=pixels,after=after,source_instructions=n))
    # Reuse the independently generated500 histories for both source NPC IDs.
    # The kernel's moves array is per actor, whereas C64 records are interleaved.
    histories=[]
    original=json.loads((ROOT/'reference/analysis/movement-audit-2026-10-25/wall-report.json').read_text())
    for actor in (1,2):
        for case in original['results']:
            a=Actor(**case['input']);w=Wall();m=list(source)
            m[0xb6+actor]=case['contact'];m[0xc8+actor]=0;m[0x29]=0
            for k,address in FIELDS.items():m[address+actor]=getattr(a,k)
            for i,row in enumerate(case['history']):
                w.moves[i][:]=row
                for d,value in enumerate(row):m[0x4f57+i*12+d*3+actor]=value
            result=lib.bl_source_wall_step(ctypes.byref(w),ctypes.byref(a),case['contact'])
            cpu,n=execute(m,0x1c5b,actor,stops=(0x02ff,0x1d6f,0x2f8e))
            expected_result=0 if cpu.pc==0x1d6f else 2 if cpu.pc==0x2f8e else 1
            assert result==expected_result,(actor,case['name'],'dispatch')
            for k,address in FIELDS.items():assert getattr(a,k)==m[address+actor],(actor,case['name'],k)
            expected=[[m[0x4f57+i*12+d*3+actor] for d in range(4)] for i in range(11)]
            assert [list(row) for row in w.moves]==expected,(actor,case['name'],'history')
            if result==2:assert m[0x51]==0,'The source emergency re-entry explicitly selects Bruce'
            histories.append(dict(actor=actor,fixture=case['name'],dispatch=result,
                after={k:getattr(a,k) for k in FIELDS},source_instructions=n))
    OUT.mkdir(parents=True,exist_ok=True)
    dis=Disassembler(MPU(memory=list(source)));lines=[]
    for lo,hi in ((0x1c5b,0x1d6f),(0x240e,0x2509),(0x2f8e,0x2fc2)):
        at=lo
        while at<hi:
            length,text=dis.instruction_at(at);lines.append(f'{at:04X} {source[at:at+length].hex(" "):<9} {text}');at+=length
    (OUT/'source-disassembly.txt').write_text('\n'.join(lines)+'\n')
    report=dict(status='passed_original6502_recoil_helpers_and_npc_history',
        source_sha256=SHA,edition_verified=False,natural_playthrough=False,
        helpers_compared=len(helpers),npc_histories_compared=len(histories),
        source_emergency_reentry_retained=True,helpers=helpers,histories=histories,
        source_files=[item(p) for p in ('core/combat.c','core/game.c','core/game.h',
            'core/source_wall.c','core/source_wall.h','tests/movement_bridge.c',
            'tests/npc_recoil_fixture.h','test-source-movement.ps1','tools/audit_npc_recoil.py',
            'reference/analysis/movement-audit-2026-10-25/wall-report.json')],
        limitations=['Contact/history inputs are controlled, not natural play',
                     'Native pair contact, pose projection and full NPC actor/exit/life logic remain partial'])
    (OUT/'source-controls.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {len(helpers)} original6502 recoil/boundary/history helpers and {len(histories)} NPC wall histories')


if __name__=='__main__':main()
