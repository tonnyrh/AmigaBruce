/* Diagnostic measurement outside C64 RAM. The -mshort TU exports only
 * fixed-size globals and calls the no-argument clock function. */
enum { OP2_KINDS=6, OP2_RESULTS=3, OP2_STATS=9, OP2_CAPACITY=128, OP2_WORDS=20 };
unsigned short op2_origin;
unsigned char op2_kind,op2_builds;
unsigned long op2_vic_lines,op2_cache_lines;
static ULONG op2_stats[OP2_KINDS][OP2_RESULTS][OP2_STATS];
static ULONG op2_events[OP2_CAPACITY][OP2_WORDS],op2_seen,op2_ticks,op2_losses;
static ULONG op2_fields,op2_nested,op2_field_start,op2_field_cost;
static ULONG op2_since_vic,op2_since_fields,op2_since_fieldcost,op2_since_cache;
static ULONG op2_step,op2_first_field;
static UWORD op2_live,op2_inside,op2_inner_polls,op2_previous_site,op2_previous_tick;
static UWORD op2_previous_phase,op2_previous_origin,op2_tick_known;
static ULONG line_clock(void);
static ULONG field_clock(void);
unsigned long op2_clock(void){return line_clock();}
static ULONG op2_elapsed(ULONG start){return (line_clock()-start)&0xffffffUL;}

static void op2_start(void){
    op2_live=1;
    op2_first_field=field_clock();
}
static void op2_before_field(void){
    op2_inside=1;
    op2_inner_polls=0;
    op2_kind=op2_builds=0;
    op2_vic_lines=op2_cache_lines=0;
    if(OP2_FULL)op2_field_start=line_clock();
}
static void op2_after_field(void){
    if(OP2_FULL)op2_field_cost=op2_elapsed(op2_field_start);
    op2_inside=0;
}

/* site 2 is the existing first poll after a completed field. Attribute
 * intervals only after observing the poll, including zero-gap polls. */
static void op2_poll(ULONG now,ULONG gap,UWORD site,UWORD phase){
    ULONG *stats,*event;
    if(!op2_live)return;
    if(op2_inside)++op2_inner_polls;
    if(site==2){
        ULONG outcome=gap==0?0:gap==1?1:2;
        stats=op2_stats[op2_kind][outcome];
        ++stats[0];
        stats[1]+=op2_vic_lines;
        if(op2_vic_lines>stats[2])stats[2]=op2_vic_lines;
        stats[3]+=op2_field_cost;
        if(op2_field_cost>stats[4])stats[4]=op2_field_cost;
        stats[5]+=op2_cache_lines;
        stats[6]+=op2_builds;
        stats[7]+=op2_inner_polls;
        if(op2_cache_lines>stats[8])stats[8]=op2_cache_lines;
        ++op2_fields;
        op2_nested+=op2_inner_polls;
        ++op2_since_fields;
        op2_since_vic+=op2_vic_lines;
        op2_since_fieldcost+=op2_field_cost;
        op2_since_cache+=op2_cache_lines;
    }
    if(gap>1){
        if(op2_seen<OP2_CAPACITY){
            event=op2_events[op2_seen];
            event[0]=(now-op2_first_field)&0xffffffUL;
            event[1]=op2_step;
            event[2]=gap;
            event[3]=op2_previous_site;
            event[4]=site;
            event[5]=op2_previous_origin;
            event[6]=op2_origin;
            event[7]=op2_previous_phase;
            event[8]=phase;
            event[9]=op2_previous_tick;
            event[10]=site==2?op2_kind:255;
            event[11]=site==2?op2_field_cost:0;
            event[12]=site==2?op2_vic_lines:0;
            event[13]=site==2?op2_cache_lines:0;
            event[14]=site==2?op2_builds:0;
            event[15]=op2_since_fields;
            event[16]=op2_since_fieldcost;
            event[17]=op2_since_vic;
            event[18]=op2_since_cache;
            event[19]=op2_tick_known;
        }
        ++op2_seen;
        op2_losses+=gap-1;
    }
    if(gap){
        ++op2_ticks;
        op2_tick_known=1;
        op2_since_fields=op2_since_vic=op2_since_fieldcost=op2_since_cache=0;
    }
    op2_previous_tick=(gap!=0);
    op2_previous_site=site;
    op2_previous_phase=phase;
    op2_previous_origin=op2_origin;
}
static int op2_save(void){
    ULONG header[]={0x4f503202UL,OP2_FULL,op2_fields,op2_ticks,op2_losses,
                    op2_seen,op2_nested,OP2_KINDS,OP2_RESULTS,OP2_STATS,OP2_WORDS};
    ULONG size=(op2_seen<OP2_CAPACITY?op2_seen:OP2_CAPACITY)*sizeof(op2_events[0]);
    BPTR file=Open((CONST_STRPTR)"DH1:op2-fields.bin",MODE_NEWFILE);
    LONG a,b,c;
    if(!file)return 0;
    a=Write(file,header,sizeof(header));
    b=Write(file,op2_stats,sizeof(op2_stats));
    c=Write(file,op2_events,size);
    Close(file);
    return a==sizeof(header)&&b==sizeof(op2_stats)&&c==size;
}
