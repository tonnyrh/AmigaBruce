/* Keep a full entry image. At each stopped service boundary encode ALL
 * differences from that image as (16-bit start, byte length, raw bytes).
 * The capture is a separate controlled call with IRQ and audio held. */
extern volatile unsigned char probe_capture,probe_live;
extern unsigned char *probe_image,*probe_trace;
extern unsigned long probe_used,probe_records,probe_overflow;
extern void probe_begin(void),probe_finish(void),probe_seam(long,long);
extern void probe_freeze(void);
static unsigned char probe_collecting;
static void probe_byte(unsigned char v){
    if(probe_used<16384UL)probe_trace[probe_used++]=v;else probe_overflow=1;
}
static void probe_point(unsigned char id){
    unsigned long at=0,start,count,i;
    probe_byte(id);probe_byte(a);probe_byte(x);probe_byte(y);
    probe_byte(c);probe_byte(z);probe_byte(n);probe_byte(v);
    probe_byte(d);probe_byte(sp);probe_byte(actor_i);
    while(at<65536UL){
        if(m[at]==probe_image[at]){++at;continue;}
        start=at;
        do{++at;}while(at<65536UL && at-start<255 && m[at]!=probe_image[at]);
        count=at-start;probe_byte((unsigned char)(start>>8));probe_byte((unsigned char)start);
        probe_byte((unsigned char)count);
        for(i=start;i<at;i++)probe_byte(m[i]);
    }
    probe_byte(0);probe_byte(0);probe_byte(0);++probe_records;
}
static void probe_entry(void){
    unsigned long at;
    if(probe_capture && probe_live){
        probe_capture=0;probe_collecting=1;probe_freeze();
        for(at=0;at<65536UL;at++)probe_image[at]=m[at];
        probe_point(0);
    }
}
static void probe_service(unsigned char site){
    if(probe_collecting){probe_point(site);return;}
    probe_seam((long)site,(long)x);io_service();probe_seam(0,0);
}
