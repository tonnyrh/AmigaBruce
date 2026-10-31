#include "presentation.h"

void bl_visual_reset(BlVisual *v,const BlGame *g) {
    v->x=v->start_x=v->target_x=g->x;
    v->y=v->start_y=v->target_y=g->y;
    v->elapsed=0;v->duration=0;
}

void bl_visual_target(BlVisual *v,const BlGame *g,unsigned char previous_state) {
    /* The three waiting logic steps must not restart the same visual segment. */
    if(v->target_x==g->x && v->target_y==g->y)return;
    v->start_x=v->x;v->start_y=v->y;
    v->target_x=g->x;v->target_y=g->y;v->elapsed=0;
    v->duration=(g->state==BL_CLIMB ||
        (previous_state==BL_CLIMB && g->state==BL_GROUND))?12:3;
}

void bl_visual_frame(BlVisual *v) {
    if(v->elapsed>=v->duration)return;
    ++v->elapsed;
    v->x=(BlCoord)(v->start_x+(v->target_x-v->start_x)*v->elapsed/v->duration);
    v->y=(BlCoord)(v->start_y+(v->target_y-v->start_y)*v->elapsed/v->duration);
}

unsigned char bl_visual_pose(const BlGame *g,unsigned char staff){
    if(g->prone)return BL_POSE_PRONE;
    if(g->state==BL_CLIMB)return (unsigned char)(BL_POSE_CLIMB+((bl_y(g)/2)&3));
    if(staff)return staff>=8?BL_POSE_WINDUP:staff>=3?BL_POSE_STRIKE:BL_POSE_RECOVER;
    if(g->attack==BL_FLYING_KICK)return g->attack_phase<2?BL_POSE_KICK_PREP:
        g->attack_phase<=10?BL_POSE_KICK:BL_POSE_KICK_END;
    if(g->attack==BL_PUNCH)return g->attack_phase==0?BL_POSE_WINDUP:
        g->attack_phase<3?BL_POSE_STRIKE:BL_POSE_RECOVER;
    if(g->state==BL_AIR)return BL_POSE_KICK_PREP;
    if(g->walk_steps)return (unsigned char)((bl_x(g)/3)&3);
    return BL_POSE_IDLE;
}

unsigned char bl_visual_face(const BlGame *g,unsigned char pose,int kind){
    /* Back-facing climbing is independent of combat facing. The generated
     * Bruce atlas repeated one side; reflect its reach/transfer for the
     * opposite half-cycle in the renderer, as with ordinary facing. */
    if(g->state==BL_CLIMB)return (unsigned char)(kind==2 && pose>=6?0:1);
    return g->facing;
}
