"""Private four-row zero-contact fast path, preserving ordered hit handling."""
import hashlib,json
from pathlib import Path
from build_stationary_enemy_probe import HELPER
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/contact-zero-2026-10-31'

def candidate(text):
    end=text.index('/* GENERATED_CONTACT_CLASSES_BEGIN */')
    head,tail=text[:end],text[end:]
    head=head.replace('%d2-%d3/%d5/%a2-%a6','%d2-%d5/%a2-%a6')
    anchor='    adda.w #0x4eed,%a0\n1:\n'
    assert head.count(anchor)==1
    head=head.replace(anchor,'''    adda.w #0x4eed,%a0
    /* A long read requires even effective addresses on68000. */
    move.l %a2,%d4
    move.l %a3,%d0
    or.l %d0,%d4
    move.l %a4,%d0
    or.l %d0,%d4
    move.l %a5,%d0
    or.l %d0,%d4
    andi.w #1,%d4
1:
    /* Try once per four-row boundary. No writes occur when all twelve
     * intersections are zero, so even glyph/flag aliases are safe here.
     * Nonzero blocks execute the original row/column order unchanged. */
    cmpi.w #3,%d3
    bcs.s .Lcontact_row
    move.w %d2,%d0
    andi.w #3,%d0
    bne.s .Lcontact_row
    tst.w %d4
    bne.s .Lcontact_row
    move.l (%a2,%d2.w),%d0
    and.l (%a5,%d2.w),%d0
    bne.s .Lcontact_row
    move.l (%a3,%d2.w),%d0
    and.l 32(%a5,%d2.w),%d0
    bne.s .Lcontact_row
    move.l (%a4,%d2.w),%d0
    and.l 64(%a5,%d2.w),%d0
    bne.s .Lcontact_row
    addq.w #4,%d2
    subq.w #4,%d3
    bpl.s 1b
    bra .Lcontact_finish
.Lcontact_row:
''')
    # The backward DBRA now exceeds short-branch range (DBRA has word disp).
    head=head.replace('    move.b %d0,6(%a1)',' .Lcontact_finish:\n    move.b %d0,6(%a1)')
    return head+tail

def summary(text):
    # Keep the exact generated operand reduction behind an early empty-set
    # wrapper. A private label change only, never a new contact class map.
    text=text.replace('.text.bl_contact_classes4,','.text.bl_contact_classes4_ordered,')
    text=text.replace('.globl bl_contact_classes4\nbl_contact_classes4:', '.globl bl_contact_classes4_ordered\nbl_contact_classes4_ordered:')
    anchor='/* GENERATED_CONTACT_CLASSES_BEGIN */'
    assert text.count(anchor)==1
    wrapper='''/* The source class tables occupy69 bytes. All zero is sufficient
 * for the original four OR chains to return zero. RAM reads have no I/O
 * side effect; nonempty sets retain the exact ordered operand reduction. */
    .section .text.bl_contact_classes4,"ax"
    .globl bl_contact_classes4
bl_contact_classes4:
    move.l 4(%sp),%a0
    moveq #0,%d1
    move.b 0x4eed(%a0),%d1
'''
    for at in range(0x4eee,0x4f32,4):
        wrapper+=f'    or.l 0x{at:04x}(%a0),%d1\n    bne .Lcontact_class_nonempty\n'
    wrapper+='''    moveq #0,%d0
    rts
.Lcontact_class_nonempty:
    jmp bl_contact_classes4_ordered
'''
    return text.replace(anchor,wrapper+anchor)

EXTRA=r'''
/* Additional actual68000 differential controls. The existing C row helper
 * is the portable reference already checked against frozen$537E bytes.
 * Class/scratch bytes and batch outputs are compared explicitly. Only diagnostic code contains this loop. */
static unsigned short zero_row_cases,zero_row_errors;
static void zero_row_controls(void){
    unsigned short t,i;unsigned char saved[70],wanted[70];SourceContactBatch q,initial,expected;
    for(t=0;t<512;t++){
        unsigned short base=(unsigned short)(0xa000+(t&1));
        q.lane0=base;q.lane1=(unsigned short)(base+32);q.lane2=(unsigned short)(base+64);
        q.yy=(unsigned char)(((t>>1)&7)*32+((t>>4)&7));q.count=(unsigned char)(1+((t>>6)&7));
        if((unsigned short)q.yy+q.count>256)q.count=(unsigned char)(256-q.yy);
        q.aa=(unsigned char)t;q.xx=(unsigned char)(t*17);
        for(i=0;i<256;i++){m[0xa000+i]=(unsigned char)((i*37+t*13)^(i>>2));m[0xcae0+i]=0;}
        /* Empty blocks, exactly one contact at each column/row, and mixed
         * blocks. Odd glyphs exercise the mandatory non-long fallback. */
        if(t&16)for(i=0;i<3;i++)m[0xcae0+32*i+q.yy+(t%q.count)]=(unsigned char)(1u<<((t>>5)&7));
        if(t&32)for(i=0;i<128;i++)m[0xcae0+i]=(unsigned char)(i*19+t);
        if(t&64){q.lane1=0x4eed;q.lane2=q.yy<=0x4e?(unsigned short)(0x4e - q.yy):0x4eed;}
        for(i=0;i<69;i++){m[0x4eed+i]=(unsigned char)(i*7+t);}
        m[0x4e]=(unsigned char)t;
        saved[0]=m[0x4e];for(i=0;i<69;i++)saved[i+1]=m[0x4eed+i];initial=q;
        source_contact_scan_c(&q);expected=q;wanted[0]=m[0x4e];for(i=0;i<69;i++)wanted[i+1]=m[0x4eed+i];
        m[0x4e]=saved[0];for(i=0;i<69;i++)m[0x4eed+i]=saved[i+1];q=initial;
        bl_contact_rows8(m,&q);
        for(i=0;i<sizeof(q);i++)if(((unsigned char*)&q)[i]!=((unsigned char*)&expected)[i])++zero_row_errors;
        if(m[0x4e]!=wanted[0])++zero_row_errors;
        for(i=0;i<69;i++)if(m[0x4eed+i]!=wanted[i+1])++zero_row_errors;
        ++zero_row_cases;
    }
}
void bl_zero_row_controls(unsigned long *out){zero_row_controls();out[0]=zero_row_cases;out[1]=zero_row_errors;bl_c64_reset();}
'''

