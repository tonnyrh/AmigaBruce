"""Isolated trials against the measured November 1 game; never overwrite the release."""
import re
import shutil
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WORK=ROOT/".tmp/field-work"
LAST=ROOT/".tmp/kage-paula"
sys.path.insert(0,str(HERE.parent/"op1-contact-budget-2026-10-31"))
from build import change,compile_program

def blits(main):
    # Consecutive DMA jobs already wait before reprogramming the registers.
    # Leave explicit barriers on the three paths that resume CPU pixel writes.
    main=change(main,"(UWORD)(((height*4)<<6)|(width>>1));\n        wait_blitter();","(UWORD)(((height*4)<<6)|(width>>1));")
    main=change(main,"(UWORD)((height*4<<6)|(width>>1));\n    wait_blitter();","(UWORD)((height*4<<6)|(width>>1));")
    main=change(main,"restore_source_cells(buffers[back],back);","restore_source_cells(buffers[back],back);\n            wait_blitter();")
    main=change(main,"draw_fighter(buffers[back],&world.player,&render_game,2,frame,back);\n            source_audio_service();",
                "draw_fighter(buffers[back],&world.player,&render_game,2,frame,back);\n            wait_blitter();")
    main=change(main,"if(!target.respawn && (changed ||","wait_blitter();\n            if(!target.respawn && (changed ||")
    return main

def dma_source():
    import subprocess
    code=subprocess.check_output(["git","show","5ed53f6:core/source_dma.c"],cwd=ROOT,text=True,encoding="utf-8")
    code=change(code,"void bl_source_dma_reset(", "#ifdef __m68k__\n"+(HERE/"dma.c").read_text()+"\n#endif\nvoid bl_source_dma_reset(")
    start=code.index("        for(repeat=");end=code.index("        s->offset",start)
    return code[:start]+"#ifdef __m68k__\n        source_dma_fill(dst,src,v->length);\n#else\n"+code[start:end]+"#endif\n"+code[end:]

