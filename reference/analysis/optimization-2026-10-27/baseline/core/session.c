#include "session.h"
#include "c64_rooms.h"
void bl_options_reset(BlOptions *o){
    o->players=1;o->human_yamo=o->start_room=o->infinite_lives=o->invincible=o->debug=0;
}
static void source_fighter(BlFighter *f,unsigned char actor){
    BlC64Actor src;BlGame *g=&f->body;unsigned char row,col,state;
    bl_c64_world_actor(actor,&src);state=src.state;
    g->previous_x=g->x;g->previous_y=g->y;
    g->x=(BlCoord)(((int)src.x*2-24)*16);g->y=(BlCoord)(src.y*16);
    g->source_canonical=1;g->source_actor=actor;g->source_state=state;g->source_counter=src.counter;
    g->source_wait=src.wait;g->source_pose=src.pose;g->source_mask=src.mask;g->facing=src.facing;g->room=bl_c64_room();
    g->state=(unsigned char)((state==5||state==6||state==7||state==12||state==13||state==14)?BL_AIR:
        (state==1||state==2||state==3||state==4||state==23||src.contact&4)?BL_CLIMB:BL_GROUND);
    g->prone=(unsigned char)(state==26);g->attack=(unsigned char)(state==17?BL_PUNCH:state==12||state==13?BL_FLYING_KICK:state==22?BL_SAI:BL_ATTACK_NONE);
    g->attack_phase=src.counter;g->net_delay=src.net_delay;g->net_hold=src.net_hold;g->fall_push=src.fall_push;
    g->wall.state=state;g->wall.counter=src.counter;g->wall.previous=src.previous;g->wall.animation=src.animation;
    g->wall.pose=src.pose;g->wall.tracked=1;g->wall.contact=src.contact;
    for(row=0;row<11;row++)for(col=0;col<4;col++)g->wall.moves[row][col]=src.moves[row*4+col];
    f->active=(unsigned char)(src.active!=0);f->health=(signed char)src.health;f->respawn=src.respawn;
    f->timer=src.counter;f->stun=src.wait;f->allowance=src.quota;f->sai=(unsigned char)(state==22);f->entering=0;
    f->reaction=(unsigned char)(state==25?BL_REACTION_DEAD:state==19||state==27?BL_REACTION_DOWN:state==18?BL_REACTION_HURT:BL_REACTION_NONE);
}
static void source_session_view(BlSession *s,BlProgress *p,BlCombat *w){
    unsigned char i,room=bl_c64_room();unsigned short old_revision=(unsigned short)bl_c64_world_stat(9);
    /* saved[].revision is a renderer epoch only, never source progress. */
    if(s->saved[0].revision!=old_revision){++p->revision;s->saved[0].revision=old_revision;}
    if(p->room!=room)++p->transitions;
    p->room=room;p->score=bl_c64_world_stat(7);
    for(i=0;i<20;i++)p->collected[i]=bl_c64_collected(i);
    source_fighter(&w->player,0);source_fighter(&w->enemy[BL_YAMO],1);source_fighter(&w->enemy[BL_NINJA],2);
    w->step=(unsigned short)bl_c64_world_stat(0);w->spawns=(unsigned short)bl_c64_world_stat(1);
    w->player_respawns=w->player_deaths=(unsigned short)bl_c64_world_stat(2);
    w->lives=(signed char)bl_c64_world_stat(6);w->game_over=(unsigned char)(bl_c64_world_stat(3)!=0);
    w->infinite_lives=s->options.infinite_lives;w->invincible=s->options.invincible;w->human_yamo=s->options.human_yamo;
    s->current=(unsigned char)bl_c64_world_stat(5);s->lives[s->current]=w->lives;s->over=(unsigned char)bl_c64_world_stat(4);
}
void bl_session_source_start(BlSession *s,const BlOptions *o,BlProgress *p,BlCombat *w){
    unsigned char i;unsigned short at;
    s->options=*o;s->current=s->over=0;s->saved[0].revision=65535;
    bl_combat_reset(w);p->transitions=p->revision=p->pickups=0;p->room=0;p->blocked_exit=p->openings=0;p->score=0;
    bl_c64_world_start(o->players,o->human_yamo);
    if(o->start_room && o->start_room<20){
        bl_c64_world_jump(o->start_room);
        /* Explicit debug extension: prepare both players identically. The
         * normal two-player swap remains $183B/$0FED original code. */
        if(o->players==2){
            for(i=0;i<28;i++)bl_c64_test_write(0x439f+i,bl_c64_read(0x28+i));
            at=0x340;
            for(i=0;i<20;i++){
                unsigned short record=(unsigned short)(bl_c64_read(0x4ce2+2*i)|((unsigned short)bl_c64_read(0x4ce3+2*i)<<8));
                while(!(bl_c64_read(record)&128)){bl_c64_test_write(at++,bl_c64_read(record));record+=4;}
            }
        }
    }
    source_session_view(s,p,w);
}
void bl_session_source_step(BlSession *s,BlProgress *p,BlCombat *w,unsigned char input,unsigned char yamo_input){
    bl_c64_world_input(input,yamo_input);bl_c64_world_step(s->options.infinite_lives,s->options.invincible);
    source_session_view(s,p,w);
}
void bl_session_source_jump(BlSession *s,BlProgress *p,BlCombat *w,unsigned char room){
    bl_c64_world_jump(room);source_session_view(s,p,w);
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