def main():
    BASE.mkdir(exist_ok=True)
    original=(ROOT/'amiga/main.c').read_text(encoding='utf-8-sig')
    original=original.replace('if(BL_AUTOTEST){capture=AllocMem(BL_CAPTURE_BYTES,MEMF_PUBLIC|MEMF_CLEAR);tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}', 'if(BL_AUTOTEST){tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}')
    original=original.replace('(BL_AUTOTEST&&(!capture||!tone))','(BL_AUTOTEST&&!tone)')
    original=original.replace('int main(void) {','extern void bl_enemy_stationary_probe(unsigned long *out);\nextern unsigned long bl_enemy_probe_ram(void);\nextern void bl_zero_row_controls(unsigned long *out);\nstatic ULONG enemy_stationary[40],enemy_stationary_mem,zero_controls[2];\nint main(void) {')
    original=original.replace('    intro_start=field_clock();','    bl_zero_row_controls(zero_controls);\n    bl_enemy_stationary_probe(enemy_stationary);enemy_stationary_mem=TypeOfMem((APTR)bl_enemy_probe_ram());\n    intro_start=field_clock();')
    report='''        append(&p,"\\nzero_row_cases=");number(&p,zero_controls[0]);
        append(&p,"\\nzero_row_errors=");number(&p,zero_controls[1]);
        append(&p,"\\nenemy_stationary_ram_type=");number(&p,enemy_stationary_mem);
        {UWORD q,j;for(q=0;q<8;q++){append(&p,"\\nenemy_stationary_");number(&p,q);append(&p,"=");
        for(j=0;j<5;j++){if(j)append(&p,",");number(&p,enemy_stationary[q*5+j]);}}}
'''
    original=original.replace('        append(&p,"\\nsource_clock_elapsed=");number(&p,source_clock_elapsed);',report+'        append(&p,"\\nsource_clock_elapsed=");number(&p,source_clock_elapsed);')
    asm=(ROOT/'amiga/contact_rows.s').read_text()
    generated=[]
    for variant in ['baseline','candidate','summary','combined']:
        folder=BASE/variant;folder.mkdir(exist_ok=True)
        (folder/'main.c').write_text(original)
        (folder/'c64_rooms.c').write_text((ROOT/'core/c64_rooms.c').read_text(encoding='utf-8-sig')+HELPER+EXTRA)
        (folder/'c64_actor_programs.h').write_bytes((ROOT/'core/c64_actor_programs.h').read_bytes())
        rows=candidate(asm) if variant in ['candidate','combined'] else asm
        (folder/'contact_rows.s').write_text(summary(rows) if variant in ['summary','combined'] else rows)
        builder=(ROOT/'amiga-build.ps1').read_text(encoding='utf-8-sig').replace('$taskRoot=$PSScriptRoot',f"$taskRoot='{ROOT}'",1)
        builder=builder.replace("'amiga/out'",f"'{folder.relative_to(ROOT).as_posix()}/out'")
        anchor='    & $compiler @sourceFlags -c (Join-Path $taskRoot $source) -o $obj'
        replacements=['    $actualPath=Join-Path $taskRoot $source']
        for source in ['amiga/main.c','core/c64_rooms.c','amiga/contact_rows.s']:
            p=(folder/Path(source).name).relative_to(ROOT).as_posix()
            replacements.append(f"    if($source -eq '{source}'){{$actualPath=Join-Path $taskRoot '{p}';$sourceFlags+='-I'+(Join-Path $taskRoot '{Path(source).parent.as_posix()}')}}")
        replacements.append('    & $compiler @sourceFlags -c $actualPath -o $obj');assert anchor in builder
        (BASE/(variant+'-build.ps1')).write_text(builder.replace(anchor,'\n'.join(replacements)))
        generated += list(folder.glob('*.*'))+[BASE/(variant+'-build.ps1')]
    def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    (BASE/'scope.json').write_text(json.dumps(dict(production_changed=False,inputs=[item(ROOT/p) for p in ['amiga/main.c','core/c64_rooms.c','core/c64_actor_programs.h','amiga/contact_rows.s','amiga/out/bruce_amiga.exe']],generated=[item(p) for p in generated],scope='No source rule/service changes; zero-only four-row grouping with original ordered hit fallback'),indent=2)+'\n')
    print('Generated private four-row zero-contact experiment')

if __name__=='__main__':main()
