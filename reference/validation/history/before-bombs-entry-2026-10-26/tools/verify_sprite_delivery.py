"""Bind source sprite extraction/selector controls to the current A500 build."""
from datetime import date
from pathlib import Path
import argparse
import hashlib
import json
import shutil
from verify_movement_delivery import verify as verify_movement

ROOT=Path(__file__).resolve().parents[1]
REPORT='reference/validation/c64-sprites-delivery.json'
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'


def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def artifact(p):return dict(path=p,sha256=sha(p),size_bytes=(ROOT/p).stat().st_size)
def save(p,v):(ROOT/p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def identities(items):
    for item in items:assert sha(item['path'])==item['sha256'],f"Stale sprite evidence: {item['path']}"


def controls():
    verify_movement()
    host=read('reference/validation/c64-sprites-host.json')
    atlas=read('assets/c64/sprites-v1/manifest.json')
    identities(host['source_files']+[host['native_fixture'],host['host_library']])
    identities(atlas['outputs']+[atlas['generator']]+atlas['dependencies'])
    assert host['source_sha256']==atlas['source']['sha256']==SHA
    assert host['selector_cases']==17280 and host['pixel_checks']==211680
    assert host['native_fixture_cases']==324
    assert not host['full_actor_fsm_ported'] and not host['natural_playthrough']
    assert atlas['original_c64_actor_pixels'] and not atlas['new_art_generated']
    assert atlas['frame_count']==210 and atlas['unique_dma_frames']==80
    raw=read('reference/validation/source-audio-raw.json')
    for run in raw['runs']:
        assert run['sprite_fixture_cases']=='324' and run['sprite_fixture_failure']=='0'
        assert run['fighter_cache_bytes']==str(atlas['cache_bytes'])
        assert run['fighter_cache_hash']==str(atlas['native_fnv'])
    # The regular build cannot silently return to AI art or reflection.
    build=(ROOT/'amiga-build.ps1').read_text();main=(ROOT/'amiga/main.c').read_text()
    assert 'tools/build_c64_sprites.py' in build
    assert 'tools/build_fighter_art.py' not in build and 'tools/build_fighter_dma.py' not in build
    assert '#include "c64_sprite_data.h"' in main
    assert '#include "fighter_art_data.h"' not in main and '#include "fighter_dma_data.h"' not in main
    assert 'render_game.x=visual.x' not in main and 'body.x=enemy_visual' not in main
    source=ROOT/atlas['source']['path']
    if source.exists():assert sha(atlas['source']['path'])==SHA
    return host,atlas,raw,read('reference/validation/movement-delivery.json')


def record():
    host,atlas,raw,movement=controls()
    frame='reference/validation/c64-sprites-frame.bpl'
    shutil.copyfile(ROOT/'amiga/out/autotest-frame.bpl',ROOT/frame)
    from preview_planar import render
    image='docs/images/c64-sprites.png'
    render(ROOT/frame,ROOT/image,int(raw['runs'][-1]['capture_color15']),True)
    files=['reference/validation/c64-sprites-host.json','reference/validation/movement-delivery.json',
           'assets/c64/sprites-v1/manifest.json','docs/C64_SPRITES.md','docs/ACTIVE_TESTS.md',
           'docs/PROJECT_PLAN.md','docs/AMIGA_ART_PIPELINE.md','docs/parity/register.csv',
           'AGENTS.md','README.md','tools/verify_sprite_delivery.py','tools/verify_c64_candidate.py',frame,image]
    result=dict(date=str(date.today()),status='verified_ripped_c64_sprites_and_scoped_source_selector',
        source_sha256=SHA,edition_verified=False,full_c64_game_parity=False,
        complete_actor_fsm_ported=False,natural_playthrough=False,enhanced_art_active=False,
        components=210,composites=210,unique_dma_frames=80,selector_cases=17280,
        pixel_checks=211680,native_fixture_cases=324,native_fixture_launches=2,
        native_fixture_failure=0,native_cache_hash_verified=True,
        cache_bytes=atlas['cache_bytes'],packed_bytes=atlas['packed_bytes'],
        previous_cache_bytes=90912,previous_packed_bytes=44042,
        all_room_native_rerun=False,realtime_gate_passed=movement['realtime_gate_passed'],
        cli_chip_reserve_passed=movement['cli_chip_reserve_passed'],
        native_runs=raw['runs'],normal_build=movement['normal_build'],
        native_binaries=movement['native_binaries'],native_captures=movement['native_captures'],
        source_files=raw['source_files'],evidence=[artifact(p) for p in files],
        limitations=['Source selector is decoded; its native actor/counter projection remains partial',
                     'Full movement/contact/combat/AI and input/timing parity remain open',
                     'Existing OCS12-bit palette reproduces source colour indices, not analog C64 RGB',
                     'Native cache signature proves decoding, not visual exercise of every pose/overlap',
                     'No natural all-room playthrough or certified retail edition',
                     'Strict A500 timing/memory gates remain independent'])
    save(REPORT,result)
    for p in ('reference/validation/c64-candidate.json','reference/validation/visual-candidate.json'):
        save(p,dict(status=result['status'],date=result['date'],actor_logic_fully_ported=False,
            full_m2_parity=False,full_m4_parity=False,full_m5_complete=False,
            natural_playthrough_verified=False,primary_edition_verified=False,
            all_room_realtime_gate_passed=False,all_room_native_rerun_after_actor_changes=False,
            enhanced_art_active=False,artifact=artifact(REPORT)))
    save('docs/parity/evidence/SPRITES-0001.json',dict(id='SPRITES-0001',date=result['date'],
        status='candidate_code_derived_partial',full_original_parity=False,
        summary='210 source components composed through actual6502 copy/position into210 pose/facing images;17280 source pose cases and211680 source/DMA pixels checked.324 selector fixtures on two68000 launches; source DMA FNV matches. Native actor bridge and full gameplay/timing remain open.',
        artifacts=[artifact(REPORT)]))
    verify()


def verify():
    result=read(REPORT)
    identities(result['source_files']+result['normal_build']+result['native_binaries']+
               result['native_captures']+result['evidence'])
    host,atlas,raw,movement=controls()
    assert result['native_runs']==raw['runs']
    assert result['cache_bytes']==atlas['cache_bytes']
    assert result['realtime_gate_passed']==movement['realtime_gate_passed']
    assert result['cli_chip_reserve_passed']==movement['cli_chip_reserve_passed']
    assert not result['full_c64_game_parity'] and not result['enhanced_art_active']
    assert not result['complete_actor_fsm_ported'] and not result['natural_playthrough']
    print('VERIFIED C64 sprites:210 components/210 composites,17280 selector cases,211680 pixels; '
          f"324 fixtures on two A500 launches. Strict timing={result['realtime_gate_passed']}, CLI reserve={result['cli_chip_reserve_passed']}; full actor port open")


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--record',action='store_true');args=parser.parse_args()
    record() if args.record else verify()
