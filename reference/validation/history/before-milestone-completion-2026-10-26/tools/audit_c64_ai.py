"""Verify Kage/Yamo decisions in frozen machine code, separately from the adapter.

CPU inputs/contact/clock/mode are injected. Random-memory READ DATA may be
injected at $1163; instructions are never patched by this harness. The real
source may self-modify its table operands. Adapter physics/doors are stubs:
its recorded decision request is compared, not a natural game trajectory.
"""
from pathlib import Path
import argparse
import ctypes
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler

SHA = '092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
OUT = ROOT/'reference/analysis/ai-audit-2026-10-25'
REPORT = OUT/'report.json'
SOURCE = ROOT/'.reference/c64/work/untrained-memory.bin'
REG = dict(x=0x9e, y=0xa1, facing=0xa4, state=0xbf, previous=0xc2,
           counter=0xce, health=0xd1, active=0x95, wait=0x106)
ROWS = []


def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))


def identities(items):
    for item in items:
        assert digest(ROOT/item['path']) == item['sha256'], item['path']


def memory():
    m = list(SOURCE.read_bytes())
    m[0x0104] = 1
    m[0x42ca] = m[0x40] = m[0x88] = 0
    m[0x87] = m[0x60] = m[0x65] = 0
    m[0x16], m[0x17] = 0, 0x60  # Controlled memory-read data lives outside code.
    m[0x8a:0x93] = [0]*9
    m[0x4f57:0x4fe1] = [0]*(0x4fe1-0x4f57)
    for i in range(3):
        m[0x95+i] = 1 if i == 0 else (0x81 if i == 1 else 0x41)
        m[0x9e+i], m[0xa1+i] = 80, 150
        m[0xa4+i] = 1
        m[0xbf+i] = m[0xc2+i] = m[0xce+i] = m[0x106+i] = 0
        m[0xd1+i], m[0xb6+i], m[0x9b+i], m[0x98+i] = 20, 1, 1, 15
        m[0xcb+i] = 6
    for address in (0xeb00, 0xef70, 0xf070): m[address] = 0
    return m


def execute(m, entry, actor=0, stop=0x02ff, random_data=(), registers=None):
    cpu = MPU(memory=m, pc=entry)
    cpu.x, cpu.sp = actor, 0xff
    cpu.stPushWord(0x02fe)
    trace, random_reads = set(), []
    for count in range(100000):
        if cpu.pc == stop:
            if registers is not None:registers.update(a=cpu.a,x=cpu.x,y=cpu.y,p=cpu.p)
            return trace, count, random_reads
        trace.add(cpu.pc)
        if cpu.pc == 0x1163:
            address = (((m[0x17] << 8) | m[0x16])+cpu.y) & 65535
            assert 0x6000 <= address < 0x6200
            value = random_data[min(len(random_reads), len(random_data)-1)] if random_data else 0
            m[address] = value
            random_reads.append(dict(address=f'${address:04X}', value=value))
        cpu.step()
    raise AssertionError(f'CPU did not finish ${entry:04X}; PC=${cpu.pc:04X}')


def actor_values(m, actor): return {key:m[base+actor] for key,base in REG.items()}


def motion(actor=1, dx=10, dy=0, facing=1, state=20, counter=20,
           contact=1, age=0, round_=0, px=80, py=150, wait=0):
    m = memory()
    m[0x9e], m[0xa1] = px, py
    m[0x9e+actor], m[0xa1+actor] = px+dx, py+dy
    m[0xa4+actor], m[0xbf+actor], m[0xc2+actor] = facing, state, state
    m[0xce+actor], m[0xb6+actor], m[0x106+actor] = counter, contact, wait
    m[0x88], m[0x40] = age, round_
    before = actor_values(m, actor)
    trace, count, _ = execute(m, 0x1c5b, actor)
    intent = ('waiting' if wait else 'retreat' if 0x2327 in trace else
              'punch_attempt' if 0x238f in trace else 'kick' if 0x23a8 in trace else
              'sai' if 0x23c4 in trace else 'face_wait' if 0x2366 in trace else
              'turn' if 0x23dd in trace else 'fall' if 0x1dc4 in trace else
              'retreat_move' if (0x23f7 in trace or 0x23ff in trace) else
              'walk' if 0x2352 in trace else 'other')
    result = dict(group='actor', inputs=dict(actor=actor, dx_half_pixels=dx,
                  dy_pixels=dy, state=state, counter=counter, contact=contact,
                  age_0088=age, round_0040=round_, facing=facing, px=px, py=py, wait=wait),
                  before=before, after=actor_values(m, actor), intent=intent,
                  moved=[m[0x4f57+3*d+actor] for d in range(4)], instructions=count)
    ROWS.append(result)
    return result


