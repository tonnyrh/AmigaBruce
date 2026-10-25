#include "game.h"
#include "c64_rooms.h"

#define Q 16
#define WALK (4*Q)
/* AI gait $2358/$236C/$23F7/$23FF calls movement helpers directly,
 * bypassing the player direction branch's $1FC4 locomotion sound. */
static unsigned char player_movement_sound=1;
/* MACHINE-0001: measured candidate target-Y deltas at the game-step seam.
 * Retail identity, collision masks and end-to-end input parity remain open. */
static const signed char standing_jump[]={0,0,0,0,-4,-2,-2,-2,-2,2,2,2,2,2,2,0,0};
static const signed char moving_jump[]={0,-2,-2,-2,-2,-2,-1,0,0,0,2,2,2,2,2,0};
/* Legacy geometry API retained for old laboratory fixtures only. Runtime
 * support, landing and climbing now query source glyphs and source masks. */
const BlPlatform bl_platforms[]={{0,0,0}};
const unsigned short bl_platform_count=0;
const BlClimbable bl_climbables[]={{0,0,0,0,0}};
const unsigned short bl_climbable_count=0;
static const BlGeometry no_rectangles={bl_platforms,bl_climbables,0,0};
const BlGeometry *bl_geometry(const BlGame *g){(void)g;return &no_rectangles;}

int bl_x(const BlGame *g) { return g->x / Q; }
int bl_y(const BlGame *g) { return g->y / Q; }

/* Deliberately provisional test geometry, separate from measured movement.
 * Do not use these constants as C64 enemy/hitbox evidence. */
int bl_attack_overlaps(const BlGame *g,int x,int feet,int prone) {
    int left,right,top,bottom,body_top=feet-(prone?6:22);
    if(g->prone || g->attack==BL_ATTACK_NONE)return 0;
    if(g->attack==BL_PUNCH){
        /* The extended fist is drawn for all four punch steps. C64 $2A63
         * dispatches state17 directly to $2AA5 with no counter-phase gate;
         * exact sprite-pixel collision remains a separate parity task. */
        if(g->attack_phase>3)return 0;
        top=bl_y(g)-16;bottom=bl_y(g)-11;
    }else{
        if(g->attack_phase<2 || g->attack_phase>10)return 0;
        top=bl_y(g)-11;bottom=bl_y(g)-6;
    }
    left=bl_x(g)+(g->facing?4:-14);right=left+10;
    return left<x+7 && right>x-7 && top<feet && bottom>body_top;
}

void bl_target_reset(BlTarget *t) {
    t->x=112;t->y=196;t->health=3;t->invulnerable=0;t->respawn=0;t->hits=0;t->stomps=0;
}

int bl_contact_kind(const BlGame *g,int x,int feet,int prone) {
    if(bl_attack_overlaps(g,x,feet,prone))
        return g->attack==BL_PUNCH?BL_CONTACT_PUNCH:BL_CONTACT_KICK;
    /* C64 $2AFA: contact from an actor in free-fall state $0E, victim
     * feet at least ten pixels lower. Test boxes remain provisional;
     * the original additionally gates with VIC sprite-pixel collision. */
    if(!prone && !g->attack && g->state==BL_AIR && g->jump_phase==255 &&
       g->velocity_y>0 && bl_y(g)<=feet-10 &&
       g->y>=(feet-22)*Q && bl_x(g)>x-12 && bl_x(g)<x+12)
        return BL_CONTACT_FALL;
    return BL_CONTACT_NONE;
}

