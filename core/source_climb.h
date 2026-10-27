#ifndef BRUCE_SOURCE_CLIMB_H
#define BRUCE_SOURCE_CLIMB_H
#include "source_wall.h"
/* Ready, counter-zero Bruce direction dispatch with B6&4 and without B6&8.
 * $1C68/history/animation prefix and the $0106 wait belong to the caller.
 * Input uses game.h bits. Returns the source $1FC4 sound-call condition. */
long bl_source_climb_step(BlSourceActor *actor,long input,long fire);
unsigned char bl_source_climb_pose(const BlSourceActor *actor,long previous_pose);
/* $2187-$2234: tile $62 selects state23, not a combat reaction. AD is
 * independent of $0106; AA keeps the pose during carry-only steps. */
long bl_source_moving_net_step(BlSourceActor *actor,unsigned char *delay,
    unsigned char *hold,long input,long contact,long phase,long reverse);
#endif
