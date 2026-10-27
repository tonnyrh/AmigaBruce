#include "source_climb.h"

static void idle(BlSourceActor *a){
    /* $1F89-$1F9F: an already idle actor keeps its sprite latch. */
    if(!a->previous)++a->pose_lock;
    a->state=a->wait=a->counter=0;
}
static void unit(BlSourceActor *a,unsigned char direction){
    /* $1DF2/$1E39/$1E86/$1EC4. Horizontal X is in half-pixels.
     * $C8 was cleared by the source black/history entry. */
    if((direction==1 && a->y<46) || (direction==2 && a->y>=199) ||
       (direction==3 && a->x<13) || (direction==4 && a->x>=163)){
        idle(a);return;
    }
    if(direction==1)--a->y;
    else if(direction==2)++a->y;
    else if(direction==3){--a->x;a->facing=0;}
    else {++a->x;a->facing=1;}
    a->state=direction;a->counter=0;
    a->wait=(unsigned char)(direction<=2?3:0); /* $4A8C+state */
}
long bl_source_climb_step(BlSourceActor *a,long input,long fire){
    unsigned char direction,count,i;
    switch(input&15){
    case 4:direction=1;break; /* source $98=$0E */
    case 8:direction=2;break; /* source $98=$0D */
    case 1:direction=3;break; /* source $98=$0B */
    case 2:direction=4;break; /* source $98=$07 */
    default:idle(a);return 0; /* All diagonals stop on net, $1EDF etc. */
    }
    /* Source entry bounds precede the sound and repeated helper calls. */
    if((direction==1 && a->y<46) || (direction==2 && a->y>=199) ||
       (direction==3 && a->x<13) || (direction==4 && a->x>=163)){
        idle(a);return 0;
    }
    count=(unsigned char)((direction<=2?3:2)+(a->animation==0));
    for(i=0;i<count;i++){
        /* $1E70/$1EB1 test the prior state and CB each time, even on net.
         * Repeated calls select the same kick without a displacement. */
        if(direction>=3 && a->previous==direction && a->animation<4 && fire){
            a->facing=(unsigned char)(direction==4);
            a->state=(unsigned char)(direction==4?13:12);a->counter=12;a->wait=0;
        }else unit(a,direction);
    }
    return 1;
}
unsigned char bl_source_climb_pose(const BlSourceActor *a,long previous_pose){
    unsigned char old=(unsigned char)previous_pose;
    /* $2780, $288B-$28F2, $2974-$2993 with known net contact. */
    if(a->pose_lock)return old;
    if(a->state==12)return 22;
    if(a->state==13)return 26;
    if(!a->state && (old==10 || old==12))return old;
    return (unsigned char)(old==10?12:10);
}
