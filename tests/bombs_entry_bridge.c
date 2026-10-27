#include "../core/rooms.h"
#include "../core/c64_rooms.h"
#include "../core/c64_sprites.h"
static BlCombat world;static BlProgress progress;
static long sx,sy,health;
void bl_entry_prepare(long room,long actor,long first,long second,long saved){
    bl_c64_reset();bl_c64_load(room);
    bl_c64_test_write(0x16,0x20);bl_c64_test_write(0x17,0x60);
    bl_c64_test_write(0x6021+3-actor,first);bl_c64_test_write(0x6022+3-actor,second);
    if(saved)bl_c64_enemy_follow(actor,1,44,81,6);
    health=actor==1?20:7;sx=sy=0;
}
void bl_entry_run(long actor){bl_c64_enemy_entry(actor,&sx,&sy,&health);}
long bl_entry_read(long field){return field==0?sx:field==1?sy:health;}
void bl_bomb_prepare(long room,long actor,long x,long y,long dying){
    BlFighter *f;int i;bl_combat_reset(&world);bl_progress_reset(&progress);
    bl_progress_inspect_room(&progress,&world,(unsigned char)room);
    bl_c64_test_write(0x7a,1); /* Contact fixture: no unrelated spawns. */
    for(i=0;i<2;i++){world.enemy[i].active=0;world.enemy[i].respawn=0;}
    f=actor?&world.enemy[actor-1]:&world.player;
    f->active=1;f->body.x=(BlCoord)(x*16);f->body.y=(BlCoord)(y*16);f->body.facing=1;
    f->body.room=(unsigned char)room;f->body.source_actor=(unsigned char)actor;
    f->ai=BL_AI_WAIT;f->timer=6;
    if(dying==1){f->health=-1;f->reaction=BL_REACTION_DOWN;f->stun=12;world.player_deaths=1;}
    if(dying==2){f->body.wall.state=24;f->body.wall.pose=2;f->body.wall.counter=64;}
}
void bl_bomb_contact(void){bl_progress_contacts(&progress,&world,0);}
void bl_bomb_step(void){bl_progress_step(&progress,&world,0);}
void bl_bomb_actor_step(void){bl_combat_step(&world,0);}
long bl_bomb_read(long field){
    BlC64Sprite v;v.initialized=0;bl_c64_sprite_step(&v,&world.player,2);
    switch(field){case 0:return world.player.health;case 1:return world.player.stun;
    case 2:return world.player.reaction;case 3:return world.player_deaths;
    case 4:return bl_x(&world.player.body);case 5:return bl_y(&world.player.body);
    case 6:return v.pose;case 7:return world.player_respawns;case 8:return world.lives;
    case 9:return world.enemy[0].active;case 10:return world.enemy[1].active;
    case 11:return world.enemy[0].respawn;case 12:return world.enemy[1].respawn;
    default:return -1;}
}
