"""Private direct68000 exact mask memoization; production remains unchanged."""
import hashlib,json
from pathlib import Path
from build_stationary_enemy_probe import HELPER
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/contact-memo-2026-10-31'

DECL='''typedef struct {unsigned char valid,phase,offset,carry;unsigned short pointer,pad;unsigned long input[24],output[34];} SourceAlignMemo;
typedef char SourceAlignMemoLayout[(sizeof(SourceAlignMemo)==240 && offsetof(SourceAlignMemo,input)==8 && offsetof(SourceAlignMemo,output)==104)?1:-1];
static SourceAlignMemo align_memo[3];
extern unsigned long bl_contact_align_memo(unsigned char *,unsigned long,unsigned long,unsigned long,SourceAlignMemo *);
'''
CALL='''        if(phase && !(pointer&1) && m[0x50]<3 && (pointer+96UL<=0xcae0 || pointer>=0xcb68))
            c=(unsigned char)bl_contact_align_memo(m,pointer,phase,offset,&align_memo[m[0x50]]);
        else c=(unsigned char)bl_contact_align4(m,pointer,phase,offset);'''

TEST=r'''
static unsigned long memo_control_cases,memo_control_errors;
void bl_memo_controls(unsigned long *out){
    unsigned short t,i,pass;unsigned char saved[320],wanted[320],got_c,want_c;SourceAlignMemo q;
    for(t=0;t<192;t++){
        unsigned short pointer=(unsigned short)(0xa000+((t>>4)&3)*128);
        unsigned char phase=(unsigned char)(1+t%3),off=(unsigned char)((t>>1)&7);
        q.valid=0;
        for(i=0;i<96;i++)m[pointer+i]=(unsigned char)(i*37+t*11);
        for(pass=0;pass<4;pass++){
            /* Cold, same input with changed destination, changed input,
             * then same mutated input. Cache must validate all96 bytes. */
            if(pass==2)m[pointer+(t%96)]^=(unsigned char)(1u<<((t>>3)&7));
            for(i=0;i<320;i++){m[0xcae0+i]=(unsigned char)(t*17+i*13+pass);saved[i]=m[0xcae0+i];}
            want_c=(unsigned char)bl_contact_align4(m,pointer,phase,off);
            for(i=0;i<320;i++){wanted[i]=m[0xcae0+i];m[0xcae0+i]=saved[i];}
            got_c=(unsigned char)bl_contact_align_memo(m,pointer,phase,off,&q);
            if(got_c!=want_c)++memo_control_errors;
            for(i=0;i<320;i++)if(m[0xcae0+i]!=wanted[i])++memo_control_errors;
            ++memo_control_cases;
        }
    }
    out[0]=memo_control_cases;out[1]=memo_control_errors;bl_c64_reset();
}
'''

def main():
    BASE.mkdir(exist_ok=True)
    main=(ROOT/'reference/analysis/contact-zero-2026-10-31/baseline/main.c').read_text()
    main=main.replace('bl_zero_row_controls','bl_memo_controls').replace('zero_controls','memo_controls').replace('zero_row_cases','memo_cases').replace('zero_row_errors','memo_errors')
    main=main.replace('enemy_stationary[40]','enemy_stationary[160]').replace('q<8;q++','q<32;q++')
    helper=HELPER.replace('layout<2;layout++','layout<8;layout++').replace('layout?80+4*j:40+60*j','((layout&1)?80+4*j:40+60*j)+layout/2')
    for variant in ['baseline','candidate','hashed','hashed2']:
        folder=BASE/variant;folder.mkdir(exist_ok=True)
        core=(ROOT/'core/c64_rooms.c').read_text(encoding='utf-8-sig')
        anchor='static void source_contact_align(void){'
        assert core.count(anchor)==1
        declaration=DECL.replace('align_memo[3]','align_memo[16]') if variant.startswith('hashed') else DECL
        core=core.replace(anchor,declaration+'\n'+anchor)
        old='        c=(unsigned char)bl_contact_align4(m,pointer,phase,offset);';assert core.count(old)==1
        if variant in ['candidate','hashed','hashed2']:
            call=CALL
            if variant.startswith('hashed'):
                key='((pointer>>5)^(phase<<2)^offset'+('^m[0x50]' if variant=='hashed' else '')+')&15'
                call=CALL.replace('&align_memo[m[0x50]]','&align_memo['+key+']')
            core=core.replace(old,call)
        (folder/'main.c').write_text(main)
        (folder/'c64_rooms.c').write_text(core+helper+TEST)
        (folder/'c64_actor_programs.h').write_bytes((ROOT/'core/c64_actor_programs.h').read_bytes())
        (folder/'contact_align_memo.s').write_bytes((ROOT/'tools/contact_align_memo.s').read_bytes())
        b=(ROOT/'reference/analysis/contact-zero-2026-10-31/baseline-build.ps1').read_text()
        b=b.replace('contact-zero-2026-10-31/baseline','contact-memo-2026-10-31/'+variant)
        # Rows stay canonical; only the align wrapper is changed.
        row_override="    if($source -eq 'amiga/contact_rows.s')"
        b='\n'.join(line for line in b.splitlines() if not line.startswith(row_override))+'\n'
        b=b.replace("$sources=@('amiga/start.s'", "$sources=@('reference/analysis/contact-memo-2026-10-31/"+variant+"/contact_align_memo.s','amiga/start.s'")
        (BASE/(variant+'-build.ps1')).write_text(b)
    def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    inputs=[ROOT/p for p in ['amiga/main.c','core/c64_rooms.c','core/c64_actor_programs.h','amiga/contact_align.s','amiga/contact_rows.s','amiga/out/bruce_amiga.exe']]
    variants=['baseline','candidate','hashed','hashed2']
    generated=[BASE/(v+'-build.ps1') for v in variants]+[BASE/v/p for v in variants for p in ['main.c','c64_rooms.c','c64_actor_programs.h','contact_align_memo.s']]
    (BASE/'scope.json').write_text(json.dumps(dict(production_changed=False,inputs=[item(p) for p in inputs],generated=[item(p) for p in generated],cache_bytes={'baseline':0,'candidate':720,'hashed':3840,'hashed2':3840},chip_bytes=0,scope='Exact96-byte validation, same pointer/phase/offset, nonalias even source only; replay exact written output range. All other paths use original native align. No new service or changed C64 rule.'),indent=2)+'\n')
    print('Generated exact-mask memo pilots,720/3840CPU bytes and no Chip allocation')

if __name__=='__main__':main()
