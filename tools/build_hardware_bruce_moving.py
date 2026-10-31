"""Same private v3 renderer, with joystick-only moving benchmark inputs."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/hardware-bruce-2026-10-31/v3'
def main():
    out=BASE/'moving';out.mkdir(exist_ok=True)
    (out/'bruce_hw.h').write_bytes((BASE/'bruce_hw.h').read_bytes())
    for variant in ['bob','sprite']:
        folder=out/variant;folder.mkdir(exist_ok=True)
        text=(BASE/variant/'main.c').read_text()
        old='            input=frame+BL_COMBAT_WARMUP*3<3000?0:BL_FIRE;'
        assert text.count(old)==1
        new='''            {unsigned short phase=(unsigned short)(bl_c64_world_stat(0)%240);
            input=phase<40?(BL_UP|BL_RIGHT|BL_FIRE):phase<80?(BL_UP|BL_LEFT|BL_FIRE):
                  phase<120?BL_RIGHT:phase<160?BL_LEFT:phase<200?BL_UP:BL_DOWN;}'''
        (folder/'main.c').write_text(text.replace(old,new),encoding='utf-8')
        builder=(BASE/(variant+'-build.ps1')).read_text().replace('/v3/'+variant+'/', '/v3/moving/'+variant+'/')
        (out/(variant+'-build.ps1')).write_text(builder,encoding='utf-8')
    scope=json.loads((BASE/'scope.json').read_text())
    for e in scope['generated']:
        e['path']=e['path'].replace('/v3/','/v3/moving/');e['sha256']=hashlib.sha256((ROOT/e['path']).read_bytes()).hexdigest()
    scope['scope']+=' Moving test replaces only diagnostic joystick input; 240-step cycle:40 right/up/fire,40 left/up/fire,40 right,40 left,40 up,40 down. No actor/room placement injection; existing invincibility diagnostic remains. Not natural playthrough.'
    (out/'scope.json').write_text(json.dumps(scope,indent=2)+'\n');print('Built v3 moving-input pair')
if __name__=='__main__':main()
