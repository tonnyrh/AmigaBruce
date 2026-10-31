"""Build the capped lookup experiment separately from the route/timer probe."""
import build
ROOT,OUT,HERE=build.ROOT,build.OUT,build.HERE
folder=OUT/"replay";folder.mkdir(exist_ok=True)
main=(OUT/"op0/main.c").read_text();c=(ROOT/"core/c64_rooms.c").read_text()
c=build.change(c,'#include "c64_actor_programs.h"',(HERE/"replay.h").read_text()+'\n#include "c64_actor_programs.h"')
main=build.change(main,"static void light_config(void){",'''extern void bench_run(unsigned char *,unsigned char *,unsigned long);
extern unsigned long bench_result[8];
static UBYTE *case_memory,*case_tape;
static LONG case_bytes;
unsigned long probe_clock_public(void){return line_clock();}
static void light_config(void){''')
main=build.change(main,'    intro_decode(buffers[1]);','''    {
        BPTR file=Open((CONST_STRPTR)"DH1:replay.bin",MODE_OLDFILE);
        case_memory=AllocMem(65536UL,MEMF_CHIP);case_tape=AllocMem(4096UL,MEMF_PUBLIC);
        if(!case_memory || !case_tape || !file){if(file)Close(file);result=20;goto cleanup;}
        if(Read(file,case_memory,65536)!=65536){Close(file);result=20;goto cleanup;}
        case_bytes=Read(file,case_tape,4096);Close(file);
        if(case_bytes<=0 || case_bytes==4096){result=20;goto cleanup;}
    }
    intro_decode(buffers[1]);''')
main=build.change(main,"            if(!light_started && step>=light_warmup){","""            if(step>=light_warmup){
                game_field_active=source_audio_active=0;
                bench_run(case_memory,case_tape,(unsigned long)case_bytes);
                break;
            }
            if(!light_started && step>=light_warmup){""")
anchor='        append(&p,"\\nrestored_os=1\\nfinished=1\\n");'
main=build.change(main,anchor,'''        append(&p,"\\nreplay_benchmark=");for(k=0;k<7;k++){if(k)append(&p,",");number(&p,bench_result[k]);}
'''+anchor)
main=build.change(main,"cleanup:\n","cleanup:\n    if(case_memory)FreeMem(case_memory,65536UL);if(case_tape)FreeMem(case_tape,4096UL);\n")
(folder/"c64_rooms.c").write_text(c);(folder/"main.c").write_text(main)
build.compile_program(folder,OUT)
