#include <assert.h>
#include <stdio.h>
#include <stdint.h>
#include "../core/game.h"

static void repeat(BlGame *g,unsigned char input,int count){while(count--)bl_step(g,input);}
void test_visual(void);
void test_combat(void);
void test_rooms(void);
int main(void) {
    BlGame g,other;
    BlTarget target;
    int n,top;
    /* Measured attack timing; test-target damage/boxes remain lab rules. */
    bl_reset(&g);bl_step(&g,BL_FIRE);assert(g.attack==BL_PUNCH);
    repeat(&g,0,3);assert(g.attack==BL_PUNCH);
    bl_step(&g,0);assert(g.attack==BL_ATTACK_NONE);
    bl_reset(&g);repeat(&g,BL_FIRE,8);assert(g.attack==BL_ATTACK_NONE);
    bl_step(&g,BL_FIRE);assert(g.attack==BL_PUNCH);
    bl_reset(&g);g.x=100*16;bl_target_reset(&target);
    bl_step(&g,BL_FIRE);bl_step(&g,0);
    assert(bl_attack_overlaps(&g,112,196,0));
    assert(!bl_attack_overlaps(&g,112,196,1));
    assert(!bl_attack_overlaps(&g,80,196,0));
    bl_target_step(&target,&g);assert(target.health==2&&target.hits==1&&target.x==120);
    bl_target_step(&target,&g);assert(target.hits==1);
    target.invulnerable=0;target.health=1;target.x=112;
    bl_target_step(&target,&g);assert(!target.health&&target.respawn==60);
    for(n=0;n<59;n++)bl_target_step(&target,&g);
    assert(!target.health&&target.respawn==1);
    bl_target_step(&target,&g);assert(target.health==3&&target.x==112);
    bl_reset(&g);g.x=100*16;g.walk_steps=4;bl_step(&g,BL_RIGHT|BL_FIRE);
    assert(g.attack==BL_FLYING_KICK);
    repeat(&g,0,14);assert(g.attack==BL_ATTACK_NONE&&bl_x(&g)==124&&bl_y(&g)==196);
    bl_reset(&g);g.x=100*16;g.walk_steps=4;g.facing=0;bl_step(&g,BL_LEFT|BL_FIRE);
    repeat(&g,0,14);assert(bl_x(&g)==76&&bl_y(&g)==196);
    bl_reset(&g);bl_step(&g,BL_DOWN|BL_FIRE);assert(g.prone&&!g.attack);
    /* A fire read can change after direction was read: preserve both cases. */
    bl_reset(&g);g.walk_steps=4;
    bl_step_phased(&g,BL_RIGHT,BL_FIRE);assert(g.attack==BL_FLYING_KICK&&bl_x(&g)==28);
    bl_reset(&g);g.walk_steps=4;
    bl_step_phased(&g,BL_RIGHT|BL_FIRE,0);assert(!g.attack&&bl_x(&g)==32);
    bl_reset(&g);g.walk_steps=3;
    bl_step_phased(&g,BL_RIGHT,BL_FIRE);assert(!g.attack&&bl_x(&g)==32);
    bl_reset(&g);bl_step(&g,BL_UP|BL_RIGHT|BL_FIRE);
    assert(!g.attack&&g.state==BL_AIR&&g.jump_phase!=255);
    /* Falling contact is separate from a normal jump and cannot hit below/aside. */
    bl_reset(&g);g.x=112*16;g.y=176*16;g.state=BL_AIR;g.velocity_y=2*16;
    assert(bl_contact_kind(&g,112,196,0)==BL_CONTACT_FALL);
    assert(!bl_contact_kind(&g,112,196,1));
    assert(!bl_contact_kind(&g,130,196,0));
    g.velocity_y=-2*16;assert(!bl_contact_kind(&g,112,196,0));
    g.velocity_y=2*16;g.jump_phase=12;assert(!bl_contact_kind(&g,112,196,0));
    g.jump_phase=255;g.y=187*16;assert(!bl_contact_kind(&g,112,196,0));
    g.y=176*16;bl_target_reset(&target);bl_target_step(&target,&g);
    assert(target.stomps==1&&target.hits==1&&target.health==1);
    bl_target_step(&target,&g);assert(target.stomps==1);
    /* Long measured C64 free fall stays at two pixels per three PAL fields. */
    bl_reset(&g);g.x=128*16;g.y=138*16;g.state=BL_AIR;g.velocity_y=2*16;
    for(n=0;n<29;n++){
        int before=bl_y(&g);bl_step(&g,0);assert(bl_y(&g)==before+2);
    }
    assert(g.state==BL_GROUND&&bl_y(&g)==196);
    /* Whole lab route: walk in, punch, flying kick, defeat and respawn. */
    bl_reset(&g);bl_target_reset(&target);
    {
        int defeated=0;
        for(n=0;n<130;n++){
            unsigned char input=n<14?BL_RIGHT:n<30?BL_FIRE:
                n<40?(BL_RIGHT|BL_FIRE):0;
            bl_step(&g,input);bl_target_step(&target,&g);
            if(!target.health)defeated=1;
        }
        assert(defeated&&target.hits>=2&&target.health==3&&!target.respawn);
    }
    bl_reset(&g);repeat(&g,0,120);
    assert(bl_x(&g)==28&&bl_y(&g)==196&&g.state==BL_GROUND);
    repeat(&g,BL_LEFT,200);assert(bl_x(&g)==4);
    repeat(&g,BL_RIGHT,200);assert(bl_x(&g)==314);
    bl_reset(&g);bl_step(&g,BL_UP);assert(g.state==BL_AIR);
    top=bl_y(&g);
    for(n=0;n<80;n++){bl_step(&g,0);if(bl_y(&g)<top)top=bl_y(&g);}
    assert(top<196&&bl_y(&g)==196&&g.state==BL_GROUND);
    /* The measured upper-right ledge is reachable from x198 without a boost. */
    bl_reset(&g);g.x=198*16;g.y=101*16;
    bl_step(&g,BL_RIGHT|BL_UP);repeat(&g,0,24);
    assert(g.state==BL_GROUND&&bl_x(&g)==250&&bl_y(&g)==98);
    /* C64 rules: no post-edge jump allowance, steering or mid-air turn. */
    for(n=0;n<2;n++){
        unsigned char direction=(unsigned char)(n?BL_LEFT:BL_RIGHT);
        unsigned char reverse=(unsigned char)(n?BL_RIGHT:BL_LEFT);
        int edge_x,fall_y;
        bl_reset(&g);g.x=(n?52:212)*16;g.y=(n?152:101)*16;
        other=g;bl_step(&other,(unsigned char)(direction|BL_UP));
        assert(other.jump_phase==1 && other.velocity_y==0);
        bl_step(&g,direction);
        assert(g.state==BL_AIR);edge_x=bl_x(&g);fall_y=bl_y(&g);
        bl_step(&g,(unsigned char)(reverse|BL_UP));
        assert(g.jump_phase==255 && g.velocity_y>0);
        assert(bl_x(&g)==edge_x && bl_y(&g)>fall_y && g.facing==!n);
    }
    /* T06: body support survives past the centre, with symmetric landings.
     * A later jump is still forbidden after the footprint clears the edge. */
    bl_reset(&g);g.x=212*16;g.y=101*16;
    bl_step(&g,0);assert(g.state==BL_GROUND);
    bl_step(&g,BL_UP|BL_RIGHT);assert(g.jump_phase==1);
    bl_reset(&g);g.x=212*16;g.y=98*16;g.state=BL_AIR;g.velocity_y=2*16;
    repeat(&g,0,2);assert(g.state==BL_GROUND&&bl_y(&g)==101);
    bl_reset(&g);g.x=52*16;g.y=149*16;g.state=BL_AIR;g.velocity_y=2*16;
    repeat(&g,0,2);assert(g.state==BL_GROUND&&bl_y(&g)==152);
    /* T10-NET: launched sideways entry auto-grabs; full-body exit drops
     * straight down even when the opposite direction/up is then held. */
    bl_reset(&g);g.x=140*16;g.y=150*16;g.state=BL_AIR;
    g.jump_phase=4;g.jump_direction=1;
    bl_step(&g,BL_RIGHT);assert(g.state==BL_CLIMB&&bl_y(&g)==150);
    for(n=0;n<80&&g.state==BL_CLIMB;n++)bl_step(&g,BL_RIGHT);
    assert(g.state==BL_AIR&&bl_x(&g)>=174);
    top=bl_x(&g);bl_step(&g,BL_LEFT|BL_UP);
    assert(bl_x(&g)==top&&g.jump_phase==255);
    /* Held-up pendulum jumps can reverse at the next ground read, while
     * contrary input during flight cannot turn or steer the active jump. */
    bl_reset(&g);g.x=160*16;
    {
        int starts=0;unsigned char direction=BL_RIGHT;
        for(n=0;n<160;n++){
            unsigned char old_state=g.state,old_facing=g.facing;
            if(g.state==BL_GROUND){direction=(unsigned char)(starts&1?BL_LEFT:BL_RIGHT);++starts;}
            bl_step(&g,(unsigned char)(BL_UP|(old_state==BL_AIR?
                (direction==BL_RIGHT?BL_LEFT:BL_RIGHT):direction)));
            if(old_state==BL_AIR && g.state==BL_AIR)assert(g.facing==old_facing);
        }
        assert(starts>=8);
    }
    bl_reset(&g);g.x=158*16;g.y=160*16;g.state=BL_CLIMB;
    bl_step(&g,BL_UP|BL_RIGHT);assert(bl_x(&g)==158 && bl_y(&g)==157);
    repeat(&g,0,3);bl_step(&g,BL_RIGHT);
    assert(bl_x(&g)==160 && bl_y(&g)==157);
    /* Down lies still even with a diagonal; release stands, up can jump. */
    bl_reset(&g);repeat(&g,BL_DOWN|BL_RIGHT,24);
    assert(g.prone&&bl_x(&g)==28&&bl_y(&g)==196&&g.facing==1);
    repeat(&g,0,3);assert(!g.prone&&g.state==BL_GROUND);
    repeat(&g,BL_DOWN,8);repeat(&g,BL_UP,2);
    assert(!g.prone&&g.state==BL_AIR);
    bl_step(&g,BL_DOWN);assert(!g.prone&&g.state==BL_AIR);
    /* Landing must catch the first crossed surface even at terminal speed. */
    bl_reset(&g);g.x=70*16;g.y=145*16;g.state=BL_AIR;g.velocity_y=8*16;
    bl_step(&g,0);assert(bl_y(&g)==152&&g.state==BL_GROUND);
    /* Pagoda decoration must not behave as a ladder. */
    bl_reset(&g);g.x=70*16;bl_step(&g,BL_UP);assert(g.state==BL_AIR);
    /* Catch the central net with the upper body, then climb in timed actions. */
    bl_reset(&g);g.x=158*16;g.y=186*16;g.state=BL_AIR;bl_step(&g,BL_UP);
    assert(g.state==BL_CLIMB&&bl_y(&g)==186);
    bl_step(&g,BL_UP);assert(bl_y(&g)==183);
    top=bl_y(&g);repeat(&g,0,4);assert(bl_y(&g)==top);
    bl_step(&g,BL_DOWN);assert(g.state==BL_CLIMB&&!g.prone&&bl_y(&g)>top);
    repeat(&g,0,4);
    for(n=0;n<160&&g.state==BL_CLIMB;n++)bl_step(&g,BL_UP);
    assert(bl_y(&g)==101&&g.state==BL_GROUND);
    /* Held up at the top must jump repeatedly, without regrabbing this net. */
    {
        int jumps=0;
        unsigned char state=g.state;
        for(n=0;n<64;n++){
            bl_step(&g,BL_UP);
            if(state==BL_GROUND&&g.state==BL_AIR)++jumps;
            assert(g.state!=BL_CLIMB&&bl_y(&g)<=101);
            state=g.state;
        }
        assert(jumps>=3);
        repeat(&g,0,24);assert(g.state==BL_GROUND&&bl_y(&g)==101);
    }
    repeat(&g,BL_RIGHT,14);assert(g.state==BL_AIR);
    /* Deterministic replay across mixed movement and climb transitions. */
    bl_reset(&g);bl_reset(&other);
    for(n=0;n<1000;n++){
        unsigned char input=n%100<40?BL_RIGHT:n%100<70?BL_UP:BL_LEFT;
        bl_step(&g,input);bl_step(&other,input);
        assert(g.x==other.x&&g.y==other.y&&g.state==other.state);
        assert(bl_x(&g)>=4&&bl_x(&g)<=314&&bl_y(&g)<=196);
    }
    /* Exercise every button combination, counter wrap and rare net transitions. */
    {
        uint32_t seed=0x42525543;
        bl_reset(&g);g.step=65535;bl_step(&g,0);assert(g.step==0);
        for(n=0;n<100000;n++){
            seed=seed*1664525u+1013904223u;
            bl_step(&g,(unsigned char)((seed>>16)&31));
            assert(g.x>=4*16&&g.x<=314*16&&g.y>=0&&g.y<=196*16);
            assert(g.state<=BL_CLIMB&&g.climb_wait<=3);
            assert(g.jump_direction>=-1&&g.jump_direction<=1);
        }
    }
    puts("PASS: idle, bounds, jump/landing, right-ledge crossing, prone, swept collision, climb/detach, deterministic replay");
    puts("These are prototype contracts, not C64 parity tests.");
    puts("PASS: 100000 mixed-input steps, state/bounds invariants and step-counter wrap");
    test_visual();
    test_combat();
    test_rooms();
    return 0;
}
