"""Preserve failed-gate native replay results; never turn them into a pass.

Run immediately after the two-launch collection. Compile inputs must still
match the source-room build, and the executed runner is recorded by hash.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
from datetime import date

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def artifact(p):return dict(path=p,sha256=sha(ROOT/p))

def main():
    identity=read('reference/validation/a500-c64-rooms-diagnostic.json')['source_files']
    for item in identity:assert sha(ROOT/item['path'])==item['sha256'],item['path']
    host=read('reference/validation/c64-core.json')
    for item in host['source_files']:assert sha(ROOT/item['path'])==item['sha256'],item['path']
    expected=dict(part.split('=') for line in host['output'] if line.startswith('M3_6000 ') for part in line.split()[1:])
    assert len(expected)==7
    runs=[];raw=[];errors=[]
    for index in (1,2):
        p=ROOT/f'amiga/out/autotest-{index}.txt'
        run=dict(line.split('=',1) for line in p.read_text().splitlines() if '=' in line)
        assert run['frames']=='6000' and run['room_tour']=='0' and run['combat_mode']=='1'
        assert run['source_profile']=='0' and run['collect_frame_drops']=='1'
        for key in ('runtime_arithmetic_errors','canvas_residue_bytes','c64_room_fault','c64_render_mismatches','bad_presents'):
            assert run[key]=='0',(index,key)
        for key in ('restored_os','intro_finished','intro_silence_reload','intro_dma_stopped','intro_bitmap_restored'):
            assert run[key]=='1',(index,key)
        assert run['sfx_variant_mask']=='15' and int(run['sfx_played'])>=4
        assert run['sfx_played']==run['sfx_silence_reloads']
        assert all(run[key]==value for key,value in expected.items())
        assert 300<=int(run['present_min_line'])<=int(run['present_max_line'])<=308
        assert int(run['chip_largest_loaded'])>0
        gap=int(run['max_gap_excluding_framebuffer_capture'])
        if gap>1:errors.append(f'Run{index}: runtime gap{gap} PAL periods exceeds1')
        if int(run['chip_largest_loaded'])<49152:errors.append(f"Run{index}: Chip reserve{run['chip_largest_loaded']} below49152-byte target")
        dest=f'reference/validation/c64-replay-{index}.txt'
        (ROOT/dest).write_bytes(p.read_bytes());raw.append(artifact(dest));runs.append(run)
    for key in ('chip_available_before','expansion_available_before','final_x','final_y'):
        assert runs[0][key]==runs[1][key],key
    for suffix in ('exe','adf'):
        p=ROOT/f'amiga/out/bruce_test.{suffix}'
        (ROOT/f'amiga/out/validated/source-combat.{suffix}').write_bytes(p.read_bytes())
    preview='docs/images/c64-combat-replay.png'
    subprocess.run([sys.executable,str(ROOT/'tools/preview_planar.py'),str(ROOT/'amiga/out/autotest-frame.bpl'),str(ROOT/preview),'--color15',runs[0]['capture_color15'],'--interleaved'],check=True)
    result=dict(date=str(date.today()),profile='PAL A500 68000 OCS 512KiB Chip +512KiB slow; Kickstart1.3',
        execution='filesystem CLI, two consecutive launches',
        status='host_replay_states_match_native_runtime_and_memory_gates_failed',
        collection_only=True,realtime_contract_passed=False,memory_margin_passed=False,
        chip_headroom_requirement=49152,c64_parity='not_certified',runs=runs,
        failed_gates=errors,raw_reports=raw,preview=artifact(preview),
        original_runner_result='test-amiga.ps1 exited1 at the49152-byte Chip reserve assertion; this record does not override that failure',
        diagnostic_collector=artifact('tools/collect_c64_native_replay.py'),
        executable_sha256=sha(ROOT/'amiga/out/validated/source-combat.exe'),
        adf_sha256=sha(ROOT/'amiga/out/validated/source-combat.adf'),
        uae_config_sha256=sha(ROOT/'.tmp/bruce-a500-test.uae'),source_files=identity)
    assert errors
    (ROOT/'reference/validation/a500-c64-combat-diagnostic.json').write_text(json.dumps(result,indent=2)+'\n')
    print('RECORDED: two native6000-field replays match host states; timing and CLI Chip reserve gates remain failed')

if __name__=='__main__':main()
