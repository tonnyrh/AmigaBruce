#ifndef BRUCE_GAME_H
#define BRUCE_GAME_H
#include "source_wall.h"

/* All coordinates are screen pixels in the original 320x200 playfield.
 * Prototype rules remain explicitly provisional until candidate traces pass. */
typedef signed short BlCoord;
enum { BL_LEFT=1, BL_RIGHT=2, BL_UP=4, BL_DOWN=8, BL_FIRE=16 };
enum { BL_GROUND, BL_AIR, BL_CLIMB };
enum { BL_ATTACK_NONE, BL_PUNCH, BL_FLYING_KICK, BL_SAI };
enum { BL_CONTACT_NONE, BL_CONTACT_PUNCH, BL_CONTACT_KICK, BL_CONTACT_FALL };
typedef struct { BlCoord x0, x1, y; } BlPlatform;
typedef struct { BlCoord x0, x1, y0, y1, exit_y; } BlClimbable;
typedef struct {
    const BlPlatform *platforms;
    const BlClimbable *climbables;
    unsigned short platform_count, climbable_count;
} BlGeometry;
typedef struct {
    BlCoord x, y;              /* Q4 source sprite-left / bottom+1, not centre */
    BlCoord previous_x, previous_y;
    BlCoord velocity_y;
    unsigned short step;
    unsigned char state, facing, last_input, jump_phase, walk_steps, jump_cooldown;
    /* jump_phase254 = completed jump/counter0;255 = free-fall state14. */
    unsigned char climb_wait, climb_steps,climb_state; /* source BF0..4 on net */
    unsigned char net_delay,net_hold; /* $AD/$AA in moving-net state23 */
    unsigned char prone, prone_wait;
    unsigned char attack, attack_phase, attack_recovery;
    signed char climb_direction;
    signed char jump_direction;
    unsigned char room;
    BlSourceWall wall;
    unsigned char fall_push; /* $B0: obstruction-release allowance in state14 */
    unsigned char source_actor; /* $95 flags select pose bank: Bruce0/Yamo1/Kage2 */
    unsigned char source_canonical,source_state,source_counter,source_wait,source_pose,source_mask;
} BlGame;
/* Passive combat laboratory only: values are NOT measured enemy rules. */
typedef struct {
    BlCoord x,y;
    unsigned char health,invulnerable,respawn;
    unsigned short hits;
    unsigned short stomps;
} BlTarget;

extern const BlPlatform bl_platforms[];
extern const unsigned short bl_platform_count;
extern const BlClimbable bl_climbables[];
extern const unsigned short bl_climbable_count;
const BlGeometry *bl_geometry(const BlGame *game);
void bl_reset(BlGame *game);
void bl_step(BlGame *game, unsigned char input);
void bl_step_npc(BlGame *game,unsigned char input);
void bl_step_npc_ai(BlGame *game,unsigned char input);
/* Spawn-only BF0/16/18 countdown, with the ordinary black/history prefix. */
void bl_step_npc_entry(BlGame *game,unsigned char *state,unsigned char *counter,long player_x,long mask);
/* Separate observed direction and later fire read; ordinary input uses both. */
void bl_step_phased(BlGame *game, unsigned char input, unsigned char attack_input);
int bl_x(const BlGame *game);
int bl_y(const BlGame *game);
/* Record displacement made by the still separate combat-reaction adapter. */
void bl_record_recoil(BlGame *game,int pixels);
/* $2E4E/$2E10 and $310C: object-pass state reset/selection, before input. */
void bl_moving_net_contact(BlGame *game,long touching);
void bl_target_reset(BlTarget *target);
void bl_target_step(BlTarget *target,const BlGame *game);
int bl_attack_overlaps(const BlGame *game,int x,int feet,int prone);
int bl_contact_kind(const BlGame *game,int x,int feet,int prone);

#endif
