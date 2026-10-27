#include "../core/rooms.h"
#include "../core/c64_rooms.h"
static BlCombat w;static BlProgress p;static unsigned char tested_actor;
void bl_spawn_copy(unsigned char *out){long i;for(i=0;i<65536;i++)out[i]=bl_c64_read(i);}
void bl_spawn_prepare(long room,long age,long round,long mode,long active,long kdelay,long ydelay,long data,long saved){
    long i;bl_c64_reset();bl_c64_load(room);bl_c64_test_execute(0x10c5);
    bl_c64_test_write(0x88,age);bl_c64_test_write(0x40,round);bl_c64_test_write(0x42ca,mode);
    bl_c64_test_write(0x16,0);bl_c64_test_write(0x17,0x60);
    for(i=0x6000;i<0x6300;i++)bl_c64_test_write(i,data);
    bl_c64_spawn_sync(1,active&1,56,98,20,ydelay);bl_c64_spawn_sync(2,active&2,120,98,7,kdelay);
    if(saved&1)bl_c64_enemy_follow(1,1,84,130,6);
    if(saved&2)bl_c64_enemy_follow(2,1,84,130,6);
}
void bl_spawn_run(void){bl_c64_spawn_services(80,196);}
void bl_spawn_entry_prepare(long actor,long bits,long color,long player_x,long history){
    long i;BlFighter *f;
    bl_combat_reset(&w);bl_progress_reset(&p);w.player.active=0;w.player.body.x=(BlCoord)(player_x*16);
    w.enemy[0].respawn=w.enemy[1].respawn=200;w.enemy[actor-1].respawn=1;
    bl_c64_test_write(0x16,0);bl_c64_test_write(0x17,0x60);
    for(i=0x6000;i<0x6300;i++)bl_c64_test_write(i,0);
    if(history){
        f=&w.enemy[actor-1];f->body.wall.moves[0][2]=1;f->body.wall.previous=19;f->body.wall.animation=5;
        bl_c64_test_write(0x4f5d+actor,1);bl_c64_test_write(0xc2+actor,19);bl_c64_test_write(0xcb+actor,5);
    }
    bl_combat_spawn_service(&w);w.spawn_ready=0;bl_c64_test_write(0x7a,1);
    bl_c64_test_write(0x7c,0xa0);
    /* Uniform, injected contact field. Original masks and $5212 still
     * determine contacts; this is not natural room geometry or a playthrough. */
    for(i=120;i<1000;i++){bl_c64_test_write(0x8c00+i,0);bl_c64_test_write(0xd800+i,color);}
    for(i=0;i<8;i++)bl_c64_test_write(0xa000+i,bits);
    tested_actor=(unsigned char)actor;f=&w.enemy[actor-1];f->body.wall.contact=0;
}
void bl_spawn_entry_step(long player_x){w.player.body.x=(BlCoord)(player_x*16);bl_combat_step(&w,0);}
long bl_spawn_entry_read(long field){
    BlFighter *f=&w.enemy[tested_actor-1];
    switch(field){case 0:return (bl_x(&f->body)+24)/2;case 1:return bl_y(&f->body);
    case 2:return f->body.facing;case 3:return f->entry_state;case 4:return f->timer;
    case 5:return f->entering;case 6:return f->body.wall.pose;case 7:return bl_combat_object_pose(f);
    case 8:return f->body.wall.counter;default:return -1;}
}
long bl_spawn_entry_transition(void){long x,y;unsigned char room;return bl_c64_transition(&x,&y,&room);}
void bl_spawn_world_prepare(void){
    long i;bl_combat_reset(&w);bl_progress_reset(&p);
    w.player.body.x=302*16;w.player.body.previous_x=w.player.body.x;w.player.active=0;
    bl_c64_test_write(0x95,0);
    bl_c64_test_write(0x17,0x60);bl_c64_test_write(0x16,0);bl_c64_test_write(0x9e,163);
    for(i=0x6000;i<0x6300;i++)bl_c64_test_write(i,1);
    for(i=0;i<2;i++)bl_c64_spawn_sync(i+1,0,bl_x(&w.enemy[i].body),bl_y(&w.enemy[i].body),w.enemy[i].health,w.enemy[i].respawn);
}
void bl_spawn_world_step(void){bl_c64_field();bl_c64_field();bl_c64_field();bl_progress_step(&p,&w,0);}
long bl_spawn_world_read(long actor,long field){
    BlFighter *f=&w.enemy[actor-1];
    switch(field){case 0:return f->active;case 1:return (bl_x(&f->body)+24)/2;case 2:return bl_y(&f->body);
    case 3:return f->body.facing;case 4:return f->respawn;case 5:return w.spawns;default:return -1;}
}
void bl_spawn_bomb_prepare(long actor,long col,long row,long phase){
    long i;bl_combat_reset(&w);bl_progress_reset(&p);bl_progress_inspect_room(&p,&w,7);
    w.player.active=0;bl_c64_test_write(0x95,0);
    w.enemy[0].respawn=w.enemy[1].respawn=200;w.enemy[actor-1].respawn=1;
    bl_c64_test_write(0x16,0);bl_c64_test_write(0x17,0x60);bl_c64_test_write(0x7c,0xa0);
    for(i=0x6000;i<0x6300;i++)bl_c64_test_write(i,1);
    bl_c64_enemy_follow(actor,1,col*8+4,row*16+4,6);
    for(i=0;i<2;i++)bl_c64_spawn_sync(i+1,0,bl_x(&w.enemy[i].body),bl_y(&w.enemy[i].body),w.enemy[i].health,w.enemy[i].respawn);
    bl_c64_test_write(0x4fde,phase);bl_c64_test_write(0x4fe1,col-1);bl_c64_test_write(0x4fe4,row-1);bl_c64_test_execute(0x3228);
}
void bl_spawn_bomb_step(void){bl_progress_step(&p,&w,0);}
