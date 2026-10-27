#include "session.h"
#include "c64_rooms.h"
void bl_options_reset(BlOptions *o){
    o->players=1;o->human_yamo=o->start_room=o->infinite_lives=o->invincible=o->debug=0;
}
static void apply(BlSession *s,BlCombat *w){
    w->infinite_lives=s->options.infinite_lives;w->invincible=s->options.invincible;
    w->human_yamo=s->options.human_yamo;
}
static void prepare_cheat_room(BlProgress *p,BlCombat *w,unsigned char room){
    unsigned char i;
    bl_c64_debug_complete_before(room);
    for(i=0;i<room;i++)p->collected[i]=bl_c64_collected(i);
    bl_progress_inspect_room(p,w,room);
}
void bl_session_start(BlSession *s,const BlOptions *o,BlProgress *p,BlCombat *w){
    unsigned char i;
    s->options=*o;s->current=s->over=0;
    bl_combat_reset(w);bl_progress_reset(p);
    /* $0FBC-$0FC7: four spare falls, nine with human opponent selected. */
    w->lives=(signed short)(o->human_yamo?9:4);
    bl_c64_set_lives(w->lives);
    bl_c64_set_opponent_mode(o->human_yamo);
    if(o->start_room<20 && o->start_room)prepare_cheat_room(p,w,o->start_room);
    else if(o->human_yamo)bl_progress_inspect_room(p,w,0);
    for(i=0;i<2;i++){
        s->saved[i]=*p;s->lives[i]=w->lives;
        bl_c64_save_progress(s->source[i]);
    }
    apply(s,w);
}
void bl_session_jump(BlSession *s,BlProgress *p,BlCombat *w,unsigned char room){
    if(room>=20)return;
    prepare_cheat_room(p,w,room);w->game_over=0;s->over=0;apply(s,w);
    s->saved[s->current]=*p;s->lives[s->current]=w->lives;
    bl_c64_save_progress(s->source[s->current]);
}
void bl_session_step(BlSession *s,BlProgress *p,BlCombat *w,unsigned char input,unsigned char yamo_input){
    unsigned short respawns=w->player_respawns;
    unsigned char was_over=w->game_over,other=(unsigned char)(s->current^1);
    if(s->over)return;
    apply(s,w);w->yamo_input=yamo_input;
    bl_progress_step(p,w,input);
    if(respawns==w->player_respawns && was_over==w->game_over)return;
    s->lives[s->current]=w->lives;s->saved[s->current]=*p;
    bl_c64_save_progress(s->source[s->current]);
    if(s->options.players==2 && s->lives[other]>=0){
        unsigned short revision=p->revision;
        /* $183B-$1884: alternate after a lost life while the other player
         * still has an attempt. Restore independent room/lamps/score. */
        s->current=other;*p=s->saved[other];
        bl_c64_restore_progress(s->source[other],p->collected);
        bl_c64_set_opponent_mode(s->options.human_yamo);
        bl_combat_reset(w);w->lives=s->lives[other];
        bl_progress_inspect_room(p,w,p->room);p->revision=(unsigned short)(revision+1);
        apply(s,w);
    }else if(w->game_over)s->over=1;
}
