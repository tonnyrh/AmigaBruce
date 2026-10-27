#ifndef BRUCE_SOURCE_WALL_H
#define BRUCE_SOURCE_WALL_H
/* $4F57..$4FDA: current movement plus ten records, four directions/actor.
 * Counts are C64 helper units: one vertical pixel, two horizontal pixels. */
typedef struct {
    unsigned char moves[11][4];
    unsigned char state,counter,previous,animation,pose,tracked,contact;
} BlSourceWall;
typedef struct {
    unsigned char x,y,facing,state,counter,previous,animation,wait,pose_lock;
} BlSourceActor;
void bl_source_wall_reset(BlSourceWall *wall);
/* $1C6B-$1C9A history prefix, shared by ordinary NPC motion and recoil. */
void bl_source_wall_age(BlSourceWall *wall);
/* One ready actor entry $1C68. 0=normal dispatch,1=recovery,2=room re-entry.
 * The source $0106 wait is handled by the caller before this entry. */
long bl_source_wall_step(BlSourceWall *wall,BlSourceActor *actor,long contact);
void bl_source_wall_record(BlSourceWall *wall,long dx,long dy);
#endif
