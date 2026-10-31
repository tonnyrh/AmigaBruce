#ifndef BRUCE_ROOMS_H
#define BRUCE_ROOMS_H
#include "combat.h"
enum { BL_ROOM_COUNT=20, BL_PLAYABLE_ROOMS=20, BL_MAX_LANTERNS=13 };
enum { BL_OPEN_R02_HATCH=1, BL_OPEN_R03_EAST=2,
    BL_OPEN_R06_RETURN=4, BL_OPEN_R06_WEST=8 };
typedef struct { unsigned char column,row; } BlLantern;
typedef struct {
    unsigned char target;
    signed short entry_x,entry_y;
    unsigned char column,row,valid;
} BlDoor;
typedef struct {
    signed short entry_x,entry_y,enemy_x,enemy_y;
    unsigned char enemies_enabled,lantern_count;
    BlLantern lanterns[BL_MAX_LANTERNS];
    BlDoor doors[4];
    unsigned char enemy_exit_wait[2]; /* Yamo/Ninja room-local full counters. */
} BlRoomFacts;
typedef struct {
    unsigned short collected[BL_ROOM_COUNT];
    unsigned short transitions,revision,pickups;
    unsigned long score;
    unsigned char room,blocked_exit,openings;
} BlProgress;
const BlRoomFacts *bl_room(unsigned char room);
unsigned char bl_progress_room_openings(const BlProgress *progress,unsigned char room);
/* Includes the source-defined dynamic doors omitted from the base tile map. */
void bl_progress_door(const BlProgress *progress,int slot,BlDoor *door);
int bl_enemy_leave_room(BlFighter *fighter,int kind);
void bl_progress_reset(BlProgress *progress);
void bl_progress_step(BlProgress *progress,BlCombat *world,unsigned char input);
/* Explicit inspection mode; does not claim natural access to every room. */
void bl_progress_inspect_room(BlProgress *progress,BlCombat *world,unsigned char room);
/* Exposed for deterministic interaction fixtures, not a player teleport key. */
void bl_progress_contacts(BlProgress *progress,BlCombat *world,unsigned char input);
#endif
