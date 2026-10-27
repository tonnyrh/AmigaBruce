/* Generated entry expectations from actual6502 calls. */
#ifndef BRUCE_BOMBS_ENTRY_FIXTURE_H
#define BRUCE_BOMBS_ENTRY_FIXTURE_H
#include "../core/rooms.h"
#include "../core/c64_rooms.h"
#include "../core/c64_sprites.h"
static const short source_entry_cases[][8]={
{5,1,0,0,0,44,81,20},
{5,1,0,0,1,44,81,6},
{5,1,255,0,0,44,81,20},
{5,1,255,1,0,56,194,20},
{5,2,0,0,0,44,81,7},
{5,2,0,0,1,44,81,6},
{5,2,255,0,0,44,81,7},
{5,2,255,1,0,56,194,7},
{6,1,0,0,0,244,179,20},
{6,1,0,0,1,44,81,6},
{6,1,255,0,0,234,114,20},
{6,1,255,1,0,234,114,20},
{6,2,0,0,0,244,179,7},
{6,2,0,0,1,44,81,6},
{6,2,255,0,0,244,179,7},
{6,2,255,1,0,234,114,7},
{7,1,0,0,0,38,116,20},
{7,1,0,0,1,44,81,6},
{7,1,255,0,0,32,68,20},
{7,1,255,1,0,38,116,20},
{7,2,0,0,0,38,116,7},
{7,2,0,0,1,44,81,6},
{7,2,255,0,0,32,68,7},
{7,2,255,1,0,38,116,7},
{10,1,0,0,0,276,92,20},
{10,1,0,0,1,44,81,6},
{10,1,255,0,0,80,140,20},
{10,1,255,1,0,276,92,20},
{10,2,0,0,0,276,92,7},
{10,2,0,0,1,44,81,6},
{10,2,255,0,0,80,140,7},
{10,2,255,1,0,276,92,7}
};
static const short source_bomb_contacts[][3]={{0,132,173},{1,134,173},{2,132,173}};
static const short source_blast_contacts[][4]={{1,134,163,238},{2,132,163,48}};
static unsigned short bombs_entry_fixture_run(void){
    BlCombat w;BlProgress p;BlC64Sprite v;unsigned short i,j;long px,py,h;
    for(i=0;i<sizeof(source_entry_cases)/sizeof(source_entry_cases[0]);i++){
        const short *c=source_entry_cases[i];
        bl_c64_reset();bl_c64_load(c[0]);bl_c64_test_write(0x16,0x20);bl_c64_test_write(0x17,0x60);
        bl_c64_test_write(0x6021+3-c[1],c[2]);bl_c64_test_write(0x6022+3-c[1],c[3]);
        if(c[4])bl_c64_enemy_follow(c[1],1,44,81,6);
        h=c[1]==1?20:7;px=py=0;bl_c64_enemy_entry(c[1],&px,&py,&h);
        if(px!=c[5] || py!=c[6] || h!=c[7])return 1+i;
    }
    for(i=0;i<2;i++){
        const short *c=source_blast_contacts[i];BlFighter *f;
        bl_combat_reset(&w);bl_progress_reset(&p);bl_progress_inspect_room(&p,&w,6);
        for(j=0;j<2;j++){w.enemy[j].active=0;w.enemy[j].respawn=0;}
        f=&w.enemy[c[0]-1];f->active=1;f->body.x=c[1]*16;f->body.y=c[2]*16;f->body.facing=1;f->ai=BL_AI_WAIT;f->timer=6;
        bl_c64_test_write(0x4fde,8);bl_c64_test_write(0x4fe1,17);bl_c64_test_write(0x4fe4,10);bl_c64_test_execute(0x3228);
        bl_progress_step(&p,&w,0);if(f->active || f->respawn!=c[3])return 90+i;
    }
    for(i=0;i<3;i++){
        const short *c=source_bomb_contacts[i];BlFighter *f;
        bl_combat_reset(&w);bl_progress_reset(&p);bl_progress_inspect_room(&p,&w,6);
        for(j=0;j<2;j++){w.enemy[j].active=0;w.enemy[j].respawn=0;}
        f=c[0]?&w.enemy[c[0]-1]:&w.player;f->active=1;f->body.x=c[1]*16;f->body.y=c[2]*16;
        f->body.facing=1;f->ai=BL_AI_WAIT;f->timer=6;
        if(c[0])bl_progress_step(&p,&w,0);else bl_progress_contacts(&p,&w,0);
        if(bl_c64_read(0x4fde)!=1 || bl_c64_read(0x4fe1)!=17 || bl_c64_read(0x4fe4)!=10)return 40+i;
    }
    for(i=0;i<3;i++){
        bl_combat_reset(&w);bl_progress_reset(&p);bl_progress_inspect_room(&p,&w,6);
        w.enemy[0].respawn=w.enemy[1].respawn=0;
        w.player.body.x=124*16;w.player.body.y=170*16;w.player.body.facing=1;
        if(i==1){w.player.health=-1;w.player.stun=12;w.player.reaction=BL_REACTION_DOWN;w.player_deaths=1;}
        if(i==2){w.player.body.wall.state=24;w.player.body.wall.counter=64;w.player.body.wall.pose=2;}
        bl_c64_test_write(0x4fde,8);bl_c64_test_write(0x4fe1,17);bl_c64_test_write(0x4fe4,10);bl_c64_test_execute(0x3228);
        bl_progress_contacts(&p,&w,0);v.initialized=0;bl_c64_sprite_step(&v,&w.player,2);
        if(w.player.reaction!=BL_REACTION_DEAD || w.player.stun!=16 || w.player_deaths!=1 || v.pose!=8 ||
           !(bl_c64_audio_requests()&4096))return 50+i;
        bl_c64_test_write(0x8b,44);bl_c64_test_write(0x8c,56);
        for(j=0;j<16;j++){
            bl_combat_step(&w,0);
            if(j<15 && (bl_x(&w.player.body)!=124 || bl_y(&w.player.body)!=170))return 60+i;
        }
        if(w.player_respawns!=1 || w.lives!=3 || bl_c64_read(0x8b) || bl_c64_read(0x8c))return 70+i;
    }
    /* Live spawn integration must not overwrite the decoded point later. */
    for(i=0;i<4;i++){
        BlFighter *f;unsigned char actor=(unsigned char)(i/2+1),alternate=(unsigned char)(i&1);
        bl_combat_reset(&w);bl_progress_reset(&p);bl_progress_inspect_room(&p,&w,7);
        for(j=0;j<2;j++){w.enemy[j].active=0;w.enemy[j].respawn=0;}
        f=&w.enemy[actor-1];f->respawn=1;
        bl_c64_test_write(0x16,0x20);bl_c64_test_write(0x17,0x60);
        bl_c64_test_write(0x6021+3-actor,255);bl_c64_test_write(0x6022+3-actor,alternate?1:0);
        bl_combat_step(&w,0);
        if(!f->active || bl_x(&f->body)!=(alternate?38:32) || bl_y(&f->body)!=(alternate?116:68))return 80+i;
    }
    return 0;
}
#endif
