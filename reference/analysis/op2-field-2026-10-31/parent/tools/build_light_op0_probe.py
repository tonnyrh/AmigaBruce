"""Generate a bounded normal-path OP0 probe; never overwrite normal outputs."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/op0-light-2026-10-31'

SETUP=r'''
/* Diagnostic route only: room, allowed enemy bits, input route, reserved,
 * warmup steps (BE16), measured steps (BE16). Not natural play. */
static UBYTE light_route[8]={0,3,0,0,0,240,0,240};
static ULONG light_started,light_start_line,light_last_line,light_start_step;
static ULONG light_work,light_wait,light_loops,light_steps,light_fields;
static ULONG light_audio_start,light_miss_start,light_max_loop,light_max_work;
static ULONG light_active[4],light_rooms,light_climb,light_air;
static ULONG light_restrictions,light_steps_begin,light_audio_fields;
static ULONG light_step_bins[40],light_step_max,light_step_line;
static ULONG light_chip,light_slow,light_fault,light_dma_fault,light_audio_fault;
static UWORD light_warmup,light_target;
static void light_config(void){
    BPTR f=Open((CONST_STRPTR)"DH1:op0-route.bin",MODE_OLDFILE);
    if(f){if(Read(f,light_route,8)!=8)light_route[0]=255;Close(f);}
    light_warmup=((UWORD)light_route[4]<<8)|light_route[5];
    light_target=((UWORD)light_route[6]<<8)|light_route[7];
}
static void light_bin(ULONG cost){
    UWORD bucket;
    if(cost<16)bucket=(UWORD)cost;
    else if(cost<256)bucket=(UWORD)(16+(cost-16)/16);
    else if(cost<2304)bucket=(UWORD)(30+cost/256);
    else bucket=39;
    ++light_step_bins[bucket];if(cost>light_step_max)light_step_max=cost;
}
static UBYTE light_input(ULONG step){
    if(light_route[2]==1){UWORD phase=(UWORD)(step%160);return phase<80?BL_UP:BL_DOWN;}
    return 0;
}
static void light_restrict(void){
    UWORD actor;
    if(light_route[1]==3)return;
    for(actor=1;actor<3;actor++)if(!(light_route[1]&(1<<(actor-1)))){
        UBYTE sprite=bl_c64_read(0x276d+actor),mask=bl_c64_read(0x2778+sprite),second=bl_c64_read(0x2770+actor);
        if(second<128)mask&=bl_c64_read(0x2778+second);
        bl_c64_test_write(0x95+actor,bl_c64_read(0x95+actor)&254);
        bl_c64_test_write(actor==1?0x5e:0x5d,255);
        bl_c64_test_write(0xd015,bl_c64_read(0xd015)&mask);++light_restrictions;
    }
}
'''
REPORT=r'''
    {
        char *report=(char*)buffers[0],*p=report;BPTR file;UWORD slot,k;
        append(&p,"Bruce OP0 normal-path diagnostic\nlight_op0=1\nroom=");number(&p,light_route[0]+1);
        append(&p,"\nenemy_mask=");number(&p,light_route[1]);
        append(&p,"\ninput_route=");number(&p,light_route[2]);
        append(&p,"\nwarmup_steps=");number(&p,light_warmup);
        append(&p,"\nsteps=");number(&p,light_steps);
        append(&p,"\nloops=");number(&p,light_loops);
        append(&p,"\npal_fields=");number(&p,light_fields);
        append(&p,"\npal_lines=");number(&p,(light_last_line-light_start_line)&0xffffffUL);
        append(&p,"\nwork_lines=");number(&p,light_work);
        append(&p,"\nwait_lines=");number(&p,light_wait);
        append(&p,"\nmax_loop_lines=");number(&p,light_max_loop);
        append(&p,"\nmax_work_lines=");number(&p,light_max_work);
        append(&p,"\nmax_step_lines=");number(&p,light_step_max);
        append(&p,"\nstep_bins=");for(k=0;k<40;k++){if(k)append(&p,",");number(&p,light_step_bins[k]);}
        append(&p,"\naudio_ticks=");number(&p,light_audio_fields);
        append(&p,"\naudio_missed=");number(&p,light_miss_start);
        append(&p,"\nactive_loops=");for(k=0;k<4;k++){if(k)append(&p,",");number(&p,light_active[k]);}
        append(&p,"\nvisited_rooms=");number(&p,light_rooms);
        append(&p,"\nclimb_steps=");number(&p,light_climb);
        append(&p,"\nair_steps=");number(&p,light_air);
        append(&p,"\nrestriction_writesets=");number(&p,light_restrictions);
        append(&p,"\nchip_largest_loaded=");number(&p,light_chip);
        append(&p,"\nslow_largest_loaded=");number(&p,light_slow);
        append(&p,"\nsource_fault=");number(&p,light_fault);
        append(&p,"\ndma_fault=");number(&p,light_dma_fault);
        append(&p,"\naudio_fault=");number(&p,light_audio_fault);
        append(&p,"\nsource_profile=");number(&p,BL_C64_PROFILE);
#if BL_C64_PROFILE
        append(&p,"\nperf_errors=");number(&p,bl_perf_value(-1,0));
        append(&p,"\nperf_overhead_32_pairs_lines=");number(&p,bl_perf_value(-1,1));
        for(slot=0;slot<BL_PERF_SLOTS;slot++){
            append(&p,"\nperf_");number(&p,slot);append(&p,"=");
            for(k=0;k<5+BL_PERF_BINS;k++){if(k)append(&p,",");number(&p,bl_perf_value(slot,k));}
        }
#endif
        append(&p,"\nrestored_os=1\nfinished=1\n");
        file=Open((CONST_STRPTR)"DH1:op0-light.txt",MODE_NEWFILE);
        if(file){Write(file,report,(LONG)(p-report));Close(file);}else result=20;
    }
'''
BEGIN=r'''
        {
            ULONG step=bl_c64_world_stat(0);
            if(!light_started && step>=light_warmup){
                light_started=1;light_start_step=step;light_steps_begin=step;
                light_start_line=line_clock();light_last_line=light_step_line=light_start_line;
                light_fields=field_clock();light_audio_start=source_audio_fields;light_miss_start=source_clock_missed;
                light_restrictions=0;bl_perf_reset();
            }
            if(light_started && step!=light_steps_begin){
                ULONG stamp=line_clock();light_bin((stamp-light_step_line)&0xffffffUL);
                light_step_line=stamp;light_steps_begin=step;
                if(world.player.body.state==BL_CLIMB)++light_climb;
                if(world.player.body.state==BL_AIR)++light_air;
            }
            if(light_started && step-light_start_step>=light_target){
                light_steps=step-light_start_step;
                light_fields=(field_clock()-light_fields)&0xffffffUL;
                light_audio_fields=source_audio_fields-light_audio_start;
                light_miss_start=source_clock_missed-light_miss_start;
                light_fault=bl_c64_fault();light_dma_fault=source_dma_faults;light_audio_fault=bl_source_audio_faults();
                break;
            }
            if(frame>10000){result=20;break;}
        }
'''

def replace(s,old,new):
    assert s.count(old)==1,(old[:100],s.count(old));return s.replace(old,new)

def main():
    BASE.mkdir(exist_ok=True)
    s=(ROOT/'amiga/main.c').read_text(encoding='utf-8-sig')
    s=replace(s,'int main(void) {',SETUP+'\nint main(void) {')
    s=replace(s,'    if(BL_AUTOTEST){BPTR previous=', '    light_config();if(light_route[0]>=20 || light_route[1]>3 || light_route[2]>1 || !light_target){result=20;goto cleanup;}\n    if(BL_AUTOTEST){BPTR previous=')
    s=replace(s,'        if(!choose_options(&options,menu_game_over,&back))goto restore_os;',
      '        options.invincible=1;options.infinite_lives=1;options.debug=1;options.start_room=light_route[0];')
    s=replace(s,'    source_audio_copy();','    source_audio_copy();\n    light_chip=AvailMem(MEMF_CHIP|MEMF_LARGEST);light_slow=AvailMem(MEMF_FAST|MEMF_LARGEST);')
    s=replace(s,'        PERF_BEGIN(BL_PERF_LOOP);',BEGIN+'\n        render_clock=line_clock();\n        PERF_BEGIN(BL_PERF_LOOP);')
    s=replace(s,'        input=(!BL_AUTOTEST && session.current)?read_port(0):read_input();',
      '        input=light_input(bl_c64_world_stat(0));light_restrict();')
    s=replace(s,'        PERF_END(BL_PERF_LOOP);PERF_BEGIN(BL_PERF_WAIT);',
      '''        {ULONG work=elapsed_work(render_clock);if(light_started){light_work+=work;if(work>light_max_work)light_max_work=work;}}
        light_last_line=line_clock();
        PERF_END(BL_PERF_LOOP);PERF_BEGIN(BL_PERF_WAIT);''')
    s=replace(s,'        PERF_END(BL_PERF_WAIT);',
      '''        PERF_END(BL_PERF_WAIT);
        if(light_started){ULONG stamp=line_clock(),cost=(stamp-render_clock)&0xffffffUL;
            light_wait+=(stamp-light_last_line)&0xffffffUL;light_last_line=stamp;
            if(cost>light_max_loop)light_max_loop=cost;
            ++light_active[(world.enemy[0].active?1:0)|(world.enemy[1].active?2:0)];
            light_rooms|=1UL<<progress.room;++light_loops;}
''')
    s=replace(s,'    Enable();DisownBlitter();LoadView(old_view);WaitTOF();WaitTOF();Permit();',
      '    Enable();DisownBlitter();LoadView(old_view);WaitTOF();WaitTOF();Permit();\n'+REPORT)
    (BASE/'main.c').write_text(s)
    # Compile normal BL_AUTOTEST=0 with canonical core and audio header.
    builder=(ROOT/'amiga-build.ps1').read_text(encoding='utf-8-sig')
    builder=replace(builder,'$taskRoot=$PSScriptRoot',"$taskRoot='C:\\vscode\\_EXT\\AmigaBruceLee'")
    for variant in ['light','profile']:
        b=builder
        b=replace(b,"$out=Join-Path $taskRoot 'amiga/out'",f"$out=Join-Path $taskRoot 'reference/analysis/op0-light-2026-10-31/{variant}/out'")
        anchor='    & $compiler @sourceFlags -c (Join-Path $taskRoot $source) -o $obj'
        if anchor not in b:
            raise AssertionError('Inspect canonical build compile anchor before proceeding')
        b=replace(b,anchor,"    $actualPath=Join-Path $taskRoot $source\n    if($source -eq 'amiga/main.c'){$actualPath=Join-Path $taskRoot 'reference/analysis/op0-light-2026-10-31/main.c';$sourceFlags+='-I'+(Join-Path $taskRoot 'amiga')}\n    & $compiler @sourceFlags -c $actualPath -o $obj")
        if variant=='profile':
            b=replace(b,"$flags += if($Autotest){'-DBL_AUTOTEST=1'}else{'-DBL_AUTOTEST=0'}", "$flags += if($Autotest){'-DBL_AUTOTEST=1'}else{'-DBL_AUTOTEST=0'}\n$flags+='-DBL_C64_PROFILE=1'")
        # OP0 measures a mounted CLI executable, not disk packaging.
        tail=b.index("& (Join-Path $bin 'exe2adf.exe')")
        b=b[:tail]+'Get-Item "$program.exe" | Select-Object Name,Length\n'
        (BASE/(variant+'-build.ps1')).write_text(b)
    runner=(ROOT/'reference/analysis/native-d7-2026-10-31/run-private.ps1').read_text()
    runner=runner.replace('native-d7-2026-10-31','op0-light-2026-10-31').replace('native-d7','op0-light')
    runner=replace(runner,"$program=if($Autotest){'bruce_test.exe'}else{'bruce_amiga.exe'}","$program='bruce_amiga.exe'")
    runner=replace(runner,"$config=Join-Path $taskRoot $(if($Autotest){'.tmp/op0-light-a500-test.uae'}else{'.tmp/op0-light-a500.uae'})","$config=Join-Path $privateOut 'a500.uae'")
    runner=replace(runner,"$emulator.Id | Set-Content (Join-Path $taskRoot $(if($Autotest){'.tmp/op0-light-test.pid'}else{'.tmp/op0-light.pid'}))","$emulator.Id | Set-Content (Join-Path $privateOut 'owned.pid')")
    (BASE/'run-private.ps1').write_text(runner)
    print('Generated normal-path OP0 main; canonical engine/audio/normal outputs unchanged')

if __name__=='__main__':main()
