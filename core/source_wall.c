#include "source_wall.h"

void bl_source_wall_reset(BlSourceWall *w){
    unsigned char i,d;
    for(i=0;i<11;i++)for(d=0;d<4;d++)w->moves[i][d]=0;
    w->state=w->counter=w->previous=w->animation=w->tracked=w->contact=0;w->pose=2;
}
void bl_source_wall_record(BlSourceWall *w,long dx,long dy){
    if(dy<0)w->moves[0][0]+=(unsigned char)-dy;
    else w->moves[0][1]+=(unsigned char)dy;
    if(dx<0)w->moves[0][2]+=(unsigned char)(-dx/2);
    else w->moves[0][3]+=(unsigned char)(dx/2);
}
long bl_source_sai_step(BlSourceWall *w,BlSourceActor *a){
    long sound=a->counter==12;
    if(a->counter==1){a->state=0;a->counter=6;}
    else {++w->moves[0][a->facing?3:2];--a->counter;}
    return sound;
}
void bl_source_wall_age(BlSourceWall *w){
    unsigned char i,d;
    /* $1C6B-$1C9A: history ages only when current movement is nonzero. */
    if(w->moves[0][0]|w->moves[0][1]|w->moves[0][2]|w->moves[0][3])
        for(i=10;i;i--)for(d=0;d<4;d++)w->moves[i][d]=w->moves[i-1][d];
    for(d=0;d<4;d++)w->moves[0][d]=0;
}
static void begin(BlSourceWall *w,BlSourceActor *a){
    a->pose_lock=0;
    bl_source_wall_age(w);
    if(a->state && a->state==a->previous){if(a->animation)--a->animation;}
    else a->animation=6;
    a->previous=a->state;
}
static void move(BlSourceWall *w,BlSourceActor *a,unsigned char d){
    unsigned char moved=0;
    /* $1DF2/$1E39/$1E86/$1EC4 with $C8=0. Limits are checked BEFORE
     * the operation: raw X13 can decrement12; raw X162 can increment163. */
    if(d==0 && a->y>=46){--a->y;moved=1;}
    if(d==1 && a->y<199){++a->y;moved=1;}
    if(d==2 && a->x>=13){--a->x;a->facing=0;moved=1;}
    if(d==3 && a->x<163){++a->x;a->facing=1;moved=1;}
    if(moved){++w->moves[0][d];a->state=(unsigned char)(d+1);}
    else {a->state=0;if(!a->previous)++a->pose_lock;}
    a->counter=0;a->wait=(unsigned char)(a->state==1||a->state==2?3:0);
}
long bl_source_wall_step(BlSourceWall *w,BlSourceActor *a,long contact){
    unsigned char i,d,tries=8,vertical_only;
    begin(w,a);
    if(a->state==25)return 0; /* $1CB5: death bypasses the black branch. */
    /* $1CBC/$24B7-$24EA: state24 has its own recovery entry. */
    if(a->state==24 && a->counter){
        if(!(contact&8)){a->state=24;a->counter=0;a->wait=0;return 1;}
        for(i=1;i<11;i++)for(d=0;d<4;d++)if(w->moves[i][d])goto undo;
        return 2;
    }
    if(!(contact&8))return 0;
undo:
    /* $1CD0-$1D6E. $B6 is NOT recomputed inside this retry loop.
     * Up/horizontal inverses clear $85; down inverses leave it set. */
    vertical_only=1;
    for(d=0;d<4;d++)for(;;){
        --w->moves[1][d];
        if(w->moves[1][d]&128)break;
        if(d!=1)vertical_only>>=1;
        move(w,a,(unsigned char)(d^1));
    }
    /* $1D0A-$1D37: drop the consumed record and clear the final two. */
    for(i=0;i<9;i++)for(d=0;d<4;d++)w->moves[i][d]=w->moves[i+2][d];
    for(i=9;i<11;i++)for(d=0;d<4;d++)w->moves[i][d]=0;
    a->wait=0;
    if((--tries&128) || (contact&4))goto blocked;
    if(vertical_only){
        if(a->previous==26)goto blocked;
        begin(w,a);goto undo;
    }
    if(tries!=7)move(w,a,(unsigned char)(a->facing?2:3));
blocked:
    a->state=24;a->counter=64;return 1;
}
