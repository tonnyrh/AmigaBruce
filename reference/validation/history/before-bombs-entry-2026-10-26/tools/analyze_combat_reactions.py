"""Check reaction/AI instructions against the frozen C64 candidate memory.

This verifies instruction evidence, not complete runtime combat parity.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze():
    memory_path = ROOT / '.reference/c64/work/untrained-memory.bin'
    memory = memory_path.read_bytes()
    checks = {
        'punch_state17_dispatch_without_phase_counter_gate': (0x2A63, 'c9 11 f0 3e'),
        'punch_path_front_distance_height_and_hit_no_counter_gate': (0x2AA5, 'a9 06 85 61 20 54 2c 90 c8 30 c6 b9 a1 00 38 f5 a1 10 04 49 ff 69 01 c9 16 b0 b6 20 29 2e 20 3e 2b b5 bc 09 04 c0 00 d0 02 09 80 95 bc'),
        'sai_front_distance_minimum_4_half_pixels': (0x2A82, 'a9 04 85 61 20 54 2c 90 eb 30 e9'),
        'punch_front_distance_minimum_6_half_pixels': (0x2AA5, 'a9 06 85 61 20 54 2c 90 c8 30 c6'),
        'kick_front_distance_minimum_6_half_pixels': (0x2ADB, 'a9 06 85 61 20 54 2c 90 57 30 55'),
        'signed_distance_uses_attacker_facing': (0x2C54, 'b9 9e 00 38 f5 9e 48 08 b9 a4 00 c9 01 d0 08 28 68 49 ff 69 01 48 08 28 68 c5 61 60'),
        'victim_turns_opposite_attacker_before_recoil': (0x2B46, 'b9 a4 00 49 01 95 a4 60'),
        'sai_active_below_counter_8': (0x2A7B, 'b9 ce 00 c9 08 b0 f4'),
        'sai_hurt_counter_3': (0x2BA9, 'a9 0f 95 bf a9 03 95 ce'),
        'punch_hurt_counter_4': (0x2BCD, 'a9 0f 95 bf a9 04 95 ce'),
        'kick_down_counter_12': (0x2BF1, 'a9 13 95 bf a9 0c 95 ce'),
        'fall_counter_8': (0x2C15, 'a9 1b 95 bf a9 08 95 ce'),
        'hurt_recoil_left_two_half_pixels': (0x241F, '20 86 1e 20 86 1e'),
        'hurt_recoil_right_two_half_pixels': (0x242E, '20 c4 1e 20 c4 1e'),
        'living_npc_down_stops_before_last_move': (0x2444, '8a f0 08 b5 d1 30 04 c0 02 90 61'),
        'keep_facing_until_distance_33_half_pixels': (0x230B, 'b5 a4 a4 63 30 02 49 01 c9 01 f0 64 98 29 7f c9 21 90 09'),
        'retreat_target_15_half_pixels': (0x2327, 'a5 9e a4 63 10 05 38 e9 0f d0 03 18 69 0f'),
        'retreat_turns_only_at_last_counter': (0x23D7, 'b5 ce c9 01 d0 14 b5 a4 49 01 95 a4'),
    }
    verified = []
    for name, (address, expected) in checks.items():
        raw = bytes.fromhex(expected)
        assert memory[address:address+len(raw)] == raw, name
        verified.append(dict(rule=name, address=hex(address), bytes=expected))
    trace_path = ROOT / 'reference/traces/COMBAT-0001.json'
    rows = json.loads(trace_path.read_text(encoding='utf-8'))['scenarios']['net-drop-contact']
    slide = rows[363:369]
    x = [2*r['actors'][0]['x']-24 for r in slide]
    assert x == [80, 76, 72, 68, 64, 60]
    assert all(r['actors'][0]['state'] == 19 for r in slide[1:])
    report = dict(checks_passed=True, full_combat_parity=False,
                  primary_edition_verified=False, instructions=verified,
                  native_bruce_slide=dict(ticks=[r['tick'] for r in slide], x=x,
                                          pixels_per_step=4, pal_fields_per_step=3),
                  limitations=['Yamo complete knockdown duration is instruction-derived; no natural Yamo kick-hit recording yet',
                               'Room edges, collision masks, death/respawn and complete AI trajectories remain open'],
                  source_files=[dict(path=str(p.relative_to(ROOT)).replace('\\', '/'), sha256=sha(p))
                                for p in (memory_path, trace_path, Path(__file__).resolve(),
                                          ROOT/'core/combat.c', ROOT/'core/combat.h', ROOT/'tests/combat_test.c')])
    (ROOT/'reference/validation/candidate-combat-reactions.json').write_text(
        json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(f'PASS: {len(verified)} frozen C64 instruction checks; native four-pixel recoil over five consecutive intervals')


if __name__ == '__main__':
    analyze()
