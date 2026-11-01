/* Diagnostic only. Install the next COP1LC during active display, without
 * COPJMP. Copper restarts it at field zero. Game computation may run in
 * the tail of the current field. Neither bitmap is reused until the
 * next field has passed display start. Late offers use the blank path. */
static ULONG queued_field,op_owner_waits,op_queued;
static UBYTE queued_image;
static void wait_display_owner(void){
    if(!queued_image)return;
    if(field_clock()==queued_field || raster()<44){
        ++op_owner_waits;
        while(field_clock()==queued_field || raster()<44)source_audio_service();
    }
    queued_image=0;
}
static UWORD queue_game_frame(UWORD *list){
    ULONG stamp;UWORD line;
    wait_display_owner();wait_blitter();stamp=field_clock();line=raster();
    if(line<44 || line>285)return present_frame(list);
    list[1]=0x4200;hw->cop1lc=(ULONG)list;
    queued_field=stamp;queued_image=1;++op_queued;
    return line;
}
