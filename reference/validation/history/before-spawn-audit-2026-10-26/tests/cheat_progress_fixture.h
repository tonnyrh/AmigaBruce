#ifndef BRUCE_CHEAT_PROGRESS_FIXTURE_H
#define BRUCE_CHEAT_PROGRESS_FIXTURE_H
#include "../core/session.h"
#include "../core/c64_rooms.h"
#define CHEAT_CHECK(q) do{if(!(q))return __LINE__;}while(0)
static unsigned short cheat_room_case(unsigned char target){
    BlSession s;BlOptions o;BlCombat w;BlProgress p;unsigned char room;
    bl_options_reset(&o);o.debug=1;o.start_room=target;bl_session_start(&s,&o,&p,&w);
    CHEAT_CHECK(p.room==target && !p.score && !p.pickups && w.lives==4);
    for(room=0;room<20;room++){
        unsigned char count=bl_room(room)->lantern_count;
        unsigned short mask=(unsigned short)((1U<<count)-1);
        CHEAT_CHECK(bl_c64_remaining(room)==(room<target?0:count));
        CHEAT_CHECK(bl_c64_collected(room)==(room<target?mask:0));
        CHEAT_CHECK(p.collected[room]==(room<target?mask:0));
        CHEAT_CHECK(s.saved[0].collected[room]==p.collected[room] && s.saved[1].collected[room]==p.collected[room]);
        CHEAT_CHECK(s.source[0][room+2]==bl_c64_remaining(room) && s.source[1][room+2]==bl_c64_remaining(room));
    }
    CHEAT_CHECK(!(bl_c64_audio_requests()&(1U<<14))); /* No fake $8E pickups. */
    return 0;
}
static unsigned short cheat_progress_fixture_run(void){
    BlSession s;BlOptions o;BlCombat w;BlProgress p;unsigned short failure,mask;unsigned char i;
    failure=cheat_room_case(2);if(failure)return failure;
    failure=cheat_room_case(9);if(failure)return failure;
    failure=cheat_room_case(19);if(failure)return failure;
    bl_options_reset(&o);bl_session_start(&s,&o,&p,&w);
    CHEAT_CHECK(bl_c64_collect(2,10));p.collected[0]=bl_c64_collected(0);p.score=125;p.pickups=1;w.lives=3;
    bl_session_jump(&s,&p,&w,9);
    CHEAT_CHECK(p.room==9 && p.score==125 && p.pickups==1 && w.lives==3 && s.lives[0]==3);
    CHEAT_CHECK(bl_c64_remaining(0)==0 && p.collected[0]==63 && s.saved[0].collected[0]==63);
    CHEAT_CHECK(bl_c64_collect(bl_room(9)->lanterns[0].column,bl_room(9)->lanterns[0].row));
    p.collected[9]=mask=bl_c64_collected(9);bl_session_jump(&s,&p,&w,9);
    CHEAT_CHECK(p.collected[9]==mask && bl_c64_collected(9)==mask && bl_c64_remaining(9)==4);
    bl_session_jump(&s,&p,&w,3);CHEAT_CHECK(!bl_c64_remaining(3) && p.collected[3]==3);
    bl_session_jump(&s,&p,&w,255);CHEAT_CHECK(p.room==3 && p.score==125 && w.lives==3);
    /* Both players start with the chosen prefix. A later live cheat belongs
     * to the current player and must not complete the other player's lamps. */
    bl_options_reset(&o);o.debug=1;o.start_room=9;o.players=2;bl_session_start(&s,&o,&p,&w);
    CHEAT_CHECK(bl_c64_collect(bl_room(9)->lanterns[0].column,bl_room(9)->lanterns[0].row));
    p.collected[9]=mask=bl_c64_collected(9);
    bl_combat_hazard(&w,0);for(i=0;i<16;i++)bl_session_step(&s,&p,&w,0,0);
    CHEAT_CHECK(s.current==1 && p.room==9 && !p.collected[9] && !bl_c64_remaining(8) && bl_c64_remaining(9)==5);
    bl_session_jump(&s,&p,&w,19);
    bl_combat_hazard(&w,0);for(i=0;i<16;i++)bl_session_step(&s,&p,&w,0,0);
    CHEAT_CHECK(s.current==0 && p.room==9 && p.collected[9]==mask && bl_c64_remaining(9)==4 && !p.collected[10]);
    /* Inspection fixtures keep raw source progress, and normal starts stay
     * untouched. The cheat is deliberately separate from this API. */
    bl_options_reset(&o);bl_session_start(&s,&o,&p,&w);
    bl_progress_inspect_room(&p,&w,19);
    CHEAT_CHECK(bl_c64_remaining(0)==6 && !p.collected[0]);
    return 0;
}
#undef CHEAT_CHECK
#endif
