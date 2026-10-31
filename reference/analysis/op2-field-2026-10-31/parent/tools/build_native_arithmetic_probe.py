"""Use68000 byte arithmetic flags for binary ADC/SBC; decimal path unchanged."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'reference/analysis/native-arithmetic-2026-10-31'

def arithmetic(text,name):
    original=re.search(r'static void '+name+r'\(unsigned char q\)\{.*?\n\}',text,re.S)[0]
    native='''#if defined(__m68k__)
    if(!d){
        unsigned char value=a,carry='''+('c' if name=='adc' else '(unsigned char)(c^1)')+''';
        /* LSR of a0/1 input sets X and leaves Z=1. ADDX/SUBX then gives
         * ordinary byte Z (not a stale multi-precision sticky zero).
         * Capture all CCR conditions before normalizing their0/255 bytes. */
        __asm__ volatile(
            "lsr.b #1,%1\\n\\t"
            "'''+('addx' if name=='adc' else 'subx')+'''.b %6,%0\\n\\t"
            "'''+('scs' if name=='adc' else 'scc')+''' %2\\n\\tseq %3\\n\\tsmi %4\\n\\tsvs %5\\n\\t"
            "neg.b %2\\n\\tneg.b %3\\n\\tneg.b %4\\n\\tneg.b %5"
            : "+&d"(value),"+&d"(carry),"=m"(c),"=m"(z),"=m"(n),"=m"(v)
            : "d"(q) : "cc");
        a=value;return;
    }
#endif
'''
    return original,original.replace('{\n','{\n'+native,1)

PACKED_DECL='''static unsigned char a,x,y,d,sp,loaded=255,transition_pending;
#if defined(__m68k__)
/* Internal backend representation only. Individual virtual flags keep
 * byte0/1 semantics; an arithmetic instruction can publish all four once. */
static unsigned long bruce_native_flags __attribute__((used,aligned(4)));
extern unsigned char c __asm__("bruce_native_c");
extern unsigned char z __asm__("bruce_native_z");
extern unsigned char n __asm__("bruce_native_n");
extern unsigned char v __asm__("bruce_native_v");
__asm__(".set bruce_native_c,bruce_native_flags\\n"
        ".set bruce_native_z,bruce_native_flags+1\\n"
        ".set bruce_native_n,bruce_native_flags+2\\n"
        ".set bruce_native_v,bruce_native_flags+3\\n");
static const unsigned long bruce_ccr_flags[16]={TABLE};
#else
static unsigned char c,z,n,v;
#endif'''

UNION_DECL='''static unsigned char a,x,y,d,sp,loaded=255,transition_pending;
#if defined(__m68k__)
typedef union {
    unsigned long word;
    struct {unsigned char carry,overflow,zero,negative;} byte;
    struct {unsigned short cv,nz;} half;
} BruceNativeFlags;
static BruceNativeFlags bruce_flags __attribute__((aligned(4)));
typedef char BruceFlagLayout[(sizeof(BruceNativeFlags)==4 && offsetof(BruceNativeFlags,byte.zero)==2 && offsetof(BruceNativeFlags,half.nz)==2)?1:-1];
#define c bruce_flags.byte.carry
#define v bruce_flags.byte.overflow
#define z bruce_flags.byte.zero
#define n bruce_flags.byte.negative
static const unsigned long bruce_ccr_flags[16]={TABLE};
#else
static unsigned char c,z,n,v;
#endif'''

def packed_arithmetic(original,name):
    native='''#if defined(__m68k__)
    if(!d){
        unsigned char value=a;unsigned short carry='''+('c' if name=='adc' else '(unsigned char)(c^1)')+''';
        /* 68000 (A500 target) permits reading SR in user mode. Only the
         * four low CCR bits index this64-byte table; no SR write occurs.
         * LSR gives X=carry/borrow and Z=1 before sticky-zero ADDX/SUBX. */
        __asm__ volatile(
            "lsr.b #1,%1\\n\\t'''+('addx' if name=='adc' else 'subx')+'''.b %3,%0\\n\\t"
            "move.w %%sr,%1\\n\\tandi.w #15,%1\\n\\t"
'''+('            "eori.w #1,%1\\n\\t"\n' if name=='sbc' else '')+'''            "lsl.w #2,%1\\n\\tmove.l (%4,%1.w),%2"
            : "+&d"(value),"+&d"(carry),"=m"(bruce_native_flags)
            : "d"(q),"a"(bruce_ccr_flags) : "cc","memory");
        a=value;return;
    }
#endif
'''
    return original.replace('{\n','{\n'+native,1)

TEST=r'''
static unsigned long math_cases,math_errors;
void bl_math_controls(unsigned long *out){
    unsigned short op,aa,qq,cc;unsigned char expected[5];
    for(op=0;op<2;op++)for(aa=0;aa<256;aa++)for(qq=0;qq<256;qq++)for(cc=0;cc<2;cc++){
        a=(unsigned char)aa;c=(unsigned char)cc;d=0;
        if(op)sbc_reference((unsigned char)qq);else adc_reference((unsigned char)qq);
        expected[0]=a;expected[1]=c;expected[2]=z;expected[3]=n;expected[4]=v;
        a=(unsigned char)aa;c=(unsigned char)cc;d=0;
        if(op)sbc_native_probe((unsigned char)qq);else adc_native_probe((unsigned char)qq);
        if(a!=expected[0] || c!=expected[1] || z!=expected[2] || n!=expected[3] || v!=expected[4] || d)++math_errors;
        ++math_cases;
    }
    out[0]=math_cases;out[1]=math_errors;bl_c64_reset();
}
'''

NZ_TEST=r'''
void bl_nz_controls(unsigned long *out){
    unsigned short value,cv;unsigned long cases=0,errors=0;
    for(value=0;value<256;value++)for(cv=0;cv<4;cv++){
        a=(unsigned char)(value^0x5a);x=17;y=41;sp=133;d=(value>>5)&1;
        c=cv&1;v=(cv>>1)&1;z=1;n=1;
        NZ(value);
        if(z!=(value==0) || n!=(value>=128) || c!=(cv&1) || v!=((cv>>1)&1) ||
           a!=(unsigned char)(value^0x5a) || x!=17 || y!=41 || sp!=133 || d!=((value>>5)&1))++errors;
        ++cases;
    }
    out[0]=cases;out[1]=errors;bl_c64_reset();
}
'''

def main():
    BASE.mkdir(exist_ok=True)
    parent=(ROOT/'core/c64_rooms.c').read_text(encoding='utf-8-sig')
    pairs={name:arithmetic(parent,name) for name in ['adc','sbc']}
    main=(ROOT/'amiga/main.c').read_text(encoding='utf-8-sig')
    main=main.replace('if(BL_AUTOTEST){capture=AllocMem(BL_CAPTURE_BYTES,MEMF_PUBLIC|MEMF_CLEAR);tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}','if(BL_AUTOTEST){tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}')
    main=main.replace('(BL_AUTOTEST&&(!capture||!tone))','(BL_AUTOTEST&&!tone)')
    main=main.replace('int main(void) {','extern void bl_math_controls(unsigned long *out);\nstatic ULONG math_controls[2];\nint main(void) {')
    main=main.replace('    intro_start=field_clock();','    bl_math_controls(math_controls);\n    intro_start=field_clock();')
    report='''        append(&p,"\\nmath_cases=");number(&p,math_controls[0]);
        append(&p,"\\nmath_errors=");number(&p,math_controls[1]);
'''
    main=main.replace('        append(&p,"\\nsource_clock_elapsed=");number(&p,source_clock_elapsed);',report+'        append(&p,"\\nsource_clock_elapsed=");number(&p,source_clock_elapsed);')
    variants=['baseline','candidate','packed','union','union-nz']
    for variant in variants:
        folder=BASE/variant;folder.mkdir(exist_ok=True);core=parent
        if variant=='packed':
            table=','.join('0x%08xUL'%(((i&1)<<24)|(((i>>2)&1)<<16)|(((i>>3)&1)<<8)|((i>>1)&1)) for i in range(16))
            core=core.replace('static unsigned char a,x,y,c,z,n,v,d,sp,loaded=255,transition_pending;',PACKED_DECL.replace('TABLE',table))
        if variant.startswith('union'):
            table=','.join('0x%08xUL'%(((i&1)<<24)|(((i>>1)&1)<<16)|(((i>>2)&1)<<8)|((i>>3)&1)) for i in range(16))
            core=core.replace('static unsigned char a,x,y,c,z,n,v,d,sp,loaded=255,transition_pending;',UNION_DECL.replace('TABLE',table))
            if variant=='union-nz':
                old_nz='#define NZ(q) do{z=((unsigned char)(q)==0);n=(((unsigned char)(q)&128)!=0);}while(0)'
                new_nz='''#if defined(__m68k__)
#define NZ(q) do{unsigned char nz_value=(unsigned char)(q);bruce_flags.half.nz=(unsigned short)((nz_value==0?256:0)|(nz_value>>7));}while(0)
#else
'''+old_nz+'\n#endif'
                assert core.count(old_nz)==1;core=core.replace(old_nz,new_nz)
        for name,(old,new) in pairs.items():
            if variant=='packed' or variant.startswith('union'):new=packed_arithmetic(old,name)
            if variant.startswith('union'):
                new=new.replace('bruce_native_flags','bruce_flags.word').replace('volatile(','(').replace(': "cc","memory"',': "cc"')
            if variant!='baseline':core=core.replace(old,new)
            reference=old.replace('NZ(a);','z=(a==0);n=((a&128)!=0);') if variant.startswith('union') else old
            core+='\n'+reference.replace('static void '+name+'(','static void '+name+'_reference(')+'\n'
            core+='\n'+new.replace('static void '+name+'(','static void '+name+'_native_probe(')+'\n'
        variant_main=main
        if variant=='union-nz':
            variant_main=variant_main.replace('static ULONG math_controls[2];','extern void bl_nz_controls(unsigned long *out);\nstatic ULONG math_controls[2],nz_controls[2];')
            variant_main=variant_main.replace('    bl_math_controls(math_controls);','    bl_math_controls(math_controls);bl_nz_controls(nz_controls);')
            variant_main=variant_main.replace('        append(&p,"\\nmath_cases=");', '        append(&p,"\\nnz_cases=");number(&p,nz_controls[0]);\n        append(&p,"\\nnz_errors=");number(&p,nz_controls[1]);\n        append(&p,"\\nmath_cases=");')
        (folder/'main.c').write_text(variant_main)
        (folder/'c64_rooms.c').write_text(core+TEST+(NZ_TEST if variant=='union-nz' else ''))
        (folder/'c64_actor_programs.h').write_bytes((ROOT/'core/c64_actor_programs.h').read_bytes())
        b=(ROOT/'reference/analysis/contact-zero-2026-10-31/baseline-build.ps1').read_text()
        b=b.replace('contact-zero-2026-10-31/baseline','native-arithmetic-2026-10-31/'+variant)
        b='\n'.join(line for line in b.splitlines() if not line.startswith("    if($source -eq 'amiga/contact_rows.s')"))+'\n'
        (BASE/(variant+'-build.ps1')).write_text(b)
    def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    generated=[BASE/(v+'-build.ps1') for v in variants]+[BASE/v/p for v in variants for p in ['main.c','c64_rooms.c','c64_actor_programs.h']]
    (BASE/'scope.json').write_text(json.dumps(dict(production_changed=False,inputs=[item(ROOT/p) for p in ['core/c64_rooms.c','core/c64_actor_programs.h','amiga/main.c','amiga/out/bruce_amiga.exe']],generated=[item(p) for p in generated],scope='Binary arithmetic only:68000 ADDX/SUBX and CCR flags, full262144 native input combinations. D=1 path retains previous C unchanged; no new source rule or service seam.'),indent=2)+'\n')
    print('Generated binary68000 arithmetic pilot')

if __name__=='__main__':main()
