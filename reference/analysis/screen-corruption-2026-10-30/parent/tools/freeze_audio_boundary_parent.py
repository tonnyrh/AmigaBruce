"""Freeze the currently validated delivery before any production edit."""
import hashlib,json,shutil
from pathlib import Path
from verify_compact_actor_delivery import verify
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/audio-service-2026-10-30/parent'
def main():
    report=verify();old=json.loads((ROOT/'reference/validation/compact-actor-delivery.json').read_text())
    assert old==report
    assert not BASE.exists(),'Keep the existing frozen delivery'
    paths={e['path'] for e in report['artifacts']+report['normal_build']}
    paths.update(['reference/validation/compact-actor-delivery.json','reference/validation/source-world-delivery.json','reference/validation/source-optimization.json','docs/parity/evidence/ACTOR-CHAIN-0001.json','amiga-build.ps1'])
    for directory in ['core','amiga']:
        paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT/directory).iterdir() if p.is_file() and p.suffix in ['.c','.h','.s'])
    entries=[]
    for path in sorted(paths):
        src=ROOT/path;dst=BASE/path;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
        digest=hashlib.sha256(dst.read_bytes()).hexdigest();assert digest==hashlib.sha256(src.read_bytes()).hexdigest()
        entries.append(dict(path=path,sha256=digest))
    (BASE/'manifest.json').write_text(json.dumps(dict(status='frozen_pre_audio_boundary_delivery',files=entries),indent=2)+'\n')
    print('Frozen validated preceding delivery:',len(entries),'artifacts')
if __name__=='__main__':main()
