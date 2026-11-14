"""Share a timestamp across the two consumers only on the no-audio-work path."""
def apply(main,audio):
    start=audio.index("static void source_audio_service(void){")
    pre,body=audio[:start],audio[start:]
    old="""static void source_audio_service(void){
    ULONG now,gap;
    if(!source_audio_active || source_audio_busy)return;
    now=field_clock();gap=(now-source_clock_last)&0xffffffUL;if(!gap)return;"""
    assert body.count(old)==1
    body=body.replace(old,"""static UBYTE source_audio_service_at(ULONG now){
    ULONG gap=(now-source_clock_last)&0xffffffUL;
    if(!gap)return 0;""")
    end="    source_audio_busy=1;source_audio_tick();source_audio_busy=0;\n}"
    assert body.count(end)==1
    audio=pre+body.replace(end,end[:-1]+"""    return 1;
}
static void source_audio_service(void){
    if(source_audio_active && !source_audio_busy)source_audio_service_at(field_clock());
}""")
    old="""    ULONG now,gap;source_audio_service();
    if(!game_field_active || game_field_busy)return;
    now=field_clock();gap=(now-game_field_last)&0xffffffUL;game_field_last=now;
    if(game_field_loading)return;"""
    new="""    ULONG now,gap;
    if(!game_field_active || game_field_busy){source_audio_service();return;}
    now=field_clock();
    if(source_audio_active && !source_audio_busy && source_audio_service_at(now))now=field_clock();
    gap=(now-game_field_last)&0xffffffUL;if(!gap)return;
    game_field_last=now;if(game_field_loading)return;"""
    assert main.count(old)==1
    return main.replace(old,new),audio
