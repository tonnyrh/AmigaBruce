#include <assert.h>
#include <stdio.h>
#include "../core/presentation.h"

void test_visual(void) {
    BlGame game;
    BlVisual visual;
    int frame,changes=0;
    BlCoord previous;
    bl_reset(&game);game.y=186*16;game.state=BL_CLIMB;
    bl_visual_reset(&visual,&game);
    game.y=183*16;bl_visual_target(&visual,&game,BL_CLIMB);
    for(frame=0;frame<12;frame++){
        previous=visual.y;
        if(frame%3==0)bl_visual_target(&visual,&game,BL_CLIMB);
        bl_visual_frame(&visual);
        assert(visual.y<=previous&&visual.y>=game.y);
        assert(previous-visual.y<=6); /* At most 3/8 pixel, no three-pixel burst. */
        if(previous!=visual.y)++changes;
    }
    assert(changes==12&&visual.y==game.y&&visual.x==game.x);
    for(frame=0;frame<40;frame++)bl_visual_frame(&visual);
    assert(visual.y==game.y);
    /* Leaving the net retargets from the drawn position and settles in 3 fields. */
    game.y=180*16;bl_visual_target(&visual,&game,BL_CLIMB);
    bl_visual_frame(&visual);previous=visual.y;
    game.state=BL_AIR;game.y=190*16;
    bl_visual_target(&visual,&game,BL_CLIMB);
    assert(visual.y==previous&&visual.duration==3);
    for(frame=0;frame<3;frame++){
        bl_visual_frame(&visual);assert(visual.y>=previous&&visual.y<=game.y);
        previous=visual.y;
    }
    assert(visual.y==game.y&&game.state==BL_AIR);
    /* Both sides of Bruce's reach are selected independent of facing;
     * stopping freezes it, descending visits the same phases in reverse. */
    for(frame=0;frame<4;frame++){
        unsigned char pose;
        game.state=BL_CLIMB;game.y=(BlCoord)((160+frame*2)*16);game.facing=0;
        pose=bl_visual_pose(&game,0);
        assert(pose==BL_POSE_CLIMB+frame);
        assert(bl_visual_face(&game,pose,2)==(frame<2?1:0));
        game.facing=1;assert(bl_visual_pose(&game,0)==pose);
        assert(bl_visual_face(&game,pose,2)==(frame<2?1:0));
    }
    game.state=BL_GROUND;game.walk_steps=0;
    assert(bl_visual_pose(&game,0)==BL_POSE_IDLE);
    assert(bl_visual_pose(&game,9)==BL_POSE_WINDUP);
    assert(bl_visual_pose(&game,4)==BL_POSE_STRIKE);
    assert(bl_visual_pose(&game,1)==BL_POSE_RECOVER);
    puts("PASS: smooth 12-field climb presentation, idle stability, 3-field detach retarget");
}