void bl_target_step(BlTarget *t,const BlGame *g) {
    int contact;
    if(t->respawn){
        if(!--t->respawn){t->health=3;t->x=112;t->invulnerable=0;}
        return;
    }
    if(t->invulnerable){--t->invulnerable;return;}
    contact=bl_contact_kind(g,t->x,t->y,0);
    if(contact){
        unsigned char damage=contact==BL_CONTACT_PUNCH?1:2;
        t->health=t->health>damage?t->health-damage:0;
        ++t->hits;t->invulnerable=8;
        if(contact==BL_CONTACT_FALL)++t->stomps;
        t->x=(BlCoord)(t->x+(g->facing?8:-8));
        if(t->x<16)t->x=16;
        if(t->x>304)t->x=304;
        if(!t->health)t->respawn=60;
    }
}

static const BlClimbable *climbable(const BlGame *g){
    static const BlClimbable contact={0,0,0,0,0};
    return (bl_c64_contact(bl_x(g),bl_y(g),2,0)&4)?&contact:0;
}
static int supported(const BlGame *g){
    return (bl_c64_contact(bl_x(g),bl_y(g),2,0)&5)!=0;
}
static int land_on_source(BlGame *g,BlCoord previous){
    int yy,first=previous/Q,last=g->y/Q;
    if(last<first)return 0;
    for(yy=first;yy<=last;yy++){
        /* $1D99-$1DCC: body class1 keeps the fall moving; whole actor
         * class1/4 can finish it. Standing mask2 is a documented adapter
         * until original actor pose selection is ported in full. */
        if((bl_c64_contact(bl_x(g),yy,2,0)&5) &&
           !(bl_c64_contact(bl_x(g),yy,2,1)&1)){
            g->y=(BlCoord)(yy*Q);return 1;
        }
    }
    return 0;
}

void bl_reset(BlGame *g) {
    g->room=0;
    g->x=28*Q; g->y=196*Q;
    g->previous_x=g->x; g->previous_y=g->y;
    g->velocity_y=0; g->step=0;
    g->state=BL_GROUND; g->facing=1; g->last_input=0; g->jump_phase=255;
    g->walk_steps=0;g->jump_direction=0;g->jump_cooldown=0;
    g->climb_wait=0;g->climb_steps=0;g->climb_direction=0;
    g->prone=0;g->prone_wait=0;
    g->attack=BL_ATTACK_NONE;g->attack_phase=0;g->attack_recovery=0;
}

void bl_step(BlGame *g, unsigned char input) {
    bl_step_phased(g,input,input);
}
void bl_step_npc(BlGame *g,unsigned char input){
    player_movement_sound=0;bl_step(g,input);player_movement_sound=1;
}

