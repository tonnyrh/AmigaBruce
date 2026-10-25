#include "combat.h"
#include "rooms.h"
#include "c64_rooms.h"
static int magnitude(int x){return x<0?-x:x;}
static void fighter_reset(BlFighter *f,int health,int x,int y){
    bl_reset(&f->body);f->body.x=(BlCoord)(x*16);f->body.y=(BlCoord)(y*16);
    f->body.previous_x=f->body.x;f->body.previous_y=f->body.y;
    f->health=(signed short)health;f->active=1;f->respawn=0;
    f->stun=0;f->allowance=2;f->ai=BL_AI_WAIT;f->timer=16;f->sai=0;
    f->reaction=BL_REACTION_NONE;
}
static void recoil(BlFighter *f,int pixels){
    f->body.x=(BlCoord)(f->body.x+(f->body.facing?-pixels:pixels)*16);
    if(f->body.x<4*16)f->body.x=4*16;
    if(f->body.x>314*16)f->body.x=314*16;
}
static void reaction_step(BlFighter *f,int actor){
    int pixels=4;
    /* $240E-$24B0: living NPCs recover before the final recoil step.
     * Ninja has an asymmetric extra displacement at counter ten. */
    if(f->stun>1 || actor==0 || f->health<0){
        bl_step(&f->body,0);
        if(f->reaction==BL_REACTION_DOWN && actor==2 && f->stun==10)
            pixels+=f->body.facing?16:8;
        /* Wall recovery owns Bruce's coordinates. The remaining legacy
         * reaction/life timer must still finish, including negative health. */
        if(f->reaction!=BL_REACTION_FALL && !(actor==0 && f->body.wall.state==24)){
            if(actor==0)bl_record_recoil(&f->body,pixels);else recoil(f,pixels);
        }
    }
    --f->stun;
    f->body.prone=(unsigned char)(f->reaction==BL_REACTION_DOWN);
    if(!f->stun){
        f->reaction=BL_REACTION_NONE;f->body.prone=0;
        f->ai=BL_AI_WAIT;f->timer=6;
        if(f->health<0){f->active=0;f->respawn=96;}
    }
}
void bl_combat_reset(BlCombat *w){
    fighter_reset(&w->player,36,28,196);
    fighter_reset(&w->enemy[BL_YAMO],20,294,98);
    fighter_reset(&w->enemy[BL_NINJA],7,294,98);
    w->enemy[BL_YAMO].active=0;w->enemy[BL_YAMO].respawn=232;
    w->enemy[BL_NINJA].active=0;w->enemy[BL_NINJA].respawn=96;
    w->step=0;w->recharge=0;w->hits=0;w->defeats=0;w->spawns=0;
    w->player_deaths=0;w->player_respawns=0;
}
int bl_combat_contact(BlFighter *a,BlFighter *v,int ninja){
    int damage=0,kind;
    if(!a->active||!v->active||a->health<0||v->health<0||a->stun||v->stun||v->body.prone)return 0;
    kind=bl_contact_kind(&a->body,bl_x(&v->body),bl_y(&v->body),v->body.prone);
    /* $2A7B-$2A80: sai only hits when the remaining counter is below
     * eight. Counters 19..8 are wind-up, not an active hit window. */
    if(ninja && a->sai){
        int dx=bl_x(&v->body)-bl_x(&a->body);
        int forward=a->body.facing?dx:-dx;
        /* $2A82/$2C54: reject distances below four C64 half-pixels,
         * as well as the rear side. Upper extent still uses blockout boxes. */
        if(a->timer>0 && a->timer<8 && forward>=8 && forward<23 &&
           magnitude(bl_y(&a->body)-bl_y(&v->body))<22)damage=2;
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
static void enemy_step(BlFighter *f,const BlFighter *player,int kind){
    BlGame *g=&f->body;
    int dx=bl_x(&player->body)-bl_x(g),dy=bl_y(&player->body)-bl_y(g);
    unsigned char input=0;
    /* Only the first two rooms are playable; their horizontal doors are
     * above Y180. Avoid a room-table scan during bottom-floor combat. */
    if((g->room>=2 || g->y<180*16) && (g->x>=302*16 || g->x<=4*16) &&
       bl_enemy_leave_room(f,kind))return;
    /* COMBAT-0001: state20 advances four Amiga pixels per step for both
     * enemies. Player walk acceleration must not carry into enemy AI. */
    g->walk_steps=0;
    if(f->stun){reaction_step(f,kind+1);return;}
    if(f->timer && f->ai==BL_AI_WAIT){--f->timer;bl_step_npc(g,0);return;}
    if(f->sai){
        if(f->timer==12)bl_c64_audio_request(0x85); /* $22CA-$22D2 */
        if(f->timer)--f->timer;else{f->sai=0;f->ai=BL_AI_WAIT;f->timer=6;}return;}
    if(g->attack){int kick=g->attack==BL_FLYING_KICK;
        bl_step_npc(g,0);if(!g->attack){f->ai=BL_AI_WAIT;f->timer=(unsigned char)(kick?24:6);}return;}
    if(f->ai==BL_AI_RETREAT && f->timer){
        if(f->timer==1){g->facing=(unsigned char)!g->facing;
            f->timer=0;f->ai=BL_AI_CHASE;return;}
        --f->timer;input=g->facing?BL_RIGHT:BL_LEFT;
        bl_step_npc(g,input);return;
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
            f->sai=1;f->ai=BL_AI_ATTACK;f->timer=19;return;
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
    bl_step_npc(g,input);
}
void bl_combat_step(BlCombat *w,unsigned char input){
    int i;
    ++w->step;
    /* 256 candidate PAL fields, quantized to the three-field logic seam. */
    w->recharge=(unsigned short)(w->recharge+3);
    if(w->recharge>=256){w->recharge=(unsigned short)(w->recharge-256);
        w->player.allowance=2;for(i=0;i<BL_ENEMIES;i++)w->enemy[i].allowance=2;}
    /* Main $1C23 -> $29C3 resolves existing poses/states BEFORE $1C29 ->
     * $179E reads input and updates actors. Keep that seam here. This is
     * still the prototype pair resolver: $29C3's collect-all-then-apply
     * flags and actual VIC sprite contact remain a separate source port. */
    for(i=0;i<BL_ENEMIES;i++){
        BlFighter *f=&w->enemy[i];
        if(bl_combat_contact(&w->player,f,0)){++w->hits;if(f->health<0)++w->defeats;}
        if(bl_combat_contact(f,&w->player,i==BL_NINJA)){
            ++w->hits;if(w->player.health<0)++w->player_deaths;
        }
    }
    if(bl_combat_contact(&w->enemy[0],&w->enemy[1],0)){
        ++w->hits;if(w->enemy[1].health<0)++w->defeats;
    }
    if(bl_combat_contact(&w->enemy[1],&w->enemy[0],1)){
        ++w->hits;if(w->enemy[0].health<0)++w->defeats;
    }
    /* $17BC-$17DF: actor2 (Ninja), actor1 (Yamo), actor0 (Bruce).
     * Enemy decisions must not see Bruce's movement from later in this step. */
    for(i=BL_ENEMIES-1;i>=0;i--){
        BlFighter *f=&w->enemy[i];
        if(!f->active){
            if(f->respawn && !--f->respawn){
                unsigned char room=f->body.room;
                const BlRoomFacts *r=bl_room(room);
                fighter_reset(f,i==BL_YAMO?20:7,r->enemy_x,r->enemy_y);
                f->body.room=room;
                f->body.facing=(unsigned char)(bl_x(&w->player.body)>=r->enemy_x);
                /* First movement: Ninja112 after entry96; Yamo259 after232.
                 * Spawn step itself consumes the first paused observation. */
                f->timer=i==BL_YAMO?26:15;++w->spawns;
                bl_c64_audio_request(0x82); /* entry helper $10B5 */
            }
            continue;
        }
        enemy_step(f,&w->player,i);
    }
    if(!w->player.active){
        if(w->player.respawn && !--w->player.respawn){
            unsigned char room=w->player.body.room;
            const BlRoomFacts *r=bl_room(room);
            fighter_reset(&w->player,36,r->entry_x,r->entry_y);
            w->player.body.room=room;++w->player_respawns;
        }
    }else if(w->player.stun){reaction_step(&w->player,0);}
    else bl_step(&w->player.body,input);
}
