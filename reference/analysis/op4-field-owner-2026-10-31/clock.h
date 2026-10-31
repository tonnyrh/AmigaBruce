/* Compare the scheduled C64 raster line with the current PAL field and
 * beam. Only advance the pending deadline after a successful source RTI. */
extern unsigned long owner_pc(void),owner_vector(void),owner_line(void);
extern unsigned long owner_dispatch(unsigned long,unsigned char *);
static ULONG owner_due,owner_target,owner_games,owner_bands,owner_kage,owner_kage_irqs,owner_publications;
static ULONG owner_hw_duplicate,owner_hw_missing,owner_slot_errors,owner_fault,owner_last_hw,owner_last_due;
static ULONG owner_late,owner_max_late,owner_mapped[5],owner_max_events;
static ULONG owner_first_hw,owner_first_due,owner_crossed_publish,owner_started;
static UWORD owner_trace[128][8];static UWORD owner_records,owner_keep;
static UWORD raster(void);
static void owner_arm(void){
    ULONG line=owner_line(),now=field_clock();
    if(owner_vector()!=0x48c1 || line>=312){owner_fault=1;return;}
    owner_due=(now+(raster()>=line))&0xffffffUL;owner_target=line;
    owner_started=now;owner_on=1;
}
static void owner_poll(void){
    ULONG now,lag,pc,vector,following,line,hw_field,previous,events=0,elapsed;
    UWORD beam;
    if(owner_busy || !source_audio_active || !game_field_active || game_field_loading || owner_fault)return;
    now=field_clock();lag=(now-owner_due)&0xffffffUL;
    if(lag&0x800000UL)return;
    beam=raster();
    if(!lag && beam<owner_target)return;
    pc=owner_pc();if(!pc)return;
    owner_busy=1;
    while(lag<0x800000UL && (lag || beam>=owner_target)){
        if(++events>16 || lag>2){owner_fault=2;break;}
        previous=owner_target;
        vector=owner_dispatch(pc,source_registers);
        if(!vector){owner_fault=3;break;}
        if(pc==0x2c51)++owner_kage_irqs;
        switch(pc){
        case 0x2c51:++owner_mapped[0];break;case 0x5214:++owner_mapped[1];break;
        case 0x5380:++owner_mapped[2];break;case 0x2586:++owner_mapped[3];break;
        default:++owner_mapped[4];break;
        }
        if(vector==0x48c1){
            if(owner_games && ((owner_due-owner_last_due)&0xffffffUL)!=1)++owner_slot_errors;
            if(!owner_games)owner_first_due=owner_due;
            ++owner_games;owner_last_due=owner_due;
            if(pc==0x2c51){++owner_kage;if(!owner_keep && !owner_records)owner_keep=2;}
            /* The handler has already advanced SID. Only publish here. */
            source_audio_output(0);hw_field=owner_write_first;++owner_publications;
            if(owner_write_last!=hw_field)++owner_crossed_publish;
            if(owner_games==1)owner_first_hw=hw_field;
            else{
                elapsed=(hw_field-owner_last_hw)&0xffffffUL;
                if(!elapsed)++owner_hw_duplicate;
                else if(elapsed>1)owner_hw_missing+=elapsed-1;
            }
            owner_last_hw=hw_field;
            if(lag){++owner_late;if(lag>owner_max_late)owner_max_late=lag;}
        }else ++owner_bands;
        following=owner_vector();line=owner_line();
        if(owner_keep && owner_records<128){
            UWORD *r=owner_trace[owner_records++];
            r[0]=(UWORD)owner_due;r[1]=(UWORD)pc;r[2]=(UWORD)vector;r[3]=(UWORD)previous;
            r[4]=(UWORD)following;r[5]=(UWORD)line;r[6]=(UWORD)lag;r[7]=beam;
            if(vector==0x48c1 && owner_keep)--owner_keep;
        }
        if(line>=312){owner_fault=4;break;}
        if(line<=previous)owner_due=(owner_due+1)&0xffffffUL;
        owner_target=line;lag=(now-owner_due)&0xffffffUL;
    }
    if(events>owner_max_events)owner_max_events=events;
    owner_busy=0;
}
