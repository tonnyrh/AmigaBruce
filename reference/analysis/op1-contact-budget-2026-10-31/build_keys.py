"""Collect positional repeat counts separately from timing; they do not prove cache hits."""
from pathlib import Path
import build
from build import OUT, ROOT, HERE, change
def generate(folder):
    main=(OUT/"op0/main.c").read_text();core=(ROOT/"core/c64_rooms.c").read_text()
    main=change(main,"static void light_config(void){","""unsigned char *key_records;
unsigned long key_used;
unsigned char key_live;
static void light_config(void){""")
    main=change(main,"    intro_decode(buffers[1]);","""    key_records=AllocMem(7*720UL,MEMF_CHIP);
    if(!key_records){result=20;goto cleanup;}
    intro_decode(buffers[1]);""")
    main=change(main,"light_started=1;light_start_step=step;","key_live=1;light_started=1;light_start_step=step;")
    main=change(main,"light_steps=step-light_start_step;","key_live=0;light_steps=step-light_start_step;")
    anchor='        append(&p,"\\nrestored_os=1\\nfinished=1\\n");'
    main=change(main,anchor,'''        append(&p,"\\nactor_records=");number(&p,key_used/7);
        file=Open((CONST_STRPTR)"DH1:actor-keys.bin",MODE_NEWFILE);
        if(file){if(Write(file,key_records,key_used)!=(LONG)key_used)result=20;Close(file);}else result=20;
'''+anchor)
    main=change(main,"cleanup:\n","cleanup:\n    if(key_records)FreeMem(key_records,7*720UL);\n")
    core=change(core,"static void source_contact_driver(void){","""static void source_contact_driver(void){
    extern unsigned char *key_records,key_live;
    extern unsigned long key_used;
    unsigned char *record;""")
    core=change(core,"if(actor_world_enabled && io_service)io_service();\n        m[0x50]", """if(actor_world_enabled && io_service)io_service();
        record=0;
        if(key_live && key_used<7*720UL){
            record=key_records+key_used;key_used+=7;
            record[0]=x;record[1]=m[0x9e + x];record[2]=m[0xa1+x];record[3]=m[0x4f4e + x];record[4]=m[0x95+x]&1;
        }
        m[0x50]""")
    anchor="        x=(unsigned char)(m[0x50]-1);NZ(x);"
    core=change(core,anchor,"        if(record){record[5]=m[0xa7+m[0x50]];record[6]=m[0xb6+m[0x50]];}\n"+anchor)
    (folder/"main.c").write_text(main);(folder/"c64_rooms.c").write_text(core)
if __name__=="__main__":
    folder=OUT/"keys";folder.mkdir(exist_ok=True);generate(folder);build.compile_program(folder,OUT)

