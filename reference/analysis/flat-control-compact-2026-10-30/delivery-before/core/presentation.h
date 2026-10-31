#ifndef BRUCE_PRESENTATION_H
#define BRUCE_PRESENTATION_H
#include "game.h"

/* Presentation only: never feed these interpolated coordinates to collision. */
typedef struct {
    BlCoord x,y,start_x,start_y,target_x,target_y;
    unsigned char elapsed,duration;
} BlVisual;
void bl_visual_reset(BlVisual *visual,const BlGame *game);
void bl_visual_target(BlVisual *visual,const BlGame *game,unsigned char previous_state);
void bl_visual_frame(BlVisual *visual);
/* Atlas order. Presentation changes never alter attack/contact state. */
enum { BL_POSE_RUN=0, BL_POSE_CLIMB=4, BL_POSE_IDLE=8,
    BL_POSE_WINDUP=9, BL_POSE_STRIKE=10, BL_POSE_RECOVER=11,
    BL_POSE_KICK_PREP=12, BL_POSE_KICK=13, BL_POSE_KICK_END=14,
    BL_POSE_PRONE=15, BL_POSE_COUNT=16 };
unsigned char bl_visual_pose(const BlGame *game,unsigned char staff);
unsigned char bl_visual_face(const BlGame *game,unsigned char pose,int kind);
#endif
