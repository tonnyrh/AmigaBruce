#include <stdio.h>
#include <stdlib.h>
#include "../core/rooms.h"
#include "../core/c64_rooms.h"
#include "../core/source_audio.h"
#include "contact_fixture.h"
#include "movement_fixture.h"
#include "climb_fixture.h"
#include "npc_recoil_fixture.h"
#include "session_fixture.h"
#include "session_wall_fixture.h"
#define CHECK(q) do{if(!(q)){fprintf(stderr,"FAIL line%d: %s\n",__LINE__,#q);return 1;}}while(0)

static void clear_room(unsigned char room){
    unsigned char i;const BlRoomFacts *facts=bl_room(room);bl_c64_load(room);
    for(i=0;i<facts->lantern_count;i++)
        if(!bl_c64_collect(facts->lanterns[i].column,facts->lanterns[i].row))abort();
}

static int audited_actor_cases(void){
    BlGame g;BlCombat world;int x,y,i,net_x=-1,net_y=-1;
    const unsigned char diagonals[]={BL_UP|BL_LEFT,BL_UP|BL_RIGHT,BL_DOWN|BL_LEFT,BL_DOWN|BL_RIGHT};
    const unsigned char catch_input[]={0,BL_LEFT,BL_RIGHT,BL_UP,BL_UP|BL_RIGHT};
    bl_c64_reset();bl_c64_load(0);
    /* Pick a class4 location from actual R01 glyphs, independently of a
     * hand-drawn platform/net rectangle. This only tests the current pose2
     * adapter, not full source animation/contact equivalence. */
    for(y=100;y<176 && net_x<0;y++)for(x=120;x<190;x+=2)
        if((bl_c64_contact(x,y,2,0)&13)==4){net_x=x;net_y=y;break;}
    CHECK(net_x>=0);
    bl_reset(&g);g.x=100*16;g.y=196*16;
    bl_step_npc(&g,BL_RIGHT);CHECK(!(bl_c64_audio_requests()&1));
    bl_step(&g,BL_RIGHT);CHECK(bl_c64_audio_requests()&1);
    for(i=0;i<4;i++){
        bl_reset(&g);g.x=(BlCoord)(net_x*16);g.y=(BlCoord)(net_y*16);g.state=BL_CLIMB;
        bl_step(&g,diagonals[i]);
        CHECK(bl_x(&g)==net_x && bl_y(&g)==net_y && !g.climb_wait);
    }
    for(i=0;i<5;i++){
        bl_reset(&g);g.x=(BlCoord)(net_x*16);g.y=(BlCoord)(net_y*16);
        g.state=BL_AIR;g.jump_phase=7;g.jump_direction=1;
        bl_step(&g,catch_input[i]);
        CHECK(g.state==BL_CLIMB && bl_x(&g)==net_x && bl_y(&g)==net_y);
    }
    bl_combat_reset(&world);
    world.enemy[0].active=1;world.enemy[0].body.x=112*16;world.enemy[0].body.y=196*16;
    world.player.body.x=100*16;world.player.body.y=196*16;
    world.player.body.attack=BL_PUNCH;world.player.body.attack_phase=1;
    CHECK(bl_combat_contact(&world.player,&world.enemy[0],0)==3);
    CHECK(world.enemy[0].health==17 && world.enemy[0].stun==4);
    CHECK(bl_x(&world.enemy[0].body)==112 && world.enemy[0].body.facing==0);
    bl_combat_step(&world,0);
    CHECK(world.enemy[0].health==17 && world.enemy[0].stun==3);
    CHECK(bl_x(&world.enemy[0].body)==116);
    bl_combat_reset(&world);
    world.player.health=-1;world.player.stun=1;world.player.reaction=BL_REACTION_DOWN;
    world.player.body.wall.state=24;world.player.body.wall.counter=64;
    bl_combat_step(&world,0);
    CHECK(world.player.active && world.player.health==36 && world.player_respawns==1 && world.lives==3);
    puts("PASS source-audited T10 diagonal stop/input-independent net catch and T13 assignment then one recoil update (actor adapter scope)");
    return 0;
}

int main(void){
    BlCombat world;BlProgress progress;BlGame fall;unsigned char room;int i;long px,py;
    BlSourceAudio audio;BlPaulaVoice voices[3];unsigned char registers[26];
    unsigned long audio_hash=2166136261UL,music_hash=2166136261UL;int ch,k;
    CHECK(!audited_actor_cases());
    CHECK(!session_fixture_run());
    CHECK(!session_wall_fixture_run());
    puts("PASS source life countdown, fall reserves, Game Over, debug flags and independent two-player progress");
    CHECK(!npc_recoil_fixture_run());
    printf("PASS %u NPC recoil/wall/re-entry regressions in R02\n",(unsigned)BL_NPC_RECOIL_FIXTURE_CASES);
    CHECK(!movement_fixture_run());
    puts("PASS 70 source-derived wall/kick/jump checks");
    CHECK(!climb_fixture_run());
    printf("PASS %u source-derived net dispatch and room5 climb checks\n",(unsigned)BL_CLIMB_FIXTURE_CASES);
    CHECK(!contact_fixture_run());
    puts("PASS 29 source-checked object/door fixtures, directional masks and single pickup");
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
    bl_source_audio_reset(&audio);
    for(i=0;i<120;i++){
        bl_source_audio_music(&audio,registers);bl_source_audio_render(&audio,registers,voices);
        for(ch=0;ch<3;ch++){
            const BlPaulaVoice *v=voices+ch;
            unsigned char bytes[7]={(unsigned char)(v->offset>>8),(unsigned char)v->offset,
                (unsigned char)(v->length>>8),(unsigned char)v->length,
                (unsigned char)(v->period>>8),(unsigned char)v->period,(unsigned char)v->volume};
            for(k=0;k<7;k++)music_hash=(music_hash^bytes[k])*16777619UL;
        }
    }
    CHECK(!bl_source_audio_faults());
    bl_source_audio_reset(&audio);bl_c64_audio_reset();
    for(i=0;i<6000;i++){
        if(i>=20&&i<=300&&i%20==0)bl_c64_audio_request(0x80+i/20-1);
        bl_c64_audio_frame(registers);bl_source_audio_render(&audio,registers,voices);
        for(ch=0;ch<3;ch++){
            const BlPaulaVoice *v=voices+ch;
            unsigned char bytes[7]={(unsigned char)(v->offset>>8),(unsigned char)v->offset,
                (unsigned char)(v->length>>8),(unsigned char)v->length,
                (unsigned char)(v->period>>8),(unsigned char)v->period,(unsigned char)v->volume};
            for(k=0;k<7;k++)audio_hash=(audio_hash^bytes[k])*16777619UL;
        }
        bl_c64_field();
        if(i%3==0)bl_progress_step(&progress,&world,(unsigned char)(i<3000?0:BL_FIRE));
    }
    CHECK(!bl_c64_fault());
    CHECK(!bl_c64_audio_faults() && !bl_source_audio_faults());
    printf("AUDIO_6000 source_audio_hash=%lu source_music_hash=%lu source_sfx_request_mask=%u source_audio_chip_bytes=%lu\n",
        audio_hash,music_hash,bl_c64_audio_requests(),bl_source_audio_chip_bytes());
    printf("M3_6000 combat_hits=%u enemy_defeats=%u enemy_spawns=%u player_deaths=%u player_respawns=%u final_x=%d final_y=%d\n",
        world.hits,world.defeats,world.spawns,world.player_deaths,world.player_respawns,
        bl_x(&world.player.body),bl_y(&world.player.body));
    return 0;
}
