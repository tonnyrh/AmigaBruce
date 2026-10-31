"""Record the actual CLI/ADF startup and source-progress artifacts."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/contact-unroll-2026-10-31'
def main():
    c=json.loads((BASE/'normal-ui/cli/report.json').read_text())
    a=json.loads((BASE/'normal-ui/adf/report.json').read_text())
    assert c['complete_menu'] and a['complete_menu'] and a['game_states'][-1]['steps']>a['game_states'][0]['steps']
    assert c['elf']==a['elf']
    paths=['tools/check_contact_unroll_boot.py','tools/test-contact-unroll-normal.ps1','tools/record_contact_unroll_boot.py']+[f'reference/analysis/contact-unroll-2026-10-31/normal-ui/{mode}/{name}' for mode in ['cli','adf'] for name in ['report.json','menu.bpl']]
    artifacts=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths]
    report=dict(cli_complete_menu=True,adf_complete_menu=True,adf_source_progress=True,elf_sha256=a['elf']['sha256'],artifacts=artifacts,natural_playthrough=False)
    (BASE/'normal-boot.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS both normal boots and ADF source progress')
if __name__=='__main__':main()
