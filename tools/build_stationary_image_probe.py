"""Repeat the fixed-actor probe with the isolated native image driver."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/enemy-cost-2026-10-30'
def main():
    out=BASE/'stationary-image-v2';out.mkdir(exist_ok=True)
    old=BASE/'stationary';candidate=BASE/'image-driver-v2'
    # Keep exactly the established stationary harness, replacing only the core.
    original=(ROOT/'core/c64_rooms.c').read_text(encoding='utf-8-sig')
    probe=(old/'c64_rooms.c').read_text(encoding='utf-8-sig')
    assert probe.startswith(original)
    (out/'c64_rooms.c').write_text((candidate/'c64_rooms.c').read_text(encoding='utf-8-sig')+probe[len(original):],encoding='utf-8')
    for name in ['c64_actor_programs.h','image_driver.h']:(out/name).write_bytes((candidate/name).read_bytes())
    (out/'main.c').write_bytes((old/'main.c').read_bytes())
    builder=(BASE/'stationary-build.ps1').read_text().replace('/stationary/', '/stationary-image-v2/')
    (BASE/'stationary-image-v2-build.ps1').write_text(builder,encoding='utf-8')
    entries=[dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in list(out.iterdir())+[BASE/'stationary-image-v2-build.ps1']]
    (BASE/'stationary-image-v2-scope.json').write_text(json.dumps(dict(production_changed=False,generated=entries),indent=2)+'\n')
    print('Generated identical stationary harness with image-driver-v2')
if __name__=='__main__':main()
