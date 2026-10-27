"""Bind scoped source controls and native results to the delivered files."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FOLDER='reference/analysis/actor-chain-2026-10-26'
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))
def artifact(path):return dict(path=path,sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest())
def identities(items):
    for item in items:assert artifact(item['path'])['sha256']==item['sha256'],f'Stale evidence: {item["path"]}'
def verify():
    source=artifact('.reference/c64/work/untrained-memory.bin')['sha256']
    assert source=='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
    controls=read(FOLDER+'/report.json');world=read(FOLDER+'/integrated-controls.json')
    translation=read(FOLDER+'/translation.json');fixture=read(FOLDER+'/native-fixture.json')
    for report in (controls,world,translation,fixture):
        assert report['source_sha256']==source and not report['edition_verified'] and not report['natural_playthrough']
        identities(report.get('source_files',[]));identities(report.get('generated',[]))
    assert controls['checks']==3034 and len(controls['rows'])==3034
    assert len(world['checks'])==5 and world['instructions']==7055873
    assert world['checks'][-1]['stop']=='$0584' and world['checks'][-1]['terminal_life']
    assert all(row['life_events']>=1 for row in world['checks'])
    vic=read('reference/validation/source-vic-host.json')
    assert vic['status']=='passed_field_sampled_pixel_and_latch_controls' and vic['calls']==6485
    assert not vic['original_raster_verified'];identities(vic['source_files'])
    contact=read('reference/validation/source-contact-host.json')
    assert contact['status']=='passed_original_byte_contact_controls' and contact['checks']==3304
    assert contact['service_register_cases']==224
    assert contact['source_sha256']==source and not contact['natural_playthrough'];identities(contact['source_files'])
    visibility=read('reference/validation/source-visibility-host.json')
    assert visibility['status']=='passed_original_active_bit_projection' and visibility['checks']==768
    assert visibility['source_sha256']==source and visibility['source_ram_unchanged_except_injected_flags']
    identities(visibility['source_files'])
    native_visibility=read('reference/validation/source-visibility-native.json')
    assert native_visibility['status']=='passed_owned_native_visibility_lifecycle'
    assert native_visibility['controlled_injection'] and not native_visibility['natural_playthrough']
    identities([native_visibility['binary']]+native_visibility['source_files']+native_visibility['artifacts'])
    assert [x['flags']&1 for x in native_visibility['states']]==[1,0,1]
    assert all(not any(rect) for rect in native_visibility['states'][1]['buffer_dirty'])
    assert len(fixture['cases'])==53;identities([fixture['fixture']])
    native=read('reference/validation/source-world-native.json');identities(native['source_files']+native['build'])
    assert native['status']=='passed_scoped_native_source_contract' and not native['failures']
    assert native['run']['source_actor_fixture_cases']=='53' and native['run']['source_actor_fixture_failure']=='0'
    assert native['run']['vic_compare_errors']=='0'
    assert native['run']['restored_os']=='1' and native['run']['c64_room_fault']=='0'
    assert int(native['run']['chip_largest_loaded'])>=49152
    clock=read(FOLDER+'/normal-clock.json');identities([clock['binary']])
    assert all(x['fault']==0 for x in clock['samples']) and len(clock['pairs'])==3
    assert all(x['source_fields']>0 and x['clock_min']-2<=x['source_fields']<=x['clock_max']+2 for x in clock['pairs'])
    return source,controls,world,native
def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');args=p.parse_args()
    source,controls,world,native=verify()
    path='reference/validation/source-world-delivery.json'
    if args.record:
        proofs=[FOLDER+'/'+name for name in ('report.json','translation.json','integrated-controls.json','native-fixture.json','native-final.txt')]
        proofs += ['tools/audit_normal_source_clock.py',FOLDER+'/normal-clock.json','reference/validation/source-world-native.json','docs/MILESTONE_COMPLETION.md','docs/ACTIVE_TESTS.md','docs/PROJECT_PLAN.md','docs/parity/register.csv','tools/verify_source_world_delivery.py','test-parity.ps1','README.md']
        proofs += ['reference/validation/source-vic-host.json','docs/AMIGA_OPTIMIZATION_PLAN.md','docs/AMIGA_OPTIMIZATION_REPORT.md']
        proofs += ['reference/validation/source-contact-host.json','docs/CONTACT_OPTIMIZATION.md','docs/VIC_NATIVE_OPTIMIZATION.md']
        proofs += ['reference/validation/source-visibility-native.json','reference/validation/source-visibility-host.json','reference/analysis/yamo-r02-2026-10-27/snapshot.json','reference/analysis/yamo-r02-2026-10-27/source-memory.bin','tools/inspect_source_snapshot.py','docs/YAMO_VISIBILITY_PERFORMANCE.md','docs/CONTACT_REGISTERS_OPTIMIZATION.md']
        normal=[artifact('amiga/out/bruce_amiga.'+suffix) for suffix in ('exe','elf','adf')]
        report=dict(date='2026-10-27',status='scoped_complete_source_chain_implemented_acceptance_open',source_sha256=source,
            edition_verified=False,natural_playthrough=False,raster_exact=False,full_original_parity=False,
            source_controls=3034,integrated_scenarios=5,source_instructions=world['instructions'],native_controls=53,
            native_replay_loops=int(native['run']['frames']),largest_chip_block=int(native['run']['chip_largest_loaded']),
            realtime_gate_passed=native['realtime_contract_passed'],artifacts=[artifact(x) for x in proofs],normal_build=normal,
            open_gates=['Verified untouched1984 edition','PAL real-time budget across all rooms','Natural VIC/IRQ phase and reader distribution','Complete natural playthrough and next round','Physical A500 and final distribution'])
        (ROOT/path).write_text(json.dumps(report,indent=2)+'\n')
        evidence=dict(id='ACTOR-CHAIN-0001',date='2026-10-27',status=report['status'],source_sha256=source,
            primary_edition_verified=False,natural_playthrough=False,full_original_parity=False,
            source_ranges=['$0743-$1100','$15A8-$1981','$1BC2-$33CA','$40BC','$5212-$56FF'],
            condition='Complete source main/actor/contact/object/combat/lifetime/score chain in shared RAM; explicit CIA/VIC/field-wait seams',
            controls=dict(source=3034,integrated=5,native=53),artifacts=[artifact(path),artifact('docs/MILESTONE_COMPLETION.md')],
            limitations=report['open_gates'])
        (ROOT/'docs/parity/evidence/ACTOR-CHAIN-0001.json').write_text(json.dumps(evidence,indent=2)+'\n')
    else:
        report=read(path);identities(report['artifacts']+report['normal_build']);assert report['source_sha256']==source
    print('PASS source-world delivery; original-parity and real-time acceptance remain open' if not native['realtime_contract_passed'] else 'PASS scoped source-world delivery')
if __name__=='__main__':main()
