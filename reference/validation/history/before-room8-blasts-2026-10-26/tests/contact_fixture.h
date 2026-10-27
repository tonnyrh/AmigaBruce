#ifndef BRUCE_CONTACT_FIXTURE_H
#define BRUCE_CONTACT_FIXTURE_H
#include "../core/rooms.h"
#include "../core/c64_rooms.h"
/* Injected states, checked independently against $5212 -> $2E39 and the
 * transition boundary $2F8E. They do not claim natural play or retail identity.
 * room,x,y,dx,action(0 idle/1 punch/2 prone),face,newroom,newx,newy,pickups */
static const signed short contact_cases[][10]={
 {0,296,98,2,0,1,0,296,98,0},
 {0,298,98,2,0,1,0,298,98,0},
 {0,300,98,0,0,1,0,300,98,0},
 {0,300,98,2,0,1,1,6,98,0},
 {0,302,98,2,0,1,1,6,98,0},
 {0,300,98,-2,0,1,0,300,98,0},
 {0,300,75,2,0,1,0,300,75,0},
 {0,300,76,2,0,1,1,6,98,0},
 {0,300,107,2,0,1,1,6,98,0},
 {0,300,108,2,0,1,0,300,108,1},
 {0,300,123,2,0,1,0,300,123,1},
 {0,300,124,2,0,1,1,8,146,1},
 {0,300,155,2,0,1,1,8,146,0},
 {0,300,156,2,0,1,0,300,156,1},
 {1,8,98,-2,0,0,1,8,98,0},
 {1,6,98,-2,0,0,0,298,98,0},
 {1,6,146,-2,0,0,0,296,146,0},
 {0,238,108,0,1,0,0,238,108,1},
 {0,248,108,0,1,0,0,248,108,0},
 {0,238,108,0,1,1,0,238,108,1},
 {0,248,109,0,1,1,0,248,109,0},
 {0,244,108,0,2,0,0,244,108,0},
 {0,236,115,0,2,0,0,236,115,1},
 {0,244,108,0,2,1,0,244,108,0},
 {0,236,115,0,2,1,0,236,115,1},
 {0,242,108,0,0,0,0,242,108,1},
 {0,238,121,0,0,0,0,238,121,0},
 {0,238,108,0,0,1,0,238,108,0},
 {0,248,108,0,0,1,0,248,108,1}
};
#define BL_CONTACT_CASE_COUNT (sizeof(contact_cases)/sizeof(contact_cases[0]))
static void contact_fixture_prepare(BlProgress *p,BlCombat *w,unsigned short index){
    const signed short *v=contact_cases[index];BlGame *g=&w->player.body;
    bl_combat_reset(w);bl_progress_reset(p);
    if(v[0])bl_progress_inspect_room(p,w,(unsigned char)v[0]);
    g->x=(BlCoord)(v[1]*16);g->y=(BlCoord)(v[2]*16);
    g->previous_x=(BlCoord)((v[1]-v[3])*16);g->previous_y=g->y;
    g->facing=(unsigned char)v[5];g->walk_steps=0;
    g->attack=(unsigned char)(v[4]==1?BL_PUNCH:BL_ATTACK_NONE);
    g->prone=(unsigned char)(v[4]==2);
}
static unsigned short contact_fixture_run(void){
    BlProgress p;BlCombat w;unsigned short i;
    for(i=0;i<BL_CONTACT_CASE_COUNT;i++){
        const signed short *v=contact_cases[i];
        contact_fixture_prepare(&p,&w,i);bl_progress_contacts(&p,&w,0);
        if(p.room!=v[6] || bl_x(&w.player.body)!=v[7] || bl_y(&w.player.body)!=v[8] ||
           p.pickups!=v[9] || p.score!=(unsigned long)v[9]*125 ||
           ((bl_c64_audio_requests()&16384)!=0)!=(v[9]!=0))return (unsigned short)(i+1);
        if(v[9]){
            bl_progress_contacts(&p,&w,0);
            if(p.pickups!=1 || p.score!=125 || bl_c64_remaining(v[0])!=5)return (unsigned short)(i+1);
        }
    }
    return 0;
}
#endif
