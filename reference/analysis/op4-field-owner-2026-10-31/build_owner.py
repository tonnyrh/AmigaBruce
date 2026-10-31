"""Build the real-PAL-clock gameplay pilot outside normal game outputs."""
from pathlib import Path
import sys,shutil
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2];WORK=ROOT/".tmp/op4-owner"
sys.path.insert(0,str(HERE.parent/"op1-kage-prefix-2026-10-31"))
from build_pilot import sources,change,compile_program

def build(mode="candidate"):
    if mode=="reference":
        from build_pilot import build_mode
        build_mode("reference")
        out=WORK/"reference";out.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/".tmp/op1-kage/reference/bruce_amiga.exe",out/"bruce_amiga.exe")
        return
    if mode not in ("candidate","handoff","combat","meter"):raise ValueError(mode)
    main,core=sources("reference");f=WORK/mode;f.mkdir(parents=True,exist_ok=True)
    actor=(ROOT/"core/c64_actor_programs.h").read_text()
    audio=(ROOT/"amiga/source_audio.h").read_text()
    core=change(core,"/* Virtual registers remain local until a source helper, service or return. */",(HERE/"checkpoints.h").read_text()+"\n/* Virtual registers remain local until a source helper, service or return. */")
    core=change(core,"z=zz;n=nn;io_service();","z=zz;n=nn;owner_at(0x5380);")
    core=change(core,"if(actor_world_enabled && io_service)io_service();\n        m[0x50]","if(actor_world_enabled && io_service)owner_at(0x5214);\n        m[0x50]")
    for pc in (0x2586,0x5214):
        t=f"L{pc:04x}:; /* ${pc:04X} */\nif(actor_world_enabled && io_service)"
        actor=change(actor,t+"io_service();",t+f"owner_at(0x{pc:04x});")
    t="L2c51:; /* $2C51 */"
    actor=change(actor,t,t+"\nif(actor_world_enabled && !actor_i && !d && x==2 && (m[0xbc+x]&0x10) && m[0xd1+x]>=133 && io_service)owner_at(0x2c51);")
    core+='\n'+(HERE/"dispatch.h").read_text()
    for name in ("input_slot.h","irq_context.h"):shutil.copyfile(HERE.parent/"irq-input-2026-10-30/candidate"/name,f/name)
    main=change(main,'#include "source_audio.h"','''static UBYTE owner_on,owner_busy;
static ULONG owner_write_first,owner_write_last,owner_voice_writes,owner_legacy_ticks;
static void owner_poll(void);
#include "source_audio.h"''')
    clock=(HERE/"clock.h").read_text()
    main=change(main,"static void source_game_service(void){",clock+"\nstatic void source_game_service(void){\n    if(owner_on){owner_poll();return;}")
    audio=change(audio,"static void source_audio_service(void){","static void source_audio_service(void){\n    if(owner_on){owner_poll();return;}")
    audio=change(audio,"static void source_audio_tick(void){","static void source_audio_tick(void){\n    if(owner_on)++owner_legacy_ticks;")
    audio=change(audio,"    for(c=0;c<3;c++){\n        const BlPaulaVoice *p=", "    if(owner_on)owner_write_first=field_clock();\n    for(c=0;c<3;c++){\n        const BlPaulaVoice *p=")
    audio=change(audio,"        if(p->volume)source_voice_mask","        if(owner_on)++owner_voice_writes;\n        if(p->volume)source_voice_mask")
    audio=change(audio,"    if(music)++source_music_fields;","    if(owner_on)owner_write_last=field_clock();\n    if(music)++source_music_fields;")
    main=change(main,"light_started=1;light_start_step=step;","owner_arm();light_started=1;light_start_step=step;")
    main=change(main,"do{wait_frame();line=raster();}while(line<300 || line>308);",'''if(owner_on){
        /* Once the beam approaches the Copper publication window, keep the
         * final wait bounded. Pending source IRQs retain their deadlines. */
        for(;;){
            line=raster();
            if(line>=300 && line<=308)break;
            if(line<235 || line>308)owner_poll();
        }
    }else do{wait_frame();line=raster();}while(line<300 || line>308);''')
    main=change(main,"if(light_started && step-light_start_step>=light_target){","if(owner_fault || (light_started && step-light_start_step>=light_target)){")
    main=change(main,"light_steps=step-light_start_step;","owner_on=0;light_steps=step-light_start_step;")
    main=change(main,"light_miss_start=source_clock_missed-light_miss_start;","light_miss_start=owner_hw_missing;")
    t='append(&p,"\\nrestored_os=1\\nfinished=1\\n");'
    keys="owner_fault owner_games owner_bands owner_kage owner_kage_irqs owner_publications owner_hw_duplicate owner_hw_missing owner_slot_errors owner_max_events owner_late owner_max_late owner_legacy_ticks owner_voice_writes owner_crossed_publish owner_first_hw owner_last_hw owner_first_due owner_last_due owner_records".split()
    main=change(main,t,"\n".join(f'append(&p,"\\n{k}=");number(&p,{k});' for k in keys)+'''
        append(&p,"\\nowner_mapped=");for(k=0;k<5;k++){if(k)append(&p,",");number(&p,owner_mapped[k]);}
        file=Open((CONST_STRPTR)"DH1:chain.bin",MODE_NEWFILE);
        if(file){if(Write(file,owner_trace,owner_records*16)!=(LONG)(owner_records*16))result=20;Close(file);}else result=20;
        '''+t)
    if mode in ("handoff","combat","meter"):
        main=change(main,"static UBYTE owner_on,owner_busy;",'''UBYTE owner_on,owner_requested;
static UBYTE owner_busy,owner_complete,owner_measuring;
static ULONG owner_all_first,owner_all_last,owner_all_count,owner_all_duplicates,owner_all_gaps;''')
        core=change(core,"static unsigned short owner_checkpoint;","extern unsigned char owner_on,owner_requested;\nstatic unsigned short owner_checkpoint;")
        core=change(core,"unsigned short saved=owner_checkpoint;owner_checkpoint=pc;","unsigned short saved;\n    if(!owner_on && pc!=0x2c51){io_service();return;}\n    saved=owner_checkpoint;owner_checkpoint=pc;")
        actor=change(actor,"if(actor_world_enabled && !actor_i && !d && x==2","if((owner_requested || owner_on) && actor_world_enabled && !actor_i && !d && x==2")
        main=change(main,"owner_arm();light_started=1;","owner_requested=owner_measuring=1;light_started=1;")
        main=change(main,"owner_on=0;light_steps=","owner_measuring=owner_requested=owner_on=0;light_steps=")
        main=change(main,"light_miss_start=owner_hw_missing;","light_miss_start=owner_all_gaps;")
        main=change(main,"if(owner_on){owner_poll();return;}\n    ULONG now,gap;source_audio_service();",'''if(owner_on){owner_poll();return;}
    ULONG now,gap;
    if(owner_requested && owner_pc()==0x2c51 && !game_field_busy && !source_audio_busy){
        now=field_clock();
        /* Both legacy services must have consumed the same field. Give the
         * next unconsumed one to the IRQ, even if it falls after this visit. */
        if(source_clock_last==game_field_last && ((now-source_clock_last)&0xffffffUL)<=1 &&
           owner_vector()==0x48c1){
            owner_arm();owner_due=(source_clock_last+1)&0xffffffUL;
            owner_requested=0;owner_poll();return;
        }
    }
    source_audio_service();''')
        main=change(main,"owner_target=line;lag=(now-owner_due)&0xffffffUL;",'''owner_target=line;lag=(now-owner_due)&0xffffffUL;
        if(owner_games>=2 && following==0x48c1){
            /* Finish the pending bands before returning ownership.
             * The next source game vector is now ready. */
            game_field_last=source_clock_last=owner_last_due;
            owner_on=0;owner_complete=1;break;
        }''')
        audio=change(audio,"if(owner_on)owner_write_first=field_clock();",'''if(owner_measuring){
        ULONG stamp=field_clock(),gap=(stamp-owner_all_last)&0xffffffUL;
        if(!owner_all_count)owner_all_first=stamp;
        else if(!gap)++owner_all_duplicates;
        else owner_all_gaps+=gap-1;
        ++owner_all_count;owner_all_last=stamp;owner_write_first=stamp;
    }''')
        more="owner_complete owner_all_first owner_all_last owner_all_count owner_all_duplicates owner_all_gaps".split()
        main=change(main,t,"\n".join(f'append(&p,"\\n{k}=");number(&p,{k});' for k in more)+"\n"+t)
        if mode=="meter":
            main=change(main,"owner_requested=owner_measuring=1;","owner_requested=0;owner_measuring=1;")
        if mode=="combat":
            main=change(main,"static UBYTE owner_busy,owner_complete,owner_measuring;","static UBYTE owner_busy,owner_complete,owner_measuring,owner_episode_first;")
            main=change(main,"if(owner_games>=2 && following==0x48c1){",
                        "if(pc!=0x2c51 && following==0x48c1){")
            main=change(main,"game_field_last=source_clock_last=owner_last_due;",
                        "game_field_last=owner_last_due;source_clock_last=owner_last_hw;")
            main=change(main,"owner_on=0;owner_complete=1;break;",
                        "owner_on=0;++owner_complete;owner_requested=1;break;")
            # The legacy path owns the interval between the two combat calls.
            # Continuity across that interval belongs to the all-channel meter.
            main=change(main,"owner_requested=0;owner_poll();return;",
                        "owner_requested=0;owner_episode_first=1;owner_poll();return;")
            main=change(main,"if(owner_games && ((owner_due-owner_last_due)","if(!owner_episode_first && ((owner_due-owner_last_due)")
            main=change(main,"else{\n                elapsed=(hw_field-owner_last_hw)","else if(!owner_episode_first){\n                elapsed=(hw_field-owner_last_hw)")
            main=change(main,"owner_last_hw=hw_field;","owner_last_hw=hw_field;owner_episode_first=0;")
    for name,s in [("main.c",main),("c64_rooms.c",core),("c64_actor_programs.h",actor),("source_audio.h",audio)]:(f/name).write_text(s)
    compile_program(f,ROOT/".tmp/op1-kage/reference")
if __name__=="__main__":build(*sys.argv[1:])
