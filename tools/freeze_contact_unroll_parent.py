"""Preserve the validated loader-blank delivery before a kernel promotion."""
import hashlib,json,shutil
from pathlib import Path
from verify_loader_blank_delivery import verify_current
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/contact-unroll-2026-10-31/parent'

def main():
    assert not BASE.exists(),'Keep the existing parent'
    report=verify_current()
    assert report==json.loads((ROOT/'reference/validation/compact-actor-delivery.json').read_text())
    paths={e['path'] for e in report['artifacts']+report['normal_build']}
    native=json.loads((ROOT/'reference/validation/source-world-native.json').read_text(encoding='utf-8-sig'))
    paths.update(e['path'] for e in native['source_files']+native['build'])
    paths.update(['reference/validation/compact-actor-delivery.json','reference/validation/source-world-delivery.json',
      'reference/validation/source-optimization.json','reference/validation/loader-display-blank.json',
      'docs/parity/evidence/ACTOR-CHAIN-0001.json','docs/parity/evidence/LOADER-DISPLAY-0001.json','amiga-build.ps1'])
    # Earlier nested stages already own immutable copies. Freeze this
    # validator's direct inputs, not a second copy of the entire history.
    entries=[]
    for p in sorted(paths):
        dst=BASE/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/p,dst)
        entries.append(dict(path=p,sha256=hashlib.sha256(dst.read_bytes()).hexdigest()))
    (BASE/'manifest.json').write_text(json.dumps(dict(status='frozen_pre_contact_alignment_unroll',files=entries),indent=2)+'\n')
    (BASE/'verified-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Frozen validated parent:',len(entries),'files')
if __name__=='__main__':main()