def adapter(dll, r):
    i = r['inputs']
    dll.bl_ai_adapter(i['actor'], i['px']+i['dx_half_pixels'], i['py']+i['dy_pixels'],
                      i['px'], i['py'], i['facing'], i['state'], i['counter'], 0)
    ai, timer, sai, attack, facing, request, calls = [dll.bl_ai_adapter_read(j) for j in range(7)]
    intent = ('sai' if sai else 'kick' if attack == 2 else
              'punch_attempt' if request & 16 else 'retreat' if ai == 2 and i['state'] != 21 else
              'retreat_move' if ai == 2 else 'face_wait' if ai == 0 else
              'turn' if i['state'] == 21 and not calls else 'walk' if request & 3 else 'other')
    return dict(intent=intent, timer=timer, facing=facing, input_request=request, movement_calls=calls)


def verify():
    r = read(REPORT)
    assert digest(SOURCE) == r['source_sha256'] == SHA
    identities(r['source_files']+r['reviewed_sources']+r['artifacts'])
    assert r['fixture_count'] == len(r['fixtures'])
    assert not r['edition_verified'] and not r['natural_playthrough']
    assert not r['full_amiga_ai_parity'] and not r['engine_modified']
    assert r['adapter_ground_decision_checks'] == 588
    assert r['adapter_ground_decision_differences'] == 0
    assert r['adapter_differences'], 'The audit must retain known adapter gaps'
    evidence=ROOT/'docs/parity/evidence/AI-AUDIT-0001.json'
    identities(read(evidence)['artifacts'])
    print(f"VERIFIED {r['fixture_count']} actual6502 AI fixtures;588 adapter ground choices match; "
          f"{len(r['adapter_differences'])} retained adapter differences. No complete AI/physics parity")


def record_evidence(report):
    files=['reference/analysis/ai-audit-2026-10-25/report.json',
           'reference/analysis/ai-audit-2026-10-25/source-disassembly.txt',
           'docs/C64_AI.md','tools/audit_c64_ai.py','tests/ai_adapter_bridge.c','test-c64-ai.ps1']
    result=dict(id='AI-AUDIT-0001',date='2026-10-25',status='candidate_code_derived_partial',
                full_original_parity=False,engine_modified=False,fixture_count=report['fixture_count'],
                adapter_ground_decisions=report['adapter_ground_decision_checks'],
                summary=f"Actual6502 Kage/Yamo AI audit:{report['fixture_count']} controlled fixtures,"
                        f"{report['adapter_ground_decision_checks']} ordinary ground choices agree with isolated adapter requests;"
                        f"{len(report['adapter_differences'])} retained ordinary wait/support discrepancies. "
                        'Spawn/entry/clock/door integration is covered separately by SPAWN-AUDIT-0001. '
                        'This audit changes no executable; no full physics, natural-play or native AI certification.',
                artifacts=[dict(path=p,sha256=digest(ROOT/p),size_bytes=(ROOT/p).stat().st_size) for p in files])
    (ROOT/'docs/parity/evidence/AI-AUDIT-0001.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')


