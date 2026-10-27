"""Audit historical test interpretations by executing frozen candidate bytes.

These are controlled CPU fixtures, NOT VICE captures, natural play, VIC
simulation or proof that the Amiga actor implementation matches the source.
The collision latch is an explicit input. Unknown sprite contact stays open.
"""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.reference/tools/python'))
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler

SOURCE = ROOT / '.reference/c64/work/untrained-memory.bin'
SOURCE_SHA = '092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
ORIGINAL = SOURCE.read_bytes()
assert hashlib.sha256(ORIGINAL).hexdigest() == SOURCE_SHA
RESULTS = []


def cpu_at(memory, entry, actor=0):
    cpu = MPU(memory=memory, pc=entry)
    cpu.x = actor
    cpu.sp = 0xff
    cpu.stPushWord(0x02fe)  # RTS returns to $02FF; no original bytes patched.
    return cpu


def run(cpu, stop=0x02ff, limit=100000):
    for count in range(limit):
        if cpu.pc == stop:
            return count
        cpu.step()
    raise AssertionError(f'CPU did not reach ${stop:04X}; PC=${cpu.pc:04X}')


def actor(x=60, y=150, state=0, facing=1, counter=0, health=36, allowance=2):
    return dict(x=x, y=y, state=state, facing=facing, counter=counter,
                health=health, allowance=allowance)


def combat(name, actors, latch=0x1f, age=0, round_=0, mapping=(0, 0, 1, 1, 2)):
    memory = list(ORIGINAL)
    memory[0x4f40:0x4f45] = mapping
    memory[0xd01e] = latch
    memory[0x88], memory[0x40] = age, round_
    for i, a in enumerate(actors):
        for key, base in dict(x=0x9e, y=0xa1, state=0xbf, facing=0xa4,
                              counter=0xce, health=0xd1, allowance=0x4f45).items():
            memory[base+i] = a[key] & 255
        memory[0x0106+i] = 0
        memory[0x4fdb+i] = 0
    cpu = cpu_at(memory, 0x29c3)
    instructions = run(cpu, 0x2b4e if latch else 0x02ff)
    collected = dict(flags=memory[0xbc:0xbf], facing=memory[0xa4:0xa7],
                     allowance=memory[0x4f45:0x4f48],
                     health_before_apply=memory[0xd1:0xd4])
    instructions += run(cpu)
    after = {key: memory[base:base+3] for key, base in
             dict(health=0xd1, state=0xbf, counter=0xce, facing=0xa4,
                  wait=0x0106, flags=0xbc, allowance=0x4f45,
                  x=0x9e, y=0xa1).items()}
    row = dict(name=name, entry='$29C3', inputs=dict(actors=actors,
               vic_d01e=latch, actor_mapping=list(mapping), age_0088=age,
               round_0040=round_), collected=collected, after=after,
               instructions=instructions)
    RESULTS.append(row)
    return row


def movement(name, state, counter=0, contact=0, body_contact=0, input_=15,
             facing=1, x=60, y=150, previous=None, animation=0):
    memory = list(ORIGINAL)
    memory[0x9e], memory[0xa1] = x, y
    memory[0xa4], memory[0xbf] = facing, state
    memory[0xc2] = state if previous is None else previous
    memory[0xce], memory[0xb6], memory[0xa7] = counter, contact, body_contact
    memory[0x98], memory[0x9b] = input_, 1  # active-low direction; fire released
    memory[0x0106] = 0
    memory[0xcb] = animation
    memory[0xc8] = 0
    memory[0xb0] = 2
    memory[0x4f57:0x4fdb] = [0] * (0x4fdb-0x4f57)
    cpu = cpu_at(memory, 0x1c5b)
    count = run(cpu)
    after = {k: memory[a] for k, a in dict(x=0x9e, y=0xa1, state=0xbf,
             counter=0xce, facing=0xa4, wait=0x0106, obstruction_tries=0xb0).items()}
    row = dict(name=name, entry='$1C5B', inputs=dict(state=state, counter=counter,
               whole_contact=contact, body_contact=body_contact, input=input_,
               facing=facing, x=x, y=y, previous=previous, animation=animation),
               after=after, instructions=count)
    RESULTS.append(row)
    return row


