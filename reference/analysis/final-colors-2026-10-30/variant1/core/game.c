#include "game.h"
#include "c64_rooms.h"
#include "source_climb.h"

#define Q 16
#define WALK (4*Q)
/* AI gait $2358/$236C/$23F7/$23FF calls movement helpers directly,
 * bypassing the player direction branch's $1FC4 locomotion sound. */
static unsigned char player_movement_sound=1;
static unsigned char npc_ai_motion;
/* Source-CPU checked target deltas. Grounded landing and complete actor
 * dispatch remain scoped adapters; see docs/C64_MOVEMENT.md. */
/* Launch (counter15), then $2008-$2047/$20D2-$216A counters15..1.
 * Counter0 is handled separately; it is not another zero-displacement step. */
static const signed char standing_jump[]={0,0,0,0,-4,-2,-2,-2,-2,2,2,2,2,2,2,0};
/* $2111's CPY6 sees Y=3/4 left by the horizontal helper, NOT counter6;
 * both down calls therefore run. Verified against the actual CPU path. */
static const signed char moving_jump[]={0,-2,-2,-2,-2,-2,-1,0,0,0,2,2,2,2,2,2};
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
    }else if(g->attack==BL_FLYING_KICK){
        if(g->attack_phase<2 || g->attack_phase>10)return 0;
        top=bl_y(g)-11;bottom=bl_y(g)-6;
    }else return 0;
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
    return (bl_c64_contact(bl_x(g),bl_y(g),bl_c64_object_pose(g),0)&4)?&contact:0;
}
static int supported(const BlGame *g){
    return (bl_c64_contact(bl_x(g),bl_y(g),bl_c64_object_pose(g),0)&5)!=0;
}

void bl_reset(BlGame *g) {
    bl_source_wall_reset(&g->wall);
    g->room=0;
    g->x=28*Q; g->y=196*Q;
    g->previous_x=g->x; g->previous_y=g->y;
    g->velocity_y=0; g->step=0;
    g->state=BL_GROUND; g->facing=1; g->last_input=0; g->jump_phase=255;
    g->walk_steps=0;g->jump_direction=0;g->jump_cooldown=0;
    g->climb_wait=0;g->climb_steps=0;g->climb_state=0;g->climb_direction=0;
    g->net_delay=g->net_hold=0;
    g->prone=0;g->prone_wait=0;
    g->attack=BL_ATTACK_NONE;g->attack_phase=0;g->attack_recovery=0;
    g->fall_push=g->source_actor=0;
    g->source_canonical=g->source_state=g->source_counter=g->source_wait=g->source_pose=g->source_mask=0;
}

void bl_step(BlGame *g, unsigned char input) {
    bl_step_phased(g,input,input);
}
void bl_step_npc(BlGame *g,unsigned char input){
    /* $17BE-$17DB calls $1C5B for EVERY active actor. Only the player
     * locomotion sound/input branch differs; black contact does not. */
    player_movement_sound=0;bl_step(g,input);player_movement_sound=1;
}
void bl_step_npc_ai(BlGame *g,unsigned char input){
    npc_ai_motion=1;bl_step_npc(g,input);npc_ai_motion=0;
}

