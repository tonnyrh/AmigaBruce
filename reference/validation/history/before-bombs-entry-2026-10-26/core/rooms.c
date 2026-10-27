#include "rooms.h"
#include "room_data.h"
#include "c64_rooms.h"
const BlRoomFacts *bl_room(unsigned char room){return &bl_room_facts[room<20?room:0];}
/* Compatibility flags for older HUD/fixtures. Dynamic doors now exist as
 * actual source cells; no four-door substitute controls the live room. */
unsigned char bl_progress_room_openings(const BlProgress *p,unsigned char room){
    (void)p;(void)room;return 0;
}
void bl_progress_door(const BlProgress *p,int slot,BlDoor *door){
    unsigned char row,col,tile=(unsigned char)(slot+2);
    *door=bl_room(p->room)->doors[slot];door->valid=0;
    for(row=2;row<=12;row++)for(col=0;col<40;col++)
        if(bl_c64_tile(col,row)==tile){door->column=col;door->row=row;door->valid=1;return;}
}
int bl_enemy_leave_room(BlFighter *f,int kind){
    const BlRoomFacts *r=bl_room(f->body.room);
    int i,x=bl_x(&f->body),row=(bl_y(&f->body)-12)/16;
    for(i=0;i<4;i++){
        const BlDoor *d=&r->doors[i];
        if(!d->valid || d->row<row || d->row>row+1)continue;
        if(!((d->column==39 && x>=302) || (d->column==0 && x<=4)))continue;
        /* C64 $2F90/$3001 clears the NPC active bit instead of changing the
         * player's room. ENEMY-EDGE-0001 measures Ninja's 160-step return. */
        f->active=0;f->respawn=r->enemy_exit_wait[kind];
        f->stun=0;f->reaction=BL_REACTION_NONE;f->sai=0;f->timer=0;
        f->body.attack=BL_ATTACK_NONE;f->body.walk_steps=0;
        return 1;
    }
    return 0;
}
void bl_progress_reset(BlProgress *p){
    int i;for(i=0;i<20;i++)p->collected[i]=0;
    bl_c64_reset();bl_c64_load(0);
    p->room=0;p->blocked_exit=0;p->openings=0;p->transitions=0;p->revision=0;p->pickups=0;p->score=0;
}
static void place(BlGame *g,int x,int y,unsigned char room){
    unsigned char facing=g->facing,actor=g->source_actor;
    bl_reset(g);g->room=room;g->facing=facing;
    g->source_actor=actor;
    g->x=(BlCoord)(x*16);g->y=(BlCoord)(y*16);
    g->previous_x=g->x;g->previous_y=g->y;
}
static void reset_enemies(BlCombat *w,unsigned char room){
    const BlRoomFacts *r=bl_room(room);
    int i;
    for(i=0;i<2;i++){
        BlFighter *f=&w->enemy[i];
        f->active=0;f->stun=0;f->reaction=BL_REACTION_NONE;f->sai=0;
        f->health=(signed short)(i==BL_YAMO?20:7);f->allowance=2;
        f->ai=BL_AI_WAIT;f->timer=0;
        f->respawn=(unsigned short)(r->enemies_enabled?(i==BL_YAMO?232:96):0);
        place(&f->body,r->enemy_x,r->enemy_y,room);
    }
}
void bl_progress_inspect_room(BlProgress *p,BlCombat *w,unsigned char room){
    const BlRoomFacts *r;
    if(room>=BL_ROOM_COUNT)return;
    r=bl_room(room);p->room=room;p->blocked_exit=0;++p->revision;
    p->openings=0;bl_c64_load(room);
    place(&w->player.body,r->entry_x,r->entry_y,room);
    w->player.active=1;w->player.health=36;w->player.stun=0;
    w->player.reaction=BL_REACTION_NONE;w->player.sai=0;w->player.respawn=0;
    reset_enemies(w,room);
}
static int enter_source_room(BlProgress *p,BlCombat *w){
    long px,py;unsigned char room;
    if(!bl_c64_transition(&px,&py,&room))return 0;
    if(room==11 && !(bl_c64_remaining(12)|bl_c64_remaining(14)|bl_c64_remaining(16))){
        /* $09F6-$0A0B redirects the completed hub to default entry R14. */
        room=13;px=bl_room(room)->entry_x;py=bl_room(room)->entry_y;
    }
    p->room=room;++p->revision;++p->transitions;bl_c64_load_at(room,px,py);
    place(&w->player.body,px,py,room);
    w->player.stun=0;w->player.reaction=BL_REACTION_NONE;
    reset_enemies(w,room);return 1;
}
static void room_death(BlCombat *w){
    bl_combat_hazard(w,0x8c); /* $3057-$3068 -> $407D */
}
static void moving_net_contact(BlFighter *f,unsigned char flags,unsigned char touching){
    /* $2E48 excludes state25. $310C overrides other live actor states,
     * including a jump or hit; CE=$10 is NOT a recoil/stun countdown. */
    if(f->reaction==BL_REACTION_DEAD)return;
    bl_moving_net_contact(&f->body,(touching && (flags&4)));
    if(touching && (flags&4)){f->stun=0;f->reaction=BL_REACTION_NONE;f->sai=0;}
}
static void npc_moving_net_contact(BlFighter *f){
    int dx,dy,col,row;unsigned char found=0,flags;
    if(!f->active)return;
    flags=bl_c64_contact(bl_x(&f->body),bl_y(&f->body),bl_c64_object_pose(&f->body),0);
    col=((unsigned char)((bl_x(&f->body)+24)/2-12))>>2;
    row=((unsigned char)(bl_y(&f->body)+(f->body.room==13?4:0)-12))>>4;
    for(dy=0;dy<2;dy++)for(dx=0;dx<3;dx++)
        if(bl_c64_tile(col+dx,row+dy)==0x62)found=1;
    moving_net_contact(f,flags,found);
}
void bl_progress_contacts(BlProgress *p,BlCombat *w,unsigned char input){
    BlGame *g=&w->player.body;
    int col,row,dx,dy,px=bl_x(g),py=bl_y(g);
    unsigned char flags,moving_net=0;
    (void)input;p->blocked_exit=0;
    if(!w->player.active || w->player.health<0)return;
    if(bl_c64_room()!=p->room)bl_c64_load(p->room);
    bl_c64_motion(g);flags=bl_c64_contact(px,py,bl_c64_object_pose(g),0);
    /* $2E39-$2EE9 scans three cells on each of two rows. The supplemental
     * flag is global: ASL $53 remains nonzero for all six ordinary cells.
     * Doors bypass that flag and must still pass the source $30D4 gate. */
    col=((unsigned char)((px+24)/2-12))>>2;
    row=((unsigned char)(py+(p->room==13?4:0)-12))>>4;
    for(dy=0;dy<2;dy++)for(dx=0;dx<3;dx++){
        unsigned char cc=(unsigned char)(col+dx),rr=(unsigned char)(row+dy);
        unsigned char tile=bl_c64_tile(cc,rr);
        if(tile>=2 && tile<=5){
            if(bl_c64_door(tile,px,py,(unsigned char)(g->state==BL_AIR && g->jump_phase==255)) && enter_source_room(p,w))return;
        }else if((tile==0x13||tile==0x14||tile==0x31) && (flags&2)){
            if(bl_c64_collect(cc,rr)){++p->pickups;p->score+=125;p->collected[p->room]=bl_c64_collected(p->room);}
        }else if((flags&2) && tile==0x60)bl_c64_object(tile,cc,rr);
        else if((tile==0x2d||tile==0x2e) && p->room==16)bl_c64_object(tile,cc,rr);
        else if((flags&2) && p->room!=18 &&
                (tile==0x64 || (tile==0x66 && p->room>=10) || tile==0x0f || tile==0x40 ||
                 (tile>=0x54&&tile<0x5b&&tile!=0x57)||(tile>=0x71&&tile<0x7d))){
            room_death(w);return; /* $304B/$407D, native respawn adapter. */
        }else if(tile==0x62)moving_net=1;
    }
    moving_net_contact(&w->player,flags,moving_net);
}
void bl_progress_step(BlProgress *p,BlCombat *w,unsigned char input){
    int i;unsigned char active=w->player.active,enemy_active[2];
    unsigned char previous_room=p->room;unsigned short before_respawn=w->player_respawns;
    const BlRoomFacts *r=bl_room(p->room);
    if(bl_c64_room()!=p->room)bl_c64_load(p->room);
    bl_c64_set_lives(w->lives);
    bl_c64_player_sprite_contact(bl_x(&w->player.body),bl_y(&w->player.body),bl_c64_object_pose(&w->player.body));
    bl_c64_tick(bl_x(&w->player.body),bl_y(&w->player.body));
    if(enter_source_room(p,w))return;
    for(i=0;i<2;i++)enemy_active[i]=w->enemy[i].active;
    bl_progress_contacts(p,w,input);
    if(p->room!=previous_room)return;
    for(i=0;i<2;i++)npc_moving_net_contact(&w->enemy[i]);
    w->lives=(signed char)bl_c64_read(0x28);
    if(bl_c64_dead()){
        /* Room programs already queue their own sound where specified. */
        bl_combat_hazard(w,0);
        if(w->invincible)bl_c64_clear_death();
    }
    if(!r->enemies_enabled)for(i=0;i<2;i++){w->enemy[i].active=0;w->enemy[i].respawn=0;}
    bl_combat_step(w,input);
    bl_c64_set_lives(w->lives);
    if((!active && w->player.active) || w->player_respawns!=before_respawn){
        place(&w->player.body,r->entry_x,r->entry_y,p->room);
        reset_enemies(w,p->room);bl_c64_load(p->room);++p->revision;
    }
    w->player.body.room=p->room;
    for(i=0;i<2;i++){
        if(!enemy_active[i] && w->enemy[i].active)place(&w->enemy[i].body,r->enemy_x,r->enemy_y,p->room);
        w->enemy[i].body.room=p->room;
        if(bl_y(&w->enemy[i].body)>218){w->enemy[i].active=0;w->enemy[i].respawn=96;}
    }
    if(w->player.active && bl_y(&w->player.body)>218){
        room_death(w);
    }
}
