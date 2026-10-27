#ifndef BRUCE_COMBAT_H
#define BRUCE_COMBAT_H
#include "game.h"
enum { BL_YAMO, BL_NINJA, BL_ENEMIES=2 };
enum { BL_AI_WAIT, BL_AI_CHASE, BL_AI_RETREAT, BL_AI_ATTACK };
enum { BL_REACTION_NONE, BL_REACTION_HURT, BL_REACTION_DOWN, BL_REACTION_FALL, BL_REACTION_DEAD };
typedef struct {
    BlGame body;
    signed short health;
    unsigned short respawn;
    unsigned char active, stun, allowance, ai, timer, sai, reaction;
} BlFighter;
typedef struct {
    BlFighter player, enemy[BL_ENEMIES];
    unsigned short step, recharge;
    unsigned short hits, defeats, spawns, player_deaths, player_respawns;
    signed short lives; /* Source $28: spare falls, current attempt is extra. */
    unsigned char game_over,infinite_lives,invincible,human_yamo,yamo_input;
} BlCombat;
void bl_combat_reset(BlCombat *world);
void bl_combat_step(BlCombat *world,unsigned char input);
/* $304B/$407D: state25/counter16. Sound is queued by the caller only when
 * the traced source callsite requests it; combat knockdown is different. */
void bl_combat_hazard(BlCombat *world,unsigned char sound);
/* Prototype pair resolver; NOT the source's collect-all/apply-all kernel.
 * Assignment does not consume a movement step. Sprite contact, simultaneous
 * hits, recovery and terminal-fall behavior remain open; see TEST_AUDIT. */
int bl_combat_contact(BlFighter *attacker,BlFighter *victim,int ninja);
/* Source sprite occupancy of the current adapter poses; not background rays. */
int bl_combat_sprite_touch(const BlFighter *a,const BlFighter *b);
#endif
