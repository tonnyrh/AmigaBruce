/* Audit the EXISTING decision function. Movement is an explicitly recorded
 * request, not simulated C64/Amiga physics. Nothing here enters the game. */
#include <string.h>
#include "../core/combat.c"

static BlFighter fixture_enemy,fixture_player;
static unsigned char requested_input,movement_calls;
static BlRoomFacts empty_room;

int bl_x(const BlGame *g){return g->x/16;}
int bl_y(const BlGame *g){return g->y/16;}
void bl_reset(BlGame *g){memset(g,0,sizeof(*g));}
void bl_step(BlGame *g,unsigned char input){(void)g;requested_input=input;++movement_calls;}
void bl_step_npc(BlGame *g,unsigned char input){bl_step(g,input);}
void bl_record_recoil(BlGame *g,int pixels){(void)g;(void)pixels;}
int bl_contact_kind(const BlGame *g,int x,int y,int prone){(void)g;(void)x;(void)y;(void)prone;return 0;}
void bl_c64_audio_request(long effect){(void)effect;}
const BlRoomFacts *bl_room(unsigned char room){(void)room;return &empty_room;}
int bl_enemy_leave_room(BlFighter *f,int kind){(void)f;(void)kind;return 0;}

void bl_ai_adapter(long actor,long ex,long ey,long px,long py,long facing,
                   long state,long counter,long motion){
    memset(&fixture_enemy,0,sizeof(fixture_enemy));
    memset(&fixture_player,0,sizeof(fixture_player));
    fixture_enemy.active=fixture_player.active=1;
    fixture_enemy.health=fixture_player.health=20;
    fixture_enemy.body.x=(BlCoord)((ex*2-24)*16);
    fixture_enemy.body.y=(BlCoord)(ey*16);
    fixture_enemy.body.facing=(unsigned char)facing;
    fixture_enemy.body.state=(unsigned char)motion;
    fixture_enemy.ai=(unsigned char)(state==21?BL_AI_RETREAT:BL_AI_CHASE);
    if(state==22){fixture_enemy.sai=1;fixture_enemy.ai=BL_AI_ATTACK;}
    fixture_enemy.timer=(unsigned char)counter;
    fixture_player.body.x=(BlCoord)((px*2-24)*16);
    fixture_player.body.y=(BlCoord)(py*16);
    requested_input=movement_calls=0;
    enemy_step(&fixture_enemy,&fixture_player,actor==1?BL_YAMO:BL_NINJA);
}
long bl_ai_adapter_read(long field){
    switch(field){
    case 0:return fixture_enemy.ai;
    case 1:return fixture_enemy.timer;
    case 2:return fixture_enemy.sai;
    case 3:return fixture_enemy.body.attack;
    case 4:return fixture_enemy.body.facing;
    case 5:return requested_input;
    case 6:return movement_calls;
    default:return -1;
    }
}
