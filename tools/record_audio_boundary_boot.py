"""Bind actual normal CLI/ADF reports to the current A500 configuration."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/audio-service-2026-10-30'
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def main():
    exe=item('amiga/out/bruce_amiga.exe')['sha256'];elf=item('amiga/out/bruce_amiga.elf')['sha256'];paths=[]
    for mode in ['cli','adf']:
        p=BASE+'/normal-ui/'+mode+'/report.json';r=json.loads((ROOT/p).read_text())
        assert r['status']=='passed_current_normal_boot' and r['complete_menu'] and r['normal_exe_sha256']==exe and r['elf']['sha256']==elf
        if mode=='adf':assert len(r['game_states'])==3 and r['game_states'][-1]['steps']>r['game_states'][0]['steps'] and all(s['room']==1 and s['fault']==0 for s in r['game_states'])
        paths.append(p)
        for e in r['artifacts']:assert item(e['path'])['sha256']==e['sha256'];paths.append(e['path'])
    config='.tmp/bruce-a500.uae';values=set((ROOT/config).read_text().splitlines())
    required=['cpu_model=68000','cpu_speed=real','cpu_cycle_exact=true','cpu_memory_cycle_exact=true','blitter_cycle_exact=true','cycle_exact=true','ntsc=false','chipset=ocs','chipmem_size=1','bogomem_size=2','fastmem_size=0']
    assert set(required)<=values
    code=(ROOT/'tools/check_compact_boot.py').read_text().replace('ROOT=Path(__file__).resolve().parents[1]',f'ROOT=Path({str(ROOT)!r})').replace('reference/analysis/flat-control-compact-2026-10-30/normal-ui','reference/analysis/audio-service-2026-10-30/normal-ui')
    code='import sys\nsys.path.insert(0,'+repr(str(ROOT/'tools'))+')\n'+code
    assert code==(ROOT/BASE/'check-boot.py').read_text()
    frozen_config=BASE+'/normal-ui/adf/config.uae';shutil.copyfile(ROOT/config,ROOT/frozen_config)
    paths += [frozen_config,BASE+'/check-boot.py',BASE+'/ui-run.ps1',BASE+'/ui-rooms-retry.ps1',BASE+'/ui-adf-retry.ps1',BASE+'/ui-failed-room-selection/report.json','amiga-run.ps1','tools/check_compact_boot.py','tools/prepare_audio_boundary_ui.py','tools/record_audio_boundary_boot.py']
    report=dict(status='passed_audio_boundary_normal_boot',normal_exe_sha256=exe,cli_passed=True,adf_passed=True,target=required,natural_playthrough=False,artifacts=[item(p) for p in sorted(set(paths))])
    (ROOT/BASE/'normal-boot.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS current normal CLI/ADF and PAL OCS512+512 configuration')
if __name__=='__main__':main()
