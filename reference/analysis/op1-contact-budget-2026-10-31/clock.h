/* Private OP0 diagnostic. No observer is linked into the game. */
static unsigned long probe_clock(void);
extern void probe_begin(void),probe_finish(void),probe_seam(long, long);
extern unsigned long probe_bins[8],probe_calls,probe_points[2],probe_picked,probe_empty;
extern unsigned char *probe_image,*probe_trace;
extern unsigned long probe_used,probe_records,probe_overflow;
volatile unsigned char probe_enabled,probe_capture,probe_live;
unsigned char *probe_image,*probe_trace;
unsigned long probe_used,probe_records,probe_overflow;
unsigned long probe_bins[8],probe_calls,probe_points[2],probe_picked,probe_empty;
static unsigned long probe_stamp,probe_active_kind,probe_part,probe_mask;
static unsigned char probe_timing;
static unsigned long probe_empty_work;

void probe_begin(void){
    if(!probe_live)return;
    probe_timing=(unsigned char)(probe_enabled && !(probe_calls & probe_mask));
    ++probe_calls;
    if(probe_timing){
        ++probe_picked;probe_active_kind=0;probe_part=0;probe_stamp=probe_clock();
    }
}
void probe_seam(long kind,long actor){
    unsigned long stamp;
    if(!probe_timing)return;
    stamp=probe_clock();
    probe_bins[probe_active_kind]+=(stamp-probe_stamp)&0xffffffUL;
    if(kind==1 || kind==2){
        probe_points[kind-1]++;
        if(kind==1)probe_part=(unsigned long)actor+1;
        probe_active_kind=kind==1?4:5;
    }else probe_active_kind=probe_part;
    probe_stamp=stamp;
}
void probe_finish(void){
    if(probe_timing){
        unsigned long stamp=probe_clock();
        probe_bins[probe_active_kind]+=(stamp-probe_stamp)&0xffffffUL;
        probe_timing=0;
    }
}
static unsigned long probe_clock(void){return line_clock();}
static void probe_calibrate(void){
    /* Same CIA reads, flags, accumulation and dispatch without guest work.
     * Preserve the live figures and report overhead per complete pair. */
    unsigned long start,old[8],i;UWORD k;
    for(k=0;k<8;k++)old[k]=probe_bins[k];
    probe_timing=1;probe_stamp=probe_clock();probe_active_kind=0;
    start=probe_stamp;
    for(i=0;i<256;i++){probe_seam(2,0);probe_seam(0,0);}
    probe_empty=(probe_clock()-start)&0xffffffUL;
    probe_empty_work=0;for(k=0;k<4;k++)probe_empty_work+=probe_bins[k]-old[k];
    probe_timing=0;probe_points[1]-=256;
    for(k=0;k<8;k++)probe_bins[k]=old[k];
}
