"""Correct single-playfield sprite priority; retain the v3 trial intact."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/hardware-bruce-2026-10-31'
def main():
    old=BASE/'v3';out=BASE/'v4';out.mkdir(exist_ok=True)
    for moving in ['', 'moving/']:
        src=old/moving;dst=out/moving;dst.mkdir(exist_ok=True)
        (dst/'bruce_hw.h').write_bytes((src/'bruce_hw.h').read_bytes())
        for variant in ['bob','sprite']:
            folder=dst/variant;folder.mkdir(exist_ok=True)
            text=(src/variant/'main.c').read_text()
            before='emit(&p,0x104,0);';assert text.count(before)==1
            # HRM ch7/table7-2: PF2P controls the normal single playfield.
            # Code4 puts it behind all four sprite pairs. PF1P also4.
            (folder/'main.c').write_text(text.replace(before,'emit(&p,0x104,BL_HW_BRUCE?0x24:0);'),encoding='utf-8')
            (dst/(variant+'-build.ps1')).write_text((src/(variant+'-build.ps1')).read_text().replace('/v3/','/v4/'),encoding='utf-8')
        scope=json.loads((src/'scope.json').read_text())
        for e in scope['generated']:
            e['path']=e['path'].replace('/v3/','/v4/');e['sha256']=hashlib.sha256((ROOT/e['path']).read_bytes()).hexdigest()
        scope['scope']+=' V4 changes only BPLCON2 initialization in hardware mode from0 to$24. PF2P=4 places the single playfield behind all sprite pairs; same BOB/source front priority. No movement/collision/timing rule changes.'
        (dst/'scope.json').write_text(json.dumps(scope,indent=2)+'\n')
    print('Generated v4 priority correction; v3 preserved')
if __name__=='__main__':main()
