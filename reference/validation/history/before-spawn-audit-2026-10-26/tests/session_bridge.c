#include "session_fixture.h"
static BlGame probe;
static BlCombat life;
long bl_session_contracts(void){return session_fixture_run();}
long bl_cheat_room_contract(long room){return cheat_room_case((unsigned char)room);}
static BlSession cheat_session;static BlOptions cheat_options;static BlProgress cheat_progress;static BlCombat cheat_world;
void bl_cheat_start(long room){
    bl_options_reset(&cheat_options);cheat_options.debug=1;cheat_options.start_room=(unsigned char)room;
    bl_session_start(&cheat_session,&cheat_options,&cheat_progress,&cheat_world);
}
void bl_audit_prepare(long room,long px,long py,long facing,long phase){
    bl_c64_reset();bl_c64_load(room);bl_reset(&probe);
    probe.room=(unsigned char)room;probe.x=(BlCoord)(px*16);probe.y=(BlCoord)(py*16);
    probe.previous_x=probe.x;probe.previous_y=probe.y;probe.facing=(unsigned char)facing;
    if(phase){probe.state=BL_AIR;probe.jump_phase=(unsigned char)phase;probe.jump_direction=(signed char)(facing?1:-1);}
}
void bl_audit_step(long input,long npc){
    if(npc){probe.source_actor=(unsigned char)npc;bl_step_npc(&probe,(unsigned char)input);}else bl_step(&probe,(unsigned char)input);
}
long bl_audit_read(long field){
    switch(field){
    case 0:return bl_x(&probe);case 1:return bl_y(&probe);case 2:return probe.facing;
    case 3:return probe.state;case 4:return probe.jump_phase;case 5:return bl_c64_object_pose(&probe);
    case 6:return probe.wall.state;case 7:return probe.wall.counter;case 8:return probe.wall.contact;
    default:return -1;
    }
}
void bl_life_prepare(long lives){
    bl_c64_reset();bl_c64_load(0);bl_combat_reset(&life);life.lives=(signed short)lives;
    life.enemy[0].respawn=life.enemy[1].respawn=0;bl_combat_hazard(&life,0x8c);
}
long bl_life_step(void){bl_combat_step(&life,0);return life.player.stun;}
long bl_life_read(long field){
    switch(field){case 0:return life.lives;case 1:return life.game_over;
    case 2:return life.player_respawns;case 3:return bl_x(&life.player.body);
    case 4:return bl_y(&life.player.body);default:return -1;}
}
