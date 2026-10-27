#include "../core/combat.h"
#include "../core/c64_rooms.h"
static BlGame probe;
static BlFighter ninja,victim;
void bl_ninja_prepare(long x,long y,long facing,long counter,long seed){
    bl_c64_reset();bl_c64_load(5);bl_reset(&probe);probe.room=5;probe.source_actor=2;
    probe.x=(BlCoord)(x*16);probe.y=(BlCoord)(y*16);probe.facing=(unsigned char)facing;
    probe.attack=BL_SAI;probe.attack_phase=(unsigned char)counter;
    probe.wall.previous=22;probe.wall.animation=6;probe.wall.tracked=1;
    probe.wall.moves[0][facing?3:2]=(unsigned char)seed;
}
void bl_ninja_step(void){bl_step_npc(&probe,0);}
long bl_ninja_read(long field){
    switch(field){case 0:return bl_x(&probe);case 1:return bl_y(&probe);case 2:return probe.facing;
    case 3:return probe.wall.state==24?24:probe.attack==BL_SAI?22:0;
    case 4:return probe.wall.state==24?probe.wall.counter:probe.attack_phase;
    case 5:return bl_c64_object_pose(&probe);case 6:return probe.wall.contact;
    case 7:return probe.wall.previous;case 8:return probe.wall.animation;
    default:return field>=9 && field<53?probe.wall.moves[(field-9)/4][(field-9)%4]:-1;}
}
static void setup(BlFighter *f,int actor,long x,long y,long face){
    bl_reset(&f->body);f->body.source_actor=(unsigned char)actor;f->body.room=5;
    f->body.x=(BlCoord)(x*16);f->body.y=(BlCoord)(y*16);f->body.facing=(unsigned char)face;
    f->active=1;f->health=36;f->stun=f->sai=f->reaction=0;
}
long bl_ninja_touch(long pose,long face,long target_pose,long target_face,long dx,long dy){
    setup(&ninja,2,160,150,face);setup(&victim,0,160+dx,150+dy,target_face);
    ninja.body.wall.state=victim.body.wall.state=24;
    ninja.body.wall.pose=(unsigned char)pose;victim.body.wall.pose=(unsigned char)target_pose;
    return bl_combat_sprite_touch(&ninja,&victim);
}
long bl_ninja_hit(long face,long counter,long dx,long dy,long state,long target_face){
    setup(&ninja,2,160,150,face);setup(&victim,0,160+dx,150+dy,target_face);
    ninja.sai=1;ninja.timer=(unsigned char)counter;
    ninja.body.attack=BL_SAI;ninja.body.attack_phase=(unsigned char)counter;
    if(state==17){victim.body.attack=BL_PUNCH;victim.body.attack_phase=1;}
    if(state==26)victim.body.prone=1;
    if(state==14){victim.body.state=BL_AIR;victim.body.jump_phase=255;}
    if(state==1){victim.body.state=BL_CLIMB;victim.body.climb_state=1;victim.body.wall.pose=10;}
    return bl_combat_contact(&ninja,&victim,1);
}
long bl_ninja_chain(long bx,long yx){
    BlCombat w;bl_combat_reset(&w);
    setup(&w.player,0,bx,150,0);setup(&w.enemy[0],1,yx,150,0);setup(&w.enemy[1],2,160,150,1);
    w.enemy[0].ai=BL_AI_WAIT;w.enemy[0].timer=6;
    w.enemy[1].sai=1;w.enemy[1].timer=7;w.enemy[1].ai=BL_AI_ATTACK;
    w.enemy[1].body.attack=BL_SAI;w.enemy[1].body.attack_phase=7;
    bl_combat_step(&w,0);return 36-w.player.health;
}