def make(mode):
    long=mode.startswith("long-");family=mode.removeprefix("long-")
    compact=family=="release"
    early=family in ("early","release")
    candidate=family in ("candidate","early","release")
    if candidate:family="native"
    assert family in ("meter","blit","dma","both","pad","all","trace","share","clock","hits","falls","native")
    base=LAST/("long-polled-hud" if long else "polled-hud")
    dest=WORK/mode;dest.mkdir(parents=True,exist_ok=True)
    shared=ROOT/".tmp/op-pipeline/candidate"
    main=(base/"main.c").read_text()
    audio=(base/"source_audio.h").read_text()
    core=(base/"c64_rooms.c").read_text()
    if family in ("blit","both","all","trace","share","clock","hits","falls","native"):main=blits(main)
    if family in ("share","clock","hits","falls","native"):main=change(main,"|DMAF_BLITHOG;",";")
    if family in ("clock","falls","native"):
        from clock_pair import apply
        main,audio=apply(main,audio)
    if family in ("pad","all","trace","share","clock","hits","falls","native"):
        from input_field import sample_core,sample_main
        main=sample_main(main,diagnostic=True);core=sample_core(core)
        main="extern void bl_c64_set_control_reader(unsigned long (*)(long,long));\n"+main
    if family in ("falls","native"):
        core=fall_pairs(core)
    if family=="native":main=only_slot(main,diagnostic=True)
    if early:main=early_queue(main)
    if candidate:
        from input_field import single_pad
        core=single_pad(core)
        core=core.replace("Kage's negative damage result loops through a 50 and\n * a 200 award","A negative enemy damage result repeats the actor's awards").replace("source_kage_award_pairs","source_enemy_fall_awards")
    if compact:core=column_words(core)
    if family=="trace":
        main=change(main,'#include "source_audio.h"','''static ULONG gap_log[48][8],gap_count,measure_step;
static UWORD render_part,previous_poll,prior_write;
#include "source_audio.h"''')
        for i,loc in enumerate(("restore_source_cells(buffers[back],back);","bl_c64_paint_animation_frame(buffers[back],SCENE_TOP);",
                "draw_source_projectiles(buffers[back],back);","draw_fighter(buffers[back],&world.enemy[n],&body,n,frame,back);",
                "draw_fighter(buffers[back],&world.player,&render_game,2,frame,back);","draw_lives(buffers[back],&world,&session);",
                "draw_score(buffers[back],&progress,options.debug);","copper[back][65]=palette[bl_c64_flash_color()];","wait_display_owner();back^=1;")):
            main=change(main,loc,f"render_part={i+1};"+loc)
        main=change(main,"if(light_started && step!=light_steps_begin){","if(light_started)measure_step=step-light_start_step;\n            if(light_started && step!=light_steps_begin){")
        audio=change(audio,"if(score_outputs){if(!gap)","""if(score_outputs && gap!=1 && gap_count<48){
            ULONG *r=gap_log[gap_count++];r[0]=measure_step;r[1]=gap;r[2]=source_audio_context;r[3]=render_part;r[4]=previous_poll;r[5]=prior_write;r[6]=stamp;r[7]=source_clock_last;
        }prior_write=render_part;
        if(score_outputs){if(!gap)""")
        audio=change(audio,"if(!gap)return;\n    source_clock_last","if(!gap){previous_poll=render_part;return;}\n    source_clock_last")
        anchor='append(&p,"\\nrestored_os=1\\nfinished=1\\n");'
        main=change(main,anchor,'''for(k=0;k<gap_count;k++){UWORD j;append(&p,"\\ngap=");for(j=0;j<8;j++){if(j)append(&p,",");number(&p,gap_log[k][j]);}}
        '''+anchor)
    for name,body in (("main.c",main),("source_audio.h",audio),("c64_rooms.c",core)):(dest/name).write_text(body)
    shutil.copyfile(base/"c64_actor_programs.h",dest/"c64_actor_programs.h")
    if candidate:
        hdr=dest/"c64_actor_programs.h";hdr.write_text(change(hdr.read_text(),"source_kage_award_pairs();","source_enemy_fall_awards();"))
    if family=="hits":
        core=change(core,'#include "c64_actor_programs.h"','''extern unsigned long hit_clock(void);
extern void hit_time(unsigned long,unsigned long,unsigned long,unsigned long);
static unsigned long hit_start,hit_info;
#include "c64_actor_programs.h"''')
        actor=(dest/"c64_actor_programs.h").read_text()
        marker="L2bf9:; /* $2BF9 */"
        actor=change(actor,marker,marker+"\nif(!hit_start && x<3 && (m[0xbc+x]&0x10) && ((m[0xd1+x]-5)&128)){hit_start=hit_clock();hit_info=((unsigned long)x<<16)|((unsigned short)m[0xbc+x]<<8)|m[0xd1+x];}")
        marker="L2c1d:; /* $2C1D */"
        actor=change(actor,marker,marker+"\nif(hit_start){hit_time(hit_info,x,m[0xd1+x],(hit_clock()-hit_start)&0xffffffUL);hit_start=0;}")
        main=change(main,"static void light_config(void){",'''static ULONG events[48][5],nevents,hit_step;
ULONG hit_clock(void){return line_clock();}
void hit_time(ULONG a,ULONG b,ULONG c,ULONG d){if(score_meter && nevents<48){ULONG *r=events[nevents++];r[0]=hit_step;r[1]=a;r[2]=b;r[3]=c;r[4]=d;}}
static void light_config(void){''')
        main=change(main,"if(light_started && step!=light_steps_begin){","if(light_started)hit_step=step-light_start_step;\n            if(light_started && step!=light_steps_begin){")
        anchor='append(&p,"\\nrestored_os=1\\nfinished=1\\n");'
        main=change(main,anchor,'''for(k=0;k<nevents;k++){UWORD j;append(&p,"\\nhit=");for(j=0;j<5;j++){if(j)append(&p,",");number(&p,events[k][j]);}}
        '''+anchor)
        (dest/"main.c").write_text(main);(dest/"c64_rooms.c").write_text(core);(dest/"c64_actor_programs.h").write_text(actor)
    if family in ("dma","both","all","trace","share","clock","hits","falls","native"):
        import subprocess
        for obj in shared.glob("*.o"):
            if obj.name not in ("source_dma.o","c64_rooms.o","main.o"):shutil.copyfile(obj,dest/obj.name)
        (dest/"source_dma.c").write_text(dma_source())
        cc=sorted((Path.home()/".vscode/extensions").glob("bartmanabyss.amiga-debug-*/bin/win32/opt/bin/m68k-amiga-elf-gcc.exe"))[-1]
        subprocess.run([cc,"-m68000","-O2","-g","-nostdlib","-ffreestanding","-fno-builtin","-fno-tree-loop-distribute-patterns","-fomit-frame-pointer","-ffunction-sections","-fdata-sections","-I"+str(ROOT/"core"),"-c",dest/"source_dma.c","-o",dest/"source_dma.o"],check=True)
        shared=dest
    compile_program(dest,shared)

