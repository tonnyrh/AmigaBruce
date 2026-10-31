"""Build private OP0 A/B programs against the same sources and input route."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WORK=ROOT/".tmp/op1-kage"
sys.path.insert(0,str(HERE.parent/"op1-contact-budget-2026-10-31"))
from build import change, compile_program, op

def sources(mode):
    op.BASE=WORK/"op0";op.main()
    main=(op.BASE/"main.c").read_text()
    main=change(main,"if(light_route[2]==1){","""if(light_route[2]==2){
        UWORD phase=(UWORD)(step%80);
        return phase<20?BL_RIGHT:phase<40?(BL_LEFT|BL_UP):phase<60?BL_LEFT:(BL_RIGHT|BL_UP);
    }
    if(light_route[2]==1){""")
    main=change(main,"light_route[2]>1","light_route[2]>2")
    core=(ROOT/"core/c64_rooms.c").read_text()
    if mode!="reference":
        fallback=core[core.index("            m[0xe6+actor]=(unsigned char)(m[0x9e"):core.index("            for(part=0;part<4;part++){")]
        prefix=(HERE/"prefix.h").read_text().replace("/* ORIGINAL_PREFIX */",fallback)
        anchor="/* $5212-$52AC, binary path."
        core=change(core,"unsigned char part,actor,pose;","unsigned char part,actor;")
        core=change(core,fallback,"            if(actor==2)kage_first_part();else first_part(actor);\n")
        core=change(core,anchor,prefix+"\n"+anchor)
        core=change(core,"""                if(part)++m[0xe9+m[0x50]];
                m[0x4f3a]=(unsigned char)((part+1)*8);
                source_contact_frame(pointer_return[part]);source_contact_pointers();""","""                if(part){
                    ++m[0xe9+m[0x50]];m[0x4f3a]=(unsigned char)((part+1)*8);
                    source_contact_frame(pointer_return[part]);source_contact_pointers();
                }""")
        if mode=="observed":
            core="#define KAGE_COUNTS 1\n"+core
            main=change(main,"static void light_config(void){","extern unsigned long kage_counts[3];\nstatic void light_config(void){")
            main=change(main,"light_started=1;light_start_step=step;","kage_counts[0]=kage_counts[1]=kage_counts[2]=0;light_started=1;light_start_step=step;")
            anchor='        append(&p,"\\nrestored_os=1\\nfinished=1\\n");'
            main=change(main,anchor,'''        append(&p,"\\nkage_hit_fill_bypass=");for(k=0;k<3;k++){if(k)append(&p,",");number(&p,kage_counts[k]);}
'''+anchor)
    return main,core

def build_mode(mode):
    folder=WORK/mode;folder.mkdir(parents=True,exist_ok=True)
    main,core=sources(mode);(folder/"main.c").write_text(main);(folder/"c64_rooms.c").write_text(core)
    compile_program(folder,None if mode=="reference" else WORK/"reference")
if __name__=="__main__":build_mode(sys.argv[1])
