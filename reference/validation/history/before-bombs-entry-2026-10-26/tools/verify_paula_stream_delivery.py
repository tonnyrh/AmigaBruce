"""Bind fixed DMA/PAL service to current evidence; pending is never a runtime pass."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPORT='reference/validation/paula-stream-delivery.json'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))
def artifact(path):
    p=ROOT/path
    return dict(path=path,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def identities(items):
    for item in items:assert artifact(item['path'])['sha256']==item['sha256'],f"Stale Paula evidence: {item['path']}"
def save(path,value):(ROOT/path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def host():
    dma=read('reference/validation/source-dma-host.json');identities(dma['source_files'])
    assert dma['fields']==1518 and dma['channel_images']==4554 and dma['bytes_checked']==4663296
    assert dma['invalid_cases']==5 and dma['dma_bytes']==3072
    for path in ('reference/validation/c64-core.json','reference/validation/source-audio-host.json',
                 'reference/validation/c64-room-runtime.json'):
        identities(read(path)['source_files'])
    return dma


def primary(report):
    for path in ('reference/validation/c64-candidate.json','reference/validation/visual-candidate.json'):
        save(path,dict(date='2026-10-25',status=report['status'],artifact=artifact(REPORT),
            native_validation_complete=report['native_validation_complete'],
            actor_logic_fully_ported=False,full_m2_parity=False,full_m4_parity=False,
            full_m5_complete=False,natural_playthrough_verified=False,primary_edition_verified=False,
            all_room_realtime_gate_passed=False,all_room_native_rerun_after_actor_changes=False,
            enhanced_art_active=False))


def record(pending=False):
    dma=host()
    files=['amiga/main.c','amiga/source_audio.h','core/source_dma.c','core/source_dma.h',
        'core/c64_rooms.c','core/c64_rooms.h','tests/source_dma_fixture.h','tests/packed_capture.h',
        'amiga-build.ps1','amiga-run.ps1','test-amiga.ps1','tools/verify_source_dma.py','test-source-dma.ps1',
        'tools/verify_paula_stream_delivery.py','tools/verify_c64_candidate.py','docs/PAULA_STREAM.md',
        'reference/validation/source-dma-host.json','reference/validation/source-audio-host.json',
        'reference/validation/c64-core.json','reference/validation/c64-room-runtime.json']
    result=dict(date='2026-10-25',status='implemented_host_checked_native_validation_pending',
        native_validation_complete=False,edition_verified=False,full_c64_game_parity=False,
        sid_analog_emulation=False,natural_playthrough=False,source_waveform_chip_bytes=2260,
        fixed_dma_image_bytes=3072,total_audio_chip_bytes=5332,host_dma_fields=dma['fields'],
        host_dma_channel_images=dma['channel_images'],source_rules_changed=False,
        source_files=[artifact(p) for p in files],
        normal_build=[artifact('amiga/out/bruce_amiga.exe'),artifact('amiga/out/bruce_amiga.adf')],
        prior_build_archive='reference/validation/history/before-paula-stream-2026-10-25',
        pending=['Two current native6000-loop captures and current native music/SFX recordings'],
        limitations=['Fixed in-place images retain prefetched-word/current-period/copy-boundary effects',
            'Cooperative service exposes missed fields; no independent audio interrupt or blanket50Hz guarantee',
            'Actor/gameplay/full natural C64 parity and strict A500 rendering gate remain open'])
    if not pending:
        from verify_npc_recoil_delivery import verify as verify_prior
        verify_prior()
        pcm=read('reference/analysis/paula-stream-2026-10-25/report.json')
        identities(pcm['source_files']+pcm['artifacts'])
        assert pcm['native_recording_verified'] and pcm['normal_binary']==artifact('amiga/out/bruce_amiga.exe')
        raw=read('reference/validation/source-audio-raw.json')
        assert len(raw['runs'])==2 and raw['test_frames']==6000
        for run in raw['runs']:
            assert run['source_dma_fixture_cases']=='7' and run['source_dma_fixture_failure']=='0'
            assert run['source_dma_faults']=='0' and run['capture_fault']=='0'
        prior=read('reference/validation/npc-recoil-delivery.json')
        result.update(status='verified_fixed_paula_images_and_scoped_PAL_service',native_validation_complete=True,
            pending=[],native_runs=raw['runs'],native_recordings=artifact('reference/analysis/paula-stream-2026-10-25/report.json'),
            native_binaries=prior['native_binaries'],native_captures=prior['native_captures'],
            previous_delivery=artifact('reference/validation/npc-recoil-delivery.json'),
            audio_all_controlled_game_fields_serviced=all(r['source_clock_missed']=='0' for r in raw['runs']),
            realtime_gate_passed=prior['realtime_gate_passed'],cli_chip_reserve_passed=prior['cli_chip_reserve_passed'])
    save(REPORT,result);primary(result);verify()


def verify():
    host();r=read(REPORT);identities(r['source_files']+r['normal_build'])
    assert not r['full_c64_game_parity'] and not r['source_rules_changed']
    if not r['native_validation_complete']:
        assert r['pending'] and r['status']=='implemented_host_checked_native_validation_pending'
        print('VERIFIED current source/build identities and host controls ONLY; current native validation PENDING')
        return
    from verify_npc_recoil_delivery import verify as verify_prior
    verify_prior()
    identities(r['native_binaries']+r['native_captures']+[r['previous_delivery'],r['native_recordings']])
    pcm=read(r['native_recordings']['path']);identities(pcm['source_files']+pcm['artifacts'])
    assert pcm['native_recording_verified']
    assert r['native_runs']==read('reference/validation/source-audio-raw.json')['runs']
    print('VERIFIED fixed Paula DMA images, hardware-field accounting and current native PCM; strict cadence/full parity reported separately')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');p.add_argument('--pending',action='store_true');a=p.parse_args()
    record(a.pending) if a.record or a.pending else verify()
