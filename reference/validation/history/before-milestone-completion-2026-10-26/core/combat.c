#include "combat.h"
#include "rooms.h"
#include "c64_rooms.h"
#include "c64_hit_data.h"
#include "c64_sprites.h"
static int magnitude(int x){return x<0?-x:x;}
unsigned char bl_combat_object_pose(const BlFighter *f){
    const BlGame *g=&f->body;
    if(f->entering)return f->entry_mask;
    unsigned char pose=(unsigned char)(bl_c64_object_pose(g)%70);
    if(g->wall.state!=24){
        if(f->reaction==BL_REACTION_DEAD)pose=8;
        else if(f->reaction==BL_REACTION_DOWN)
            pose=(unsigned char)(g->facing?(f->stun>=10?56:58):(f->stun>=10?60:62));
        else if(f->reaction==BL_REACTION_HURT)pose=(unsigned char)(g->facing?46:44);
        else if(f->reaction==BL_REACTION_FALL)pose=(unsigned char)(g->wall.contact&8?8:68);
        else if(f->sai)pose=(unsigned char)(g->facing?(f->timer>=11?52:54):(f->timer>=11?48:50));
    }
    return (unsigned char)(pose+g->source_actor*70);
}
static unsigned short hit_index(const BlFighter *f){
    const BlGame *g=&f->body;
    unsigned char kind=(unsigned char)(g->source_actor==0?2:g->source_actor==1?0:1);
    return (unsigned short)(kind*70+(g->facing?35:0)+(f->entering?g->wall.pose:bl_combat_object_pose(f)%70)/2);
}
/* $07EF-$07FA and $2584/$25E2: source hires components, doubled X.
 * This is an occupancy check of the adapter's current poses, not a VIC
 * raster/latched-history emulator. It never tests background occlusion. */
