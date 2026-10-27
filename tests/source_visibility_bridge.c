#include "../core/session.h"
#include "../core/c64_rooms.h"
static BlSession session;static BlProgress progress;static BlCombat world;
void bl_visibility_prepare(void){
    bl_c64_reset();bl_c64_load(1);bl_options_reset(&session.options);
    session.current=session.over=0;session.saved[0].revision=65535;
    bl_combat_reset(&world);progress.room=1;progress.revision=0;
}
long bl_visibility_flag(long actor,long value){
    bl_c64_test_write(0x95+actor,value);
    bl_session_source_step(&session,&progress,&world,0,0);
    return actor==0?world.player.active:world.enemy[actor==1?BL_YAMO:BL_NINJA].active;
}
void bl_visibility_copy(unsigned char *out){long i;for(i=0;i<65536;i++)out[i]=bl_c64_read(i);}