def main():
    # The third actor has no attack and is too low for the fixture's fall hit.
    neutral = actor(x=150, y=40)
    p = actor(state=17)
    v = actor(x=68, health=20)
    r = combat('T03_no_VIC_latch_no_hit', [p, v, neutral], latch=0)
    assert r['after']['health'] == [36, 20, 36]
    for remaining in (0, 1, 4, 20):
        r = combat(f'T03_punch_no_counter_gate_{remaining}',
                   [actor(state=17, counter=remaining), v, neutral], latch=15)
        assert r['after']['health'][1] == 17
    # Both outgoing attacks survive classification, even though one victim's
    # hit flags have already been set. Damage has not happened at $2B4E.
    r = combat('T03_punch_and_kick_both_register',
               [p, actor(x=68, state=12, facing=0, counter=9, health=20), neutral], latch=15)
    assert r['collected']['flags'] == [9, 133, 0]
    assert r['collected']['health_before_apply'] == [36, 20, 36]
    assert r['after']['health'] == [29, 17, 36]
    assert r['after']['state'][:2] == [19, 15]
    for state in (5, 6, 7, 14):
        r = combat(f'T02_attacker_state_{state}',
                   [actor(y=135, state=state), v, neutral], latch=15)
        assert r['after']['health'][1] == (15 if state == 14 else 20)
    for victim_state in (12, 13, 17, 22):
        r = combat(f'T02_fall_victim_state_{victim_state}',
                   [actor(y=135, state=14), actor(x=68, state=victim_state,
                    facing=0, counter=12, health=20), neutral], latch=15)
        assert bool(r['collected']['flags'][1] & 16) == (victim_state == 22)
        assert r['after']['allowance'][0] == 1  # spent even on rejected attack states
    for diff in (9, 10):
        r = combat(f'T02_fall_height_{diff}', [actor(y=150-diff, state=14), v, neutral], latch=15)
        assert r['after']['health'][1] == (15 if diff == 10 else 20)
    # These validate the code's gates with an injected latch, not physical reach.
    for remaining in (0, 7, 8):
        r = combat(f'T07_sai_counter_{remaining}',
                   [actor(x=68), neutral, actor(state=22, counter=remaining)], latch=0x13)
        assert r['after']['health'][0] == (34 if remaining < 8 else 36)
    for raw_distance in (3, 4, -4):
        r = combat(f'T07_sai_raw_distance_{raw_distance}',
                   [actor(x=60+raw_distance), neutral, actor(state=22, counter=7)], latch=0x13)
        assert r['after']['health'][0] == (34 if raw_distance == 4 else 36)
    for state in (24, 26, 15, 19, 25, 27):
        r = combat(f'T11_immune_victim_state_{state}',
                   [p, actor(x=68, state=state, health=20), neutral], latch=15)
        assert r['after']['health'][1] == 20
    for health in (3, 2):
        r = combat(f'T13_punch_initial_health_{health}',
                   [p, actor(x=68, health=health), neutral], latch=15)
        assert r['after']['health'][1] == (health-3) & 255
        assert r['after']['state'][1] == (15 if health == 3 else 19)
    r = combat('T02_terminal_fall_candidate_anomaly',
               [actor(y=135, state=14), actor(x=68, health=4), neutral], latch=15)
    # Actual $2C24 -> $2BF9 revisits bit16 instead of finishing the actor.
    # This surprising injected-state result must not be called natural play
    # or silently replaced by the prototype's negative-health death rule.
    assert r['after']['health'][1] == 125 and r['after']['state'][1] == 27
    r['anomaly'] = 'Repeated fall subtraction after negative health; needs full-machine/edition investigation'
    r = combat('T13_hit_does_not_move_coordinates_in_resolver', [p, v, neutral], latch=15)
    assert r['after']['x'] == [a['x'] for a in (p, v, neutral)]
    assert r['after']['counter'][1] == 4
    assert r['after']['facing'][1] == 0
    # Threshold helper $10D0 reads elapsed timer $88; it is not a RNG.
    for age, expected in ((0, 3), (24, 3), (25, 8), (31, 8), (32, 10)):
        r = combat(f'T03_successful_Bruce_strike_recovery_age_{age}', [p, v, neutral], latch=15, age=age)
        assert r['after']['counter'][0] == expected and r['after']['wait'][0] == 4
    for direction in (15, 11, 7, 10, 6):
        r = movement(f'T01_free_fall_input_{direction}', 14, input_=direction)
        assert r['after']['x'] == 60 and r['after']['y'] == 152
    r = movement('T01_first_unsupported_step', 0, input_=7)
    assert r['after']['x'] == 60 and r['after']['y'] == 151 and r['after']['state'] == 14
    r = movement('T06_left_limit_is_checked_before_decrement', 0, contact=1, input_=11, x=13)
    assert r['after']['x'] == 12  # source display x0, NOT x2
    r = movement('T06_right_limit_is_checked_before_increment', 0, contact=1, input_=7, x=162)
    assert r['after']['x'] == 163  # source display x302
    for direction in (11, 7, 15):
        r = movement(f'T09_running_jump_ignores_new_direction_{direction}', 7,
                     counter=9, input_=direction)
        assert r['after']['x'] == 62
    for direction in (15, 7, 6):
        r = movement(f'T10_jump_catches_net_input_{direction}', 7,
                     counter=9, contact=4, input_=direction)
        assert r['after']['state'] == 0 and r['after']['x'] == 60
    for direction in (10, 6, 9, 5):
        r = movement(f'T10_diagonal_on_net_stops_{direction}', 0, contact=4, input_=direction)
        assert r['after']['state'] == 0 and r['after']['x'] == 60 and r['after']['y'] == 150
    for direction, y, state in ((14, 147, 1), (13, 153, 2), (11, 150, 3), (7, 150, 4)):
        r = movement(f'T10_single_axis_net_input_{direction}', 0, contact=4, input_=direction)
        assert r['after']['state'] == state and r['after']['y'] == y
    # Recoil executes in movement after damage assignment, not inside $29C3.
    # Main $1C23->$29C3, then $1C29->$179E->$1C5B: same iteration.
    r = movement('T13_sai_hurt_first_movement', 15, counter=3, contact=1, facing=0)
    assert r['after']['x'] == 62 and r['after']['counter'] == 2

    memory = list(ORIGINAL)
    memory[0x0104], memory[0x28] = 1, 2
    memory[0xd1:0xd4] = [255, 15, 3]
    memory[0x8b:0x8d] = [77, 88]
    cpu = cpu_at(memory, 0x181b)
    count = run(cpu, 0x1838)
    after = dict(lives=memory[0x28], health=memory[0xd1:0xd4], enemy_timers=memory[0x8b:0x8d])
    assert after == dict(lives=1, health=[36,36,36], enemy_timers=[0,0])
    RESULTS.append(dict(name='T14_new_life_prefix', entry='$181B', stop='$1838',
                        inputs=dict(game_active=1, lives=2, health=[255,15,3], enemy_timers=[77,88]),
                        after=after, instructions=count,
                        limitation='Only death prefix; does not execute the interlude, room reload, multiplayer or Game Over'))

    ranges = [(0x10d0, 0x10e0), (0x15c2, 0x15cd), (0x1c5b, 0x1fc4),
              (0x2008, 0x2180), (0x240e, 0x24b3), (0x2780, 0x29c3),
              (0x29c3, 0x2c70), (0x1818, 0x188e), (0x179e, 0x17e2),
              (0x1bc2, 0x1c39), (0x3a6f, 0x3a7c)]
    disasm = Disassembler(MPU(memory=list(ORIGINAL)))
    text = []
    for lo, hi in ranges:
        pc = lo
        while pc < hi:
            n, op = disasm.instruction_at(pc)
            text.append(f'{pc:04X}  {ORIGINAL[pc:pc+n].hex():8}  {op}')
            pc += n
        text.append('')
    out = ROOT / 'reference/analysis/test-audit-2026-10-25'
    out.mkdir(parents=True, exist_ok=True)
    disassembly = out / 'source-disassembly.txt'
    disassembly.write_text('\n'.join(text), encoding='utf-8')
    report = dict(date='2026-10-25', status='passed_controlled_source_cpu_fixtures',
                  source=dict(path=str(SOURCE.relative_to(ROOT)).replace('\\', '/'), sha256=SOURCE_SHA),
                  primary_edition_verified=False, natural_playthrough=False,
                  vic_collision_simulated=False, amiga_implementation_verified=False,
                  fixture_count=len(RESULTS), fixtures=RESULTS,
                  disassembly=dict(path=str(disassembly.relative_to(ROOT)).replace('\\', '/'),
                                   sha256=hashlib.sha256(disassembly.read_bytes()).hexdigest()),
                  code_ranges=[dict(start=f'${lo:04X}', end_exclusive=f'${hi:04X}',
                                    sha256=hashlib.sha256(ORIGINAL[lo:hi]).hexdigest()) for lo, hi in ranges],
                  limitations=['VIC latch, actor mapping, state and contact classes are injected inputs',
                               'No full IRQ, input sampling or natural transition sequence is emulated',
                               'Source branches establish conditional rules; fixtures only check their interpretation'],
                  source_files=[dict(path='tools/audit_c64_tests.py', sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())])
    (out / 'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(f'PASS {len(RESULTS)} controlled CPU fixtures from frozen C64 bytes; no Amiga/VIC/natural-play parity claim')


if __name__ == '__main__':
    main()
