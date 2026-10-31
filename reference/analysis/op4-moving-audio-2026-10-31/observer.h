/* Private probe. A poll only observes a call already present in the engine.
 * Window zero starts at the previous poll, window one at the last due tick. */
static ULONG line_clock(void);
static ULONG field_clock(void);
unsigned short op4_origin;
static ULONG op4_active,op4_live,op4_step,op4_events,op4_lost,op4_ticks,op4_polls,op4_field0;
static ULONG op4_prev_site,op4_prev_origin,op4_prev_gap,op4_last_site,op4_last_origin,op4_prev_phase,op4_last_phase;
static ULONG op4_epoch[2],op4_mask[2],op4_cost[2][O_COUNT],op4_tag[2][O_COUNT],op4_stamp;
enum { OP4_CAP=32,OP4_HEADER=14,OP4_WORDS=OP4_HEADER+2*O_COUNT };
static ULONG op4_rows[OP4_CAP][OP4_WORDS];
static void op4_charge(void){
    ULONG now=line_clock(),elapsed=(now-op4_stamp)&0xffffffUL;UWORD w;
    op4_stamp=now;
    for(w=0;w<2;w++){
        if(op4_tag[w][op4_active]!=op4_epoch[w]){
            op4_tag[w][op4_active]=op4_epoch[w];op4_cost[w][op4_active]=0;
        }
        op4_cost[w][op4_active]+=elapsed;
    }
}
static void op4_mark(void){
    ULONG bit=1UL<<op4_active;op4_mask[0]|=bit;op4_mask[1]|=bit;
}
unsigned long op4_region(unsigned long id){
    ULONG old=op4_active;
    if(op4_live && OP4_TIMED)op4_charge();
    op4_active=id;
    if(op4_live)op4_mark();
    return old;
}
static void op4_start(void){
    op4_polls=op4_ticks=op4_lost=op4_events=0;
    op4_epoch[0]=op4_epoch[1]=1;op4_field0=field_clock();
    op4_stamp=line_clock();op4_live=1;op4_mark();
}
static void op4_poll(ULONG now,ULONG gap,UWORD site,UWORD phase){
    ULONG *row;UWORD w,i;
    if(!op4_live)return;
    if(OP4_TIMED)op4_charge();
    ++op4_polls;
    if(gap>1){
        if(op4_events<OP4_CAP){
            row=op4_rows[op4_events];row[0]=op4_step;row[1]=(now-op4_field0)&0xffffffUL;row[2]=gap;
            row[3]=op4_prev_site;row[4]=op4_prev_origin;row[5]=op4_prev_gap;row[6]=op4_prev_phase;
            row[7]=op4_last_site;row[8]=op4_last_origin;row[9]=op4_last_phase;
            row[10]=site;row[11]=op4_origin;row[12]=op4_mask[0];row[13]=op4_mask[1];
            if(OP4_TIMED)for(w=0;w<2;w++)for(i=0;i<O_COUNT;i++)
                row[OP4_HEADER+w*O_COUNT+i]=op4_tag[w][i]==op4_epoch[w]?op4_cost[w][i]:0;
        }
        ++op4_events;op4_lost+=gap-1;
    }
    op4_prev_site=site;op4_prev_origin=op4_origin;op4_prev_phase=phase;op4_prev_gap=gap;
    ++op4_epoch[0];op4_mask[0]=0;
    if(gap){
        ++op4_ticks;op4_last_site=site;op4_last_origin=op4_origin;op4_last_phase=phase;
        ++op4_epoch[1];op4_mask[1]=0;
    }
    op4_mark();
}
static int op4_save(void){
    ULONG hdr[]={0x4f503401UL,OP4_TIMED,O_COUNT,OP4_WORDS,op4_events,op4_ticks,op4_lost,op4_polls};
    ULONG size=op4_events*sizeof(op4_rows[0]);BPTR f;LONG a,b;
    if(op4_events>OP4_CAP)return 0;
    f=Open((CONST_STRPTR)"DH1:op4-audio.bin",MODE_NEWFILE);if(!f)return 0;
    a=Write(f,hdr,sizeof(hdr));b=Write(f,op4_rows,size);Close(f);return a==sizeof(hdr)&&b==(LONG)size;
}
