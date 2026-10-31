"""Private empty-table specialization of complete source body/class helpers."""
import hashlib,json,re
from pathlib import Path
from build_stationary_enemy_probe import HELPER
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'reference/analysis/contact-empty-2026-10-31'

def candidate(text):
    start=text.index('    .section .text.bl_contact_classify_full,')
    end=text.index('    .section .text.bl_contact_swap_lane,',start)
    classes=text[start:end]
    start_body=text.index('    .section .text.bl_contact_body,')
    body=text[start_body:]
    assert classes.count('jsr .Lcontact_swap')==3 and body.count('jsr .Lcontact_swap')==3
    ordered_classes=classes.replace('bl_contact_classify_full','bl_contact_classify_full_ordered')
    zero_classes=classes.replace('bl_contact_classify_full','bl_contact_classify_full_zero').replace('.Lclass_','.Lclass_zero_')
    zero_classes=zero_classes.replace('jsr .Lcontact_swap','moveq #0,%d0')
    zero_classes=zero_classes.replace('    move.l %a0,-(%sp)\n    jsr bl_contact_classes4\n    addq.l #4,%sp','    moveq #0,%d0')
    ordered_body=body.replace('bl_contact_body','bl_contact_body_ordered').replace('jsr bl_contact_classify_full','jsr bl_contact_classify_full_ordered')
    zero_body=body.replace('bl_contact_body','bl_contact_body_zero').replace('.Lbody_','.Lbody_zero_')
    zero_body=zero_body.replace('jsr bl_contact_classify_full','jsr bl_contact_classify_full_zero').replace('jsr .Lcontact_swap','moveq #0,%d0')
    text=text[:start]+ordered_classes+zero_classes+text[end:start_body]+ordered_body+zero_body
    front='''/* Empty69-byte class table: exchanges of zero bytes and four OR
 * reductions have no RAM effect. Preserve every original conditional DEC,
 * XOR, snapshot, guest JSR byte and published register. No service inside.
 * Nonempty input executes the prior assembly unchanged. */
    .section .text.bl_contact_empty69,"ax"
.Lcontact_empty69:
    moveq #0,%d0
    move.b 0x4eed(%a0),%d0
'''
    for at in range(0x4eee,0x4f32,4):front+=f'    or.l 0x{at:04x}(%a0),%d0\n    bne.s .Lcontact_empty_return\n'
    front+='''.Lcontact_empty_return:
    rts
'''
    # The last failure displacement can exceed short range at the first OR.
    front=front.replace('bne.s .Lcontact_empty_return','bne .Lcontact_empty_return')
    for name in ['bl_contact_classify_full','bl_contact_body']:
        front+=f'''    .section .text.{name},"ax"
    .globl {name}
{name}:
    move.l 4(%sp),%a0
    jsr .Lcontact_empty69
    bne.s .L{name}_fallback
    jmp {name}_zero
.L{name}_fallback:
    jmp {name}_ordered
'''
    return text+'\n'+front

TEST=r'''
static unsigned long empty_cases,empty_errors;
void bl_empty_controls(unsigned long *out){
    unsigned short t,i,op;unsigned char saved[597],wanted[597],wr[13],gr[13];
    for(t=0;t<768;t++)for(op=0;op<2;op++){
        for(i=0;i<512;i++)m[i]=(unsigned char)(t+i*7);
        for(i=0;i<85;i++)m[0x4eec+i]=(unsigned char)(i*11+t);
        for(i=0;i<69;i++)m[0x4eed+i]=0;
        if(t&1)m[0x4eed+t%69]=(unsigned char)(1+(t&127));
        m[0x50]=(unsigned char)(t%3);
        m[0x4f32]=(t&2)?(unsigned char)(t%5==0?255:t%5==1?2:1):0;
        m[0x4f33]=(t&4)?(unsigned char)(t%7==0?255:t%7==1?2:1):0;
        m[0x4f34]=(t&8)?(unsigned char)(t%11==0?255:t%11==1?2:1):0;
        for(i=0;i<512;i++){saved[i]=m[i];}
        for(i=0;i<85;i++)saved[512+i]=m[0x4eec+i];
        source_prepare_registers(t,1,(unsigned char)(t/3));
        if(op)source_contact_body_c();else source_contact_classes_c();
        bl_c64_actor_registers(wr);
        for(i=0;i<512;i++){wanted[i]=m[i];}
        for(i=0;i<85;i++)wanted[512+i]=m[0x4eec+i];
        for(i=0;i<512;i++){m[i]=saved[i];}
        for(i=0;i<85;i++)m[0x4eec+i]=saved[512+i];
        source_prepare_registers(t,1,(unsigned char)(t/3));
        if(op)source_contact_body();else source_contact_classes();
        bl_c64_actor_registers(gr);
        for(i=0;i<512;i++)if(m[i]!=wanted[i])++empty_errors;
        for(i=0;i<85;i++)if(m[0x4eec+i]!=wanted[512+i])++empty_errors;
        for(i=0;i<13;i++)if(gr[i]!=wr[i])++empty_errors;
        ++empty_cases;
    }
    out[0]=empty_cases;out[1]=empty_errors;bl_c64_reset();
}
'''

def main():
    BASE.mkdir(exist_ok=True)
    main=(ROOT/'reference/analysis/contact-zero-2026-10-31/baseline/main.c').read_text()
    main=main.replace('bl_zero_row_controls','bl_empty_controls').replace('zero_controls','empty_controls').replace('zero_row_cases','empty_cases').replace('zero_row_errors','empty_errors')
    asm=(ROOT/'amiga/contact_prepare.s').read_text()
    for variant in ['baseline','candidate']:
        folder=BASE/variant;folder.mkdir(exist_ok=True)
        (folder/'main.c').write_text(main)
        (folder/'c64_rooms.c').write_text((ROOT/'core/c64_rooms.c').read_text(encoding='utf-8-sig')+HELPER+TEST)
        (folder/'c64_actor_programs.h').write_bytes((ROOT/'core/c64_actor_programs.h').read_bytes())
        (folder/'contact_prepare.s').write_text(candidate(asm) if variant=='candidate' else asm)
        b=(ROOT/'reference/analysis/contact-zero-2026-10-31/baseline-build.ps1').read_text()
        b=b.replace('contact-zero-2026-10-31/baseline','contact-empty-2026-10-31/'+variant)
        b=b.replace("if($source -eq 'amiga/contact_rows.s')", "if($source -eq 'amiga/contact_prepare.s')").replace("contact-empty-2026-10-31/"+variant+"/contact_rows.s'","contact-empty-2026-10-31/"+variant+"/contact_prepare.s'")
        (BASE/(variant+'-build.ps1')).write_text(b)
    def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    generated=[BASE/(v+'-build.ps1') for v in ['baseline','candidate']]+[BASE/v/p for v in ['baseline','candidate'] for p in ['main.c','c64_rooms.c','c64_actor_programs.h','contact_prepare.s']]
    (BASE/'scope.json').write_text(json.dumps(dict(production_changed=False,inputs=[item(ROOT/p) for p in ['amiga/main.c','core/c64_rooms.c','core/c64_actor_programs.h','amiga/contact_prepare.s','amiga/out/bruce_amiga.exe']],generated=[item(p) for p in generated],scope='Whole service-free body/classes specialization only when all69 class bytes are zero; retain source guest frames, DEC/XOR and register outputs; unchanged ordered fallback'),indent=2)+'\n')
    print('Generated whole empty-class/body specialization')

if __name__=='__main__':main()
