"""Reject stale/mismatched local validation records without running emulators."""
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    if (ROOT/'reference/validation/c64-candidate.json').exists():
        from verify_c64_candidate import verify as source_verify
        return source_verify()
    samples=0
    for capture in ("MACHINE-0001","MACHINE-0002","MACHINE-0003","MACHINE-0004","MACHINE-0005","MACHINE-0006","MACHINE-0007"):
        folder=ROOT/"reference/traces"/capture
        summary=read(folder/"summary.json")
        assert summary["capture_id"]==capture
        assert summary["primary_edition_verified"] is False
        assert summary["repetitions"]==2
        if "input_program_sha256" in summary:
            assert digest(ROOT/"reference/scenarios"/(capture+".json"))==summary["input_program_sha256"]
        for source in summary["recorder_sources"]:
            assert digest(ROOT/source["path"])==source["sha256"],f"Stale recorder identity: {source['path']}"
        for scenario in summary["scenarios"]:
            path=folder/(scenario["name"]+".csv")
            assert digest(path)==scenario["sha256"],f"Trace hash mismatch: {path}"
            with path.open(newline="",encoding="utf-8") as stream:
                rows=list(csv.DictReader(stream))
            assert len(rows)==scenario["samples"]
            assert [int(row["tick"]) for row in rows]==list(range(len(rows)))
            gaps=[int(rows[i]["cycles"])-int(rows[i-1]["cycles"]) for i in range(1,len(rows))]
            assert min(gaps)==scenario["min_step_cycles"]
            assert max(gaps)==scenario["max_step_cycles"]
            assert all(gap-((int(rows[i]['raster_line'])-int(rows[i-1]['raster_line']))*63+
                int(rows[i]['raster_cycle'])-int(rows[i-1]['raster_cycle']))==58968
                for i,gap in enumerate(gaps,1))
            samples+=len(rows)
    for name in ("candidate-movement","candidate-climb","candidate-net-top","candidate-ledge-prone","candidate-attacks"):
        report=read(ROOT/"reference/validation"/(name+".json"))
        assert report["regression_gates_passed"] is True
        assert report["full_m2_parity"] is False
        assert report["core_sha256"]==digest(ROOT/"core/game.c"),"Stale core comparison"
        assert report["trace_summary_sha256"]==digest(ROOT/"reference/traces"/report["capture_id"]/"summary.json")
        for source in report["source_files"]:
            assert digest(ROOT/source["path"])==source["sha256"],f"Stale comparison source: {source['path']}"
        for scenario in report["scenarios"]:
            assert scenario["samples"]-scenario["exact_position_matches"]==len(scenario["differences"])
            assert not scenario.get("pose_differences",[])
            gate=scenario.get('gate_through_tick')
            if gate is not None:
                assert not any(d['tick']<=gate for d in scenario.get('attack_differences',[]))
    for capture,suffix in (('PHASE-0001',''),('PHASE-0002','-edges')):
        path=ROOT/'reference/traces'/f'{capture}.json'
        phase=read(path)
        assert phase['primary_edition_verified'] is False and phase['repetitions']==2
        for source in phase['sources']:assert digest(ROOT/source['path'])==source['sha256']
        report=read(ROOT/'reference/validation'/f'candidate-attacks-phased{suffix}.json')
        assert report['phase_sha256']==digest(path)
        assert report['baseline_summary_sha256']==digest(ROOT/'reference/traces'/phase['baseline_capture']/'summary.json')
        assert report['all_attack_targets_passed'] and report['regression_gates_passed']
        for source in report['source_files']:assert digest(ROOT/source['path'])==source['sha256']
        for scenario in report['scenarios']:
            assert scenario['all_attack_targets_passed'] and scenario['gate_passed']
            assert all(d['tick']>scenario['position_gate_through_tick'] for d in scenario['differences'])
    fall=read(ROOT/'reference/validation/candidate-fall-rate.json')
    assert fall['passed'] and not fall['full_route_parity']
    assert fall['pixels_per_logic_step']==2 and fall['pal_fields_per_logic_step']==3
    assert fall['trace_sha256']==digest(ROOT/'reference/traces/MACHINE-0007/mid-net-left-fall.csv')
    for source in fall['source_files']:assert digest(ROOT/source['path'])==source['sha256']
    fall_control=read(ROOT/'reference/validation/fall-control.json')
    assert fall_control['checks_passed'] and fall_control['engine_changed']
    for source in fall_control['source_files']:assert digest(ROOT/source['path'])==source['sha256']
    assert len(fall_control['scenarios'])==6
    for route in fall_control['scenarios']:
        assert all(v['dx']==0 for v in route['native_freefall_intervals'])
        assert not route['amiga_airborne_horizontal_intervals']
    combat_path=ROOT/'reference/traces/COMBAT-0001.json'
    combat=read(combat_path)
    assert combat['repetitions']==2 and not combat['primary_edition_verified']
    for source in combat['sources']:assert digest(ROOT/source['path'])==source['sha256']
    contact_report=read(ROOT/'reference/validation/candidate-enemy-contacts.json')
    assert contact_report['passed'] and contact_report['trace_sha256']==digest(combat_path)
    for source in contact_report['source_files']:assert digest(ROOT/source['path'])==source['sha256']
    code=read(ROOT/'reference/validation/candidate-fall-contact-code.json')
    assert code['checks_passed'] and code['snapshot_sha256']==combat['snapshot_sha256']
    assert code['runtime_fall_hit_observed'] is False
    for source in code['source_files']:assert digest(ROOT/source['path'])==source['sha256']
    for rows in combat['scenarios'].values():
        assert [r['tick'] for r in rows]==list(range(len(rows)))
        for a,b in zip(rows,rows[1:]):
            assert b['cycles']-a['cycles']-((b['raster_line']-a['raster_line'])*63+b['raster_cycle']-a['raster_cycle'])==58968
    for name in ("a500-repeat-launch","a500-adf-boot","a500-soak"):
        report=read(ROOT/"reference/validation"/(name+".json"))
        for source in report["source_files"]:
            assert digest(ROOT/source["path"])==source["sha256"],f"Stale runtime result: {name}/{source['path']}"
        for run in report["runs"]:
            assert run["bad_presents"]=="0"
            assert 300<=int(run["present_min_line"])<=int(run["present_max_line"])<=308
            assert int(run["max_gap_excluding_framebuffer_capture"])<=1
            assert int(run["prone_periods"])>0
            assert int(run["punch_periods"])>0
            if int(run['frames'])>360:assert int(run['kick_periods'])>0
            if int(run['frames'])>=1500:
                assert all(int(run[k])>0 for k in ('target_hits','target_defeats','target_respawns','target_stomps'))
    host=read(ROOT/'reference/validation/m3-core.json')
    room_facts=read(ROOT/'reference/validation/candidate-rooms.json')
    assert room_facts['checks_passed'] and len(room_facts['rooms'])==20
    assert not room_facts['full_m4_parity']
    assert room_facts['generated_header_sha256']==digest(ROOT/'core/room_data.h')
    for source in room_facts['source_files']:assert digest(ROOT/source['path'])==source['sha256']
    room_routes=read(ROOT/'reference/validation/candidate-room-routes.json')
    assert room_routes['regression_gates_passed'] and not room_routes['full_m4_parity']
    for source in room_routes['source_files']:assert digest(ROOT/source['path'])==source['sha256']
    for capture_id in ('ROOM-0002','ROOM-0003'):
        captured=read(ROOT/'reference/traces'/f'{capture_id}.json')
        assert captured['repetitions']==2
        for source in captured['sources']:assert digest(ROOT/source['path'])==source['sha256']
    room_runtime=read(ROOT/'reference/validation/a500-m4-rooms.json')
    for source in room_runtime['source_files']:assert digest(ROOT/source['path'])==source['sha256']
    assert digest(ROOT/room_runtime['preview']['path'])==room_runtime['preview']['sha256']
    room_expected=[line for line in host['output'] if line.startswith('M4_900 ')]
    assert len(room_expected)==1
    for run in room_runtime['runs']:
        assert run['frames']=='900' and run['room_test']=='1' and run['room_load_events']=='2'
        assert run['missed_frames']=='0' and int(run['max_gap_excluding_framebuffer_capture'])<=1
        assert int(run['room_load_max_gap'])>0 and int(run['chip_largest_loaded'])>=65536
        for entry in room_expected[0].split()[1:]:
            key,value=entry.split('=');assert run[key]==value
    reactions=read(ROOT/'reference/validation/candidate-combat-reactions.json')
    edge_capture=read(ROOT/'reference/traces/ENEMY-EDGE-0001.json')
    assert edge_capture['repetitions']==2
    for source in edge_capture['sources']:assert digest(ROOT/source['path'])==source['sha256']
    assert len(edge_capture['scenarios']['right-wall-then-left'])==361
    edge=read(ROOT/'reference/validation/enemy-room-edges.json')
    assert edge['checks_passed'] and not edge['full_enemy_parity']
    native_edge=read(ROOT/'reference/validation/a500-enemy-edges.json')
    for source in native_edge['source_files']:assert digest(ROOT/source['path'])==source['sha256']
    for run in native_edge['runs']:
        assert run['enemy_edge_test']=='1' and run['enemy_edge_checks']=='15'
        assert run['frames']=='1080' and run['restored_os']=='1'
        assert run['room_transitions']=='0' and run['missed_frames']=='0'
    assert digest(ROOT/native_edge['preview']['path'])==native_edge['preview']['sha256']
    assert edge['return_wait_steps']==160 and edge['first_left_move_after_return']==290
    assert edge['events']==[[96,1,294,98],[114,0,302,98],[274,1,294,98]]
    for source in edge['source_files']:assert digest(ROOT/source['path'])==source['sha256']
    assert reactions['checks_passed'] and not reactions['full_combat_parity']
    for source in reactions['source_files']:assert digest(ROOT/source['path'])==source['sha256']
    wall=read(ROOT/'reference/traces/WALL-0001.json')
    assert wall['repetitions']==2 and len(wall['scenarios'])==4
    for source in wall['sources']:assert digest(ROOT/source['path'])==source['sha256']
    escape=read(ROOT/'reference/validation/candidate-wall-escape.json')
    assert escape['checks_passed'] and not escape['full_combat_parity']
    for source in escape['source_files']:assert digest(ROOT/source['path'])==source['sha256']
    assert host['status']=='passed_host_contracts' and host['c64_parity']=='not_certified'
    for source in host['source_files']:assert digest(ROOT/source['path'])==source['sha256']
    expected_lines=[line for line in host['output'] if line.startswith('M3_6000 ')]
    assert len(expected_lines)==1
    expected=dict(entry.split('=') for entry in expected_lines[0].split()[1:])
    candidate=read(ROOT/'reference/validation/candidate-combat.json')
    assert candidate['entry_health_gates_passed'] and candidate['initial_walk_gates_passed']
    assert not candidate['full_m3_parity'] and not candidate['primary_edition_verified']
    assert candidate['reference_sha256']==digest(combat_path)
    for source in candidate['source_files']:assert digest(ROOT/source['path'])==source['sha256']
    assert sum(len(a['differences']) for s in candidate['scenarios'] for a in s['actors'])>0
    m3=read(ROOT/'reference/validation/a500-m3-combat.json')
    for source in m3['source_files']:assert digest(ROOT/source['path'])==source['sha256']
    assert digest(ROOT/m3['preview']['path'])==m3['preview']['sha256']
    for run in m3['runs']:
        assert run['frames']=='6000' and run['combat_mode']=='1' and run['restored_os']=='1'
        assert run['combat_warmup_steps']=='0'
        assert all(run[key]==value for key,value in expected.items()),'68000/host combat replay differs'
        assert int(run['enemy_defeats'])>0 and int(run['player_respawns'])>0
        assert run['missed_frames']=='0' and run['bad_presents']=='0'
        assert int(run['max_gap_excluding_framebuffer_capture'])<=1
        assert 0<int(run['max_hsync_gap'])<2*312
        assert int(run['chip_largest_loaded'])>=65536
    milestone=read(ROOT/'docs/parity/evidence/M3-0001.json')
    assert not milestone['full_m3_parity'] and not milestone['primary_edition_verified']
    for artifact in milestone['artifacts']:assert digest(ROOT/artifact['path'])==artifact['sha256']
    m4_milestone=read(ROOT/'docs/parity/evidence/M4-0001.json')
    assert not m4_milestone['full_m4_parity'] and m4_milestone['implemented_room_count']==2
    assert m4_milestone['extracted_room_count']==20
    for artifact in m4_milestone['artifacts']:assert digest(ROOT/artifact['path'])==artifact['sha256']
    interactive=read(ROOT/"reference/validation/interactive-build.json")
    assert interactive["test_control"] is False
    for item in interactive["artifacts"]+interactive["source_files"]:
        assert digest(ROOT/item["path"])==item["sha256"],f"Stale interactive artifact/source: {item['path']}"
    timing=read(ROOT/'reference/validation/movement-timing.json')
    assert timing['all_within_timer_resolution'] and not timing['full_movement_parity']
    assert timing['clock_config_sha256']==digest(ROOT/'reference/timing-clocks.json')
    assert timing['runtime_sha256']==digest(ROOT/'reference/validation/a500-soak.json')
    for item in timing['reference_sources']+timing['source_files']:
        assert digest(ROOT/item['path'])==item['sha256']
    assert {a['id'] for a in timing['actions']}=={'walk','jump','fall'}
    for action in timing['actions']:
        assert action['c64_duration_ms']>0
        assert len(action['amiga_runs'])==2
        for run in action['amiga_runs']:
            assert run['hardware_fields']>0 and run['within_one_field_resolution']
            assert abs(run['delta_ms_from_c64'])<=run['timer_resolution_ms']
    print(f"PASS: {samples} trace observations; recorder/core/runtime source identities and validation records agree")


if __name__=="__main__":verify()
