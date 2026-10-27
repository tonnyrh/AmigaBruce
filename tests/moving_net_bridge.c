#include "../core/rooms.h"
#include "../core/c64_rooms.h"
#include "../core/source_climb.h"
#include "moving_net_fixture.h"
static BlCombat world;
static BlProgress progress;
long bl_net_native_contracts(void){return moving_net_fixture_run();}
void bl_net_prepare(long x,long y,long facing,long phase){
    BlGame *g;
    bl_progress_reset(&progress);bl_combat_reset(&world);
    bl_progress_inspect_room(&progress,&world,4);
    world.enemy[0].active=world.enemy[1].active=0;
    world.enemy[0].respawn=world.enemy[1].respawn=0;
    bl_c64_test_write(0x7a,1); /* Isolated player/net contacts, not due NPC spawns. */
    g=&world.player.body;g->x=(BlCoord)(x*16);g->y=(BlCoord)(y*16);
    g->facing=(unsigned char)facing;
    if(phase){g->state=BL_AIR;g->jump_phase=(unsigned char)phase;g->jump_direction=(signed char)(facing?1:-1);}
}
void bl_net_step(long input){bl_progress_step(&progress,&world,(unsigned char)input);}
long bl_net_read(long field){
    const BlGame *g=&world.player.body;
    switch(field){
    case 0:return bl_x(g);case 1:return bl_y(g);case 2:return g->facing;
    case 3:return g->wall.state==24?24:g->state==BL_CLIMB?g->climb_state:
        g->state==BL_AIR?(g->jump_phase==255?14:g->jump_direction<0?6:g->jump_direction>0?7:5):0;
    case 4:return g->net_delay;case 5:return g->net_hold;
    case 6:return bl_c64_object_pose(g);case 7:return g->wall.previous;
    case 8:return g->wall.animation;case 9:return world.player.stun;
    case 10:return world.player.health;case 11:return g->wall.state;
    default:return -1;
    }
}
