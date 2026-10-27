#include "../core/rooms.h"
#include "../core/c64_rooms.h"
#include "../core/c64_sprites.h"
static BlCombat world;static BlProgress progress;
static unsigned char source_state,source_counter,source_pose;
void bl_r8_prepare(long actor,long col,long row,long phase,long px,long py,long facing,long kind){
    BlFighter *f;BlSourcePose p;int i;
    bl_combat_reset(&world);bl_progress_reset(&progress);bl_progress_inspect_room(&progress,&world,7);
    for(i=0;i<2;i++){world.enemy[i].active=0;world.enemy[i].respawn=0;}
    f=&world.enemy[actor-1];f->active=1;f->body.x=(BlCoord)(px*16);f->body.y=(BlCoord)(py*16);
    f->body.facing=(unsigned char)facing;f->ai=BL_AI_WAIT;f->timer=6;
    source_state=source_counter=0;
    p.previous=(unsigned char)(facing?18:14);p.width=p.second_width=p.aa=p.locked=p.contact=0;
    if(kind==1 || kind==2){f->body.walk_steps=1;f->body.wall.pose=(unsigned char)(facing?(kind==1?18:20):(kind==1?14:16));source_state=20;source_counter=20;p.previous=(unsigned char)(facing?(kind==1?20:18):(kind==1?16:14));}
    if(kind==3 || kind==4){f->sai=1;f->ai=BL_AI_ATTACK;f->timer=(unsigned char)(kind==3?12:7);f->body.attack=BL_SAI;f->body.attack_phase=f->timer;source_state=22;source_counter=f->timer;}
    if(kind==5){f->body.attack=BL_PUNCH;f->body.attack_phase=1;source_state=17;source_counter=3;}
    if(kind==6){f->body.attack=BL_FLYING_KICK;f->body.attack_phase=4;source_state=(unsigned char)(facing?13:12);source_counter=8;}
    if(kind==7){f->body.state=BL_AIR;f->body.jump_phase=255;f->body.velocity_y=16;source_state=14;}
    if(kind==8){f->body.prone=1;source_state=26;}
    if(kind==9){f->reaction=BL_REACTION_HURT;f->stun=3;source_state=18;source_counter=3;}
    if(kind==10){f->reaction=BL_REACTION_DOWN;f->stun=12;f->body.prone=1;source_state=19;source_counter=12;}
    p.state=source_state;p.counter=source_counter;p.facing=(unsigned char)facing;
    source_pose=(unsigned char)(bl_source_pose(&p)+actor*70);
    bl_c64_test_write(0x4fde,phase);bl_c64_test_write(0x4fe1,col-1);bl_c64_test_write(0x4fe4,row-1);
    bl_c64_test_execute(0x3228);
}
void bl_r8_step(void){bl_progress_step(&progress,&world,0);}
long bl_r8_read(long actor,long field){
    const BlFighter *f=&world.enemy[actor-1];
    switch(field){case 0:return f->active;case 1:return f->respawn;case 2:return source_state;
    case 3:return source_counter;case 4:return source_pose;case 5:return bl_c64_object_pose(&f->body);
    default:return -1;}
}
