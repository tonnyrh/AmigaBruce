"""Keep the unchanged 64KiB source RAM base in A5, with public ABI bridges."""
import json,re
from pathlib import Path
from build_native_d7_probe import functions
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/native-a5-2026-10-31'

def main():
    BASE.mkdir(exist_ok=True)
    core=(ROOT/'core/c64_rooms.c').read_text(encoding='utf-8-sig')
    actor=(ROOT/'core/c64_actor_programs.h').read_text()
    sfx=(ROOT/'core/c64_sfx.h').read_text()
    graph={}
    for source in [core,actor,sfx]:
        # Reuse the conservative token/call parser with RAM as the tracked name.
        for name,q in functions(re.sub(r'\bm\b','a',source)).items():
            if name in graph:
                graph[name]['calls']|=q['calls'];graph[name]['direct_a']|=q['direct_a']
            else:graph[name]=q
    needs={name for name,q in graph.items() if q['direct_a']}
    while True:
        new=needs|{name for name,q in graph.items() if q['calls']&needs}
        if new==needs:break
        needs=new
    public={name:q for name,q in graph.items() if not q['static']}
    assert 'bl_c64_read' in needs and 'bl_c64_world_step' in needs
    prefix='#if defined(__m68k__)\n'+''.join(f'#define {name} {name}_a5\n' for name in public)+'#endif\n'
    core=core.replace('static unsigned char m[65536] BL_VIC_ALIGNED;','''#if defined(__m68k__)
unsigned char bruce_m_storage[65536] BL_VIC_ALIGNED;
register unsigned char *m __asm__("a5");
#else
static unsigned char m[65536] BL_VIC_ALIGNED;
#endif''')
    aliases='#if defined(__m68k__)\n__asm__(\n'+''.join(f'".globl {name}\\n.set {name},{name}_a5\\n"\n' for name in public if name not in needs)+');\n#endif\n'
    core=prefix+core+'\n'+aliases
    folder=BASE/'candidate';folder.mkdir(exist_ok=True)
    (folder/'c64_rooms.c').write_text(core)
    (folder/'c64_actor_programs.h').write_text(actor)
    (folder/'c64_sfx.h').write_text(sfx)
    # Identical bounded benchmark main to the contact-zero parent, without
    # its extra assembly controls, so use the unmodified canonical main.
    main=(ROOT/'amiga/main.c').read_text(encoding='utf-8-sig')
    main=main.replace('if(BL_AUTOTEST){capture=AllocMem(BL_CAPTURE_BYTES,MEMF_PUBLIC|MEMF_CLEAR);tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}','if(BL_AUTOTEST){tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}')
    main=main.replace('(BL_AUTOTEST&&(!capture||!tone))','(BL_AUTOTEST&&!tone)')
    (folder/'main.c').write_text(main)
    (folder/'abi-plan.json').write_text(json.dumps({name:{'bridge':name in needs,'args':q['args']} for name,q in public.items()},indent=2)+'\n')
    build=(ROOT/'reference/analysis/native-d7-2026-10-31/candidate-build.ps1').read_text()
    build=build.replace('native-d7-2026-10-31','native-a5-2026-10-31').replace('generate_native_d7_wrappers.py','generate_native_a5_wrappers.py')
    (BASE/'candidate-build.ps1').write_text(build)
    for name in ['run-private.ps1','test-perf-private.ps1']:
        runner=(ROOT/'reference/analysis/native-d7-2026-10-31'/name).read_text().replace('native-d7','native-a5')
        runner=runner.replace("    if($run['d7_abi_cases'] -ne '256' -or $run['d7_abi_errors'] -ne '0'){throw 'D7 ABI controls failed'}\n",'')
        (BASE/name).write_text(runner)
    print('Generated isolated fixed A5 RAM base; no C64 RAM or rules changed')

if __name__=='__main__':main()