void bl_step_phased(BlGame *g, unsigned char input,unsigned char attack_input) {
    BlCoord old_y;
    const BlClimbable *net;
    int horizontal=((input&BL_RIGHT)!=0)-((input&BL_LEFT)!=0);
    if(bl_c64_room()!=g->room)bl_c64_load(g->room);
    int changed_direction=horizontal && g->facing!=(horizontal>0);
    int left_net=0;
    int ground_supported;
    /* FALL-0001: free-fall state14 has no horizontal input movement.
     * A launched jump keeps its own direction below; kicks move explicitly. */
    if(g->state==BL_AIR && g->jump_phase==255)horizontal=0;
    g->previous_x=g->x; g->previous_y=g->y; ++g->step;
    /* MACHINE-0005: punch target state lasts four logic steps, repeats
     * every eight when held. Flying kick has its own low trajectory. */
    if(g->attack==BL_PUNCH){
        if(++g->attack_phase<4){g->last_input=input;return;}
        g->attack=BL_ATTACK_NONE;g->attack_recovery=5;
    }
    if(g->attack==BL_FLYING_KICK){
        static const signed char kick_y[]={-1,-1,-1,0,0,0,0,0,0,0,1,1,1};
        unsigned char phase=g->attack_phase++;
        if(!phase)bl_c64_audio_request(0x84); /* $2052/$2097, counter12 */
        if(phase<12){
            g->x=(BlCoord)(g->x+(g->facing?2*Q:-2*Q));
            if(g->x<2*Q)g->x=2*Q;
            if(g->x>302*Q)g->x=302*Q;
        }
        if(phase<13){
            old_y=g->y;g->y=(BlCoord)(g->y+kick_y[phase]*Q);
            if(kick_y[phase]>0)land_on_source(g,old_y);
            g->last_input=input;return;
        }
        g->attack=BL_ATTACK_NONE;g->state=supported(g)?BL_GROUND:BL_AIR;
        g->velocity_y=0;g->jump_phase=255;g->walk_steps=0;
        g->last_input=input;return;
    }
    if(g->attack_recovery)--g->attack_recovery;
    if(g->jump_cooldown)--g->jump_cooldown;
    /* MACHINE-0004: down selects lying still, with one waiting logic step.
     * This is ground posture; down on a grabbed net remains a climb action. */
    if(g->state==BL_GROUND && g->prone_wait){
        --g->prone_wait;g->last_input=input;return;
    }
    /* Candidate climb actions occur once per four game steps. */
    if((g->state==BL_CLIMB || g->state==BL_GROUND) && g->climb_wait){
        --g->climb_wait;g->last_input=input;return;
    }
    net=climbable(g);
    /* $2010/$20D6/$2124 -> $2504: launched jump states5/6/7 end
     * on net class4 before reading a new direction. This is independent
     * of held up/side input. BL_CLIMB represents that attached idle here;
     * source pose selection and the complete actor state machine remain open. */
    if(net && g->state==BL_AIR && g->jump_phase!=255){
        g->prone=0;g->prone_wait=0;g->climb_wait=0;g->climb_steps=0;
        g->climb_direction=0;g->state=BL_CLIMB;g->velocity_y=0;
        g->jump_phase=255;g->last_input=input;return;
    }
    /* $1EDF/$1F11/$1F3C/$1F52: all four diagonal codes stop on
     * class4, rather than selecting vertical priority. Preserve an action
     * wait already handled above; do not add a fresh climb wait here. */
    if(net && horizontal && (input&(BL_UP|BL_DOWN))){
        g->last_input=input;return;
    }
    if(net && (input&(BL_UP|BL_DOWN)) && (!horizontal || g->state==BL_CLIMB)) {
        if(g->state!=BL_CLIMB){
            g->prone=0;g->prone_wait=0;
            g->climb_wait=0;g->climb_steps=0;g->climb_direction=0;
            g->state=BL_CLIMB;g->velocity_y=0;g->jump_phase=255;
            g->last_input=input;return;
        }
        g->state=BL_CLIMB; g->velocity_y=0;g->jump_phase=255;
    }
    /* Position is unchanged across posture, attack and jump selection.
     * Reuse this floor query instead of scanning it for each input branch. */
    ground_supported=g->state==BL_GROUND && supported(g);
    if(player_movement_sound && ground_supported && horizontal && !(input&(BL_UP|BL_DOWN)))
        bl_c64_audio_request(0x80); /* $1E63/$1EA4 -> $1FC4 */
    if(ground_supported && (input&BL_DOWN) && !(input&BL_UP)){
        g->prone=1;g->prone_wait=1;g->walk_steps=0;
        g->last_input=input;return;
    }
    g->prone=0;
    if(ground_supported && (attack_input&BL_FIRE) &&
       !(input&BL_DOWN) && !g->attack_recovery){
        if(!horizontal && !(input&BL_UP)){
            g->attack=BL_PUNCH;g->attack_phase=0;g->walk_steps=0;
            g->last_input=input;return;
        }
        /* $1EB1/$1E70: existing walking state, animation timer below four.
         * Four same-direction steps have elapsed at the first eligible read. */
        if(horizontal && g->walk_steps>=4 && !changed_direction && !(input&BL_UP)){
            g->attack=BL_FLYING_KICK;g->attack_phase=0;g->state=BL_AIR;
            g->facing=horizontal>0;g->jump_direction=(signed char)horizontal;
            g->jump_phase=255;g->last_input=input;return;
        }
    }
    if(g->state==BL_AIR && g->jump_phase!=255)horizontal=g->jump_direction;
    if(horizontal) g->facing=horizontal>0;
    if(ground_supported && (input&BL_UP) && !g->jump_cooldown) {
        if(player_movement_sound)bl_c64_audio_request(0x80); /* $1DDC/$1F46/$1F5C */
        g->state=BL_AIR;g->velocity_y=0;g->jump_phase=0;
        g->jump_direction=(signed char)horizontal;
    }
    if(g->state==BL_AIR && g->jump_phase==0)horizontal=0;
    g->x = (BlCoord)(g->x+horizontal*(g->state==BL_CLIMB ? 2*Q :
        (g->state==BL_GROUND&&g->walk_steps>=7 ? 6*Q : WALK)));
    if(g->state==BL_GROUND&&horizontal){
        if(changed_direction && g->walk_steps)g->walk_steps=1;
        else if(g->walk_steps<7)++g->walk_steps;
    }
    else if(g->state==BL_GROUND)g->walk_steps=0;
    /* $1E86/$1EC4 raw X limits13..163, in source display coordinates. */
    if(g->x<2*Q) g->x=2*Q;
    if(g->x>302*Q) g->x=302*Q;
    /* $1CC7-$1D0A backs out recorded movement on black-class contact.
     * This adapter backs out its one horizontal move. The original history
     * replay/step-out attempts remain part of the actor-motor port. */
    if(g->x!=g->previous_x && (bl_c64_contact(bl_x(g),bl_y(g),2,0)&8) &&
       !(bl_c64_contact(g->previous_x/Q,bl_y(g),2,0)&8))g->x=g->previous_x;
    if(g->state==BL_CLIMB) {
        net=climbable(g);
        if(!net){g->state=BL_AIR;g->velocity_y=Q;left_net=1;}
        else {
            int vertical=((input&BL_DOWN)!=0)-((input&BL_UP)!=0);
            if(vertical){
                if(player_movement_sound)bl_c64_audio_request(0x80); /* $1DDC/$1E29 */
                g->y=(BlCoord)(g->y+vertical*(g->climb_steps>=7?4*Q:3*Q));
                if(vertical!=g->climb_direction && g->climb_steps)g->climb_steps=1;
                else if(g->climb_steps<7)++g->climb_steps;
                g->climb_direction=(signed char)vertical;
            }
            if(player_movement_sound && horizontal)bl_c64_audio_request(0x80); /* $1E63/$1EA4 */
            if(vertical||horizontal)g->climb_wait=3;
            /* MACHINE-0003: net ends below the standing surface. Preserve
             * its action wait before accepting the next held-up jump. */
            if(!climbable(g) && supported(g))g->state=BL_GROUND;
            g->last_input=input;
            return;
        }
    }
    if(g->state==BL_GROUND && !supported(g)) {
        g->state=BL_AIR;
    }
    old_y=g->y;
    if(g->state==BL_AIR) {
        if(g->jump_phase!=255){
            unsigned char phase=g->jump_phase;
            g->velocity_y=(g->jump_direction ? moving_jump[phase] : standing_jump[phase])*Q;
            if(++g->jump_phase>=(g->jump_direction ? sizeof(moving_jump) : sizeof(standing_jump))){g->jump_phase=255;}
        }else if(!left_net && g->velocity_y<2*Q)g->velocity_y=2*Q;
        if(g->velocity_y>8*Q)g->velocity_y=8*Q;
        g->y += g->velocity_y;
        if(g->velocity_y>=0) {
            if((g->jump_phase==255 || g->velocity_y>0) && land_on_source(g,old_y)){
                if(g->jump_phase!=255 && !g->jump_direction)g->jump_cooldown=2;
                g->velocity_y=0;g->state=BL_GROUND;g->jump_phase=255;
                g->walk_steps=0;
            }
        }
    }
    g->last_input=input;
}
