/* Per-award timing only. No extra poll or field/input delivery. */
extern unsigned long focus_clock(void),focus_step;
extern unsigned char focus_live;
unsigned long focus_slow[8][9],focus_count;
static unsigned long f_start,f_award,f_decimal,f_award_lines,f_decimal_lines,f_calls,f_loops,f_peak;
static unsigned char f_active;
static void f_begin(void){
    if(!focus_live)return;
    f_active=1;f_award_lines=f_decimal_lines=f_calls=f_loops=f_peak=0;f_start=focus_clock();
}
static void f_end(void){
    unsigned long elapsed,*r;
    if(!f_active)return;
    elapsed=(focus_clock()-f_start)&0xffffffUL;f_active=0;
    if(elapsed>312){
        if(focus_count<8){
            r=focus_slow[focus_count];r[0]=focus_step;r[1]=elapsed;r[2]=f_calls;r[3]=f_award_lines;
            r[4]=f_decimal_lines;r[5]=f_loops;r[6]=f_peak;r[7]=m[0x51];r[8]=((unsigned long)m[0x41]<<16)|((unsigned long)m[0x42]<<8)|m[0x43];
        }
        ++focus_count;
    }
}
static void f_score_start(void){if(f_active){++f_calls;f_award=focus_clock();}}
static void f_score_end(void){if(f_active){unsigned long cost=(focus_clock()-f_award)&0xffffffUL;f_award_lines+=cost;if(cost>f_peak)f_peak=cost;}}
