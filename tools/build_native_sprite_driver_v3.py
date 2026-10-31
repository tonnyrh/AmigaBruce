"""Compile the isolated native image driver for speed, not global -Os."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'reference/analysis/enemy-cost-2026-10-30'
def main():
    old=BASE/'image-driver-v2';out=BASE/'image-driver-v3';out.mkdir(exist_ok=True)
    for name in ['c64_rooms.c','c64_actor_programs.h']:(out/name).write_bytes((old/name).read_bytes())
    helper=(old/'image_driver.h').read_text()
    helper=helper.replace('static unsigned short image_destination(', 'SOURCE_INLINE unsigned short image_destination(')
    helper=helper.replace('static unsigned char image_driver_safe(', 'SOURCE_INLINE unsigned char image_driver_safe(')
    helper=helper.replace('static unsigned char source_image_driver(', '#if defined(__m68k__) && defined(__GNUC__)\n__attribute__((optimize("O2")))\n#endif\nstatic unsigned char source_image_driver(')
    (out/'image_driver.h').write_text(helper,encoding='utf-8')
    for suffix in ['-bridge.c','-build.ps1']:
        (BASE/('image-driver-v3'+suffix)).write_text((BASE/('image-driver-v2'+suffix)).read_text().replace('image-driver-v2/','image-driver-v3/'),encoding='utf-8')
    (BASE/'image-driver-v3-scope.json').write_text(json.dumps(dict(production_changed=False,change='O2 attribute on source image driver; inline read-only guards; unchanged bodies.',generated=[dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in list(out.iterdir())+[BASE/'image-driver-v3-bridge.c',BASE/'image-driver-v3-build.ps1']]),indent=2)+'\n')
    print('Generated speed-compiled image driver')
if __name__=='__main__':main()
