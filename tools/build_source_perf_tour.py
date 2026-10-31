"""Generate a diagnostic-only20-room controller from the current normal main.
The production main is not edited. Every injection has an exact anchor guard.
"""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--steps',type=int,default=120);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert 30<=a.steps<=360
 source=(ROOT/'amiga/main.c').read_text(encoding='utf-8');text=source
 def inject(old,new):
  nonlocal text
  assert text.count(old)==1,old[:80];text=text.replace(old,new)
 inject('struct DosLibrary *DOSBase;','struct DosLibrary *DOSBase;\nstatic ULONG perf_tour_animation_bytes;')
 inject('(void)bl_c64_build_animation_cache(tile_dma,TILE_DMA_BYTES);','perf_tour_animation_bytes=(ULONG)bl_c64_build_animation_cache(tile_dma,TILE_DMA_BYTES);')
 inject('int main(void) {','''typedef struct {ULONG steps,fields,lines,missed,drawn,held,preparation,actual_room,chip_largest,slow_largest,animation_bytes;} BlTourSample;
static BlTourSample perf_tour_samples[20];
static UBYTE perf_tour_room,perf_tour_active,perf_tour_completed,perf_tour_error;
static ULONG perf_tour_base_step,perf_tour_base_field,perf_tour_base_line;
static ULONG perf_tour_base_missed,perf_tour_base_drawn,perf_tour_base_held,perf_tour_loading;
int main(void) {''')
 inject('    bl_perf_reset();\n    for(;;) {','    bl_perf_reset();perf_tour_loading=line_clock();\n    for(;;) {')
 inject('        if(BL_ELECTRIC_TEST)input=0;','        input=0; /* Controlled source route: no frame-indexed fire after3000. */\n        if(BL_ELECTRIC_TEST)input=0;')
 anchor='''                {ULONG tick_start=(BL_C64_PROFILE || BL_AUTOTEST)?line_clock():0;'''
 block='''                if(!perf_tour_active && progress.room==perf_tour_room &&
                   drawn_room_revision[0]==progress.revision && drawn_room_revision[1]==progress.revision){
                    perf_tour_samples[perf_tour_room].chip_largest=AvailMem(MEMF_CHIP|MEMF_LARGEST);
                    perf_tour_samples[perf_tour_room].slow_largest=AvailMem(MEMF_FAST|MEMF_LARGEST);
                    perf_tour_samples[perf_tour_room].animation_bytes=perf_tour_animation_bytes;
                    perf_tour_base_step=bl_c64_world_stat(0);perf_tour_base_field=field_clock();perf_tour_base_line=line_clock();
                    perf_tour_base_missed=source_clock_missed;perf_tour_base_drawn=drawn_images;perf_tour_base_held=held_images;
                    perf_tour_samples[perf_tour_room].preparation=(perf_tour_base_line-perf_tour_loading)&0xffffffUL;
                    perf_tour_active=1;
                }
                if(perf_tour_active){
                    ULONG steps=bl_c64_world_stat(0)-perf_tour_base_step;
                    if(progress.room!=perf_tour_room){perf_tour_error=1;PERF_END(BL_PERF_LOOP);break;}
                    if(steps>='''+str(a.steps)+'''){
                        BlTourSample *sample=&perf_tour_samples[perf_tour_room];
                        sample->steps=steps;sample->fields=(field_clock()-perf_tour_base_field)&0xffffffUL;
                        sample->lines=(line_clock()-perf_tour_base_line)&0xffffffUL;sample->missed=source_clock_missed-perf_tour_base_missed;
                        sample->drawn=drawn_images-perf_tour_base_drawn;sample->held=held_images-perf_tour_base_held;
                        sample->actual_room=1+bl_c64_read(0x29);++perf_tour_completed;perf_tour_active=0;
                        if(steps!='''+str(a.steps)+'''){perf_tour_error=2;PERF_END(BL_PERF_LOOP);break;}
                        if(perf_tour_completed==20){PERF_END(BL_PERF_LOOP);break;}
                        ++perf_tour_room;room_request=perf_tour_room;perf_tour_loading=line_clock();
                    }
                }
'''
 inject(anchor,block+anchor)
 anchor='''        append(&p,"\\nsource_perf_test=");number(&p,BL_SOURCE_PERF_TEST);'''
 block='''        append(&p,"\\nsource_tour_completed=");number(&p,perf_tour_completed);
        append(&p,"\\nsource_tour_error=");number(&p,perf_tour_error);
        {UWORD tour;
        for(tour=0;tour<20;tour++){
            BlTourSample *sample=&perf_tour_samples[tour];
            append(&p,"\\nsource_tour_");number(&p,tour);append(&p,"=");number(&p,sample->steps);
            append(&p,",");number(&p,sample->fields);append(&p,",");number(&p,sample->lines);append(&p,",");number(&p,sample->missed);
            append(&p,",");number(&p,sample->drawn);append(&p,",");number(&p,sample->held);append(&p,",");number(&p,sample->preparation);append(&p,",");number(&p,sample->actual_room);
            append(&p,",");number(&p,sample->chip_largest);append(&p,",");number(&p,sample->slow_largest);append(&p,",");number(&p,sample->animation_bytes);
        }}
'''
 inject(anchor,block+anchor)
 a.output.parent.mkdir(exist_ok=True,parents=True);a.output.write_text(text,encoding='utf-8')
 (a.output.with_suffix('.json')).write_text(json.dumps(dict(method='Diagnostic translation unit; unchanged actual PAL scheduler, fixed no-input source route; intervals begin/end at original ready boundary; source room jumps and bitmap preparation outside timed interval',source_main_sha256=hashlib.sha256(source.encode()).hexdigest(),generated_sha256=hashlib.sha256(text.encode()).hexdigest(),steps_per_room=a.steps,normal_main_edited=False),indent=2)+'\n')
 print('Generated diagnostic20-room source tour;',a.steps,'source steps/room')
if __name__=='__main__':main()
