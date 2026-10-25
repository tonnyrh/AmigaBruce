#include <stdio.h>
#include <stdlib.h>
#include "../core/rooms.h"
#include "../core/c64_rooms.h"
#define CHECK(q) do{if(!(q)){fprintf(stderr,"FAIL line%d: %s\n",__LINE__,#q);return 1;}}while(0)

static void clear_room(unsigned char room){
    unsigned char i;const BlRoomFacts *facts=bl_room(room);bl_c64_load(room);
    for(i=0;i<facts->lantern_count;i++)
        if(!bl_c64_collect(facts->lanterns[i].column,facts->lanterns[i].row))abort();
}

int main(void){
    BlCombat world;BlProgress progress;BlGame fall;unsigned char room;int i;long px,py;
    bl_combat_reset(&world);bl_progress_reset(&progress);
    for(room=0;room<20;room++){
        bl_progress_inspect_room(&progress,&world,room);
        CHECK(progress.room==room && world.player.body.room==room && bl_c64_room()==room);
        CHECK(!bl_c64_fault());
    }
    bl_progress_reset(&progress);bl_reset(&fall);
    fall.x=220*16;fall.y=102*16;fall.state=BL_AIR;fall.jump_phase=255;
    for(i=0;i<10;i++){bl_step(&fall,(unsigned char)(i&1?BL_LEFT:BL_RIGHT));CHECK(bl_x(&fall)==220);}
    puts("PASS all20 source-room entries and confirmed T01 free-fall control");

    /* Injected source lamp collections, then ordinary native contact with
     * the animated hatch. This is not a natural-playthrough claim. */
    bl_combat_reset(&world);bl_progress_reset(&progress);
    clear_room(0);clear_room(1);clear_room(2);
    bl_progress_inspect_room(&progress,&world,1);
    for(i=0;i<4;i++)bl_c64_tick(24,98);
    CHECK(bl_c64_tile(19,12)==3 || bl_c64_tile(20,12)==3 || bl_c64_tile(21,12)==3);
    world.player.body.x=152*16;world.player.body.y=198*16;
    world.player.body.previous_x=152*16;world.player.body.previous_y=196*16;
    world.player.body.state=BL_AIR;world.player.body.jump_phase=255;
    bl_progress_contacts(&progress,&world,0);
    CHECK(progress.room==5 && progress.transitions==1);
    CHECK(bl_x(&world.player.body)==64 && bl_y(&world.player.body)==50);
    CHECK(bl_c64_remaining(0)==0 && bl_c64_remaining(1)==0 && bl_c64_remaining(2)==0);
    puts("PASS source-animated R02 hatch to R06, exact arrival and persistent lamps");

    bl_c64_reset();bl_c64_load(19);
    for(i=0;i<1113;i++){bl_c64_field();if(i%3==2)bl_c64_tick(28,196);}
    CHECK(bl_c64_transition(&px,&py,&room));
    CHECK(room==0 && px==28 && py==196);
    CHECK(bl_c64_read(0x40)==1 && bl_c64_remaining(0)==bl_room(0)->lantern_count);
    puts("PASS source final-room timer, next round and reset of original lamp counts");

    bl_c64_reset();bl_c64_load(18);
    bl_c64_test_write(0xd015,0x40);bl_c64_test_write(0xd00c,52);bl_c64_test_write(0xd00d,131);
    for(i=0;i<63;i++)bl_c64_test_write((unsigned short)(0x8340+i),255);
    bl_c64_player_sprite_contact(28,100,2);
    CHECK((bl_c64_read(0xd01e)&0x43)==0x43);
    bl_c64_tick(28,100);CHECK(bl_c64_dead());
    puts("PASS R19 source projectile bits/contact and source death branch");
    /* Same ordinary input and PAL-field seam as the6000-field native combat
     * route. This checks host/68000 agreement, not unknown C64 combat rules. */
    bl_combat_reset(&world);bl_progress_reset(&progress);
    for(i=0;i<6000;i++){
        bl_c64_field();
        if(i%3==0)bl_progress_step(&progress,&world,(unsigned char)(i<3000?0:BL_FIRE));
    }
    CHECK(!bl_c64_fault());
    printf("M3_6000 combat_hits=%u enemy_defeats=%u enemy_spawns=%u player_deaths=%u player_respawns=%u final_x=%d final_y=%d\n",
        world.hits,world.defeats,world.spawns,world.player_deaths,world.player_respawns,
        bl_x(&world.player.body),bl_y(&world.player.body));
    return 0;
}
