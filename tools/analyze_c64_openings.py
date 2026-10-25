"""Source-backed semantic opening checks; no original artwork is exported."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    memory=ROOT/'.reference/c64/work/untrained-memory.bin'
    mem=memory.read_bytes()
    def word(address):return mem[address]+256*mem[address+1]
    def string(index):
        start=word(0x43be+index*2)
        return [(b-32)&127 for b in mem[start:mem.index(160,start)]]
    assert list(mem[0x4cce:0x4cce+7])==[6,6,10,2,2,10,8]
    assert [word(0x4ec4+i*2)+1 for i in [1,2,5,6]]==[0x3679,0x36a6,0x38ab,0x39aa]
    assert mem[0x3682:0x3686]==bytes.fromhex('a530f01f')
    assert mem[0x3686:0x368c]==bytes.fromhex('a52a052b052c')
    assert mem[0x36ae:0x36b2]==bytes.fromhex('a530d04f')
    assert string(15)==[34,34,3,3,3]
    assert string(26)==[0,0,5] and string(25)==[97,5,99]
    facts=json.loads((ROOT/'reference/validation/candidate-rooms.json').read_text())['rooms']
    for room,slot,target,x,y in [(1,1,5,64,50),(2,3,3,8,196),(5,3,1,152,102),(5,0,4,288,81)]:
        door=facts[room]['doors'][slot]
        assert (door['target'],door['entry_x'],door['entry_y'])==(target,x,y)
    lantern_ptr=word(0x4ce2+5*2)
    assert [lantern_ptr+4*i for i in [2,4,6]]==[0x4d81,0x4d89,0x4d91]
    assert mem[0x38e8:0x38f6]==bytes.fromhex('a5300d814df007a5300d894dd01f')
    records=[
        dict(room='R02',trigger='R01/R02/R03 remaining all zero; R07 remaining nonzero',
             source_loop='$3679-$36A5',door=3,cells=[19,20,21],row=12,target='R06',arrival=[64,50],
             opening_strings=[18,17,16,15]),
        dict(room='R03',trigger='R07 remaining zero',source_loop='$36AE-$36CF',
             door=5,cells=[39],row=11,target='R04',arrival=[8,196]),
        dict(room='R06',trigger='R07 remaining zero AND R06 lamp2 or lamp4 collected (zero-based)',
             source_loop='$38E8-$3915',door=5,cells=[35],row=2,target='R02',arrival=[152,102]),
        dict(room='R06',trigger='R06 lamp6 collected (zero-based)',source_loop='$38CB-$38E8',
             door=2,cells=[0],row=11,target='R05',arrival=[288,81]),
    ]
    paths=['.reference/c64/work/untrained-memory.bin','.reference/upstream/bruce/brucelee_ida_dis.txt',
           '.reference/upstream/bruce-lee/README.md','.reference/upstream/bruce-lee/src/scenes.ts',
           '.reference/upstream/bruce-lee/src/sprites/Door.ts','core/rooms.c','core/rooms.h',
           'core/room_data.h','tests/gate_fixture.h','tests/rooms_test.c','tools/analyze_c64_openings.py']
    report=dict(date='2026-10-24',status='passed_static_candidate_source_checks',openings=records,
        tile_contact_source='$2E89/$2F51/$30D4: no direction-button gate for these interior tiles',
        primary_edition_verified=False,native_c64_opening_timing_certified=False,
        implementation_limits=['Amiga opens immediately; original four-stage hatch animation timing is not reproduced yet',
            'Source conditions and destination tables verified; complete natural route and exact tile masks still need play testing',
            'Other dynamic rooms, hazards, moving objects and completion remain open'],
        comparison_repo=dict(url='https://github.com/jzielinski47/bruce-lee',
            commit=subprocess.check_output(['git','-C',str(ROOT/'.reference/upstream/bruce-lee'),'rev-parse','HEAD'],text=True).strip(),
            authority='Atari-based browser reconstruction, not C64 source',
            corroboration='scenes.ts room1 key22 door; Door.ts compares total collected lanterns',
            used_for_c64_destinations=False),
        c64_disassembly_commit=subprocess.check_output(['git','-C',str(ROOT/'.reference/upstream/bruce'),'rev-parse','HEAD'],text=True).strip(),
        source_files=[dict(path=p,sha256=sha(ROOT/p)) for p in paths])
    (ROOT/'reference/validation/candidate-openings.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: candidate R02 hatch, R03 east, R06 return/west conditions and destinations; opening timing remains unmeasured')

if __name__=='__main__':main()
