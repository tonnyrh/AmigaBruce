#ifndef BRUCE_NPC_RECOIL_FIXTURE_H
#define BRUCE_NPC_RECOIL_FIXTURE_H
/* Controlled R02 reproduction, not a natural C64/VIC playthrough. The
 * C64 helpers/history are verified separately against the frozen bytes. */
#include "../core/rooms.h"
#include "../core/c64_rooms.h"
#define BL_NPC_RECOIL_FIXTURE_CASES 24
static unsigned short npc_recoil_fixture_run(void){
    BlCombat world;BlProgress progress;
    unsigned short testcase=0;int kind,dead,start,step,old_x,seen;
    for(kind=0;kind<2;kind++)for(dead=0;dead<2;dead++)for(start=0;start<6;start++){
        BlFighter *victim;int initial=start<4?276+start*4:286;
        ++testcase;
        bl_combat_reset(&world);bl_progress_reset(&progress);
        bl_progress_inspect_room(&progress,&world,1);
        world.enemy[1-kind].active=0;world.enemy[1-kind].respawn=0;
        victim=&world.enemy[kind];victim->active=1;
        victim->health=(signed short)(dead?6:20);victim->stun=0;
        victim->body.x=(BlCoord)(initial*16);
        victim->body.y=(BlCoord)((start==4?98:146)*16);
        victim->body.previous_x=victim->body.x;victim->body.previous_y=victim->body.y;
        if(start==5){
            victim->body.x=276*16;
            for(step=0;step<5;step++){
                victim->body.walk_steps=0;bl_step_npc(&victim->body,BL_RIGHT);
            }
            initial=bl_x(&victim->body);
            if(!(victim->body.wall.moves[0][3]|victim->body.wall.moves[1][3]))return testcase;
        }
        world.player.body.x=(BlCoord)((initial-14)*16);
        world.player.body.y=victim->body.y;world.player.body.facing=1;
        world.player.body.attack=BL_FLYING_KICK;world.player.body.attack_phase=3;
        if(bl_combat_contact(&world.player,victim,0)!=7)return testcase;
        /* Move Bruce away after the controlled hit, isolating the reaction
         * from further pair hits. The room/player must not be restarted. */
        world.player.body.x=24*16;world.player.body.y=98*16;
        world.player.body.attack=BL_ATTACK_NONE;seen=0;
        for(step=0;step<24;step++){
            old_x=bl_x(&victim->body);bl_progress_step(&progress,&world,0);
            if(progress.room!=1 || progress.transitions || world.player_deaths ||
               world.player_respawns || bl_x(&world.player.body)!=24 ||
               bl_y(&world.player.body)!=98 || world.player.health!=36)return testcase;
            if(bl_x(&victim->body)<0 || bl_x(&victim->body)>302)return testcase;
            if(!step && start!=5 && victim->active && victim->body.wall.moves[0][3]!=2)return testcase;
            if(victim->body.wall.state==24){
                seen=1;if(bl_x(&victim->body)>old_x)return testcase;
            }
        }
        if(start!=4 && !dead && (!seen || victim->body.wall.state==24))return testcase;
    }
    return 0;
}
#endif
