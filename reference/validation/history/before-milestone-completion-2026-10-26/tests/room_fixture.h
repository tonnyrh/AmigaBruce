#ifndef BRUCE_ROOM_FIXTURE_H
#define BRUCE_ROOM_FIXTURE_H
/* Ordinary joystick input: collect one lamp, use the upper exit, return.
 * No test teleports or gameplay RAM writes. 300 steps = 900 PAL fields. */
static unsigned char room_fixture_input(unsigned short step){
    static const unsigned short ends[]={3,13,33,58,158,166,175,177,193,217,237};
    static const unsigned char inputs[]={BL_LEFT,BL_UP,0,BL_RIGHT,BL_UP,0,
        BL_RIGHT,BL_RIGHT|BL_UP,0,BL_RIGHT,BL_LEFT};
    unsigned short i;
    for(i=0;i<11;i++)if(step<ends[i])return inputs[i];
    return 0;
}
#endif