static void step_motion(BlGame *g,unsigned char input,unsigned char attack_input);
static unsigned char actor_state(const BlGame *g){
    if(g->wall.state==24)return 24;
    if(g->attack==BL_SAI)return 22;
    if(g->attack==BL_FLYING_KICK)return (unsigned char)(g->facing?13:12);
    if(g->attack==BL_PUNCH)return 17;
    if(g->prone)return 26;
    if(g->state==BL_AIR)return (unsigned char)(g->jump_phase==255?14:
        !g->jump_direction?5:g->jump_direction<0?6:7);
    if(g->state==BL_CLIMB)return g->climb_state;
    return (unsigned char)(g->walk_steps?(g->facing?4:3):0);
}
void bl_moving_net_contact(BlGame *g,long touching){
    unsigned char pose=touching?bl_c64_object_pose(g):0;
    if(g->state==BL_CLIMB && g->climb_state==23){
        /* Source BF becomes zero while the pose latch remains unchanged.
         * BL_CLIMB/state0 also preserves that latch for the next B6 query. */
        g->climb_state=g->climb_wait=0; /* $2E10 */
    }
    if(touching){
        /* $310C clears AA but retains the displayed $4F48/$4F4E pose. */
        g->wall.pose=(unsigned char)(pose-g->source_actor*70);
        g->wall.state=g->wall.counter=0; /* BF/CE are replaced by $310C. */
        g->state=BL_CLIMB;g->climb_state=23;g->climb_wait=0;g->net_hold=0;
        g->attack=BL_ATTACK_NONE;g->prone=g->prone_wait=0;
        g->walk_steps=0;g->velocity_y=0;
    }
}
void bl_record_recoil(BlGame *g,int pixels){
    int old=bl_x(g),next=old+(g->facing?-pixels:pixels);
    if(next<0)next=0;
    if(next>302)next=302;
    g->x=(BlCoord)(next*Q);
    bl_source_wall_record(&g->wall,next-old,0);
}
void bl_step_phased(BlGame *g,unsigned char input,unsigned char attack_input){
    int px=bl_x(g),py=bl_y(g);
    unsigned char previous_pose;
    unsigned char waiting=(unsigned char)((g->state==BL_GROUND && g->prone_wait) ||
        ((g->state==BL_CLIMB || g->state==BL_GROUND) && g->climb_wait));
    if(bl_c64_room()!=g->room)bl_c64_load(g->room);
    previous_pose=bl_c64_object_pose(g);
    if(!waiting){
        BlSourceActor a;
        unsigned char flags,pose=previous_pose;
        long result;
        a.x=(unsigned char)((px+24)/2);a.y=(unsigned char)py;a.facing=g->facing;
        a.state=actor_state(g);a.counter=g->wall.state==24?g->wall.counter:
            g->attack==BL_SAI?g->attack_phase:
            a.state==23?16:
            g->attack==BL_FLYING_KICK?(unsigned char)(g->attack_phase<12?12-g->attack_phase:0):0;
        a.previous=g->wall.previous;a.animation=g->wall.animation;a.wait=a.pose_lock=0;
        flags=bl_c64_contact(px,py,pose,0);
        g->wall.contact=flags;
        result=bl_source_wall_step(&g->wall,&a,flags);
        g->wall.previous=a.previous;g->wall.animation=a.animation;g->wall.tracked=1;
        if(result){
            g->previous_x=g->x;g->previous_y=g->y;++g->step;
            g->x=(BlCoord)(((int)a.x*2-24)*Q);g->y=(BlCoord)(a.y*Q);g->facing=a.facing;
            g->wall.state=24;g->wall.counter=a.counter;
            g->wall.pose=(unsigned char)((a.pose_lock?pose:bl_c64_recovery_pose(pose))-g->source_actor*70);
            g->attack=BL_ATTACK_NONE;g->attack_phase=0;g->walk_steps=0;
            g->prone=0;
            g->prone_wait=g->climb_wait=g->jump_cooldown=0;
            g->velocity_y=0;g->jump_phase=255;g->last_input=input;
            if(result==2)bl_c64_reenter();
            return;
        }
        if(g->wall.state==24){
            g->state=(unsigned char)((flags&5)?BL_GROUND:BL_AIR);
            g->prone=0;g->wall.state=g->wall.counter=0;
            if(!(flags&5)){
                /* State24/counter0 -> $1DCA/$1DC4 uses the existing B6.
                 * Re-querying a new falling mask here can invent support. */
                g->previous_x=g->x;g->previous_y=g->y;++g->step;
                if(g->y<199*Q)g->y+=Q;
                g->jump_phase=255;g->velocity_y=Q;g->fall_push=2;
                g->walk_steps=0;g->last_input=input;
                bl_source_wall_record(&g->wall,0,bl_y(g)-py);return;
            }
        }
        if(a.state==23){
            /* $310C selected this state during the object pass. It bypasses
             * ordinary jump/net input while keeping black/history recovery. */
            long sound=bl_source_moving_net_step(&a,&g->net_delay,&g->net_hold,
                input,flags,bl_c64_read(0x60),bl_c64_read(0x65));
            g->previous_x=g->x;g->previous_y=g->y;++g->step;
            g->x=(BlCoord)(((int)a.x*2-24)*Q);g->y=(BlCoord)(a.y*Q);g->facing=a.facing;
            g->state=BL_CLIMB;g->climb_state=a.state;g->climb_wait=a.wait;
            if(!a.pose_lock && !(a.state==23 && g->net_hold))
                g->wall.pose=bl_source_climb_pose(&a,pose-g->source_actor*70);
            g->velocity_y=0;g->jump_phase=255;g->last_input=input;
            if(sound)bl_c64_audio_request(0x80);
            bl_source_wall_record(&g->wall,bl_x(g)-px,bl_y(g)-py);
            return;
        }
        if(player_movement_sound && !g->attack && (g->state==BL_GROUND || g->state==BL_CLIMB) && (flags&4)){
            /* $1DCA-$1ED5 net direction dispatch, after the exact ready
             * history/CB prefix above. No separate attach pause. */
            long sound=bl_source_climb_step(&a,input,(attack_input&BL_FIRE)!=0);
            g->previous_x=g->x;g->previous_y=g->y;++g->step;
            g->x=(BlCoord)(((int)a.x*2-24)*Q);g->y=(BlCoord)(a.y*Q);g->facing=a.facing;
            g->state=BL_CLIMB;g->climb_state=a.state;g->climb_wait=a.wait;
            if(a.state==1 || a.state==2){
                g->climb_direction=(signed char)(a.state==1?-1:1);
                if(g->climb_steps<7)++g->climb_steps;
            }
            g->wall.pose=bl_source_climb_pose(&a,pose);
            g->prone=g->prone_wait=0;g->walk_steps=0;
            g->velocity_y=0;g->jump_phase=255;g->last_input=input;
            if(a.state==12 || a.state==13){
                g->state=BL_AIR;g->attack=BL_FLYING_KICK;g->attack_phase=0;
                g->jump_direction=(signed char)(g->facing?1:-1);
            }
            if(sound)bl_c64_audio_request(0x80);
            bl_source_wall_record(&g->wall,bl_x(g)-px,bl_y(g)-py);
            return;
        }
        if(player_movement_sound && g->state==BL_CLIMB && !(flags&5)){
            /* $1DCA->$1DC4: loss of whole-mask net/support precedes input.
             * First free-fall step is one Y; no sideways steering here. */
            g->previous_x=g->x;g->previous_y=g->y;++g->step;
            if(g->y<199*Q)g->y+=Q;
            g->state=BL_AIR;g->jump_phase=255;g->velocity_y=Q;
            g->fall_push=2;
            g->climb_state=g->climb_wait=0;g->walk_steps=0;g->last_input=input;
            bl_source_wall_record(&g->wall,0,bl_y(g)-py);return;
        }
        if(player_movement_sound && g->state==BL_CLIMB && !(flags&4)){
            g->state=BL_GROUND;g->climb_state=0;
        }
    }
    step_motion(g,input,attack_input);
    if(g->state==BL_GROUND && !g->walk_steps && !g->attack && !g->prone && (g->wall.contact&4)){
        /* $2974-$2993: a jump/fall ending idle on net must select the
         * net pose using this step's B6, not a fresh idle-mask query. */
        g->state=BL_CLIMB;g->climb_state=0;
        g->wall.pose=(unsigned char)(previous_pose==10 || previous_pose==12?previous_pose:10);
    }
    if(g->state==BL_GROUND && g->walk_steps && !g->attack && !g->prone){
        /* $28C7-$28E5: walking contact must use the same alternating
         * source mask as the displayed pose, including for NPCs. */
        g->wall.pose=(unsigned char)(g->facing?(g->wall.pose==18?20:18):(g->wall.pose==14?16:14));
    }
    if(!waiting)
        bl_source_wall_record(&g->wall,bl_x(g)-px,bl_y(g)-py);
}
static void step_motion(BlGame *g,unsigned char input,unsigned char attack_input) {
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
    if(g->attack==BL_SAI){
        /* $22BD-$22F0 runs AFTER the common $1C68 black/history prefix.
         * CE is a remaining counter for this attack. The source records
         * one forward helper unit WITHOUT changing X ($22E3/$22E8). */
        BlSourceActor a;a.state=22;a.counter=g->attack_phase;a.facing=g->facing;
        if(bl_source_sai_step(&g->wall,&a))bl_c64_audio_request(0x85);
        g->attack_phase=a.counter;
        if(!a.state){g->attack=BL_ATTACK_NONE;g->attack_phase=0;}
        g->walk_steps=0;g->last_input=input;return;
    }
    /* MACHINE-0005: punch target state lasts four logic steps, repeats
     * every eight when held. Flying kick has its own low trajectory. */
    if(g->attack==BL_PUNCH){
        if(++g->attack_phase<4){g->last_input=input;return;}
        g->attack=BL_ATTACK_NONE;g->attack_recovery=5;
    }
    if(g->attack==BL_FLYING_KICK){
        unsigned char flags=bl_c64_contact(bl_x(g),bl_y(g),bl_c64_object_pose(g),0);
        unsigned char counter=(unsigned char)(g->attack_phase<12?12-g->attack_phase:0);
        /* $204C/$2091 cancels on net/black; $207C/$20C1 cancels a
         * descending kick on whole-mask solid contact. Black recovery has
         * already run above for Bruce, before action dispatch. */
        if((flags&12) || (counter && counter<3 && (flags&1))){
            g->attack=BL_ATTACK_NONE;g->attack_phase=0;
            g->state=(unsigned char)((flags&4)?BL_CLIMB:BL_GROUND);
            if(flags&4){g->wall.pose=10;g->climb_state=0;}
            g->velocity_y=0;g->jump_phase=255;g->walk_steps=0;g->last_input=input;return;
        }
        if(counter){
            if(counter==12)bl_c64_audio_request(0x84);
            g->x=(BlCoord)(g->x+(g->facing?2*Q:-2*Q));
            if(g->x<0)g->x=0;
            if(g->x>302*Q)g->x=302*Q;
            if(counter>=10 && g->y>=46*Q)g->y-=Q;
            else if(counter<3 && g->y<199*Q)g->y+=Q;
            ++g->attack_phase;
            g->last_input=input;return;
        }
        g->attack=BL_ATTACK_NONE;g->state=(unsigned char)((flags&5)?BL_GROUND:BL_AIR);
        g->velocity_y=0;g->jump_phase=255;g->walk_steps=0;
        if(g->state==BL_AIR){if(g->y<199*Q)g->y+=Q;g->last_input=input;return;}
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
    /* The source counter0 entry checks current support before reading a
     * new grounded direction. An unsupported completed jump falls one Y. */
    if(g->state==BL_AIR && g->jump_phase==254){
        if(!supported(g)){
            g->jump_phase=255;g->velocity_y=Q;
            g->fall_push=2;
            if(g->y<199*Q)g->y+=Q;
            g->last_input=input;return;
        }
        g->state=BL_GROUND;g->jump_phase=255;g->velocity_y=0;
    }
    if(g->state==BL_AIR && g->jump_phase==255){
        unsigned char pose=bl_c64_object_pose(g);
        unsigned char flags=bl_c64_contact(bl_x(g),bl_y(g),pose,0);
        unsigned char body=bl_c64_contact(bl_x(g),bl_y(g),pose,1);
        if(g->wall.previous!=14 && !(flags&5)){
            g->fall_push=2;g->velocity_y=Q;
            if(g->y<199*Q)g->y+=Q;
            g->last_input=input;return;
        }
        /* $1D84-$1DBF. The source checks the CURRENT pose once, never
         * searches intermediate Y positions for a landing. Bruce's body
         * obstruction uses $A7 and the shifted $B0 allowance; NPC landing
         * instead performs one forward helper ($1D8D-$1D96). */
        if(player_movement_sound && (body&1)){
            g->fall_push>>=1;
            if(g->fall_push){
                g->x+=(BlCoord)(g->facing?2*Q:-2*Q);
                if(g->x<0)g->x=0;
                if(g->x>302*Q)g->x=302*Q;
            }
        }else if(flags&5){
            if(!player_movement_sound){
                g->x+=(BlCoord)(g->facing?2*Q:-2*Q);
                if(g->x<0)g->x=0;
                if(g->x>302*Q)g->x=302*Q;
                g->walk_steps=1;
            }else g->walk_steps=0;
            g->state=BL_GROUND;g->velocity_y=0;g->last_input=input;return;
        }
        g->velocity_y=2*Q;if(g->y<198*Q)g->y+=2*Q;else g->y=199*Q;
        g->last_input=input;return;
    }
    if(g->state==BL_GROUND && !supported(g)){
        /* $1DCA->$1DC4->$1DBC: loss of support precedes direction input.
         * A step which walks off remains grounded until this next entry. */
        g->state=BL_AIR;g->jump_phase=255;g->fall_push=2;g->velocity_y=Q;
        if(g->y<199*Q)g->y+=Q;
        g->last_input=input;return;
    }
    net=climbable(g);
    /* $2010/$20D6/$2124 -> $2504: launched jump states5/6/7 end
     * on net class4 before reading a new direction. This is independent
     * of held up/side input. BL_CLIMB represents that attached idle here;
     * source pose selection and the complete actor state machine remain open. */
    if(net && g->state==BL_AIR && g->jump_phase!=255){
        g->prone=0;g->prone_wait=0;g->climb_wait=0;g->climb_steps=0;
        g->climb_direction=0;g->state=BL_CLIMB;g->velocity_y=0;
        g->wall.pose=10;g->climb_state=0;
        g->jump_phase=255;g->last_input=input;return;
    }
    if(g->state==BL_AIR && g->jump_phase>0 && g->jump_phase<16){
        unsigned char counter=(unsigned char)(16-g->jump_phase);
        unsigned char flags=bl_c64_contact(bl_x(g),bl_y(g),bl_c64_object_pose(g),0);
        /* $2022/$2105/$2150: solid contact cancels the descending action
         * BEFORE either movement helper. No swept platform landing occurs
         * inside a launched jump. The next counter0 entry decides support.
         * Standing jumps inspect solid only at counters2..7; side jumps
         * inspect it at counters1..6. */
        if((flags&1) && (g->jump_direction?counter<7:counter>=2 && counter<8)){
            g->previous_x=g->x;g->previous_y=g->y;
            g->state=BL_GROUND;g->jump_phase=255;g->velocity_y=0;
            g->walk_steps=0;g->last_input=input;return;
        }
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
            g->wall.pose=10;g->climb_state=0;
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
    /* $2352/$236C calls the horizontal helper twice, also on class4.
     * Human NPC input retains the ordinary single-helper net movement. */
    g->x = (BlCoord)(g->x+horizontal*(g->state==BL_CLIMB ? (npc_ai_motion?4*Q:2*Q) :
        (player_movement_sound && g->state==BL_GROUND&&g->walk_steps>=7 ? 6*Q : WALK)));
    if(g->state==BL_GROUND&&horizontal){
        if(changed_direction && g->walk_steps)g->walk_steps=1;
        else if(g->walk_steps<7)++g->walk_steps;
    }
    else if(g->state==BL_GROUND)g->walk_steps=0;
    /* $1E86/$1EC4 raw X limits13..163, in source display coordinates. */
    if(g->x<0) g->x=0;
    if(g->x>302*Q) g->x=302*Q;
    /* Bruce's source black-contact/history pass runs at the next actor
     * entry, including kick/early-return paths; no separate guessed box. */
    if(g->state==BL_CLIMB) {
        net=climbable(g);
        if(!net){g->state=BL_AIR;g->velocity_y=Q;left_net=1;}
        else {
            int vertical=((input&BL_DOWN)!=0)-((input&BL_UP)!=0);
            if(vertical){
                if(player_movement_sound)bl_c64_audio_request(0x80); /* $1DDC/$1E29 */
                g->y=(BlCoord)(g->y+vertical*(g->climb_steps>=7?4*Q:3*Q));
                if(g->y<45*Q)g->y=45*Q;
                if(g->y>199*Q)g->y=199*Q;
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
    if(g->state==BL_AIR) {
        if(g->jump_phase!=255){
            unsigned char phase=g->jump_phase;
            g->velocity_y=(g->jump_direction ? moving_jump[phase] : standing_jump[phase])*Q;
            if(++g->jump_phase>=(g->jump_direction ? sizeof(moving_jump) : sizeof(standing_jump))){g->jump_phase=254;}
        }else if(!left_net){
            g->velocity_y=(BlCoord)((player_movement_sound && g->wall.previous!=14)?Q:2*Q);
        }
        if(g->velocity_y>8*Q)g->velocity_y=8*Q;
        g->y += g->velocity_y;
        if(g->y<45*Q)g->y=45*Q;
        if(g->y>199*Q)g->y=199*Q;
    }
    g->last_input=input;
}

void bl_step_npc_entry(BlGame *g,unsigned char *state,unsigned char *counter,long player_x,long mask){
    BlSourceActor a;unsigned char flags;long result;int px=bl_x(g),py=bl_y(g);
    a.x=(unsigned char)((px+24)/2);a.y=(unsigned char)py;a.facing=g->facing;
    a.state=*state;a.counter=*counter;a.previous=g->wall.previous;a.animation=g->wall.animation;
    a.wait=a.pose_lock=0;flags=bl_c64_contact(px,py,mask,0);g->wall.contact=flags;
    result=bl_source_wall_step(&g->wall,&a,flags);
    g->wall.previous=a.previous;g->wall.animation=a.animation;g->wall.tracked=1;
    g->previous_x=g->x;g->previous_y=g->y;++g->step;g->walk_steps=0;
    if(result){
        g->x=(BlCoord)(((int)a.x*2-24)*Q);g->y=(BlCoord)(a.y*Q);g->facing=a.facing;
        g->wall.state=24;g->wall.counter=a.counter;
        g->wall.pose=(unsigned char)(bl_c64_recovery_pose(g->wall.pose+g->source_actor*70)%70);
        *state=24;*counter=a.counter;if(result==2)bl_c64_reenter();return;
    }
    /* $2239-$2269: Yamo turns only on CE1, then enters BF18/CE16.
     * BF0/16/18 countdowns use $24F4; their source wait bytes are zero. */
    if(a.state==16 && a.counter==1){
        a.facing=(unsigned char)(px<player_x);a.state=18;a.counter=16;
        bl_c64_audio_request(0x81);
    }else if(a.counter)--a.counter;
    else{
        /* BF18/CE0 cannot be promoted by $2D7C yet. One idle dispatch
         * clears it, or starts unsupported fall with one vertical pixel. */
        a.state=0;g->state=(unsigned char)((flags&4)?BL_CLIMB:BL_GROUND);g->climb_state=0;
        if(!(flags&5)){
            a.state=14;if(a.y<199)++a.y;
            g->state=BL_AIR;g->jump_phase=255;g->fall_push=2;g->velocity_y=Q;
            bl_source_wall_record(&g->wall,0,(int)a.y-py);
        }
    }
    g->x=(BlCoord)(((int)a.x*2-24)*Q);g->y=(BlCoord)(a.y*Q);g->facing=a.facing;
    g->wall.state=a.state;g->wall.counter=a.counter;*state=a.state;*counter=a.counter;
}
