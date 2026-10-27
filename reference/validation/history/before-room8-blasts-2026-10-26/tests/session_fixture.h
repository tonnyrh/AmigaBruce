#ifndef BRUCE_SESSION_FIXTURE_H
#define BRUCE_SESSION_FIXTURE_H
#include "../core/session.h"
#include "../core/c64_rooms.h"
#include "../core/c64_sprites.h"
#include "ninja_wall_fixture.h"
#include "bombs_entry_fixture.h"
#define SESSION_CHECK(q) do{if(!(q))return __LINE__;}while(0)
static unsigned short session_fixture_run(void){
    BlSession s;BlOptions o;BlCombat w;BlProgress p;BlC64Sprite sprite;
    int i,x,y;unsigned short mask;
    {unsigned short failure=ninja_wall_fixture_run();if(failure)return 1000+failure;}
    {unsigned short failure=bombs_entry_fixture_run();if(failure)return 2000+failure;}
    bl_options_reset(&o);bl_session_start(&s,&o,&p,&w);
    SESSION_CHECK(w.lives==4 && o.players==1 && !o.debug && !w.invincible);
    x=bl_x(&w.player.body);y=bl_y(&w.player.body);
    bl_combat_hazard(&w,0x8c);
    for(i=0;i<15;i++){
        bl_session_step(&s,&p,&w,BL_UP|BL_RIGHT|BL_FIRE,0);
        sprite.initialized=0;bl_c64_sprite_step(&sprite,&w.player,2);
        SESSION_CHECK(w.player.stun==15-i && bl_x(&w.player.body)==x && bl_y(&w.player.body)==y);
        SESSION_CHECK(sprite.pose==8 && w.lives==4 && !w.player_respawns);
    }
    bl_session_step(&s,&p,&w,0,0);
    SESSION_CHECK(w.lives==3 && w.player.health==36 && w.player_respawns==1);
    SESSION_CHECK(w.enemy[0].respawn==232 && w.enemy[1].respawn==96);
    w.lives=0;bl_combat_hazard(&w,0);
    for(i=0;i<16;i++)bl_session_step(&s,&p,&w,0,0);
    SESSION_CHECK(s.over && w.game_over && w.lives==-1 && !w.player.active);
    o.infinite_lives=1;bl_session_start(&s,&o,&p,&w);w.lives=0;
    bl_combat_hazard(&w,0);for(i=0;i<16;i++)bl_session_step(&s,&p,&w,0,0);
    SESSION_CHECK(w.lives==0 && w.player.health==36 && !s.over);
    o.invincible=1;bl_session_start(&s,&o,&p,&w);bl_combat_hazard(&w,0x8c);
    SESSION_CHECK(w.player.health==36 && !w.player.stun && !w.player_deaths);
    bl_options_reset(&o);o.human_yamo=1;bl_session_start(&s,&o,&p,&w);
    SESSION_CHECK(w.lives==9 && w.human_yamo);
    /* Independent lantern identities survive changing turns twice. */
    bl_options_reset(&o);o.players=2;bl_session_start(&s,&o,&p,&w);
    SESSION_CHECK(bl_c64_collect(2,10));mask=bl_c64_collected(0);p.collected[0]=mask;p.score=125;
    bl_combat_hazard(&w,0);for(i=0;i<16;i++)bl_session_step(&s,&p,&w,0,0);
    SESSION_CHECK(s.current==1 && w.lives==4 && !p.collected[0] && !p.score && !bl_c64_collected(0));
    bl_combat_hazard(&w,0);for(i=0;i<16;i++)bl_session_step(&s,&p,&w,0,0);
    SESSION_CHECK(s.current==0 && w.lives==3 && p.score==125 && p.collected[0]==mask && bl_c64_collected(0)==mask);
    for(i=0;i<20;i++){
        bl_session_jump(&s,&p,&w,(unsigned char)i);
        SESSION_CHECK(p.room==i && w.player.body.room==i && !bl_c64_fault());
    }
    return 0;
}
#undef SESSION_CHECK
#endif