def fall_pairs(core):
    start=core.index("static void source_kage_award_pairs(")
    end=core.index("\n}",start)+2
    return core[:start]+(HERE/"falls.c").read_text().strip()+core[end:]

def only_slot(main,diagnostic=False):
    if not diagnostic:
        main=change(main,"input=(!BL_AUTOTEST && session.current)?read_port(0):read_input();","if(BL_AUTOTEST)input=read_input();")
    main=change(main,"if(!BL_AUTOTEST || BL_SOURCE_WORLD_TEST)bl_c64_world_input(input,read_port","if(BL_AUTOTEST && BL_SOURCE_WORLD_TEST)bl_c64_world_input(input,read_port")
    main=change(main,"bl_session_source_step(&session,&progress,&world,input,read_port((UBYTE)(session.current?1:0)));",
                "bl_session_source_step(&session,&progress,&world,input,BL_AUTOTEST?read_port((UBYTE)(session.current?1:0)):0);")
    return change(main,"bl_c64_projectile((UBYTE)i,&sprite);if(!sprite.active)continue;",
                  "bl_c64_projectile((UBYTE)i,&sprite);if(!sprite.active)continue;\n        wait_blitter();")

def early_queue(main):
    return change(main,"wait_display_owner();wait_blitter();stamp=field_clock();line=raster();",
        """wait_display_owner();wait_blitter();
    /* An early offer can use this field's normal queue window. Both
     * paths install the image for the same upcoming Copper restart. */
    while(raster()<44)source_audio_service();
    stamp=field_clock();line=raster();""")

def column_words(core):
    core=change(core,"cell_word_mask[1000]","column_word_mask[20]")
    core=change(core,"{unsigned short row,col;for(row=0;row<25;row++)for(col=0;col<40;col++){\n        unsigned short cell=(unsigned short)(row*40+col);\n        cell_offsets",
        "{unsigned short row,col;\n    for(col=0;col<20;col++)column_word_mask[col]=1UL<<col;\n    for(row=0;row<25;row++)for(col=0;col<40;col++){\n        unsigned short cell=(unsigned short)(row*40+col);\n        cell_offsets")
    core=change(core,"        cell_word_mask[cell]=1UL<<(col>>1);\n","")
    core=change(core,"part_words[row]|=cell_word_mask[cell];","/* The 320-byte stride leaves the column in the low six bits. */\n        part_words[row]|=column_word_mask[(cell_offsets[cell]&63)>>1];")
    return change(core,"part_priority_words[row]|=cell_word_mask[cell];","part_priority_words[row]|=column_word_mask[(cell_offsets[cell]&63)>>1];")

if __name__=="__main__":make(sys.argv[1])
