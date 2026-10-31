"""Isolated native accumulator register with explicit public/callback ABI bridges.

All C64 RAM, source control flow and flag calculations remain unchanged.
"""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'reference/analysis/native-d7-2026-10-31'
TOKEN=re.compile(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[A-Za-z_]\w*|->|\S',re.S)

def functions(text):
    # Ignore directives (including multiline macros), comments and literals.
    text=re.sub(r'(?m)^\s*#(?:[^\n]*\\\n)*[^\n]*','',text)
    tokens=[m.group() for m in TOKEN.finditer(text) if not m.group().startswith(('/*','//','"',"'"))]
    result={};depth=0;start=0;active=None
    for i,t in enumerate(tokens):
        if t=='{':
            if depth==0 and i and tokens[i-1]==')':
                level=1;j=i-2
                while j>=start:
                    if tokens[j]==')':level+=1
                    elif tokens[j]=='(':
                        level-=1
                        if not level:break
                    j-=1
                if j>start and re.fullmatch(r'\w+',tokens[j-1]):
                    name=tokens[j-1];active=(name,tokens[start:j-1],tokens[j+1:i-1],i+1)
            depth+=1
        elif t=='}':
            depth-=1
            if depth==0:
                if active:
                    name,head,args,at=active;body=tokens[at:i]
                    # A conservative direct-a test. Local shadows only add
                    # an unnecessary bridge; members are never guest A.
                    direct=any(q=='a' and (k==0 or body[k-1] not in ['.','->']) for k,q in enumerate(body))
                    calls={body[k] for k in range(len(body)-1) if body[k+1]=='(' and re.fullmatch(r'\w+',body[k])}
                    n=0;nest=0
                    if args and args!=['void']:
                        n=1
                        for q in args:
                            if q=='(':nest+=1
                            elif q==')':nest-=1
                            elif q==',' and not nest:n+=1
                    if name in result:
                        result[name]['calls']|=calls;result[name]['direct_a']|=direct
                    else:result[name]=dict(static='static' in head or 'SOURCE_INLINE' in head or 'SOURCE_NOINLINE' in head,args=n,arg_tokens=args,direct_a=direct,calls=calls)
                    active=None
                start=i+1
        elif t==';' and not depth:start=i+1
    return result

ABI_CORE=r'''
unsigned long bl_d7_probe_abi(long p0,long p1,long p2,long p3,long p4,long p5,long p6,long p7){
    unsigned long value=(unsigned long)p0^((unsigned long)p1<<1)^((unsigned long)p2<<2)^((unsigned long)p3<<3)^((unsigned long)p4<<4)^((unsigned long)p5<<5)^((unsigned long)p6<<6)^((unsigned long)p7<<7);
    a=(unsigned char)(value>>7);return value;
}
'''

ABI_MAIN=r'''
extern unsigned long bl_d7_probe_abi(long,long,long,long,long,long,long,long);
static ULONG d7_abi_cases,d7_abi_errors;
static __attribute__((noinline)) void d7_abi_controls(void){
    ULONG t,got,sentinel,wanted;UBYTE regs[13];
    for(t=0;t<256;t++){
        wanted=t^((t+1)<<1)^((t+2)<<2)^((t+3)<<3)^((t+4)<<4)^((t+5)<<5)^((t+6)<<6)^((t+7)<<7);
        __asm__ volatile("move.l #0x5a17c3e9,%%d7" ::: "d7");
        got=bl_d7_probe_abi(t,t+1,t+2,t+3,t+4,t+5,t+6,t+7);
        __asm__ volatile("move.l %%d7,%0" : "=d"(sentinel));
        if(got!=wanted || sentinel!=0x5a17c3e9UL)++d7_abi_errors;
        bl_c64_actor_registers(regs);if(regs[0]!=(UBYTE)(wanted>>7))++d7_abi_errors;
        ++d7_abi_cases;
    }
    bl_c64_reset();
}
'''

CALLBACKS='''
#if defined(__m68k__)
static inline __attribute__((always_inline)) void d7_io_service(void){bruce_a_mirror=a;io_service();a=bruce_a_mirror;}
static inline __attribute__((always_inline)) void d7_load_service(long loading){bruce_a_mirror=a;load_service(loading);a=bruce_a_mirror;}
#else
static void d7_io_service(void){io_service();}
static void d7_load_service(long loading){load_service(loading);}
#endif
'''
PAINTERS='''
#if defined(__m68k__)
static inline __attribute__((always_inline)) void d7_tile_painter(const BlC64Paint *p){bruce_a_mirror=a;tile_painter(p);a=bruce_a_mirror;}
static inline __attribute__((always_inline)) void d7_block_painter(const BlC64Block *p){bruce_a_mirror=a;block_painter(p);a=bruce_a_mirror;}
#else
static void d7_tile_painter(const BlC64Paint *p){tile_painter(p);}
static void d7_block_painter(const BlC64Block *p){block_painter(p);}
#endif
'''

def main():
    BASE.mkdir(exist_ok=True);parent=(ROOT/'core/c64_rooms.c').read_text(encoding='utf-8-sig')
    main=(ROOT/'amiga/main.c').read_text(encoding='utf-8-sig')
    main=main.replace('if(BL_AUTOTEST){capture=AllocMem(BL_CAPTURE_BYTES,MEMF_PUBLIC|MEMF_CLEAR);tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}','if(BL_AUTOTEST){tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}')
    main=main.replace('(BL_AUTOTEST&&(!capture||!tone))','(BL_AUTOTEST&&!tone)')
    main=main.replace('int main(void) {',ABI_MAIN+'\nint main(void) {')
    main=main.replace('    intro_start=field_clock();','    d7_abi_controls();\n    intro_start=field_clock();')
    main=main.replace('        append(&p,"\\nsource_clock_elapsed=");','        append(&p,"\\nd7_abi_cases=");number(&p,d7_abi_cases);\n        append(&p,"\\nd7_abi_errors=");number(&p,d7_abi_errors);\n        append(&p,"\\nsource_clock_elapsed=");')
    for variant in ['baseline','candidate']:
        folder=BASE/variant;folder.mkdir(exist_ok=True);core=parent+ABI_CORE
        actor=(ROOT/'core/c64_actor_programs.h').read_text();sfx=(ROOT/'core/c64_sfx.h').read_text()
        if variant=='candidate':
            core=core.replace('static unsigned char a,x,y,c,z,n,v,d,sp,loaded=255,transition_pending;','''#if defined(__m68k__)
register unsigned char a __asm__("d7");
volatile unsigned char bruce_a_mirror;
#else
static unsigned char a;
#endif
static unsigned char x,y,c,z,n,v,d,sp,loaded=255,transition_pending;''')
            for old,new in [('io_service()','d7_io_service()'),('load_service(1)','d7_load_service(1)'),('load_service(0)','d7_load_service(0)'),('tile_painter(&paint_request)','d7_tile_painter(&paint_request)'),('block_painter(&request)','d7_block_painter(&request)')]:
                core=core.replace(old,new);actor=actor.replace(old,new);sfx=sfx.replace(old,new)
            core=core.replace('static void (*load_service)(long);','static void (*load_service)(long);\n'+CALLBACKS)
            core=core.replace('static BlC64BlockPainter block_painter;','static BlC64BlockPainter block_painter;\n'+PAINTERS)
            graph={}
            for source in [core,actor,sfx]:
                for name,q in functions(source).items():
                    if name in graph:graph[name]['calls']|=q['calls'];graph[name]['direct_a']|=q['direct_a']
                    else:graph[name]=q
            needs={name for name,q in graph.items() if q['direct_a']}
            while True:
                new={name for name,q in graph.items() if q['calls']&needs}|needs
                if new==needs:break
                needs=new
            public={name:q for name,q in graph.items() if not q['static']}
            assert len(public)>90 and 'bl_c64_read' in public and 'bl_c64_world_step' in needs
            assert 'bl_c64_read' not in needs and 'bl_c64_actor_registers' in needs
            prefix='#if defined(__m68k__)\n'+''.join('#define '+name+' '+name+'_d7\n' for name in public)+'#endif\n'
            # In-object aliases preserve the zero-cost ABI of readonly APIs.
            aliases='#if defined(__m68k__)\n__asm__(\n'+''.join('".globl '+name+'\\n.set '+name+','+name+'_d7\\n"\n' for name in public if name not in needs)+');\n#endif\n'
            core=prefix+core+'\n'+aliases
            metadata={name:{k:sorted(v) if isinstance(v,set) else v for k,v in q.items()}|{'bridge':name in needs} for name,q in public.items()}
            (folder/'abi-plan.json').write_text(json.dumps(metadata,indent=2)+'\n')
            # Actual compiled symbols filter conditional diagnostic APIs.
            (folder/'abi-wrappers.s').write_text('/* Generated after compiling core. */\n')
        (folder/'main.c').write_text(main);(folder/'c64_rooms.c').write_text(core)
        (folder/'c64_actor_programs.h').write_text(actor);(folder/'c64_sfx.h').write_text(sfx)
        b=(ROOT/'reference/analysis/contact-zero-2026-10-31/baseline-build.ps1').read_text().replace('contact-zero-2026-10-31/baseline','native-d7-2026-10-31/'+variant)
        b='\n'.join(line for line in b.splitlines() if not line.startswith("    if($source -eq 'amiga/contact_rows.s')"))+'\n'
        if variant=='candidate':
            anchor='$program=Join-Path $out'
            at=b.index(anchor)
            bridge='''& python (Join-Path $taskRoot 'tools/generate_native_d7_wrappers.py')
if($LASTEXITCODE){throw 'D7 ABI generation failed'}
$bridge=Join-Path $out 'abi-wrappers.o'
& $compiler @flags -c (Join-Path $taskRoot 'reference/analysis/native-d7-2026-10-31/candidate/abi-wrappers.s') -o $bridge
if($LASTEXITCODE){throw 'D7 ABI bridge assembly failed'}
$objects+=$bridge
'''
            b=b[:at]+bridge+b[at:]
        (BASE/(variant+'-build.ps1')).write_text(b)
    print('Generated isolated D7 accumulator and ABI/callback bridges')

if __name__=='__main__':main()
