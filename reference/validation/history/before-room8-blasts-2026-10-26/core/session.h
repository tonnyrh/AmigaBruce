#ifndef BRUCE_SESSION_H
#define BRUCE_SESSION_H
#include "rooms.h"
typedef struct {
    unsigned char players,human_yamo,start_room,infinite_lives,invincible,debug;
} BlOptions;
typedef struct {
    BlOptions options;
    BlProgress saved[2];
    unsigned char source[2][28];
    signed short lives[2];
    unsigned char current,over;
} BlSession;
void bl_options_reset(BlOptions *options);
void bl_session_start(BlSession *session,const BlOptions *options,BlProgress *progress,BlCombat *world);
void bl_session_step(BlSession *session,BlProgress *progress,BlCombat *world,unsigned char input,unsigned char yamo_input);
void bl_session_jump(BlSession *session,BlProgress *progress,BlCombat *world,unsigned char room);
#endif
