"""Reuse unused Copper allocation tails for double-buffered sprite DMA."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/hardware-bruce-2026-10-31'
def main():
    old=BASE/'v2';out=BASE/'v3';out.mkdir(exist_ok=True)
    header=(old/'bruce_hw.h').read_text()
    pairs=[
      ('(2*BRUCE_HW_CHANNELS*BRUCE_HW_WORDS+2)*2','(2*BRUCE_HW_CHANNELS*BRUCE_HW_WORDS+4)*2'),
      ('static UWORD *bruce_hw_data,*bruce_hw_pointer[2][8];','static UWORD *bruce_hw_data[2],*bruce_hw_pointer[2][8];'),
      ('bruce_hw_null(void){return bruce_hw_data+2*BRUCE_HW_CHANNELS*BRUCE_HW_WORDS;}','bruce_hw_null(int buffer){return bruce_hw_data[buffer]+BRUCE_HW_CHANNELS*BRUCE_HW_WORDS;}'),
      ('if(!BL_HW_BRUCE || !bruce_hw_data)return;','if(!BL_HW_BRUCE || !bruce_hw_data[0] || !bruce_hw_data[1])return;'),
      ('bruce_hw_data+(buffer*BRUCE_HW_CHANNELS+ch)*BRUCE_HW_WORDS','bruce_hw_data[buffer]+ch*BRUCE_HW_WORDS'),
      ('bruce_hw_data+(buffer*BRUCE_HW_CHANNELS+(col>>4))*BRUCE_HW_WORDS','bruce_hw_data[buffer]+(col>>4)*BRUCE_HW_WORDS')]
    for a,b in pairs:
        assert a in header,a;header=header.replace(a,b)
    header=header.replace('bruce_hw_null()','bruce_hw_null(buffer)')
    header=header.replace('    *out=p;','    if(p>copper[buffer]+256)++bruce_hw_errors;\n    *out=p;')
    header='/* V3: each Copper list ends below byte512; its existing1024-byte\n * Chip allocation holds three DMA images plus a null header at512..791.\n * Copper stops before this tail; no extra Chip allocation. */\n'+header
    (out/'bruce_hw.h').write_text(header,encoding='utf-8')
    for variant in ['bob','sprite']:
        folder=out/variant;folder.mkdir(exist_ok=True)
        text=(old/variant/'main.c').read_text()
        for s in ['    if(BL_HW_BRUCE)bruce_hw_data=AllocMem(BRUCE_HW_BYTES,MEMF_CHIP|MEMF_CLEAR);\n','    if(bruce_hw_data)FreeMem(bruce_hw_data,BRUCE_HW_BYTES);\n']:
            assert text.count(s)==1;text=text.replace(s,'')
        s='(BL_HW_BRUCE&&!bruce_hw_data)||';assert text.count(s)==1;text=text.replace(s,'')
        s='    source_audio_copy();';assert text.count(s)==1
        text=text.replace(s,'    if(BL_HW_BRUCE)for(n=0;n<2;n++)bruce_hw_data[n]=copper[n]+256;\n'+s)
        s='        append(&p,"\\nhw_bruce_bytes=");number(&p,BL_HW_BRUCE?BRUCE_HW_BYTES:0);'
        assert text.count(s)==1;text=text.replace(s,s+'\n        append(&p,"\\nhw_bruce_extra_chip_bytes=");number(&p,0);')
        (folder/'main.c').write_text(text,encoding='utf-8')
        (out/(variant+'-build.ps1')).write_text((old/(variant+'-build.ps1')).read_text().replace('/v2/','/v3/'),encoding='utf-8')
    scope=json.loads((old/'scope.json').read_text())
    for e in scope['generated']:
        e['path']=e['path'].replace('/v2/','/v3/');e['sha256']=hashlib.sha256((ROOT/e['path']).read_bytes()).hexdigest()
    scope['scope']+=' V3 replaces the556-byte separate allocation with560 reserved bytes in existing Copper tails, safely beyond the terminated list; no extra Chip allocation.'
    (out/'scope.json').write_text(json.dumps(scope,indent=2)+'\n')
    print('Generated private v3: no additional Chip allocation')
if __name__=='__main__':main()
