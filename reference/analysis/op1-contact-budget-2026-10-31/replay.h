/* Standalone timing in the live R01 DMA setup. File is a verified, fixed
 * input fixture. Replay is deliberately inaccessible from normal play. */
extern unsigned long probe_clock_public(void);
static unsigned char *bench_image,*bench_expected;
static volatile unsigned long bench_seams;
unsigned long bench_result[8];
static void bench_nop(void){++bench_seams;}
static unsigned char *bench_patch(unsigned char *p,unsigned char *ram){
    unsigned short addr;
    unsigned char count,*dest;
    p+=11;
    for(;;){
        addr=(unsigned short)(((unsigned short)p[0]<<8)|p[1]);count=p[2];p+=3;
        if(!count)return p;
        dest=ram+addr;
        do{*dest++=*p++;}while(--count);
    }
}
static void bench_regs(const unsigned char *p){
    a=p[1];x=p[2];y=p[3];c=p[4];z=p[5];n=p[6];v=p[7];d=p[8];sp=p[9];actor_i=p[10];
}
static void bench_compare(void){
    const unsigned char *p=bench_expected;
    unsigned long i;
    bench_expected=bench_patch(bench_expected,bench_image);
    if(a!=p[1] || x!=p[2] || y!=p[3] || c!=p[4] || z!=p[5] || n!=p[6] ||
       v!=p[7] || d!=p[8] || sp!=p[9] || actor_i!=p[10])++bench_result[2];
    for(i=0;i<65536UL;i++)if(m[i]!=bench_image[i]){++bench_result[2];break;}
    ++bench_result[3];
}
static void bench_replay(unsigned char *p){
    unsigned char kind;
    do{
        kind=*p;bench_regs(p);p=bench_patch(p,m);
        if(kind!=3)io_service();
    }while(kind!=3);
}
static unsigned char bench_valid(const unsigned char *p,unsigned long size){
    const unsigned char *end=p+size;unsigned char kind,count;unsigned short records=0;
    while((unsigned long)(end-p)>=14){
        kind=*p;
        if((!records && kind!=0) || (records && (kind<1 || kind>3)))return 0;
        ++records;p+=11;
        do{
            unsigned long address;
            if(end-p<3)return 0;
            address=((unsigned long)p[0]<<8)|p[1];count=p[2];p+=3;
            if(end-p<count || address+count>65536UL)return 0;
            p+=count;
        }while(count);
        if(kind==3)return (unsigned char)(p==end && records>=5);
    }
    return 0;
}
void bench_run(unsigned char *image,unsigned char *tape,unsigned long size){
    unsigned char *first,variant;
    unsigned short round;
    unsigned long i,stamp,lines;
    if(!bench_valid(tape,size)){++bench_result[2];return;}
    bench_image=image;
    for(i=0;i<65536UL;i++)m[i]=image[i];
    bench_regs(tape);first=bench_patch(tape,m);bench_expected=first;
    actor_world_enabled=1;io_service=bench_compare;
    source_contact_driver();bench_compare();
    if(bench_result[2])return;
    /* Both expected RAM and real RAM now contain final state. Restore
     * via the first patch; the following states are incremental. */
    bench_patch(tape,bench_image);io_service=bench_nop;
    for(round=0;round<128;round++){
        variant=(unsigned char)((round^(round>>1))&1); /* A B B A */
        bench_regs(tape);bench_patch(tape,m);bench_seams=0;
        stamp=probe_clock_public();
        if(variant)bench_replay(first);else source_contact_driver();
        lines=(probe_clock_public()-stamp)&0xffffffUL;
        bench_result[variant]+=lines;bench_result[4+variant]+=bench_seams;
    }
    /* Verify the replay path, including each callback's full result. */
    bench_regs(tape);bench_patch(tape,m);bench_expected=first;
    io_service=bench_compare;bench_replay(first);bench_compare();
    bench_result[6]=64;
}
