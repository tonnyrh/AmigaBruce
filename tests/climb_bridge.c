#include "../core/game.h"
#include "../core/c64_rooms.h"
static BlGame probe;
void bl_climb_prepare(long room,long px,long py,long state,long facing){
    bl_c64_reset();bl_c64_load(room);bl_reset(&probe);
    probe.room=(unsigned char)room;probe.x=(BlCoord)(px*16);probe.y=(BlCoord)(py*16);
    probe.previous_x=probe.x;probe.previous_y=probe.y;
    probe.state=(unsigned char)state;probe.facing=(unsigned char)facing;
}
void bl_climb_run(long input){bl_step(&probe,(unsigned char)input);}
long bl_climb_read(long field){
    if(field==0)return bl_x(&probe);
    if(field==1)return bl_y(&probe);
    if(field==2)return probe.state;
    if(field==3)return probe.facing;
    if(field==4)return probe.climb_wait;
    if(field==5)return probe.climb_steps;
    if(field==6)return probe.wall.animation;
    if(field==7)return probe.wall.previous;
    if(field==8)return bl_c64_object_pose(&probe);
    if(field==9)return bl_c64_contact(bl_x(&probe),bl_y(&probe),bl_c64_object_pose(&probe),0);
    if(field==10)return probe.wall.state;
    if(field==11)return probe.wall.counter;
    if(field==12)return probe.step;
    if(field==13)return probe.walk_steps;
    if(field==14)return probe.jump_phase;
    return probe.wall.pose;
}
