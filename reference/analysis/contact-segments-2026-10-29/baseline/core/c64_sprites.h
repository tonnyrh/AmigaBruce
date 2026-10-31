#ifndef BRUCE_C64_SPRITES_H
#define BRUCE_C64_SPRITES_H
#include "combat.h"
/* Source inputs to $2780. This pure selector does not implement movement. */
typedef struct {
    unsigned char state,counter,facing,contact,previous,width,second_width,aa,locked;
} BlSourcePose;
unsigned char bl_source_pose(const BlSourcePose *input);
/* Temporary bridge from the still partial Amiga actor state to source art.
 * It never writes back into physics, combat, object contacts or AI. */
typedef struct {
    BlCoord x,y;
    unsigned char pose,initialized;
} BlC64Sprite;
void bl_c64_sprite_step(BlC64Sprite *sprite,const BlFighter *fighter,int kind);
#endif
