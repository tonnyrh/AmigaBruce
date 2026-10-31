"""Diagnostic-only PAL audio starvation probe. No production changes."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/audio-service-2026-10-30'
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--split',action='store_true');args=parser.parse_args()
    label='split' if args.split else 'probe'
    folder=BASE/label;folder.mkdir(parents=True,exist_ok=True)
    core=(ROOT/'core/c64_rooms.c').read_text(encoding='utf-8-sig')
    anchor='static void (*io_service)(void);'
    assert core.count(anchor)==1
    core=core.replace(anchor,anchor+'''
unsigned short bl_audio_probe_site,bl_audio_probe_row;
static void probe_io(unsigned short site){
    unsigned short saved=bl_audio_probe_site;bl_audio_probe_site=site;
    bl_audio_probe_row=m[0x52];io_service();bl_audio_probe_site=saved;
}
''')
    # The wrapper itself is excluded from replacement. Each original callback
    # stays at its original source boundary; virtual RAM/flags are untouched.
    start=core.index('static void source_actor_loading_begin(void);')
    head,tail=core[:start],core[start:];assert tail.count('io_service();')==4
    for tag in range(1,5):tail=tail.replace('io_service();',f'probe_io({tag});',1)
    core=head+tail
    (folder/'c64_rooms.c').write_text(core,encoding='utf-8')
    program=(ROOT/'core/c64_actor_programs.h').read_text(encoding='utf-8-sig')
    if args.split:
        core=core.replace('unsigned short bl_audio_probe_site,bl_audio_probe_row;',
            'unsigned short bl_audio_probe_site,bl_audio_probe_row;\nunsigned long bl_audio_probe_marks[4];\nextern unsigned long bl_audio_probe_clock(void);')
        (folder/'c64_rooms.c').write_text(core,encoding='utf-8')
        for index,pc in enumerate([0x1bc2,0x1bee,0x1c0a,0x5212]):
            anchor=f'L{pc:04x}:; /* ${pc:04X} */\n';assert program.count(anchor)==1
            program=program.replace(anchor,anchor+f'bl_audio_probe_marks[{index}]=bl_audio_probe_clock();\n')
    (folder/'c64_actor_programs.h').write_text(program,encoding='utf-8')
    audio=(ROOT/'amiga/source_audio.h').read_text()
    audio+='\n' if not audio.endswith('\n') else ''
    anchor='static UWORD source_music_faults;'
    audio=audio.replace(anchor,anchor+'''
extern unsigned short bl_audio_probe_site,bl_audio_probe_row;
typedef struct {ULONG prev_start,prev_end,start,end,gap;UWORD prev_poll,site,prev_context,context,row;} AudioProbe;
static AudioProbe audio_probe[16];
static ULONG probe_prev_start,probe_prev_end;
static UWORD probe_poll_site,probe_poll_context,probe_pending=65535;
''')
    anchor='    if(BL_AUTOTEST){ULONG cost=(line_clock()-start)&0xffffffUL;if(cost>source_tick_max_lines)source_tick_max_lines=cost;}'
    assert audio.count(anchor)==1
    audio=audio.replace(anchor,'''    if(BL_AUTOTEST){ULONG end=line_clock(),cost=(end-start)&0xffffffUL;
        if(cost>source_tick_max_lines)source_tick_max_lines=cost;
        if(probe_pending<16){audio_probe[probe_pending].start=start;audio_probe[probe_pending].end=end;probe_pending=65535;}
        probe_prev_start=start;probe_prev_end=end;
    }''')
    anchor='    now=field_clock();gap=(now-source_clock_last)&0xffffffUL;if(!gap)return;'
    assert audio.count(anchor)==1
    audio=audio.replace(anchor,'''    now=field_clock();gap=(now-source_clock_last)&0xffffffUL;
    if(gap>1 && source_clock_miss_records<16){
        AudioProbe *p=&audio_probe[source_clock_miss_records];
        p->prev_start=probe_prev_start;p->prev_end=probe_prev_end;p->gap=gap;
        p->prev_poll=probe_poll_site;p->prev_context=probe_poll_context;
        p->site=bl_audio_probe_site;p->context=source_audio_context;p->row=bl_audio_probe_row;
        probe_pending=source_clock_miss_records;
    }
    probe_poll_site=bl_audio_probe_site;probe_poll_context=source_audio_context;
    if(!gap)return;''')
    if args.split:
        audio=audio.replace('static AudioProbe audio_probe[16];',
            'extern unsigned long bl_audio_probe_marks[4];\nstatic ULONG probe_field_start,probe_field_end;\nstatic AudioProbe audio_probe[16];')
        audio=audio.replace('context,row;} AudioProbe;', 'context,row;ULONG field_start,field_end,marks[4];} AudioProbe;')
        audio=audio.replace('        probe_pending=source_clock_miss_records;',
            '        p->field_start=probe_field_start;p->field_end=probe_field_end;\n        {UWORD j;for(j=0;j<4;j++)p->marks[j]=bl_audio_probe_marks[j];}\n        probe_pending=source_clock_miss_records;')
    (folder/'source_audio.h').write_text(audio,encoding='utf-8')
    main=(ROOT/'.tmp/compact-delivery/math-main.c').read_text(encoding='utf-8-sig')
    anchor='        append(&p,"\\nsource_clock_elapsed=");number(&p,source_clock_elapsed);'
    block='''        {UWORD q;for(q=0;q<source_clock_miss_records;q++){
            AudioProbe *s=&audio_probe[q];append(&p,"\\naudio_probe_");number(&p,q);append(&p,"=");
            number(&p,s->prev_start);append(&p,",");number(&p,s->prev_end);
            append(&p,",");number(&p,s->start);append(&p,",");number(&p,s->end);
            append(&p,",");number(&p,s->gap);append(&p,",");number(&p,s->prev_poll);
            append(&p,",");number(&p,s->site);append(&p,",");number(&p,s->prev_context);
            append(&p,",");number(&p,s->context);append(&p,",");number(&p,s->row);
        }}
'''
    if args.split:
        block=block.replace('number(&p,s->row);', 'number(&p,s->row);append(&p,",");number(&p,s->field_start);append(&p,",");number(&p,s->field_end);\n            {UWORD j;for(j=0;j<4;j++){append(&p,",");number(&p,s->marks[j]);}}')
        main=main.replace('#include "source_audio.h"','#include "source_audio.h"\nunsigned long bl_audio_probe_clock(void){return line_clock();}')
        anchor2='game_field_busy=1;while(gap--)bl_c64_field();game_field_busy=0;';assert main.count(anchor2)==1
        main=main.replace(anchor2,'game_field_busy=1;while(gap--){probe_field_start=line_clock();bl_c64_field();probe_field_end=line_clock();}game_field_busy=0;')
    assert main.count(anchor)==1;main=main.replace(anchor,block+anchor)
    (folder/'main.c').write_text(main,encoding='utf-8')
    builder=(ROOT/'.tmp/compact-delivery/math-build.ps1').read_text(encoding='utf-8-sig')
    builder=builder.replace("'.tmp/compact-delivery/math-main.c'",f"'reference/analysis/audio-service-2026-10-30/{label}/main.c'")
    anchor='    & $compiler @sourceFlags -c $actualPath -o $obj'
    override="    if($source -eq 'core/c64_rooms.c'){$actualPath=Join-Path $taskRoot 'reference/analysis/audio-service-2026-10-30/"+label+"/c64_rooms.c';$sourceFlags+='-I'+(Join-Path $taskRoot 'core')}\n"
    assert builder.count(anchor)==1;builder=builder.replace(anchor,override+anchor)
    builder_path=BASE/(label+'-build.ps1');builder_path.write_text(builder,encoding='utf-8')
    def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    inputs=[ROOT/p for p in ['core/c64_rooms.c','core/c64_actor_programs.h','amiga/main.c','amiga/source_audio.h','.tmp/compact-delivery/math-main.c','.tmp/compact-delivery/math-build.ps1']]
    outputs=list(folder.glob('*'))+[builder_path]
    (BASE/(label+'-scope.json')).write_text(json.dumps(dict(status='diagnostic_only_audio_service_probe',production_changed=False,split=args.split,
        callback_sites={1:'source_contact_rows_inner',2:'source_contact_driver',3:'bl_c64_contact',4:'bl_c64_tick_begin',0:'main renderer/wait'},
        record_fields=['previous_tick_start','previous_tick_end','current_tick_start','current_tick_end','field_gap','previous_poll_site','current_site','previous_poll_context','current_context','source_row'],
        limitations=['Instrumentation changes field phase and adds CPU work','Only first16 misses retained','Poll sites bracket silent work; they do not identify every interior instruction'],
        inputs=[item(p) for p in inputs],generated=[item(p) for p in outputs]),indent=2)+'\n')
    print('Generated isolated audio-service diagnostics; no scheduling/rules changed')
if __name__=='__main__':main()
