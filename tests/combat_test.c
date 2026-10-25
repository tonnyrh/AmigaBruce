/* HISTORICAL BLOCKOUT FIXTURE: retired from test-core.ps1. Its rectangles,
 * immediate-recoil and one-pair assertions are not C64 rules or current-core
 * acceptance criteria. See docs/TEST_AUDIT_2026-10-25.md. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../core/combat.h"
#include "../core/rooms.h"
static void arena(BlCombat *w){
    int i;bl_combat_reset(w);
    w->player.body.x=100*16;
    for(i=0;i<BL_ENEMIES;i++){
        w->enemy[i].active=1;w->enemy[i].body.x=(BlCoord)((112+i*100)*16);
        w->enemy[i].body.y=196*16;w->enemy[i].ai=BL_AI_CHASE;w->enemy[i].timer=0;
        w->enemy[i].body.facing=0;
    }
}
void test_combat(void){
    BlCombat w,a,b;BlProgress progress;int i,n,face,dx;unsigned long seed=12345;
    /* Native ENEMY-EDGE-0001: Ninja leaves the upper right door, waits160
     * steps, re-enters facing Bruce and can descend instead of wall-running. */
    bl_combat_reset(&w);w.enemy[BL_YAMO].respawn=0;
    w.enemy[BL_NINJA].active=1;w.enemy[BL_NINJA].respawn=0;
    w.enemy[BL_NINJA].body.x=302*16;w.enemy[BL_NINJA].body.y=98*16;
    w.enemy[BL_NINJA].body.facing=1;w.enemy[BL_NINJA].timer=0;
    bl_combat_step(&w,0);
    assert(!w.enemy[BL_NINJA].active && w.enemy[BL_NINJA].respawn==160);
    assert(w.enemy[BL_NINJA].health==7 && !w.defeats && !w.player_deaths);
    for(i=0;i<159;i++)bl_combat_step(&w,0);
    assert(!w.enemy[BL_NINJA].active && w.enemy[BL_NINJA].respawn==1);
    bl_combat_step(&w,0);
    assert(w.enemy[BL_NINJA].active && !w.enemy[BL_NINJA].body.facing);
    assert(bl_x(&w.enemy[BL_NINJA].body)==294 && bl_y(&w.enemy[BL_NINJA].body)==98);
    for(i=0;i<120 && bl_y(&w.enemy[BL_NINJA].body)<196;i++)bl_combat_step(&w,0);
    assert(bl_y(&w.enemy[BL_NINJA].body)==196 && bl_x(&w.enemy[BL_NINJA].body)<248);
    /* Every displayed extended-fist phase can hit, mirrored both ways.
     * Recovery/invalid phases, rear targets and hurt victims cannot. */
    for(face=0;face<2;face++)for(i=0;i<5;i++){
        int direction=face?1:-1;
        arena(&w);w.player.body.x=160*16;w.player.body.facing=(unsigned char)face;
        w.player.body.attack=BL_PUNCH;w.player.body.attack_phase=(unsigned char)i;
        w.enemy[0].body.x=(BlCoord)((160+direction*16)*16);
        assert(bl_combat_contact(&w.player,&w.enemy[0],0)==(i<4?3:0));
        if(i<4)assert(!bl_combat_contact(&w.player,&w.enemy[0],0));
        arena(&w);w.player.body.x=160*16;w.player.body.facing=(unsigned char)face;
        w.player.body.attack=BL_PUNCH;w.player.body.attack_phase=(unsigned char)i;
        w.enemy[0].body.x=(BlCoord)((160-direction*16)*16);
        assert(!bl_combat_contact(&w.player,&w.enemy[0],0));
    }
    /* Sai has a front-only window with an eight-pixel near limit. Test both
     * directions and victims facing either way, including a rear approach. */
    for(face=0;face<2;face++)for(dx=-24;dx<=24;dx++){
        int forward=face?dx:-dx;
        arena(&w);w.enemy[1].body.x=160*16;w.enemy[1].body.facing=(unsigned char)face;
        w.enemy[1].sai=1;w.enemy[1].timer=7;
        w.player.body.x=(BlCoord)((160+dx)*16);w.player.body.facing=(unsigned char)face;
        assert(bl_combat_contact(&w.enemy[1],&w.player,1)==
            (forward>=8 && forward<23?2:0));
        if(w.player.stun){
            assert(w.player.body.facing==!face);
            assert(bl_x(&w.player.body)==160+dx+(face?4:-4));
        }
        arena(&w);w.player.body.x=160*16;w.player.body.facing=(unsigned char)face;
        w.player.body.attack=BL_PUNCH;w.player.body.attack_phase=1;
        w.enemy[0].body.x=(BlCoord)((160+dx)*16);
        assert(bl_combat_contact(&w.player,&w.enemy[0],0)==
            (forward>=12 && forward<=20?3:0));
        arena(&w);w.player.body.x=160*16;w.player.body.facing=(unsigned char)face;
        w.player.body.attack=BL_FLYING_KICK;w.player.body.attack_phase=2;
        w.enemy[0].body.x=(BlCoord)((160+dx)*16);
        assert(bl_combat_contact(&w.player,&w.enemy[0],0)==
            (forward>=12 && forward<=20?7:0));
    }
    /* Rear kicks turn Yamo before recoil; every slide step continues along
     * the kick direction, even when Yamo was initially facing away. */
    for(face=0;face<2;face++){
        int direction=face?1:-1,old_x;
        arena(&w);w.enemy[1].active=0;
        w.player.body.x=160*16;w.player.body.facing=(unsigned char)face;
        w.player.body.attack=BL_FLYING_KICK;w.player.body.attack_phase=2;
        w.enemy[0].body.x=(BlCoord)((160+direction*12)*16);
        w.enemy[0].body.facing=(unsigned char)face;
        old_x=bl_x(&w.enemy[0].body);
        assert(bl_combat_contact(&w.player,&w.enemy[0],0)==7);
        assert(bl_x(&w.enemy[0].body)==old_x+direction*4);
        assert(w.enemy[0].body.facing==!face);
        w.player.active=0;
        for(i=0;i<10;i++){
            old_x=bl_x(&w.enemy[0].body);bl_combat_step(&w,0);
            assert(bl_x(&w.enemy[0].body)==old_x+direction*4);
        }
    }
    arena(&w);w.player.body.facing=1;w.player.body.attack=BL_PUNCH;w.player.body.attack_phase=1;
    assert(bl_combat_contact(&w.player,&w.enemy[0],0)==3);
    assert(w.enemy[0].health==17 && w.enemy[0].stun==3);
    assert(!bl_combat_contact(&w.player,&w.enemy[0],0));
    /* Zero health is alive. Only negative signed health defeats an actor. */
    w.enemy[0].health=3;w.enemy[0].stun=0;w.enemy[0].body.x=112*16;
    assert(bl_combat_contact(&w.player,&w.enemy[0],0)==3);
    assert(w.enemy[0].health==0 && w.enemy[0].active);
    w.enemy[0].stun=0;w.enemy[0].body.x=112*16;
    assert(bl_combat_contact(&w.player,&w.enemy[0],0)==3);
    assert(w.enemy[0].health==-3 && w.enemy[0].active && w.enemy[0].body.prone);
    for(i=0;i<11;i++)bl_combat_step(&w,0);
    assert(!w.enemy[0].active && w.enemy[0].respawn==96);
    for(i=0;i<96;i++)bl_combat_step(&w,0);
    assert(w.enemy[0].active && w.enemy[0].health==20 && w.spawns==1);
    arena(&w);w.player.body.attack=BL_FLYING_KICK;w.player.body.attack_phase=2;
    assert(bl_combat_contact(&w.player,&w.enemy[0],0)==7);
    /* Yamo stays visible, prone and immune while sliding backwards. At the
     * normal three-field seam, twelve reaction steps last about 720 ms. */
    assert(w.enemy[0].body.prone && bl_x(&w.enemy[0].body)==116);
    w.player.active=0;w.enemy[1].active=0;
    for(i=0;i<10;i++){
        bl_combat_step(&w,0);
        assert(w.enemy[0].body.prone && w.enemy[0].active);
    }
    assert(bl_x(&w.enemy[0].body)==156 && w.enemy[0].stun==1);
    bl_combat_step(&w,0);
    assert(!w.enemy[0].body.prone && !w.enemy[0].stun);
    assert(bl_x(&w.enemy[0].body)==156 && w.enemy[0].timer==6);
    /* A nearby Bruce behind the enemy starts a retreat, not instant facing
     * correction. Only sufficient separation permits the immediate turn. */
    arena(&w);w.enemy[1].active=0;w.player.body.x=130*16;
    bl_combat_step(&w,0);
    assert(w.enemy[0].ai==BL_AI_RETREAT && !w.enemy[0].body.facing);
    assert(bl_x(&w.enemy[0].body)==112);
    bl_combat_step(&w,0);assert(bl_x(&w.enemy[0].body)==108);
    arena(&w);w.enemy[1].active=0;w.player.body.x=200*16;
    bl_combat_step(&w,0);
    assert(w.enemy[0].body.facing && bl_x(&w.enemy[0].body)==116);
    arena(&w);w.enemy[1].active=0;w.player.body.y=144*16;
    bl_combat_step(&w,0);assert(bl_x(&w.enemy[0].body)==112);
    arena(&w);w.player.body.state=BL_AIR;w.player.body.jump_phase=255;
    w.enemy[0].body.facing=1;
    w.enemy[0].body.x=108*16;w.player.body.y=180*16;w.player.body.velocity_y=2*16;
    assert(bl_combat_contact(&w.player,&w.enemy[0],0)==5 && w.player.allowance==1);
    assert(w.enemy[0].body.facing); /* Fall branch does not call $2B3E. */
    w.enemy[0].stun=0;w.enemy[0].body.x=112*16;w.player.allowance=0;
    assert(!bl_combat_contact(&w.player,&w.enemy[0],0));
    arena(&w);w.enemy[1].body.x=116*16;w.enemy[1].body.facing=0;
    w.enemy[1].sai=1;w.enemy[1].timer=18;
    assert(!bl_combat_contact(&w.enemy[1],&w.player,1));
    w.enemy[1].timer=8;
    assert(!bl_combat_contact(&w.enemy[1],&w.player,1));
    w.enemy[1].timer=7;
    assert(bl_combat_contact(&w.enemy[1],&w.player,1)==2 && w.player.health==34);
    arena(&w);w.player.body.prone=1;w.enemy[1].body.x=116*16;
    w.enemy[1].body.facing=0;w.enemy[1].sai=1;w.enemy[1].timer=7;
    assert(!bl_combat_contact(&w.enemy[1],&w.player,1));
    arena(&w);w.enemy[0].active=0;w.enemy[1].body.x=116*16;
    bl_combat_step(&w,0);assert(w.enemy[1].sai);
    for(i=0;i<11;i++){bl_combat_step(&w,0);assert(w.player.health==36);}
    bl_combat_step(&w,0);assert(w.player.health==34);
    arena(&w);w.enemy[0].body.x=132*16;
    bl_combat_step(&w,0);assert(w.enemy[0].body.attack==BL_FLYING_KICK);
    arena(&w);w.enemy[0].body.x=116*16;
    bl_combat_step(&w,0);assert(w.enemy[0].body.attack==BL_PUNCH);
    /* Real idle pursuit must reach and kill Bruce, then restore play. */
    bl_combat_reset(&w);
    for(i=0;i<2000;i++)bl_combat_step(&w,0);
    assert(w.spawns>=2 && w.hits && w.player_deaths && w.player_respawns);
    printf("PASS: enemy pursuit, damage, death/respawn (%u hits, %u player deaths)\n",w.hits,w.player_deaths);
    bl_combat_reset(&w);
    for(i=0;i<95;i++)bl_combat_step(&w,0);
    assert(!w.enemy[BL_NINJA].active);
    bl_combat_step(&w,0);assert(w.enemy[BL_NINJA].active && w.spawns==1);
    for(i=96;i<231;i++)bl_combat_step(&w,0);
    assert(!w.enemy[BL_YAMO].active);
    bl_combat_step(&w,0);assert(w.enemy[BL_YAMO].active && w.spawns==2);
    /* Held-fire gameplay must be able to defeat real enemies, repeatedly. */
    bl_combat_reset(&w);
    for(i=0;i<3000;i++)bl_combat_step(&w,BL_FIRE);
    printf("Combat replay: %u enemy defeats, %u spawns, %u player respawns\n",w.defeats,w.spawns,w.player_respawns);
    assert(w.defeats && w.spawns>2);
    bl_combat_reset(&w);
    bl_progress_reset(&progress);
    for(i=0;i<2000;i++)bl_progress_step(&progress,&w,i<1000?0:BL_FIRE);
    assert(w.defeats && w.player_deaths && w.player_respawns);
    printf("M3_6000 enemy_spawns=%u combat_hits=%u enemy_defeats=%u player_deaths=%u player_respawns=%u final_x=%d final_y=%d\n",
        w.spawns,w.hits,w.defeats,w.player_deaths,w.player_respawns,bl_x(&w.player.body),bl_y(&w.player.body));
    memset(&a,0,sizeof(a));memset(&b,0,sizeof(b));
    bl_combat_reset(&a);bl_combat_reset(&b);
    for(n=0;n<100000;n++){
        seed=(seed*1664525ul+1013904223ul)&0xfffffffful;
        bl_combat_step(&a,(unsigned char)((seed>>16)&31));
        bl_combat_step(&b,(unsigned char)((seed>>16)&31));
        assert(!memcmp(&a,&b,sizeof(a)));
        for(i=-1;i<BL_ENEMIES;i++){
            const BlFighter *f=i<0?&a.player:&a.enemy[i];
            assert(bl_x(&f->body)>=4 && bl_x(&f->body)<=314);
            assert(bl_y(&f->body)>=0 && bl_y(&f->body)<=196);
            assert(f->health>=-7 && f->health<=36 && f->allowance<=2);
        }
    }
    puts("PASS: punch/kick/fall/sai damage, signed defeat, prone immunity, fall allowance, 100000 deterministic combat steps");
}
