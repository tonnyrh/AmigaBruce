/* Private counters. No intercepted instruction or service call is skipped. */
extern unsigned long sprite_clock(void);
enum { SETUP, SERVICE, DESTINATION, POSE, COPY, PHASES };
unsigned long sprite_lines[2][3][PHASES],sprite_calls[2][3][PHASES];
unsigned long sprite_steps,sprite_samples,sprite_outer,sprite_plain,sprite_blank;
unsigned long sprite_awards,sprite_score_changes,sprite_errors,sprite_active[3],sprite_still[3],sprite_same_pose[3];
unsigned long sprite_due[3],sprite_paid[3];
unsigned char sprite_detail,sprite_actor,sprite_phase;
static unsigned char probe_enabled,probe_group;
static unsigned char previous_pos[3][3],previous_active[3],parts[60][3];
static unsigned long origin,last_stamp,previous_score;

static unsigned long live_score(void){
    return ((unsigned long)m[0x41]<<16)|((unsigned short)m[0x42]<<8)|m[0x43];
}
static void check_score(void){
    unsigned long current=live_score();
    if(current!=previous_score)++sprite_score_changes;
    previous_score=current;
}
void sprite_arm(void){
    previous_score=live_score();probe_enabled=1;
}
static void sprite_begin(void){
    unsigned short i;
    if(!probe_enabled)return;
    check_score();
    for(i=0;i<3;i++){
        unsigned char active=m[0x95 + i]&1,px=m[0x9e + i],py=m[0xa1 + i],pose=m[0x4f4e + i];
        if(active){
            ++sprite_active[i];
            if(previous_active[i] && px==previous_pos[i][0] && py==previous_pos[i][1])++sprite_still[i];
            if(previous_active[i] && pose==previous_pos[i][2])++sprite_same_pose[i];
        }
        previous_pos[i][0]=px;previous_pos[i][1]=py;previous_pos[i][2]=pose;previous_active[i]=active;
    }
    /* Rotate through all four offsets, sampling 60 of 240 logical steps. */
    sprite_detail=(unsigned char)((sprite_steps&3)==((sprite_steps>>2)&3));
    ++sprite_steps;
    if(sprite_detail && sprite_samples>=60){++sprite_errors;sprite_detail=0;}
    sprite_phase=SETUP;sprite_actor=2;
    origin=last_stamp=sprite_clock();
}
static void sprite_mark(unsigned char phase,unsigned char actor){
    unsigned long now=sprite_clock();
    sprite_lines[probe_group][sprite_actor][sprite_phase]+=(now-last_stamp)&0xffffffUL;
    last_stamp=now;sprite_actor=actor;sprite_phase=phase;
    ++sprite_calls[probe_group][actor][phase];
}
static void sprite_end(void){
    unsigned long now;
    if(!probe_enabled)return;
    now=sprite_clock();
    if(sprite_detail){
        sprite_lines[0][sprite_actor][sprite_phase]+=(now-last_stamp)&0xffffffUL;
        sprite_outer+=(now-origin)&0xffffffUL;
        ++sprite_samples;sprite_detail=0;
    }else sprite_plain+=(now-origin)&0xffffffUL;
    if(actor_return!=0x1c2f)++sprite_errors;
}
void sprite_finish(void){
    unsigned short sample,i,k;
    check_score();probe_enabled=0;probe_group=1;
    /* Repeat the timestamp sequence with the observed component counts,
     * after recording the live measurement. The empty run estimates the
     * cost of the measuring code; it is not a replacement game path. */
    for(sample=0;sample<sprite_samples;sample++){
        unsigned long now;
        sprite_phase=SETUP;sprite_actor=2;origin=last_stamp=sprite_clock();
        for(i=3;i--;){
            sprite_mark(SERVICE,(unsigned char)i);sprite_mark(SETUP,(unsigned char)i);
            for(k=0;k<parts[sample][i];k++){
                sprite_mark(DESTINATION,(unsigned char)i);sprite_mark(SETUP,(unsigned char)i);
                sprite_mark(POSE,(unsigned char)i);sprite_mark(SETUP,(unsigned char)i);
                sprite_mark(COPY,(unsigned char)i);sprite_mark(SETUP,(unsigned char)i);
            }
        }
        now=sprite_clock();sprite_lines[1][sprite_actor][sprite_phase]+=(now-last_stamp)&0xffffffUL;
        sprite_blank+=(now-origin)&0xffffffUL;
    }
}