int bl_combat_sprite_touch(const BlFighter *a,const BlFighter *b){
    int dx=bl_x(&b->body)-bl_x(&a->body),dy=bl_y(&b->body)-bl_y(&a->body),row;
    const unsigned long *ar,*br;
    if(!a->active || !b->active || dx<=-48 || dx>=48 || dy<=-21 || dy>=21)return 0;
    ar=hit_rows[hit_frame[hit_index(a)]];br=hit_rows[hit_frame[hit_index(b)]];
    dx/=2; /* C64 actor X is always a half-pixel coordinate. */
    for(row=0;row<21;row++)if(row-dy>=0 && row-dy<21){
        unsigned long bits=br[row-dy];
        if(dx>=0)bits>>=dx;else bits<<=-dx;
        if(ar[row]&bits)return 1;
    }
    return 0;
}
static unsigned char sprite_latch(const BlFighter *const *actors,int count){
    unsigned char latch=0;int i,j;
    /* $29CE reads one aggregate latch. In a three-actor chain this can
     * enable a potential pair without that pair directly overlapping.
     * Internal component overlap also contributes its actor group. */
    for(i=0;i<count;i++){
        if(actors[i]->active && hit_self[hit_index(actors[i])])latch|=(unsigned char)(1<<i);
        for(j=0;j<i;j++)if(bl_combat_sprite_touch(actors[i],actors[j]))latch|=(unsigned char)((1<<i)|(1<<j));
    }
    return latch;
}
static void fighter_reset(BlFighter *f,int health,int x,int y){
    bl_reset(&f->body);f->body.x=(BlCoord)(x*16);f->body.y=(BlCoord)(y*16);
    f->body.previous_x=f->body.x;f->body.previous_y=f->body.y;
    f->health=(signed short)health;f->active=1;f->respawn=0;
    f->stun=0;f->allowance=2;f->ai=BL_AI_WAIT;f->timer=16;f->sai=0;
    f->reaction=BL_REACTION_NONE;
    f->entering=f->entry_state=f->entry_mask=0;
}
static void reaction_step(BlFighter *f,int actor){
    int pixels=4;
    if(f->reaction==BL_REACTION_DEAD){
        /* $1CB5 bypasses black recovery; $216B-$217A decrements the
         * counter without movement, then Bruce enters $1818 at one. */
        if(f->stun)--f->stun;
        return;
    }
    /* $240E-$24B0: living NPCs recover before the final recoil step.
     * Ninja has an asymmetric extra displacement at counter ten. */
    if(f->stun>1 || actor==0 || f->health<0){
        bl_step(&f->body,0);
        if(f->reaction==BL_REACTION_DOWN && actor==2 && f->stun==10)
            pixels+=f->body.facing?16:8;
        /* Wall recovery owns Bruce's coordinates. The remaining legacy
         * reaction/life timer must still finish, including negative health. */
        if(f->reaction!=BL_REACTION_FALL && f->body.wall.state!=24){
            /* $241F/$242E/$247E/$24A1 call the same recorded movement
             * helpers for every actor. NPC recoil must survive into the
             * next $1C68 history roll and black-contact rollback. An empty
             * history in state24 otherwise reaches $24DB's room re-entry.
             * Recovery owns NPC coordinates as well as Bruce's. */
            bl_record_recoil(&f->body,pixels);
        }
    }
    --f->stun;
    f->body.prone=(unsigned char)(f->reaction==BL_REACTION_DOWN);
    if(!f->stun){
        f->reaction=BL_REACTION_NONE;f->body.prone=0;
        f->ai=BL_AI_WAIT;f->timer=6;
        if(f->health<0){f->active=0;f->respawn=(unsigned short)(actor?bl_c64_enemy_remove(actor):0);}
    }
}
void bl_combat_reset(BlCombat *w){
    fighter_reset(&w->player,36,28,196);
    fighter_reset(&w->enemy[BL_YAMO],20,294,98);
    fighter_reset(&w->enemy[BL_NINJA],7,294,98);
    w->enemy[BL_YAMO].body.source_actor=1;w->enemy[BL_NINJA].body.source_actor=2;
    w->enemy[BL_YAMO].active=0;w->enemy[BL_YAMO].respawn=bl_c64_spawn_cold_counter(1);
    w->enemy[BL_NINJA].active=0;w->enemy[BL_NINJA].respawn=bl_c64_spawn_cold_counter(2);
    w->step=0;w->recharge=0;w->hits=0;w->defeats=0;w->spawns=0;
    w->player_deaths=0;w->player_respawns=0;
    w->lives=4;w->game_over=w->infinite_lives=w->invincible=w->human_yamo=w->yamo_input=0;
    w->spawn_ready=0;
}
void bl_combat_hazard(BlCombat *w,unsigned char sound){
    BlFighter *f=&w->player;
    if(w->invincible || !f->active || f->reaction==BL_REACTION_DEAD)return;
    if(sound)bl_c64_audio_request(sound);
    if(f->health>=0)++w->player_deaths;
    f->health=-1;f->stun=16;f->reaction=BL_REACTION_DEAD;
    f->body.attack=BL_ATTACK_NONE;f->body.prone=0;f->sai=0;
    f->body.wall.state=f->body.wall.counter=0; /* BF25 replaces BF24. */
}
static void finish_player_life(BlCombat *w){
    unsigned char room=w->player.body.room;
    const BlRoomFacts *r=bl_room(room);
    /* $1826 DEC $28; BMI $188E. Four FALLS means five attempts. */
    if(!w->infinite_lives)--w->lives;
    if(w->lives<0){w->game_over=1;w->player.active=0;w->player.respawn=0;return;}
    bl_c64_enemy_entries_clear();
    fighter_reset(&w->player,36,r->entry_x,r->entry_y);
    w->player.body.room=room;++w->player_respawns;
}
static int combat_contact(BlFighter *a,BlFighter *v,int ninja,int sprite_contact){
    int damage=0,kind;
    if(!a->active||!v->active||a->health<0||v->health<0||a->stun||v->stun||v->body.prone)return 0;
    kind=bl_contact_kind(&a->body,bl_x(&v->body),bl_y(&v->body),v->body.prone);
    /* $2A7B-$2A80: sai only hits when the remaining counter is below
     * eight. Counters 19..8 are wind-up, not an active hit window. */
    if(ninja && a->sai){
        int dx=bl_x(&v->body)-bl_x(&a->body);
        int forward=a->body.facing?dx:-dx;
        if(a->body.wall.state==24 || v->body.wall.state==24)return 0;
        /* $29CE/$2A7B/$2C54: sprite latch, counter<8, front distance
         * at least four half-pixels. There is no23px/Y box or wall ray. */
        if(sprite_contact && a->timer<8 && forward>=8)damage=2;
    }else if(kind==BL_CONTACT_PUNCH || kind==BL_CONTACT_KICK){
        int dx=bl_x(&v->body)-bl_x(&a->body);
        /* $2AA5/$2ADB use the same front-distance helper with limit six.
         * Overlapping blockout boxes alone must not permit a rear strike. */
        if((a->body.facing?dx:-dx)>=12)
            damage=kind==BL_CONTACT_PUNCH?3:7;
    }
    else if(kind==BL_CONTACT_FALL && a->allowance &&
            v->body.attack==BL_ATTACK_NONE){damage=5;--a->allowance;}
    if(!damage)return 0;
    /* $2A91 (sai), $2AC0/$2AE6/$2B2C -> $2E29 (other hits). */
    bl_c64_audio_request(damage==2?0x87:0x86);
    v->health=(signed short)(v->health-damage);
    v->reaction=damage==7 || v->health<0?BL_REACTION_DOWN:
        damage==5?BL_REACTION_FALL:BL_REACTION_HURT;
    v->stun=(unsigned char)(v->reaction==BL_REACTION_DOWN?12:
        damage==5?8:damage==3?4:3);
    v->body.attack=BL_ATTACK_NONE;v->body.attack_phase=0;v->sai=0;
    v->entering=0;
    v->body.walk_steps=0;v->body.jump_cooldown=0;
    /* $2B46-$2B4B first turns the victim opposite the attacker's facing.
     * The reaction then moves backwards from that new facing ($2419/$2458).
     * Omitting this turn sends back-hit victims towards their attacker. */
    if(damage!=5)v->body.facing=(unsigned char)!a->body.facing;
    v->body.prone=(unsigned char)(v->reaction==BL_REACTION_DOWN);
    /* $29C3-$2C23 assigns the complete reaction counter without moving
     * coordinates. Main $1C23 calls combat, then $1C29->$179E updates
     * the actors ($1C5B) and consumes the first recoil step in the same
     * iteration. Do not consume it twice. Pair geometry/order is provisional. */
    return damage;
}
int bl_combat_contact(BlFighter *a,BlFighter *v,int ninja){
    const BlFighter *actors[2];unsigned char latch;
    if(!ninja || !a->sai)return combat_contact(a,v,ninja,0);
    actors[0]=a;actors[1]=v;latch=sprite_latch(actors,2);
    return combat_contact(a,v,ninja,(latch&3)==3);
}
static void enemy_step(BlFighter *f,const BlFighter *player,int kind){
    BlGame *g=&f->body;
    int dx=bl_x(&player->body)-bl_x(g),dy=bl_y(&player->body)-bl_y(g);
    unsigned char input=0;
    if(f->entering){
        if(!f->entry_state && !f->timer)f->entering=0;
        else{
            BlSourcePose pose;
            bl_step_npc_entry(g,&f->entry_state,&f->timer,bl_x(&player->body),f->entry_mask);
            if(f->entry_state!=0 && f->entry_state!=16 && f->entry_state!=18){f->entering=0;return;}
            pose.state=f->entry_state;pose.counter=f->timer;pose.facing=g->facing;
            pose.contact=g->wall.contact;pose.previous=g->wall.pose;
            pose.width=pose.second_width=pose.aa=pose.locked=0;
            g->wall.pose=bl_source_pose(&pose);f->entry_mask=(unsigned char)(g->wall.pose+g->source_actor*70);
            if(!f->entry_state && !f->timer)f->entering=0;
            return;
        }
    }
    /* COMBAT-0001: state20 advances four Amiga pixels per step for both
     * enemies. Player walk acceleration must not carry into enemy AI. */
    if(f->stun){reaction_step(f,kind+1);return;}
    /* $2D7C only promotes idle/counter0 actors to AI state20. Recovery
     * must finish through $1C5B, rather than starting a fresh nearby stab. */
    if(g->wall.state==24){f->sai=0;bl_step_npc_ai(g,0);return;}
    /* $2191-$21A7: computer actors on the moving net keep moving in
     * their facing direction. State23 bypasses the ordinary AI branch. */
    if(g->state==BL_CLIMB && g->climb_state==23){
        bl_step_npc_ai(g,g->facing?BL_RIGHT:BL_LEFT);return;
    }
    if(f->timer && f->ai==BL_AI_WAIT){--f->timer;bl_step_npc_ai(g,0);return;}
    if(f->sai){
        g->attack=BL_SAI;g->attack_phase=f->timer;bl_step_npc_ai(g,0);
        if(g->attack==BL_SAI)f->timer=g->attack_phase;
        else {f->sai=0;f->ai=BL_AI_WAIT;f->timer=(unsigned char)(g->wall.state==24?0:6);}
        return;
    }
    if(g->attack){int kick=g->attack==BL_FLYING_KICK;
        bl_step_npc_ai(g,0);if(!g->attack){f->ai=BL_AI_WAIT;f->timer=(unsigned char)(kick?24:6);}return;}
    if(f->ai==BL_AI_RETREAT && f->timer){
        if(f->timer==1){g->facing=(unsigned char)!g->facing;
            f->timer=0;f->ai=BL_AI_CHASE;return;}
        --f->timer;input=g->facing?BL_RIGHT:BL_LEFT;
        bl_step_npc_ai(g,input);return;
    }
    f->ai=BL_AI_CHASE;
    if(player->active && magnitude(dy)<16 && g->state==BL_GROUND){
        int distance=magnitude(dx);
        int toward=g->facing?dx>=0:dx<=0;
        if(!toward && distance>=66){
            g->facing=(unsigned char)!g->facing;
            input=g->facing?BL_RIGHT:BL_LEFT;
        }else if(!toward || distance<10){
            int target=bl_x(&player->body)+(dx>0?-30:30);
            int duration=magnitude(target-bl_x(g))/2;
            if(duration<5)duration=5;
            f->ai=BL_AI_RETREAT;f->timer=(unsigned char)duration;return;
        }else if(kind==BL_NINJA && distance<22){
            f->sai=1;f->ai=BL_AI_ATTACK;f->timer=19;
            g->attack=BL_SAI;g->attack_phase=19;return;
        }else if(kind==BL_YAMO && distance<24){input=BL_FIRE;f->ai=BL_AI_ATTACK;
        }else if(kind==BL_YAMO && distance<38){
            g->attack=BL_FLYING_KICK;g->attack_phase=0;g->state=BL_AIR;
            g->jump_phase=255;g->jump_direction=g->facing?1:-1;
            f->ai=BL_AI_ATTACK;return;
        }else input=g->facing?BL_RIGHT:BL_LEFT;
    }else{
        /* $2362: above Bruce, keep the existing direction; below him,
         * face him and wait instead of continuously matching his X. */
        if(g->state==BL_GROUND && dy<=-16){
            g->facing=(unsigned char)(dx>=0);f->ai=BL_AI_WAIT;f->timer=6;
        }else input=g->facing?BL_RIGHT:BL_LEFT;
        if(g->state==BL_AIR)input=0;
    }
    bl_step_npc_ai(g,input);
}
void bl_combat_spawn_service(BlCombat *w){
    int i;unsigned char active[2];
    if(bl_c64_room()!=w->player.body.room)bl_c64_load(w->player.body.room);
    for(i=0;i<2;i++){
        BlFighter *f=&w->enemy[i];active[i]=f->active;
        bl_c64_spawn_sync(i+1,f->active,bl_x(&f->body),bl_y(&f->body),f->health,f->respawn);
    }
    bl_c64_spawn_services(bl_x(&w->player.body),bl_y(&w->player.body));
    for(i=0;i<2;i++){
        BlFighter *f=&w->enemy[i];BlC64Spawn born;
        f->respawn=bl_c64_spawn_counter(i+1);bl_c64_spawn_result(i+1,&born);
        if(!active[i] && born.active){
            unsigned char room=w->player.body.room;unsigned short delay=f->respawn;
            BlSourceWall history=f->body.wall;
            fighter_reset(f,born.health,(int)born.x*2-24,born.y);
            f->body.source_actor=(unsigned char)(i+1);f->body.room=room;f->body.facing=born.facing;
            /* $0B8E does not erase movement history/C2/CB. A later birth
             * in this room keeps it; $0A2A clears it on room loading. */
            f->body.wall=history;f->body.wall.state=born.state;f->body.wall.counter=born.counter;
            f->body.wall.contact=1;
            f->entering=1;f->entry_state=born.state;f->timer=born.counter;f->entry_mask=born.mask;
            f->body.wall.pose=born.pose;f->respawn=delay;++w->spawns;
        }
    }
    w->spawn_ready=1;
}
void bl_combat_step(BlCombat *w,unsigned char input){
    int i;unsigned char latch;const BlFighter *actors[3];
    if(!w->spawn_ready)bl_combat_spawn_service(w);
    w->spawn_ready=0;
    ++w->step;
    /* 256 candidate PAL fields, quantized to the three-field logic seam. */
    w->recharge=(unsigned short)(w->recharge+3);
    if(w->recharge>=256){w->recharge=(unsigned short)(w->recharge-256);
        w->player.allowance=2;for(i=0;i<BL_ENEMIES;i++)w->enemy[i].allowance=2;}
    /* Main $1C23 -> $29C3 resolves existing poses/states BEFORE $1C29 ->
     * $179E reads input and updates actors. Keep that seam here. This is
     * still the prototype pair resolver: $29C3's collect-all-then-apply
     * flags and actual VIC sprite contact remain a separate source port. */
    actors[0]=&w->player;actors[1]=&w->enemy[0];actors[2]=&w->enemy[1];
    latch=(unsigned char)(w->enemy[BL_NINJA].sai?sprite_latch(actors,3):0);
    for(i=0;i<BL_ENEMIES;i++){
        BlFighter *f=&w->enemy[i];
        if(combat_contact(&w->player,f,0,0)){++w->hits;if(f->health<0)++w->defeats;}
        if(!w->invincible && combat_contact(f,&w->player,i==BL_NINJA,(latch&5)==5)){
            ++w->hits;if(w->player.health<0)++w->player_deaths;
        }
    }
    if(combat_contact(&w->enemy[0],&w->enemy[1],0,0)){
        ++w->hits;if(w->enemy[1].health<0)++w->defeats;
    }
    if(combat_contact(&w->enemy[1],&w->enemy[0],1,(latch&6)==6)){
        ++w->hits;if(w->enemy[0].health<0)++w->defeats;
    }
    /* $17BC-$17DF: actor2 (Ninja), actor1 (Yamo), actor0 (Bruce).
     * Enemy decisions must not see Bruce's movement from later in this step. */
    for(i=BL_ENEMIES-1;i>=0;i--){
        BlFighter *f=&w->enemy[i];
        if(!f->active)continue;
        if(i==BL_YAMO && w->human_yamo && !f->entering){
            if(f->stun)reaction_step(f,1);
            else bl_step_npc(&f->body,w->yamo_input);
        }else enemy_step(f,&w->player,i);
    }
    if(w->game_over)return;
    if(!w->player.active && w->player.health<0){finish_player_life(w);}
    else if(!w->player.active){
        if(w->player.respawn && !--w->player.respawn){
            unsigned char room=w->player.body.room;
            const BlRoomFacts *r=bl_room(room);
            fighter_reset(&w->player,36,r->entry_x,r->entry_y);
            w->player.body.room=room;++w->player_respawns;
        }
    }else if(w->player.stun){
        reaction_step(&w->player,0);
        if((w->player.reaction==BL_REACTION_DEAD && !w->player.stun) ||
           (!w->player.active && w->player.health<0))finish_player_life(w);
    }
    else bl_step(&w->player.body,input);
}
