"""Verify source-derived Paula delivery without waiving any A500 gate."""
from pathlib import Path
from datetime import date
import argparse,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
REPORT='reference/validation/source-audio-delivery.json'
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def artifact(p):return dict(path=p,sha256=sha(p),size_bytes=(ROOT/p).stat().st_size)
def save(p,v):(ROOT/p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def identities(items):
    for i in items:assert sha(i['path'])==i['sha256'],f"Stale source audio evidence: {i['path']}"
def expected(prefix,host):
    lines=[l for l in host['output'] if l.startswith(prefix+' ')]
    assert len(lines)==1,prefix
    return dict(p.split('=') for p in lines[0].split()[1:])
def check_runs(raw,host):
    identities(raw['source_files']);identities(host['source_files'])
    assert raw['test_frames']==6000 and raw['collect_frame_drops']
    assert len(raw['runs'])==2
    values={**expected('AUDIO_6000',host),**expected('M3_6000',host)}
    for r in raw['runs']:
        assert r['frames']=='6000' and r['collect_frame_drops']=='1' and r['source_profile']=='0'
        assert all(r[k]==v for k,v in values.items()),{k:(r.get(k),v) for k,v in values.items()}
        for k in ('restored_os','intro_finished','intro_silence_reload','intro_dma_stopped','intro_bitmap_restored'):assert r[k]=='1',k
        for k in ('bad_presents','runtime_arithmetic_errors','canvas_residue_bytes','c64_room_fault','c64_render_mismatches','source_audio_faults'):assert r[k]=='0',k
        assert r['source_audio_fields']=='6000' and r['source_music_fields']=='120'
        assert r['source_audio_voice_mask']=='7' and r['source_sfx_request_mask']=='32767'
        assert r['source_audio_chip_bytes']=='2260'
        assert r['contact_fixture_cases']=='29' and r['contact_fixture_failure']=='0'
        assert r['movement_fixture_cases']=='70' and r['movement_fixture_failure']=='0'
        assert 300<=int(r['present_min_line'])<=int(r['present_max_line'])<=308
        assert int(r['chip_largest_loaded'])>0
    return values
def record():
    raw=read('reference/validation/source-audio-raw.json');host=read('reference/validation/c64-core.json')
    values=check_runs(raw,host)
    identities(read('reference/validation/source-audio-host.json')['source_files'])
    assert raw['executable_sha256']==sha('amiga/out/bruce_test.exe')
    assert raw['adf_sha256']==sha('amiga/out/bruce_test.adf')
    files=[]
    for suffix in ('exe','adf'):
        dest=f'amiga/out/validated/source-audio.{suffix}'
        shutil.copyfile(ROOT/f'amiga/out/bruce_test.{suffix}',ROOT/dest);files.append(artifact(dest))
    captures=[]
    for i in (1,2):
        dest=f'reference/validation/source-audio-native-{i}.txt'
        shutil.copyfile(ROOT/f'amiga/out/autotest-{i}.txt',ROOT/dest);captures.append(artifact(dest))
    start=ROOT/'.tmp/amiga-boot/c/start'
    if start.exists():shutil.copyfile(ROOT/'amiga/out/bruce_amiga.exe',start)
    rt=all(int(r['missed_frames'])==0 and int(r['max_gap_excluding_framebuffer_capture'])<=1 for r in raw['runs'])
    mem=all(int(r['chip_largest_loaded'])>=49152 for r in raw['runs'])
    items=['reference/validation/source-audio-host.json','reference/validation/c64-core.json',
           'reference/validation/source-audio-raw.json','reference/validation/c64-room-runtime.json',
           'assets/audio/c64-equivalent-v1/manifest.json','tools/verify_audio_delivery.py',
           'tools/verify_c64_candidate.py','docs/SOURCE_AUDIO.md']
    result=dict(date=str(date.today()),status='source_equivalent_paula_audio_verified_scoped',
        edition_verified=False,full_c64_game_parity=False,natural_playthrough=False,
        sfx_ids=15,music_loop_source_fields=1154,source_sfx_cpu_fields=7540,
        waveform_chip_bytes=2260,previous_waveform_chip_bytes=4004,
        paula_register_replays_match_host=True,sid_analog_emulation=False,
        native_execution=raw['execution'],native_runs=raw['runs'],expected_host=values,
        realtime_gate_passed=rt,cli_chip_reserve_passed=mem,cli_chip_reserve_required=49152,
        all_room_native_rerun=False,source_files=raw['source_files'],
        native_binaries=files,native_captures=captures,
        normal_build=[artifact('amiga/out/bruce_amiga.exe'),artifact('amiga/out/bruce_amiga.adf')],
        normal_build_flags=['BL_AUTOTEST=0'],
        cli_start_updated=start.exists(),interactive_process_restarted=False,
        evidence=[artifact(p) for p in items],
        limitations=['50Hz envelope and finite Paula waves/noise approximate SID timbre',
                     'Full natural triggering of unported actor states remains open',
                     'Native title replay covers120fields; full loop checked separately on host/source bytes',
                     'Strict memory/timing targets are reported independently; no blanket A500/parity pass'])
    save(REPORT,result)
    for p in ('reference/validation/c64-candidate.json','reference/validation/visual-candidate.json'):
        save(p,dict(status=result['status'],date=result['date'],actor_logic_fully_ported=False,
                    full_m2_parity=False,full_m4_parity=False,full_m5_complete=False,
                    natural_playthrough_verified=False,primary_edition_verified=False,
                    all_room_realtime_gate_passed=False,all_room_native_rerun_after_actor_changes=False,
                    artifact=artifact(REPORT)))
    save('docs/parity/evidence/SOURCE-AUDIO-0001.json',dict(id='SOURCE-AUDIO-0001',date=result['date'],
        status='candidate_code_derived_partial',full_original_parity=False,
        summary='Source title score and15 SFX sequences converted to compact Paula voices.7540 controlled source fields match native decoder; two A500 parameter replays match host. Analog SID/complete actor parity and strict A500 gates remain open.',
        artifacts=[artifact(REPORT)]))
    verify()
def verify():
    r=read(REPORT);identities(r['source_files']+r['native_binaries']+r['native_captures']+r['normal_build']+r['evidence'])
    host=read('reference/validation/c64-core.json');raw=read('reference/validation/source-audio-raw.json')
    assert check_runs(raw,host)==r['expected_host'] and raw['runs']==r['native_runs']
    h=read('reference/validation/source-audio-host.json');identities(h['source_files']+h['previews'])
    assert h['source_cpu_fields_compared']==7540 and h['sfx_ids']==15 and h['chip_bytes']==2260
    identities(read('assets/audio/c64-equivalent-v1/manifest.json')['generated'])
    identities(read('reference/validation/c64-room-runtime.json')['source_files'])
    assert not r['full_c64_game_parity'] and not r['sid_analog_emulation']
    assert r['realtime_gate_passed']==all(int(x['missed_frames'])==0 and int(x['max_gap_excluding_framebuffer_capture'])<=1 for x in r['native_runs'])
    assert r['cli_chip_reserve_passed']==all(int(x['chip_largest_loaded'])>=49152 for x in r['native_runs'])
    print(f"VERIFIED source-equivalent audio:15effects,1154-field theme,2260Chip bytes;7540 source fields;2native Paula replays. Strict timing={r['realtime_gate_passed']}, CLI reserve={r['cli_chip_reserve_passed']}; full game parity open")
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args()
    record() if a.record else verify()
