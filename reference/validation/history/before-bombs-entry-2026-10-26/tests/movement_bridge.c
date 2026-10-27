#include "../core/game.h"
#include "../core/c64_rooms.h"
static BlGame movement_probe;
void bl_recoil_prepare(long px,long facing){
    bl_reset(&movement_probe);movement_probe.x=(BlCoord)(px*16);
    movement_probe.y=150*16;movement_probe.facing=(unsigned char)facing;
}
void bl_recoil_run(long pixels){bl_record_recoil(&movement_probe,(int)pixels);}
void bl_move_prepare(long room,long px,long py,long facing,long counter){
    bl_c64_reset();bl_c64_load(room);bl_reset(&movement_probe);
    movement_probe.room=(unsigned char)room;
    movement_probe.x=(BlCoord)(px*16);movement_probe.y=(BlCoord)(py*16);
    movement_probe.previous_x=movement_probe.x;movement_probe.previous_y=movement_probe.y;
    movement_probe.facing=(unsigned char)facing;movement_probe.state=BL_AIR;
    movement_probe.attack=BL_FLYING_KICK;movement_probe.attack_phase=(unsigned char)(12-counter);
    movement_probe.wall.previous=(unsigned char)(facing?13:12);
}
void bl_move_run(void){bl_step(&movement_probe,0);}
void bl_jump_prepare(long direction){
    int i;
    bl_c64_reset();bl_c64_load(0);bl_reset(&movement_probe);
    /* Controlled empty playfield, not an altered reference binary. */
    for(i=0;i<1000;i++){bl_c64_test_write(0x8c00+i,6);bl_c64_test_write(0xd800+i,14);}
    for(i=0;i<8;i++)bl_c64_test_write(0xa030+i,0);
    movement_probe.x=120*16;movement_probe.y=130*16;
    movement_probe.previous_x=movement_probe.x;movement_probe.previous_y=movement_probe.y;
    movement_probe.state=BL_AIR;movement_probe.jump_phase=1;
    movement_probe.jump_direction=(signed char)direction;movement_probe.facing=(unsigned char)(direction>=0);
    movement_probe.wall.previous=(unsigned char)(direction<0?6:direction>0?7:5);
}
void bl_jump_run(long input){bl_step(&movement_probe,(unsigned char)input);}
long bl_move_read(long field){
    if(field==0)return bl_x(&movement_probe);
    if(field==1)return bl_y(&movement_probe);
    if(field==2)return movement_probe.facing;
    if(field==3)return movement_probe.attack;
    if(field==4)return 12-movement_probe.attack_phase;
    if(field==5)return movement_probe.wall.state;
    if(field==6)return movement_probe.wall.counter;
    if(field==7)return bl_c64_object_pose(&movement_probe);
    if(field>=8 && field<52)return movement_probe.wall.moves[(field-8)/4][(field-8)%4];
    if(field==53)return movement_probe.jump_phase;
    return movement_probe.wall.previous;
}