def main():
    assert digest(SOURCE) == SHA
    identity = read(ROOT/'.tmp/c64-ai-test/compiled-sources.json')
    identities(identity)
    dll = ctypes.CDLL(str(ROOT/'.tmp/c64-ai-test/ai.dll'))
    dll.bl_ai_adapter.argtypes = [ctypes.c_long]*9
    dll.bl_ai_adapter_read.argtypes = [ctypes.c_long]
    dll.bl_ai_adapter_read.restype = ctypes.c_long
    differences, ground_checks = [], 0
    # Boundaries in the actual state20 branch, including signed saturated axes.
    for who in (1, 2):
        for dx in (-48,-33,-32,-19,-18,-12,-11,-10,-5,-4,0,4,5,10,11,12,18,19,32,33,48):
            for dy in (-49,-16,-15,0,15,16,49):
                for facing in (0,1):
                    for contact in (0,1,4,5):
                        r = motion(who,dx,dy,facing,contact=contact)
                        if contact == 1:
                            a = adapter(dll,r);r['adapter_decision'] = a
                            ground_checks += 1
                            assert a['intent'] == r['intent'], ('ground choice',r)
                            if r['intent'] == 'retreat':assert a['timer'] == r['after']['counter'],r
    assert ground_checks == 588
    # Face-and-wait / post-sai / post-punch / retreat end are distinct state paths.
    for who in (1,2):
        for age in (0,24,25,31,32,128):
            for round_ in (0,1):
                expected = 1 if age>=32 or (age<25 and round_) else 3 if age>=25 else 6
                for state,counter,dy in ((20,20,16),(17,1,0),(22,1,0)):
                    r=motion(who,10,dy,0,state,counter,age=age,round_=round_)
                    assert r['after']['state']==0 and r['after']['counter']==expected,r
                    if state==20:
                        a=adapter(dll,r);r['adapter_decision']=a
                        if a['timer']!=expected:differences.append(dict(rule='AI-WAIT',fixture=len(ROWS)-1,source=expected,adapter=a['timer']))
        for counter in (1,2,5,20):
            for contact in (0,1,4,5):
                r=motion(who,10,0,0,21,counter,contact)
                a=adapter(dll,r);r['adapter_decision']=a
                if r['intent']!=a['intent']:
                    differences.append(dict(rule='AI-RETREAT-SUPPORT',fixture=len(ROWS)-1,source=r['intent'],adapter=a['intent']))
        # Timer zero is a dispatch boundary, not another state20/21 AI choice.
        for state in (20,21):
            r=motion(who,10,0,0,state,0)
            assert r['after']['state']==0,r
        # $232D's zero result falls into the add15 path at $2332.
        r=motion(who,-2,0,1,px=15)
        assert r['intent']=='retreat' and r['after']['counter']==5,r
        a=adapter(dll,r);r['adapter_decision']=a
        assert a['timer']==13
        differences.append(dict(rule='AI-RETREAT-ZERO-TARGET',fixture=len(ROWS)-1,source=5,adapter=13))
    # State22 duration: the adapter now uses the extracted counter/history
    # body. Background/physics are still stubs in this decision-only audit.
    for who in (1,2):
        for counter in (1,7,8,12,19):
            r=motion(who,10,0,0,22,counter)
            assert r['after']['state']==(0 if counter==1 else 22),r
            assert r['after']['counter']==(6 if counter==1 else counter-1),r
            if who==2:
                a=adapter(dll,r);r['adapter_decision']=a
                if counter==1:
                    assert a['intent']=='face_wait' and a['timer']==6,a
                else:assert a['intent']=='sai' and a['timer']==counter-1,a
    # Promotion helper and its early RETURN after processing a finished kick.
    for who in (1,2):
        for flags in (0,1,0x41,0x81,0xc1):
            for mode in (0,1):
                for health in (20,127,128,255):
                    m=memory();m[0x95:0x98]=[0,0,0];m[0x95+who]=flags
                    m[0xd1+who]=health;m[0x42ca]=mode
                    trace,count,_=execute(m,0x2d7c)
                    qualifies=health<128 and (((flags&0x81)==0x81 and not mode) or (flags&0x41)==0x41)
                    assert m[0xbf+who]==(20 if qualifies else 0)
                    ROWS.append(dict(group='promotion',inputs=dict(actor=who,flags=flags,mode=mode,health=health),
                                     after=actor_values(m,who),instructions=count))
    for age in (0,24,25,31,32,128):
        for round_ in (0,1):
            for prev in (12,13):
                m=memory();m[0x97]=0;m[0x95]=0x41;m[0xc2+1]=prev;m[0x88],m[0x40]=age,round_
                _,count,_=execute(m,0x2d7c)
                expected=1 if age>=32 or (age<25 and round_) else 3 if age>=25 else 24
                assert m[0xbf+1]==0 and m[0xce+1]==expected
                assert m[0xbf]==0 and m[0xce]==0, 'Post-kick path returns before injected lower auto actor'
                ROWS.append(dict(group='post_kick_global_return',inputs=dict(actor=1,lower_actor0_injected_auto_flags=0x41,
                                 age_0088=age,round_0040=round_,previous=prev),
                                 after=[actor_values(m,i) for i in range(3)],instructions=count))
                if expected!=24:differences.append(dict(rule='AI-POST-KICK-WAIT',fixture=len(ROWS)-1,source=expected,adapter=24))
    # $1614-$1626 clock prefix. No IRQ/raster emulation is implied.
    for active in (0,1):
        for paused in (0,128):
            for low in (254,255):
                for high in (0,24,25,31,32,127,128,255):
                    m=memory();m[0x104],m[0x105],m[0x87],m[0x88]=active,paused,low,high
                    _,count,_=execute(m,0x1614,stop=0x1628)
                    running=bool(active and not paused)
                    expected_low=(low+1)&255 if running else low
                    expected_high=high+1 if running and low==255 and high<128 else high
                    assert m[0x87:0x89]==[expected_low,expected_high]
                    ROWS.append(dict(group='room_clock_prefix',inputs=dict(game_active=active,pause_byte=paused,low=low,high=high),
                                     after=m[0x87:0x89],instructions=count))
    # Initial room counters and later entry/removal wait tables.
    source = SOURCE.read_bytes()
    tables={f'${a:04X}':list(source[a:a+20]) for a in (0x130b,0x131f,0x1333,0x1347,0x135b,0x136f,0x4bae,0x4bc2,0x4bd6,0x4bea,0x4c9e)}
    for room in range(20):
        for round_ in (0,1):
            for mode in (0,1):
                m=memory();m[0x29],m[0x40],m[0x42ca]=room,round_,mode
                _,count,_=execute(m,0xa2a,stop=0xa6b)
                e=[3,3] if round_ else [source[0x130b+room],source[0x1347+room]]
                if mode:e[1]=8
                assert m[0x5d:0x5f]==e
                assert m[0x7a]==source[0x4c9e+room]
                ROWS.append(dict(group='initial_timers',inputs=dict(room=room,round_0040=round_,mode=mode),after=e,
                                 spawn_service_disabled=m[0x7a],instructions=count))
        for who in (1,2):
            for age in (0,24,25,31,32,128):
                for round_ in (0,1):
                    for mode in (0,1):
                        m=memory();m[0x29],m[0x88],m[0x40],m[0x42ca]=room,age,round_,mode
                        _,count,_=execute(m,0xd42,who)
                        base=48 if who==1 and mode else source[(0x135b if who==1 else 0x131f)+room]
                        expected=3 if age>=32 or (age<25 and round_) else base//2 if age>=25 else base
                        value=m[0x5e if who==1 else 0x5d]
                        assert value==expected,(room,who,age,round_,mode,value,expected)
                        ROWS.append(dict(group='reentry_timer',inputs=dict(room=room,actor=who,age_0088=age,round_0040=round_,mode=mode),
                                         after=value,instructions=count))
        for who in (1,2):
            for age in (0,25,32):
                m=memory();m[0x29],m[0x88]=room,age
                _,count,_=execute(m,0x3001,who)
                base=source[(0x135b if who==1 else 0x131f)+room]
                expected=3 if age>=32 else base//2 if age>=25 else base
                assert m[0x95+who]&1==0
                assert m[0x5e if who==1 else 0x5d]==expected
                ROWS.append(dict(group='remove_and_reset_timer',inputs=dict(room=room,actor=who,age_0088=age),
                                 after=actor_values(m,who),timer=expected,instructions=count))
    # Shared direction/edge gate only: a matching object cell remains required.
    for who in (1,2):
        for raw_x in (161,162,163):
            for right_count in (0,1):
                m=memory();m[0x29],m[0x9e+who],m[0xa1+who]=0,raw_x,98
                m[0x4f60+who]=right_count;regs={}
                _,count,_=execute(m,0x30d4,who,registers=regs)
                accepted=not bool(regs['p']&1)
                assert accepted==bool(raw_x>=162 and right_count)
                ROWS.append(dict(group='r01_east_gate',inputs=dict(actor=who,raw_x=raw_x,right_count=right_count),
                                 accepted=accepted,instructions=count))
    # Original spawn path incl saved arrival/health, actual indirect memory
    # reader and the Ninja branch's shared $136F SIGN despite gate at $1333.
    for room in range(20):
        for who in (1,2):
            for first in (0,191,192,255):
                for second in (0,1):
                    for saved in (False,True):
                        m=memory();m[0x29]=room
                        if saved:m[0x8a+who],m[0x8c+who],m[0x8e+who]=34,151,6
                        trace,count,reads=execute(m,0xcd5 if who==1 else 0xdf8,who,random_data=(first,second))
                        if saved:expected=[34,151,6]
                        else:
                            gate=source[(0x136f if who==1 else 0x1333)+room]
                            alternate=(bool(source[0x136f+room]&128) if gate and first<192 else
                                       bool((second if gate else first)&1))
                            expected=[source[(0x4bd6 if alternate else 0x4bae)+room],
                                      source[(0x4bea if alternate else 0x4bc2)+room],20 if who==1 else 7]
                        assert [m[0x9e+who],m[0xa1+who],m[0xd1+who]]==expected,(room,who,first,second,saved,expected,actor_values(m,who))
                        assert m[0xbf+who]==(16 if who==1 else 0)
                        assert m[0xce+who]==(10 if who==1 else 16)
                        ROWS.append(dict(group='spawn',inputs=dict(room=room,actor=who,random_read_values=[first,second],saved=saved),
                                         after=actor_values(m,who),random_reads=reads,instructions=count))
    # Actor updates after entry; collisions are deliberately held at class1.
    # The first such update occurs in the same main iteration as spawning.
    for who in (1,2):
        for cross_before_yamo_turn in (False,True):
            m=memory();m[0x9e],m[0xa1]=26,196;m[0x95+(3-who)]=0
            execute(m,0xcd5 if who==1 else 0xdf8,who,random_data=(0,))
            stages=[dict(actor_updates=0,**actor_values(m,who))]
            for update in range(1,29):
                if cross_before_yamo_turn and update==10:m[0x9e]=160
                execute(m,0x2d7c);execute(m,0x1c5b,who)
                stages.append(dict(actor_updates=update,**actor_values(m,who)))
            first=next(s['actor_updates'] for s in stages if s['x']!=stages[0]['x'])
            assert first==(28 if who==1 else 17),(who,stages)
            if who==1:
                assert stages[0]['facing']==1 and stages[9]['state']==16 and stages[9]['counter']==1
                assert stages[10]['state']==18 and stages[10]['counter']==16
                assert stages[10]['facing']==int(cross_before_yamo_turn)
            ROWS.append(dict(group='entry_phases',inputs=dict(actor=who,player_crosses_at_update10=cross_before_yamo_turn),
                             first_moving_actor_update=first,stages=stages))
    # $0DB1 may postpone Ninja16 when Yamo is active and early room-time.
    for age in (0,24,25,31,32):
        for round_ in (0,1):
            for mode in (0,1):
                for yamo in (0,1):
                    for data in (24,25,255):
                        m=memory();m[0x5d]=0;m[0x95+2]=0;m[0x95+1]=yamo
                        m[0x88],m[0x40],m[0x42ca]=age,round_,mode
                        trace,count,reads=execute(m,0xdb1,random_data=(data,))
                        delay=bool(yamo and not round_ and not mode and age<25 and data>=25)
                        assert bool(m[0x97]&1)==(not delay)
                        if delay:assert m[0x5d]==16
                        ROWS.append(dict(group='ninja_delay',inputs=dict(age_0088=age,round_0040=round_,mode=mode,yamo_active=yamo,random_read=data),
                                         delayed=delay,after=actor_values(m,2),timer=m[0x5d],random_reads=reads,instructions=count))
    # Source helper is a real memory reader with an incremented pointer,
    # not an RNG. Demo mode returns1 without touching that pointer.
    for game_active in (0,1):
        m=memory();m[0x104]=game_active
        regs={};_,count,reads=execute(m,0x1159,random_data=(193,),registers=regs)
        assert m[0x16]==game_active
        assert regs['a']==(193 if game_active else 1)
        ROWS.append(dict(group='memory_reader',inputs=dict(game_active=game_active),pointer_low=m[0x16],returned_a=regs['a'],reads=reads,instructions=count))
    OUT.mkdir(parents=True,exist_ok=True)
    dis=Disassembler(MPU(memory=list(source)));lines=[]
    ranges=((0xa2a,0xa83),(0xb8e,0xe21),(0x1131,0x1166),(0x1614,0x1628),
            (0x179e,0x17e2),(0x1bc2,0x1c39),(0x1c5b,0x1c9d),
            (0x1d6f,0x1dcc),(0x1e6d,0x1e9a),(0x1eae,0x1ed8),
            (0x1f7e,0x1fc4),(0x2235,0x240e),(0x24f4,0x2509),
            (0x2d55,0x2e29),(0x2f8e,0x2fc5),(0x3001,0x304b),(0x30d4,0x310c))
    for lo,hi in ranges:
        p=lo
        while p<hi:
            n,t=dis.instruction_at(p);lines.append(f'{p:04X} {source[p:p+n].hex(" "):<9} {t}');p+=n
        lines.append('')
    dispath=OUT/'source-disassembly.txt';dispath.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    identities(identity)
    reviewed=[dict(path=p,sha256=digest(ROOT/p)) for p in ('core/game.c','core/rooms.c','core/c64_rooms.c')]
    report=dict(date='2026-10-25',status='verified_scoped_actual6502_ai_and_adapter_differences',
                source_sha256=SHA,edition_verified=False,natural_playthrough=False,
                engine_modified=False,full_amiga_ai_parity=False,adapter_physics_stubbed=True,
                fixture_count=len(ROWS),fixtures=ROWS,adapter_ground_decision_checks=ground_checks,
                adapter_ground_decision_differences=0,adapter_differences=differences,
                tables=tables,source_files=identity,reviewed_sources=reviewed,
                artifacts=[dict(path=str(p.relative_to(ROOT)).replace('\\','/'),sha256=digest(p))
                           for p in (dispath,ROOT/'.tmp/c64-ai-test/ai.dll')],
                limitations=['Contacts, modes, timers and actor states are injected; no VIC/IRQ or natural-play replay',
                             'Existing adapter decisions use recorded movement/door stubs; full physics is not compared',
                             'Memory-reader data is injected at $1163; no random distribution is assumed',
                             'This isolated adapter audit stubs motion/doors and excludes integrated entry phases; see SPAWN-AUDIT-0001',
                             'Full collect/apply combat, ordinary waits/retreat and natural physical navigation remain open'])
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    record_evidence(report)
    verify()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    verify() if args.verify else main()
