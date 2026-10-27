#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../core/rooms.h"
#include "room_fixture.h"
#include "gate_fixture.h"
static int floor_at(unsigned char room,int x,int y){
    BlGame g;const BlGeometry *geometry;int i;
    bl_reset(&g);g.room=room;geometry=bl_geometry(&g);
    for(i=0;i<geometry->platform_count;i++){
        const BlPlatform *floor=&geometry->platforms[i];
        if(x>=floor->x0 && x<floor->x1 && y==floor->y)return 1;
    }
    return 0;
}
void test_rooms(void){
    BlProgress p,q;BlCombat w,v;int i,j;
    const BlRoomFacts *r;
    r=bl_room(0);
    assert(r->enemy_exit_wait[BL_NINJA]==160 && r->enemy_exit_wait[BL_YAMO]==238);
    assert(r->entry_x==28 && r->entry_y==196 && r->enemy_x==294 && r->enemy_y==98);
    assert(r->lanterns[r->lantern_count-1].row==10);
    for(i=0;i<20;i++){
        r=bl_room((unsigned char)i);assert(r->lantern_count<=13);
        for(j=0;j<4;j++)if(r->doors[j].valid){
            assert(r->doors[j].target<20 && r->doors[j].entry_x>=0 && r->doors[j].entry_x<320);
            if(i<2)assert(r->doors[j].row<=8);
            if(i<2 && r->doors[j].target<2){
                const BlDoor *door=&r->doors[j];
                /* Rendered floors use this same geometry: both sides of a
                 * horizontal connection must meet at the native arrival Y. */
                assert(floor_at((unsigned char)i,door->column==0?4:314,door->entry_y));
                assert(floor_at(door->target,door->entry_x,door->entry_y));
            }
        }
    }
    bl_progress_reset(&p);bl_combat_reset(&w);
    /* Departures are NPC-local, including the closed-for-player R03 link.
     * A solid bottom-floor boundary must not remove an enemy. */
    w.enemy[BL_NINJA].active=1;w.enemy[BL_NINJA].body.room=1;
    w.enemy[BL_NINJA].body.x=302*16;w.enemy[BL_NINJA].body.y=98*16;
    assert(bl_enemy_leave_room(&w.enemy[BL_NINJA],BL_NINJA));
    assert(!w.enemy[BL_NINJA].active && p.room==0 && !p.transitions && !w.defeats);
    w.enemy[BL_NINJA].active=1;w.enemy[BL_NINJA].body.y=196*16;
    assert(!bl_enemy_leave_room(&w.enemy[BL_NINJA],BL_NINJA));
    assert(w.enemy[BL_NINJA].active);
    bl_combat_reset(&w);
    w.player.body.x=16*16;w.player.body.y=196*16;
    bl_progress_contacts(&p,&w,0);assert(!p.pickups);
    w.player.body.y=184*16;w.player.body.state=BL_AIR;
    bl_progress_contacts(&p,&w,0);assert(p.pickups==1 && p.collected[0]==4 && p.score==125);
    bl_progress_contacts(&p,&w,0);assert(p.pickups==1 && p.score==125);
    /* Native upper exit: R01 -> R02 x6/y98; do not auto-bounce on arrival. */
    w.player.body.x=298*16;w.player.body.y=98*16;
    bl_progress_contacts(&p,&w,BL_RIGHT);
    assert(p.room==1 && p.transitions==1 && bl_x(&w.player.body)==6 && bl_y(&w.player.body)==98);
    assert(w.player.body.room==1 && !w.enemy[0].active && !w.enemy[1].active);
    bl_progress_contacts(&p,&w,BL_RIGHT);assert(p.room==1);
    bl_progress_contacts(&p,&w,BL_LEFT);
    assert(p.room==0 && bl_x(&w.player.body)==298 && bl_y(&w.player.body)==98);
    assert(p.collected[0]==4 && p.pickups==1);
    /* Both continuous lanes retain the exact foot height across either
     * direction: upper Y98 and lower Y146, with no arrival correction. */
    for(j=0;j<2;j++){
        bl_progress_reset(&p);bl_combat_reset(&w);
        w.player.body.x=298*16;w.player.body.y=(j?146:98)*16;
        bl_progress_contacts(&p,&w,BL_RIGHT);
        assert(p.room==1 && bl_y(&w.player.body)==(j?146:98));
        for(i=0;i<8;i++)bl_progress_step(&p,&w,0);
        assert(w.player.body.state==BL_GROUND && bl_y(&w.player.body)==(j?146:98));
        bl_progress_step(&p,&w,BL_LEFT);
        bl_progress_contacts(&p,&w,BL_LEFT);
        assert(p.room==0 && bl_y(&w.player.body)==(j?146:98));
        assert(w.player.body.previous_y==w.player.body.y);
        for(i=0;i<8;i++)bl_progress_step(&p,&w,0);
        assert(w.player.body.state==BL_GROUND && bl_y(&w.player.body)==(j?146:98));
    }
    /* The previously closed R03 connection now uses its native table entry. */
    p.room=1;w.player.body.room=1;w.player.body.x=298*16;w.player.body.y=98*16;
    bl_progress_contacts(&p,&w,BL_RIGHT);
    assert(p.room==2 && !p.blocked_exit && bl_x(&w.player.body)==8);
    /* Every room has a distinct geometry and is available in inspection
     * mode. Inspection is explicitly not proof of natural reachability. */
    for(j=0;j<BL_ROOM_COUNT;j++){
        const BlGeometry *geometry;
        bl_progress_inspect_room(&p,&w,(unsigned char)j);
        geometry=bl_geometry(&w.player.body);
        assert(p.room==j && w.player.body.room==j && geometry->platform_count);
        if(j>=2){
            BlGame first=w.player.body;first.room=0;
            assert(geometry!=bl_geometry(&first));
        }
        for(i=0;i<180;i++)bl_progress_step(&p,&w,0);
        assert(p.room==j && w.player.body.room==j);
        if(!bl_room((unsigned char)j)->enemies_enabled)
            assert(!w.enemy[0].active && !w.enemy[1].active);
    }
    /* Player death resets room-local enemies, not just the player body.
     * Lantern reset on death remains a separate, unmeasured rule. */
    bl_progress_reset(&p);bl_combat_reset(&w);
    w.player.active=0;w.player.respawn=1;
    w.enemy[0].active=1;w.enemy[0].body.x=100*16;
    bl_progress_step(&p,&w,0);
    assert(w.player.active && !w.enemy[0].active && w.enemy[0].respawn==232);
    assert(bl_x(&w.enemy[0].body)==294 && w.enemy[0].health==20);
    bl_progress_reset(&p);bl_combat_reset(&w);
    for(i=0;i<300;i++)bl_progress_step(&p,&w,room_fixture_input((unsigned short)i));
    assert(p.transitions==2 && p.pickups==1 && p.collected[0]==4 && p.room==0);
    printf("M4_900 room_transitions=%u lantern_pickups=%u score=%lu final_room=%u final_x=%d final_y=%d\n",
        p.transitions,p.pickups,p.score,p.room,bl_x(&w.player.body),bl_y(&w.player.body));
    /* The exit in R03 is not unlocked by its own ten lamps. First collect
     * the22 lamps in R01-R03, enter R06, clear R07 and use the return. */
    bl_progress_reset(&p);bl_combat_reset(&w);
    {
        unsigned short checks=0;
        for(i=0;i<300;i++){
            unsigned char input=gate_fixture_prepare(&p,&w,(unsigned short)i);
            bl_progress_step(&p,&w,input);
            checks|=gate_fixture_check(&p,&w,(unsigned short)i);
        }
        assert(checks==127 && p.transitions==3 && p.pickups==31);
        printf("GATES_900 gate_checks=%u room_transitions=%u lantern_pickups=%u score=%lu\n",checks,p.transitions,p.pickups,p.score);
    }
    /* Every single remaining opening prerequisite keeps the hatch shut. */
    for(i=0;i<22;i++){
        int room=i<6?0:i<12?1:2,index=i<6?i:i<12?i-6:i-12;
        bl_progress_reset(&p);bl_combat_reset(&w);
        p.collected[0]=63;p.collected[1]=63;p.collected[2]=1023;
        p.collected[room]&=(unsigned short)~(1u<<index);
        bl_progress_inspect_room(&p,&w,1);
        gate_position(&w,150,196);bl_progress_contacts(&p,&w,BL_DOWN);
        assert(!(p.openings&BL_OPEN_R02_HATCH) && p.room==1);
    }
    for(i=0;i<8;i++){
        bl_progress_reset(&p);bl_combat_reset(&w);
        p.collected[6]=(unsigned short)(255u&~(1u<<i));p.collected[5]=0x14;
        bl_progress_inspect_room(&p,&w,2);
        gate_position(&w,298,196);bl_progress_contacts(&p,&w,BL_RIGHT);
        assert(p.room==2 && !(p.openings&(BL_OPEN_R03_EAST|BL_OPEN_R06_RETURN)));
    }
    /* Clearing R07 alone opens R03, but not the R06 upper return. */
    bl_progress_reset(&p);bl_combat_reset(&w);p.collected[6]=255;
    bl_progress_inspect_room(&p,&w,5);gate_position(&w,272,50);
    bl_progress_contacts(&p,&w,0);
    assert(p.room==5 && !(p.openings&BL_OPEN_R06_RETURN));
    p.collected[5]=0x10;bl_progress_inspect_room(&p,&w,5);gate_position(&w,272,50);
    bl_progress_contacts(&p,&w,0);
    assert(p.room==1 && bl_x(&w.player.body)==152 && bl_y(&w.player.body)==102);
    /* The separate lower-left lamp opens R06 west independently. */
    bl_progress_reset(&p);bl_combat_reset(&w);p.collected[5]=0x40;
    bl_progress_inspect_room(&p,&w,5);gate_position(&w,4,196);
    bl_progress_contacts(&p,&w,BL_LEFT);
    assert(p.room==4 && bl_x(&w.player.body)==288 && bl_y(&w.player.body)==81);
    memset(&p,0,sizeof(p));memset(&q,0,sizeof(q));
    memset(&w,0,sizeof(w));memset(&v,0,sizeof(v));
    bl_progress_reset(&p);bl_progress_reset(&q);bl_combat_reset(&w);bl_combat_reset(&v);
    for(i=0;i<4000;i++){
        unsigned char input=(unsigned char)(i%200<60?BL_RIGHT:i%200<120?BL_UP:BL_LEFT);
        bl_progress_step(&p,&w,input);bl_progress_step(&q,&v,input);
        assert(!memcmp(&p,&q,sizeof(p)) && !memcmp(&w,&v,sizeof(w)));
        assert(p.room<BL_ROOM_COUNT && w.player.body.room==p.room);
    }
    puts("PASS: 20 room inspection, disabled enemies, NPC reset on death, pickups, first-room return and 4000 deterministic progression steps");
}
